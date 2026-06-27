"""ffmpeg-based video rendering service."""
import asyncio
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from app.core.config import settings


class RendererNotAvailableError(Exception):
    pass


class RenderError(Exception):
    pass


def check_ffmpeg() -> tuple[str, str]:
    """Returns (state, message). state: 'disabled' | 'dependency_missing' | 'working'."""
    if not settings.VIDEO_RENDERER_ENABLED:
        return "disabled", "Video renderer is disabled. Set VIDEO_RENDERER_ENABLED=true to enable."

    ffmpeg_path = settings.FFMPEG_PATH or "ffmpeg"
    if not shutil.which(ffmpeg_path):
        return (
            "dependency_missing",
            f"ffmpeg not found at '{ffmpeg_path}'. Install ffmpeg and restart the server.",
        )

    return "working", "Video renderer is ready."


async def render_slideshow_mp4(
    image_paths: list[str],
    output_dir: str,
    duration_per_image: float = 2.5,
) -> str:
    """
    Render a slideshow MP4 from local image paths.
    Returns the output file path.
    Raises RendererNotAvailableError or RenderError on failure.
    subprocess args are always a list — shell=True is never used.
    """
    state, message = check_ffmpeg()
    if state != "working":
        raise RendererNotAvailableError(message)

    if not image_paths:
        raise RenderError("No images provided.")

    max_images = settings.VIDEO_MAX_IMAGES
    images = image_paths[:max_images]

    max_duration = float(settings.VIDEO_MAX_DURATION_SECONDS)
    total = len(images) * duration_per_image
    if total > max_duration:
        duration_per_image = max_duration / len(images)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    render_id = str(uuid.uuid4())
    output_path = os.path.join(output_dir, f"{render_id}.mp4")
    concat_path = os.path.join(output_dir, f"{render_id}_concat.txt")

    try:
        with open(concat_path, "w") as f:
            for img in images:
                f.write(f"file '{img}'\n")
                f.write(f"duration {duration_per_image:.3f}\n")
            # Repeat last image to prevent last-frame drop
            f.write(f"file '{images[-1]}'\n")

        ffmpeg_path = settings.FFMPEG_PATH or "ffmpeg"
        cmd = [
            ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_path,
            "-vf", (
                "scale=1080:1080:force_original_aspect_ratio=decrease,"
                "pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black,"
                "format=yuv420p"
            ),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            "-an",
            output_path,
        ]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            ),
        )

        if result.returncode != 0:
            raise RenderError(f"ffmpeg failed (exit {result.returncode}).")

        if not os.path.exists(output_path):
            raise RenderError("ffmpeg completed but output file not found.")

        return output_path

    finally:
        if os.path.exists(concat_path):
            try:
                os.unlink(concat_path)
            except OSError:
                pass
