"""FFmpeg-based video rendering service.

Assembles scene clips, voiceovers, background music, and subtitles into a
final MP4. All work is done in a temporary scratch directory; the finished
file is moved to storage on success.

Requires: ffmpeg binary in PATH (included in backend/Dockerfile).
"""
import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class SceneAssets:
    index: int
    clip_path: str           # .mp4 video clip
    audio_path: str          # .mp3/.wav voiceover
    duration_seconds: float
    subtitle_text: str = ""


@dataclass
class RenderJob:
    video_id: int
    scenes: list[SceneAssets]
    music_path: Optional[str] = None
    music_volume: float = 0.15      # background music at 15% of narration
    output_width: int = 1920
    output_height: int = 1080
    fps: int = 24
    output_path: str = ""
    thumbnail_path: str = ""


@dataclass
class RenderResult:
    success: bool
    output_path: str = ""
    thumbnail_path: str = ""
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    error: str = ""


class RenderService:
    """Render a final video from per-scene assets using FFmpeg."""

    async def render(self, job: RenderJob) -> RenderResult:
        with tempfile.TemporaryDirectory(prefix="tinytales_render_") as tmp:
            try:
                return await self._render_in(job, Path(tmp))
            except Exception as exc:
                log.exception("Render failed for video %d", job.video_id)
                return RenderResult(success=False, error=str(exc))

    async def _render_in(self, job: RenderJob, tmp: Path) -> RenderResult:
        # 1. Normalise every scene clip to the same resolution / fps
        norm_clips = []
        for scene in job.scenes:
            out = tmp / f"norm_{scene.index:03d}.mp4"
            await self._run([
                "ffmpeg", "-y", "-i", scene.clip_path,
                "-vf", f"scale={job.output_width}:{job.output_height}:force_original_aspect_ratio=decrease,"
                       f"pad={job.output_width}:{job.output_height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                       f"fps={job.fps}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-an",  # strip original audio
                str(out),
            ])
            norm_clips.append(out)

        # 2. Attach voiceover to each normalised clip
        voiced_clips = []
        for scene, norm in zip(job.scenes, norm_clips):
            out = tmp / f"voiced_{scene.index:03d}.mp4"
            await self._run([
                "ffmpeg", "-y",
                "-i", str(norm),
                "-i", scene.audio_path,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                str(out),
            ])
            voiced_clips.append(out)

        # 3. Concatenate all voiced clips
        concat_list = tmp / "concat.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in voiced_clips))
        concat_path = tmp / "concat.mp4"
        await self._run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c", "copy",
            str(concat_path),
        ])

        # 4. Mix background music under narration (optional)
        mixed_path = concat_path
        if job.music_path and Path(job.music_path).exists():
            mixed_path = tmp / "mixed.mp4"
            await self._run([
                "ffmpeg", "-y",
                "-i", str(concat_path),
                "-stream_loop", "-1", "-i", job.music_path,
                "-filter_complex",
                f"[1:a]volume={job.music_volume},apad[music];"
                f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(mixed_path),
            ])

        # 5. Burn subtitles (SRT) if any scenes have text
        sub_path = await self._write_srt(job.scenes, tmp)
        final_path = Path(job.output_path) if job.output_path else tmp / "final.mp4"
        final_path.parent.mkdir(parents=True, exist_ok=True)

        if sub_path:
            await self._run([
                "ffmpeg", "-y",
                "-i", str(mixed_path),
                "-vf", f"subtitles={sub_path}:force_style='FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=3'",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "copy",
                str(final_path),
            ])
        else:
            await self._run([
                "ffmpeg", "-y", "-i", str(mixed_path),
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "copy",
                str(final_path),
            ])

        # 6. Extract thumbnail from first frame
        thumb_path = Path(job.thumbnail_path) if job.thumbnail_path else tmp / "thumb.jpg"
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        await self._run([
            "ffmpeg", "-y", "-i", str(final_path),
            "-ss", "00:00:01", "-frames:v", "1",
            "-vf", f"scale={job.output_width}:{job.output_height}",
            str(thumb_path),
        ])

        duration = await self._get_duration(final_path)
        size = final_path.stat().st_size

        return RenderResult(
            success=True,
            output_path=str(final_path),
            thumbnail_path=str(thumb_path),
            duration_seconds=duration,
            file_size_bytes=size,
        )

    async def _run(self, cmd: list[str]) -> None:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"FFmpeg command failed (rc={proc.returncode}): {' '.join(cmd[:4])}…\n"
                + stderr.decode(errors="replace")[-2000:]
            )

    async def _get_duration(self, path: Path) -> float:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        try:
            data = json.loads(stdout)
            return float(data["format"]["duration"])
        except Exception:
            return 0.0

    async def _write_srt(self, scenes: list[SceneAssets], tmp: Path) -> Optional[str]:
        entries = [s for s in scenes if s.subtitle_text.strip()]
        if not entries:
            return None

        srt_path = tmp / "subs.srt"
        lines = []
        offset = 0.0
        for i, scene in enumerate(entries, 1):
            start = self._fmt_ts(offset)
            end = self._fmt_ts(offset + max(scene.duration_seconds - 0.5, 1.0))
            lines.append(f"{i}\n{start} --> {end}\n{scene.subtitle_text}\n")
            offset += scene.duration_seconds
        srt_path.write_text("\n".join(lines))
        return str(srt_path)

    @staticmethod
    def _fmt_ts(secs: float) -> str:
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        s = int(secs % 60)
        ms = int((secs % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
