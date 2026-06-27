"""Unit tests for video_renderer service."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.video_renderer import (
    ASPECT_RATIO_PRESETS,
    ETSY_MAX_FILE_SIZE_BYTES,
    ETSY_MIN_DURATION,
    ETSY_MAX_DURATION,
    ETSY_MIN_RESOLUTION,
    check_ffmpeg,
    check_etsy_ready,
    render_slideshow_mp4,
    RendererNotAvailableError,
    RenderError,
)


# --- check_ffmpeg ---

def test_check_ffmpeg_disabled_when_not_enabled(monkeypatch):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", False)
    state, msg = check_ffmpeg()
    assert state == "disabled"
    assert "VIDEO_RENDERER_ENABLED" in msg


def test_check_ffmpeg_dependency_missing_when_no_binary(monkeypatch):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", True)
    monkeypatch.setattr("app.services.video_renderer.settings.FFMPEG_PATH", "ffmpeg")
    with patch("shutil.which", return_value=None):
        state, msg = check_ffmpeg()
    assert state == "dependency_missing"
    assert "ffmpeg" in msg


def test_check_ffmpeg_working_when_binary_found(monkeypatch):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", True)
    monkeypatch.setattr("app.services.video_renderer.settings.FFMPEG_PATH", "ffmpeg")
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        state, msg = check_ffmpeg()
    assert state == "working"
    assert "ready" in msg.lower()


def test_check_ffmpeg_custom_path(monkeypatch):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", True)
    with patch("shutil.which", return_value="/custom/ffmpeg") as mock_which:
        state, _ = check_ffmpeg(ffmpeg_path="/custom/ffmpeg")
    mock_which.assert_called_with("/custom/ffmpeg")
    assert state == "working"


# --- aspect ratio presets ---

def test_aspect_ratio_presets_have_correct_dimensions():
    assert ASPECT_RATIO_PRESETS["9:16"] == (1080, 1920)
    assert ASPECT_RATIO_PRESETS["1:1"] == (1080, 1080)
    assert ASPECT_RATIO_PRESETS["4:5"] == (1080, 1350)
    assert ASPECT_RATIO_PRESETS["16:9"] == (1920, 1080)


def test_all_preset_dimensions_meet_etsy_minimum():
    for ratio, (w, h) in ASPECT_RATIO_PRESETS.items():
        assert w >= ETSY_MIN_RESOLUTION, f"{ratio} width {w} below minimum"
        assert h >= ETSY_MIN_RESOLUTION, f"{ratio} height {h} below minimum"


# --- check_etsy_ready ---

def test_etsy_ready_happy_path():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=50 * 1024 * 1024,
        duration_seconds=10.0,
        aspect_ratio="9:16",
        width=1080,
        height=1920,
    )
    assert is_ready is True
    assert issues == []


def test_etsy_ready_fails_oversized_file():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=ETSY_MAX_FILE_SIZE_BYTES + 1,
        duration_seconds=10.0,
        aspect_ratio="1:1",
        width=1080,
        height=1080,
    )
    assert is_ready is False
    assert any("100 MB" in i for i in issues)


def test_etsy_ready_fails_duration_too_short():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=1024,
        duration_seconds=3.0,
        aspect_ratio="1:1",
        width=1080,
        height=1080,
    )
    assert is_ready is False
    assert any("5-second" in i or "minimum" in i for i in issues)


def test_etsy_ready_fails_duration_too_long():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=1024,
        duration_seconds=20.0,
        aspect_ratio="1:1",
        width=1080,
        height=1080,
    )
    assert is_ready is False
    assert any("15-second" in i or "maximum" in i for i in issues)


def test_etsy_ready_fails_unsupported_aspect_ratio():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=1024,
        duration_seconds=10.0,
        aspect_ratio="3:4",
        width=1080,
        height=1440,
    )
    assert is_ready is False
    assert any("3:4" in i for i in issues)


def test_etsy_ready_fails_low_resolution():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=1024,
        duration_seconds=10.0,
        aspect_ratio="1:1",
        width=400,
        height=400,
    )
    assert is_ready is False
    assert any("500px" in i for i in issues)


def test_etsy_ready_accumulates_multiple_issues():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=ETSY_MAX_FILE_SIZE_BYTES + 1,
        duration_seconds=2.0,
        aspect_ratio="bad",
        width=100,
        height=100,
    )
    assert is_ready is False
    assert len(issues) >= 3


def test_etsy_ready_boundary_duration_exactly_5():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=1024,
        duration_seconds=5.0,
        aspect_ratio="1:1",
        width=1080,
        height=1080,
    )
    assert is_ready is True
    assert issues == []


def test_etsy_ready_boundary_duration_exactly_15():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=1024,
        duration_seconds=15.0,
        aspect_ratio="1:1",
        width=1080,
        height=1080,
    )
    assert is_ready is True
    assert issues == []


def test_etsy_ready_boundary_file_size_exactly_100mb():
    is_ready, issues = check_etsy_ready(
        file_size_bytes=100 * 1024 * 1024,
        duration_seconds=10.0,
        aspect_ratio="16:9",
        width=1920,
        height=1080,
    )
    assert is_ready is True
    assert issues == []


# --- render_slideshow_mp4 ---

@pytest.mark.anyio
async def test_render_raises_when_renderer_disabled(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", False)
    with pytest.raises(RendererNotAvailableError):
        await render_slideshow_mp4(
            image_paths=["a.jpg"],
            output_dir=str(tmp_path),
        )


@pytest.mark.anyio
async def test_render_raises_on_empty_images(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", True)
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with pytest.raises(RenderError, match="No images"):
            await render_slideshow_mp4(
                image_paths=[],
                output_dir=str(tmp_path),
            )


@pytest.mark.anyio
async def test_render_raises_on_invalid_aspect_ratio(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", True)
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with pytest.raises(RenderError, match="Invalid aspect ratio"):
            await render_slideshow_mp4(
                image_paths=["a.jpg"],
                output_dir=str(tmp_path),
                aspect_ratio="bad",
            )


@pytest.mark.anyio
async def test_render_returns_correct_dimensions(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_RENDERER_ENABLED", True)
    monkeypatch.setattr("app.services.video_renderer.settings.FFMPEG_PATH", "ffmpeg")
    monkeypatch.setattr("app.services.video_renderer.settings.VIDEO_MAX_IMAGES", 10)

    fake_output = tmp_path / "fake.mp4"
    fake_output.write_bytes(b"fakemp4")

    def fake_run(cmd, **kwargs):
        # Write the output file so the function believes ffmpeg succeeded
        Path(cmd[-1]).write_bytes(b"fakemp4")
        m = MagicMock()
        m.returncode = 0
        return m

    from pathlib import Path
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with patch("subprocess.run", side_effect=fake_run):
            result = await render_slideshow_mp4(
                image_paths=[str(tmp_path / "a.jpg")],
                output_dir=str(tmp_path),
                aspect_ratio="1:1",
                duration_seconds=10.0,
            )

    assert result["width"] == 1080
    assert result["height"] == 1080
    assert "output_path" in result
    assert "file_size_bytes" in result
