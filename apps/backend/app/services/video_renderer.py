"""ffmpeg-based video rendering service."""
import asyncio
import json
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


# --- Branding overlay (M13.05C) --------------------------------------------

import re

# Candidate system fonts (Linux prod containers). Logo is NOT rendered
# server-side — fetching arbitrary logo URLs is an SSRF risk with no safe
# allowlist/proxy yet, so logo stays preview-only (see docs/runbook).
_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
)

_BRANDING_MAX_LEN = {"headline": 60, "slogan": 80, "cta": 30, "outro": 80}
_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def find_branding_font() -> str | None:
    """First existing system font, or None. Text overlay is skipped (not
    failed) when no font is available."""
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def sanitize_branding_text(value: object, field: str) -> str:
    """Strip control chars and clamp to the field's max length. The result is
    written to a drawtext *textfile* (never the command line) and drawn with
    expansion=none, so it cannot inject ffmpeg options — this is defense in
    depth on top of that."""
    if not isinstance(value, str):
        return ""
    cleaned = "".join(ch for ch in value if ch == "\n" or (ord(ch) >= 32 and ch != "\x7f"))
    cleaned = cleaned.strip()
    return cleaned[: _BRANDING_MAX_LEN.get(field, 80)]


def _safe_hex_color(value: object) -> str:
    if isinstance(value, str) and _HEX_COLOR_RE.match(value):
        return value
    return "#FFFFFF"


def _escape_ff_path(path: str) -> str:
    """Escape a filesystem path for use inside an ffmpeg filtergraph option
    value (forward slashes everywhere; escape the option separator)."""
    return path.replace("\\", "/").replace(":", "\\:")


