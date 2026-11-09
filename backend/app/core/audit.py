"""Audit logging middleware and helper.

Records admin actions to the audit_logs table without exposing sensitive
values. PII and secrets are never written to logs.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

log = logging.getLogger(__name__)

# Fields that must never appear in audit payloads
_REDACT = frozenset({
    "password", "hashed_password", "access_token", "refresh_token",
    "access_token_encrypted", "refresh_token_encrypted", "api_key",
    "secret_key", "totp_secret", "client_secret",
})


def _sanitize(data: dict) -> dict:
    return {k: ("***" if k.lower() in _REDACT else v) for k, v in data.items()}


async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    safe_details = _sanitize(details or {})
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=safe_details,
        ip_address=ip_address,
    )
    db.add(entry)
    log.info(
        "AUDIT user=%d action=%s resource=%s/%s",
        user_id, action, resource_type, resource_id,
    )
