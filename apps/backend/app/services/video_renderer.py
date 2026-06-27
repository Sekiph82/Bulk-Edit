"""ffmpeg-based video rendering service."""
import asyncio
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from app.core.config import settings

ASPECT_RATIO_PRESETS: dict[str, tuple[int, int]] = {
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "16:9": (1920, 1080),
}

ETSY_MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
ETSY_MIN_DURATION = 5
ETSY_MAX_DURATION = 15
ETSY_MIN_RESOLUTION = 500


class RendererNotAvailableError(Exception):
    pass


class RenderError(Exception):
    pass


def check_ffmpeg(ffmpeg_path: str | None = None) -> tuple[str, str]:
    """Returns (state, message). state: 'disabled' | 'dependency_missing' | 'working'."""
    if not settings.VIDEO_RENDERER_ENABLED:
        return "disabled", "Video renderer is disabled. Set VIDEO_RENDERER_ENABLED=true to enable."

    path = ffmpeg_path or settings.FFMPEG_PATH or "ffmpeg"
    if not shutil.which(path):
        return (
            "dependency_missing",
            f"ffmpeg not found at '{path}'. Install ffmpeg and restart the server.",
        )

    return "working", "Video renderer is ready."


async def render_slideshow_mp4(
    image_paths: list[str],
    output_dir: str,
    duration_seconds: float = 10.0,
    aspect_ratio: str = "9:16",
    title_text: str | None = None,
    ffmpeg_path: str | None = None,
) -> dict:
    """
    Render a slideshow MP4 from local image paths.
    Returns dict: {output_path, file_size_bytes, width, height}.
    subprocess args are always a list — shell=True is never used.
    """
    state, message = check_ffmpeg(ffmpeg_path)
    if state != "working":
        raise RendererNotAvailableError(message)

    if not image_paths:
        raise RenderError("No images provided.")

    if aspect_ratio not in ASPECT_RATIO_PRESETS:
        raise RenderError(
            f"Invalid aspect ratio '{aspect_ratio}'. "
            f"Must be one of: {', '.join(ASPECT_RATIO_PRESETS)}."
        )

    width, height = ASPECT_RATIO_PRESETS[aspect_ratio]
    max_images = settings.VIDEO_MAX_IMAGES
    images = image_paths[:max_images]
    duration_per_image = duration_seconds / len(images)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    render_id = str(uuid.uuid4())
    output_path = os.path.join(output_dir, f"{render_id}.mp4")
    concat_path = os.path.join(output_dir, f"{render_id}_concat.txt")

    try:
        with open(concat_path, "w") as f:
            for img in images:
                f.write(f"file '{img}'\n")
                f.write(f"duration {duration_per_image:.3f}\n")
            # Repeat last image to avoid last-frame drop in concat demuxer
            f.write(f"file '{images[-1]}'\n")

        _ffmpeg = ffmpeg_path or settings.FFMPEG_PATH or "ffmpeg"
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"format=yuv420p"
        )
        cmd = [
            _ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            "-an",
            output_path,
        ]

        loop = asyncio.get_event_loop()
        proc_result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            ),
        )

        if proc_result.returncode != 0:
            raise RenderError(f"ffmpeg failed (exit {proc_result.returncode}).")

        if not os.path.exists(output_path):
            raise RenderError("ffmpeg completed but output file not found.")

        file_size_bytes = os.path.getsize(output_path)
        return {
            "output_path": output_path,
            "file_size_bytes": file_size_bytes,
            "width": width,
            "height": height,
        }

    finally:
        if os.path.exists(concat_path):
            try:
                os.unlink(concat_path)
            except OSError:
                pass


def check_etsy_ready(
    file_size_bytes: int,
    duration_seconds: float,
    aspect_ratio: str,
    width: int,
    height: int,
) -> tuple[bool, list[str]]:
    """Returns (is_ready, issues). Checks video against Etsy listing video specs."""
    issues: list[str] = []

    if file_size_bytes > ETSY_MAX_FILE_SIZE_BYTES:
        mb = file_size_bytes / 1024 / 1024
        issues.append(f"File size {mb:.1f} MB exceeds Etsy's 100 MB limit.")

    if duration_seconds < ETSY_MIN_DURATION:
        issues.append(f"Duration {duration_seconds:.1f}s is below Etsy's 5-second minimum.")

    if duration_seconds > ETSY_MAX_DURATION:
        issues.append(f"Duration {duration_seconds:.1f}s exceeds Etsy's 15-second maximum.")

    if aspect_ratio not in ASPECT_RATIO_PRESETS:
        supported = ", ".join(ASPECT_RATIO_PRESETS)
        issues.append(f"Aspect ratio '{aspect_ratio}' is not supported by Etsy ({supported}).")

    if width < ETSY_MIN_RESOLUTION or height < ETSY_MIN_RESOLUTION:
        issues.append(f"Resolution {width}×{height} is below Etsy's 500px minimum per side.")

    return (len(issues) == 0, issues)
