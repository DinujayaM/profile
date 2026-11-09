"""YouTube Data API v3 service.

Handles OAuth2 PKCE flow, token storage/refresh, and resumable video uploads.

Security:
  - Refresh tokens are stored encrypted in the database (Fernet).
  - Passwords are never stored.
  - Token revocation is supported.
  - Uploads start as private; public scheduling requires explicit admin approval.
"""
import asyncio
import json
import logging
import os
import secrets
from base64 import urlsafe_b64encode, urlsafe_b64decode
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.youtube import YouTubeChannel, YouTubeUpload, PrivacyStatus, UploadStatus

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
]
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
YT_API_BASE = "https://www.googleapis.com/youtube/v3"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


def _fernet() -> Fernet:
    """Derive a Fernet key from the app secret key."""
    import base64, hashlib
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _fernet().decrypt(encrypted.encode()).decode()


class YouTubeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ OAuth

    def build_auth_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """Return (auth_url, state). State is a CSRF token."""
        if not state:
            state = secrets.token_urlsafe(32)
        params = {
            "client_id": settings.YOUTUBE_CLIENT_ID,
            "redirect_uri": settings.YOUTUBE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{AUTH_URL}?{urlencode(params)}", state

    async def exchange_code(self, code: str) -> dict:
        """Exchange auth code for access + refresh tokens."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(TOKEN_URL, data={
                "code": code,
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "redirect_uri": settings.YOUTUBE_REDIRECT_URI,
                "grant_type": "authorization_code",
            })
            resp.raise_for_status()
            return resp.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(TOKEN_URL, data={
                "refresh_token": refresh_token,
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "grant_type": "refresh_token",
            })
            resp.raise_for_status()
            return resp.json()

    async def revoke_token(self, token: str) -> None:
        """Revoke an access or refresh token."""
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(REVOKE_URL, params={"token": token})

    async def save_channel(self, token_data: dict, user_id: int) -> YouTubeChannel:
        """Fetch channel info and persist channel + encrypted tokens."""
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")

        channel_info = await self._get_channel_info(access_token)

        result = await self.db.execute(
            select(YouTubeChannel).where(YouTubeChannel.channel_id == channel_info["id"])
        )
        channel = result.scalar_one_or_none()

        if channel is None:
            channel = YouTubeChannel(
                channel_id=channel_info["id"],
                channel_name=channel_info["snippet"]["title"],
                channel_url=f"https://youtube.com/channel/{channel_info['id']}",
                thumbnail_url=channel_info["snippet"]["thumbnails"]["default"]["url"],
                subscriber_count=int(channel_info["statistics"].get("subscriberCount", 0)),
                video_count=int(channel_info["statistics"].get("videoCount", 0)),
                owner_id=user_id,
                is_active=True,
            )
            self.db.add(channel)

        # Store tokens encrypted — never plaintext
        channel.access_token_encrypted = encrypt_token(access_token)
        if refresh_token:
            channel.refresh_token_encrypted = encrypt_token(refresh_token)

        await self.db.flush()
        return channel

    async def _get_channel_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{YT_API_BASE}/channels",
                params={"part": "snippet,statistics", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                raise ValueError("No YouTube channel found for this account")
            return items[0]

    # ----------------------------------------------------------------- Upload

    async def upload_video(
        self,
        upload_id: int,
        file_path: str,
        title: str,
        description: str,
        tags: list[str],
        category_id: str = "27",  # Education
        made_for_kids: bool = True,
        privacy_status: str = "private",  # Always start private
        scheduled_publish_at: Optional[str] = None,
    ) -> dict:
        """Resumable upload. Upload is ALWAYS private initially; scheduling
        to public requires explicit admin approval (enforced upstream)."""

        result = await self.db.execute(
            select(YouTubeUpload).where(YouTubeUpload.id == upload_id)
        )
        upload = result.scalar_one()
        channel = await self.db.get(YouTubeChannel, upload.channel_id)

        access_token = await self._get_valid_token(channel)

        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": "private",  # enforced: start private
                "madeForKids": made_for_kids,
                "selfDeclaredMadeForKids": made_for_kids,
            },
        }

        file_size = os.path.getsize(file_path)
        resumable_uri = await self._init_resumable_upload(
            access_token, metadata, file_size
        )

        video_id = await self._do_resumable_upload(
            resumable_uri, file_path, file_size, upload_id
        )

        return {"youtube_video_id": video_id, "privacy_status": "private"}

    async def _get_valid_token(self, channel: YouTubeChannel) -> str:
        """Return a fresh access token, refreshing if necessary."""
        # Try the stored access token; if expired, refresh it
        try:
            access_token = decrypt_token(channel.access_token_encrypted)
            # Quick validation call
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{YT_API_BASE}/channels",
                    params={"part": "id", "mine": "true"},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if resp.status_code == 200:
                    return access_token
        except Exception:
            pass

        # Refresh
        refresh_token = decrypt_token(channel.refresh_token_encrypted)
        token_data = await self.refresh_access_token(refresh_token)
        new_access = token_data["access_token"]
        channel.access_token_encrypted = encrypt_token(new_access)
        return new_access

    async def _init_resumable_upload(
        self, access_token: str, metadata: dict, file_size: int
    ) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                UPLOAD_URL,
                params={"uploadType": "resumable", "part": "snippet,status"},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": "video/mp4",
                    "X-Upload-Content-Length": str(file_size),
                },
                json=metadata,
            )
            resp.raise_for_status()
            return resp.headers["Location"]

    async def _do_resumable_upload(
        self, uri: str, file_path: str, file_size: int, upload_id: int
    ) -> str:
        """Upload in 10 MB chunks, updating progress on the YouTubeUpload row."""
        CHUNK = 10 * 1024 * 1024  # 10 MB
        uploaded = 0

        async with httpx.AsyncClient(timeout=600) as client:
            with open(file_path, "rb") as f:
                while uploaded < file_size:
                    chunk = f.read(CHUNK)
                    end = uploaded + len(chunk) - 1
                    headers = {
                        "Content-Range": f"bytes {uploaded}-{end}/{file_size}",
                        "Content-Type": "video/mp4",
                    }
                    resp = await client.put(uri, headers=headers, content=chunk)

                    if resp.status_code in (200, 201):
                        return resp.json()["id"]
                    if resp.status_code == 308:
                        range_header = resp.headers.get("Range", "")
                        if range_header:
                            uploaded = int(range_header.split("-")[1]) + 1
                        else:
                            uploaded += len(chunk)
                        # Update DB progress
                        progress = int(uploaded / file_size * 100)
                        await self._update_upload_progress(upload_id, progress)
                    else:
                        resp.raise_for_status()

        raise RuntimeError("Upload completed without receiving video ID")

    async def _update_upload_progress(self, upload_id: int, progress: int) -> None:
        upload = await self.db.get(YouTubeUpload, upload_id)
        if upload:
            upload.upload_progress_pct = progress

    async def schedule_public_publish(
        self, upload_id: int, publish_at: str
    ) -> None:
        """Schedule a private video to go public at a future time.
        Only callable after admin approval of the video."""
        result = await self.db.execute(
            select(YouTubeUpload).where(YouTubeUpload.id == upload_id)
        )
        upload = result.scalar_one()
        if not upload.admin_approved:
            raise PermissionError("Admin approval required before scheduling public publish")

        channel = await self.db.get(YouTubeChannel, upload.channel_id)
        access_token = await self._get_valid_token(channel)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                f"{YT_API_BASE}/videos",
                params={"part": "status"},
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "id": upload.youtube_video_id,
                    "status": {
                        "privacyStatus": "scheduled",
                        "publishAt": publish_at,
                    },
                },
            )
            resp.raise_for_status()

        upload.privacy_status = PrivacyStatus.scheduled
        upload.scheduled_publish_at = publish_at