def build_branding_drawtext(
    branding: dict | None,
    width: int,
    height: int,
    work_dir: str,
    render_id: str,
    font_path: str | None,
) -> tuple[list[str], list[str]]:
    """Build drawtext filter strings + the temp textfiles they reference.
    Returns ([], []) when there is no branding text or no usable font — the
    caller then renders the plain slideshow unchanged. Text is passed via
    `textfile=` with `expansion=none`, so user text never touches the command
    line or filter parser."""
    if not branding or not font_path:
        return [], []

    color = _safe_hex_color(branding.get("brand_color"))
    placement = branding.get("text_placement") or "bottom"
    font_opt = _escape_ff_path(font_path)

    # Primary block (headline + slogan) and secondary block (cta + outro).
    primary = [t for t in (sanitize_branding_text(branding.get("headline"), "headline"),
                           sanitize_branding_text(branding.get("slogan"), "slogan")) if t]
    secondary = [t for t in (sanitize_branding_text(branding.get("cta"), "cta"),
                             sanitize_branding_text(branding.get("outro"), "outro")) if t]
    if not primary and not secondary:
        return [], []

    fontsize = max(24, int(width * 0.05))

    # Primary block Y by placement; secondary always near the bottom.
    if placement == "center":
        primary_y = "(h-text_h)/2"
    elif placement in ("intro-card", "outro-card"):
        # MVP: no separate card clip yet — treat as a lower-third overlay.
        primary_y = "h*0.75"
    else:  # bottom
        primary_y = "h*0.78"

    filters: list[str] = []
    temp_files: list[str] = []

    def _add(lines: list[str], idx: int, y_expr: str) -> None:
        text = "\n".join(lines)
        tf = os.path.join(work_dir, f"{render_id}_brand{idx}.txt")
        with open(tf, "w", encoding="utf-8") as fh:
            fh.write(text)
        temp_files.append(tf)
        filters.append(
            "drawtext="
            f"fontfile='{font_opt}':"
            f"textfile='{_escape_ff_path(tf)}':"
            "expansion=none:"
            f"fontcolor={color}:"
            f"fontsize={fontsize}:"
            "line_spacing=8:"
            "box=1:boxcolor=black@0.5:boxborderw=16:"
            "x=(w-text_w)/2:"
            f"y={y_expr}"
        )

    if primary:
        _add(primary, 0, primary_y)
    if secondary:
        _add(secondary, 1, "h*0.90")

    return filters, temp_files


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
    branding: dict | None = None,
) -> dict:
    """
    Render a slideshow MP4 from local image paths.
    Returns dict: {output_path, file_size_bytes, width, height, branding_text_rendered}.
    subprocess args are always a list — shell=True is never used.

    When `branding` carries text fields, they are burned in via ffmpeg
    drawtext (text passed through a textfile with expansion=none — never the
    command line). If the overlay attempt fails, or no system font is
    available, the plain slideshow is rendered instead so generation never
    breaks; `branding_text_rendered` reports what actually happened.
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
    branding_text_files: list[str] = []

    try:
        with open(concat_path, "w") as f:
            for img in images:
                f.write(f"file '{img}'\n")
                f.write(f"duration {duration_per_image:.3f}\n")
            # Repeat last image to avoid last-frame drop in concat demuxer
            f.write(f"file '{images[-1]}'\n")

        _ffmpeg = ffmpeg_path or settings.FFMPEG_PATH or "ffmpeg"
        vf_base = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            # Force limited/TV color range + yuv420p. JPEG inputs decode as
            # full-range yuvj420p, and `format=yuv420p` alone keeps the
            # full-range flag (output stays yuvj420p / color_range=pc). Some
            # browsers refuse to decode yuvj420p H.264 in <video> even though
            # desktop players accept it — the "plays in Windows, not in the
            # browser" preview bug. scale=out_range=tv converts to limited
            # range so the output is true yuv420p (color_range=tv), which
            # browsers decode reliably. Duration is unaffected (no fps change).
            f"scale=out_range=tv,"
            f"format=yuv420p"
        )

        font_path = find_branding_font()
        drawtext_filters, branding_text_files = build_branding_drawtext(
            branding, width, height, output_dir, render_id, font_path
        )
        vf_branded = vf_base + ("," + ",".join(drawtext_filters) if drawtext_filters else "")

        def _build_cmd(vf: str) -> list[str]:
            return [
                _ffmpeg,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_path,
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                # Belt-and-suspenders with the vf format filter: guarantees the
                # encoder input is 8-bit yuv420p (browser-safe H.264).
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-an",
                output_path,
            ]

        loop = asyncio.get_event_loop()

        def _run(vf: str):
            return subprocess.run(_build_cmd(vf), capture_output=True, text=True, timeout=120)

        proc_result = await loop.run_in_executor(None, lambda: _run(vf_branded))

        branding_text_rendered = False
        if drawtext_filters and proc_result.returncode == 0:
            branding_text_rendered = True
        elif drawtext_filters and proc_result.returncode != 0:
            # Graceful degradation: never let a branding-overlay failure break
            # generation — retry the plain slideshow.
            proc_result = await loop.run_in_executor(None, lambda: _run(vf_base))

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
            "branding_text_rendered": branding_text_rendered,
        }

    finally:
        for _tmp in [concat_path, *branding_text_files]:
            if _tmp and os.path.exists(_tmp):
                try:
                    os.unlink(_tmp)
                except OSError:
                    # Best-effort temp cleanup — a leftover scratch file must
                    # never mask a real render result or raise from finally.
                    pass


def check_ffprobe(ffprobe_path: str | None = None) -> tuple[str, str]:
    """Returns (state, message). state: 'disabled' | 'dependency_missing' | 'working'.
    Uploaded videos are validated with ffprobe rather than re-encoded, so this
    is gated the same way as check_ffmpeg but checks the probe binary."""
    if not settings.VIDEO_RENDERER_ENABLED:
        return "disabled", "Video validation is disabled. Set VIDEO_RENDERER_ENABLED=true to enable."

    path = ffprobe_path or settings.FFPROBE_PATH or "ffprobe"
    if not shutil.which(path):
        return (
            "dependency_missing",
            f"ffprobe not found at '{path}'. Install ffmpeg (which includes ffprobe) and restart the server.",
        )

    return "working", "Video validation is ready."


class ProbeError(Exception):
    pass


def probe_video_file(file_path: str, ffprobe_path: str | None = None) -> dict:
    """
    Run ffprobe on a local video file and return its real duration/resolution.
    Returns dict: {duration_seconds, width, height}.
    Raises ProbeError if ffprobe fails or the file has no video stream.
    """
    _ffprobe = ffprobe_path or settings.FFPROBE_PATH or "ffprobe"
    cmd = [
        _ffprobe,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-i", file_path,
    ]
    try:
        proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeError(f"ffprobe failed to run: {exc}") from exc

    if proc_result.returncode != 0:
        raise ProbeError(f"ffprobe exited with error (code {proc_result.returncode}).")

    try:
        info = json.loads(proc_result.stdout)
    except (ValueError, TypeError) as exc:
        raise ProbeError("ffprobe returned invalid output.") from exc

    video_stream = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "video"), None
    )
    if not video_stream:
        raise ProbeError("No video stream found in file.")

    width = video_stream.get("width")
    height = video_stream.get("height")
    if not width or not height:
        raise ProbeError("Could not determine video resolution.")

    duration_raw = video_stream.get("duration") or info.get("format", {}).get("duration")
    try:
        duration_seconds = float(duration_raw)
    except (TypeError, ValueError):
        raise ProbeError("Could not determine video duration.")

    return {"duration_seconds": duration_seconds, "width": int(width), "height": int(height)}


def classify_aspect_ratio(width: int, height: int, tolerance: float = 0.02) -> str | None:
    """Match (width, height) to the nearest supported Etsy aspect ratio preset,
    within a small tolerance. Returns None if no preset matches closely enough —
    callers should treat that as an unsupported aspect ratio."""
    if height == 0:
        return None
    ratio = width / height
    for label, (w, h) in ASPECT_RATIO_PRESETS.items():
        preset_ratio = w / h
        if abs(ratio - preset_ratio) / preset_ratio <= tolerance:
            return label
    return None


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
