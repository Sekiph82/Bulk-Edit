"""Sprint 1 QA: HTML entity decoding for Etsy-synced text fields."""
from app.services.etsy_sync import _decode_entities, _parse_listing


def test_decode_entities_apostrophe():
    assert _decode_entities("Black Cat Men&#39;s Wallet") == "Black Cat Men's Wallet"


def test_decode_entities_ampersand_and_quotes():
    assert _decode_entities("Tom &amp; Jerry &quot;Classic&quot;") == 'Tom & Jerry "Classic"'


def test_decode_entities_leaves_clean_text_unchanged():
    assert _decode_entities("Plain title, no entities") == "Plain title, no entities"


def test_decode_entities_handles_list():
    assert _decode_entities(["men&#39;s", "clean"]) == ["men's", "clean"]


def test_decode_entities_none_passthrough():
    assert _decode_entities(None) is None


def test_parse_listing_decodes_title_and_description():
    raw = {
        "listing_id": 123,
        "title": "Black Cat Men&#39;s Minimalist Wallet",
        "description": "Made with love &amp; care",
        "tags": ["men&#39;s", "wallet"],
        "materials": ["PU &quot;leather&quot;"],
        "sku": "SKU&#39;1",
        "price": {"amount": 5988, "divisor": 100, "currency_code": "USD"},
    }
    parsed = _parse_listing(raw, org_id="org1", shop_db_id="shop1")
    assert parsed["title"] == "Black Cat Men's Minimalist Wallet"
    assert parsed["description"] == "Made with love & care"
    assert parsed["tags"] == ["men's", "wallet"]
    assert parsed["materials"] == ['PU "leather"']
    assert parsed["sku"] == "SKU'1"
