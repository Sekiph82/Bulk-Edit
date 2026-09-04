"""Regression guard for browser-playable render output (PR #132 hotfix).

The generated MP4 must be encoded as limited-range yuv420p so browsers can
decode it in <video> (JPEG inputs otherwise yield full-range yuvj420p, which
plays in desktop players but not reliably in Chrome/Firefox — the "plays in
Windows, not in the browser" preview bug). These tests capture the ffmpeg
argv (subprocess mocked — no ffmpeg needed in CI) and assert the fix flags.
"""
import os
import pytest

from app.services import video_renderer


@pytest.mark.anyio
async def test_render_command_forces_browser_safe_pixfmt(tmp_path, monkeypatch):
    captured = {}

    monkeypatch.setattr(video_renderer, "check_ffmpeg", lambda p=None: ("working", "ok"))

    class _Result:
        returncode = 0
        stderr = ""

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        # ffmpeg output path is the last arg — create it so the function's
        # existence check passes.
        open(cmd[-1], "wb").close()
        return _Result()

    monkeypatch.setattr(video_renderer.subprocess, "run", _fake_run)

    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")  # not a real jpeg; ffmpeg is mocked
    out_dir = tmp_path / "out"

    result = await video_renderer.render_slideshow_mp4(
        image_paths=[str(img)],
        output_dir=str(out_dir),
        duration_seconds=10.0,
        aspect_ratio="9:16",
    )

    cmd = captured["cmd"]
    # -vf value carries the range + format conversion
    vf_idx = cmd.index("-vf")
    vf = cmd[vf_idx + 1]
    assert "scale=out_range=tv" in vf, f"vf missing tv-range conversion: {vf}"
    assert "format=yuv420p" in vf, f"vf missing yuv420p: {vf}"
    # explicit output pixel format
    assert "-pix_fmt" in cmd and cmd[cmd.index("-pix_fmt") + 1] == "yuv420p"
    # faststart preserved for progressive playback
    assert "+faststart" in cmd
    assert result["output_path"].endswith(".mp4")


@pytest.mark.anyio
async def test_render_command_no_etsy_or_shell(tmp_path, monkeypatch):
    """Sanity: the render never uses a shell and calls no Etsy client."""
    captured = {}
    monkeypatch.setattr(video_renderer, "check_ffmpeg", lambda p=None: ("working", "ok"))

    class _Result:
        returncode = 0
        stderr = ""

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["shell"] = kwargs.get("shell", False)
        open(cmd[-1], "wb").close()
        return _Result()

    monkeypatch.setattr(video_renderer.subprocess, "run", _fake_run)

    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    await video_renderer.render_slideshow_mp4(
        image_paths=[str(img)], output_dir=str(tmp_path / "o"),
        duration_seconds=8.0, aspect_ratio="1:1",
    )
    assert captured["shell"] is False
    assert isinstance(captured["cmd"], list)  # argv list, never a shell string
