"""Tests for CORS origin parsing in Settings.get_cors_origins().

Production uses a comma-separated value:
    BACKEND_CORS_ORIGINS=https://www.bulkeditapp.com,https://bulkeditapp.com
so the parser must split on commas, trim whitespace, and also accept a JSON array.
"""
from app.core.config import Settings


def _settings(value: str) -> Settings:
    return Settings(BACKEND_CORS_ORIGINS=value)


def test_single_origin():
    assert _settings("http://localhost:3100").get_cors_origins() == ["http://localhost:3100"]


def test_production_comma_separated_origins():
    s = _settings("https://www.bulkeditapp.com,https://bulkeditapp.com")
    assert s.get_cors_origins() == [
        "https://www.bulkeditapp.com",
        "https://bulkeditapp.com",
    ]


def test_comma_separated_trims_whitespace():
    s = _settings("https://www.bulkeditapp.com , https://bulkeditapp.com")
    assert s.get_cors_origins() == [
        "https://www.bulkeditapp.com",
        "https://bulkeditapp.com",
    ]


def test_json_array_origins():
    s = _settings('["https://www.bulkeditapp.com", "https://bulkeditapp.com"]')
    assert s.get_cors_origins() == [
        "https://www.bulkeditapp.com",
        "https://bulkeditapp.com",
    ]


def test_empty_segments_dropped():
    assert _settings("http://localhost:3100,,").get_cors_origins() == ["http://localhost:3100"]
