"""M13.05C branding-overlay renderer unit tests (no ffmpeg needed).

These cover the pure helpers that build the drawtext filters — text is passed
via a textfile with expansion=none, so it can never inject ffmpeg options.
"""
import os

from app.services.video_renderer import (
    build_branding_drawtext,
    sanitize_branding_text,
    find_branding_font,
    _safe_hex_color,
)

FAKE_FONT = "/fake/font.ttf"


def test_no_branding_returns_nothing(tmp_path):
    filters, files = build_branding_drawtext(None, 1080, 1920, str(tmp_path), "rid", FAKE_FONT)
    assert filters == [] and files == []


def test_no_font_skips_overlay(tmp_path):
    b = {"headline": "Hello"}
    filters, files = build_branding_drawtext(b, 1080, 1920, str(tmp_path), "rid", None)
    assert filters == [] and files == []


def test_empty_text_returns_nothing(tmp_path):
    b = {"headline": "", "slogan": "  ", "cta": "", "outro": ""}
    filters, files = build_branding_drawtext(b, 1080, 1920, str(tmp_path), "rid", FAKE_FONT)
    assert filters == [] and files == []


def test_text_builds_drawtext_with_textfile_and_expansion_none(tmp_path):
    b = {"headline": "Handmade Mug", "cta": "Shop now", "brand_color": "#112233"}
    filters, files = build_branding_drawtext(b, 1080, 1920, str(tmp_path), "rid", FAKE_FONT)
    assert len(filters) == 2  # primary (headline) + secondary (cta)
    joined = "\n".join(filters)
    assert "drawtext=" in joined
    assert "textfile=" in joined
    assert "expansion=none" in joined
    assert "fontcolor=#112233" in joined
    # textfiles actually written with the sanitized content
    assert len(files) == 2
    contents = "".join(open(f, encoding="utf-8").read() for f in files)
    assert "Handmade Mug" in contents and "Shop now" in contents


def test_injection_text_goes_to_file_not_command(tmp_path):
    """Dangerous drawtext/filtergraph metacharacters must never appear in the
    filter option string — they live only inside the textfile."""
    evil = "x':drawtext=text=PWNED:%{gmtime}\\,y=0"
    b = {"headline": evil}
    filters, files = build_branding_drawtext(b, 1080, 1920, str(tmp_path), "rid", FAKE_FONT)
    assert len(filters) == 1
    # The evil string is in the file, not the filter args.
    assert "PWNED" not in filters[0]
    assert "PWNED" in open(files[0], encoding="utf-8").read()


def test_sanitize_strips_control_chars_and_clamps():
    assert sanitize_branding_text("a\x00b\x07c", "headline") == "abc"
    assert sanitize_branding_text("x" * 200, "cta") == "x" * 30  # cta max 30
    assert sanitize_branding_text(None, "headline") == ""
    assert sanitize_branding_text("line1\nline2", "slogan") == "line1\nline2"  # newline kept


def test_safe_hex_color():
    assert _safe_hex_color("#AABBCC") == "#AABBCC"
    assert _safe_hex_color("red") == "#FFFFFF"        # not hex → default
    assert _safe_hex_color("#GGG") == "#FFFFFF"
    assert _safe_hex_color(None) == "#FFFFFF"


def test_find_font_returns_str_or_none():
    # Environment-dependent; just assert the contract.
    result = find_branding_font()
    assert result is None or (isinstance(result, str) and os.path.exists(result))
