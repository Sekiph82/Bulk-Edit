"""
Sprint 14 tests: CSV import/export — parsing, validation, preview, convert, org isolation.

CSV import NEVER writes to Etsy. Converts to BulkEditSession only.
"""
import csv
import io
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.services.csv_tools import (
    parse_csv_upload,
    normalize_pipe_array,
    parse_bool,
    parse_int,
    csv_template,
    CSVToolsError,
    EXPORT_HEADERS,
)

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
EXPORT_URL = "/api/v1/csv/export"
IMPORT_URL = "/api/v1/csv/import"
TEMPLATE_URL = "/api/v1/csv/template"
JOBS_URL = "/api/v1/csv/jobs"


# ── helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(client, user: dict) -> str:
    payload = {**user}
    if "organization_name" not in payload:
        payload["organization_name"] = payload.get("full_name", "Org") + " Org"
    payload.setdefault("terms_accepted", True)
    await client.post(REGISTER_URL, json=payload)
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    return result.scalar_one().organization_id


async def _setup_listing(db_session, org_id: str, etsy_id: str = "CSV001", **kwargs) -> "Listing":
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"csv_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(
            organization_id=org_id,
            etsy_shop_id=shop_etsy_id,
            shop_name="CSV Test Shop",
            is_connected=True,
        )
        db_session.add(shop)
        await db_session.flush()
        token = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake_csv_token"),
            refresh_token_enc=encrypt_token("fake_r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scopes="listings_r listings_w",
        )
        db_session.add(token)
        await db_session.flush()

    defaults = dict(
        organization_id=org_id,
        etsy_shop_id=shop.id,
        etsy_listing_id=etsy_id,
        title=f"Original Title {etsy_id}",
        description="Original description.",
        state="active",
        tags=["handmade", "gift"],
        materials=["wood"],
        price_amount=1500,
        price_divisor=100,
        currency_code="USD",
        quantity=10,
        has_variations=False,
    )
    defaults.update(kwargs)
    listing = Listing(**defaults)
    db_session.add(listing)
    await db_session.flush()
    await db_session.commit()
    return listing


def _make_csv(rows: list[dict], headers: list[str] | None = None) -> bytes:
    if headers is None:
        headers = list(rows[0].keys()) if rows else EXPORT_HEADERS
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    w.writeheader()
    for row in rows:
        w.writerow(row)
    return buf.getvalue().encode("utf-8")


# ── unit tests — parsers ───────────────────────────────────────────────────────

def test_normalize_pipe_array_basic():
    assert normalize_pipe_array("a|b|c") == ["a", "b", "c"]


def test_normalize_pipe_array_trims_whitespace():
    assert normalize_pipe_array(" a | b | c ") == ["a", "b", "c"]


def test_normalize_pipe_array_deduplicates():
    assert normalize_pipe_array("a|b|a|c") == ["a", "b", "c"]


def test_normalize_pipe_array_empty():
    assert normalize_pipe_array("") == []
    assert normalize_pipe_array("   ") == []


def test_parse_bool_variants():
    for v in ("true", "True", "TRUE", "yes", "YES", "1", "y", "Y"):
        assert parse_bool(v) is True
    for v in ("false", "False", "FALSE", "no", "NO", "0", "n", "N"):
        assert parse_bool(v) is False


def test_parse_bool_invalid():
    assert parse_bool("maybe") is None
    assert parse_bool("") is None


def test_parse_int_valid():
    assert parse_int("42") == 42
    assert parse_int("0") == 0
    assert parse_int("  100  ") == 100


def test_parse_int_invalid():
    assert parse_int("abc") is None
    assert parse_int("") is None
    assert parse_int(None) is None


def test_csv_template_has_headers():
    template = csv_template()
    reader = csv.DictReader(io.StringIO(template))
    assert set(reader.fieldnames) == set(EXPORT_HEADERS)


def test_parse_csv_upload_empty():
    with pytest.raises(CSVToolsError) as exc_info:
        parse_csv_upload(b"", "test.csv")
    assert exc_info.value.status_code == 400


def test_parse_csv_upload_bom_stripped():
    bom = b"\xef\xbb\xbf"
    content = bom + b"listing_id,title\nabc,New Title\n"
    rows, ignored = parse_csv_upload(content, "test.csv")
    assert rows[0]["listing_id"] == "abc"


def test_parse_csv_upload_unknown_columns_tracked():
    content = b"listing_id,title,my_custom_field\nabc,Title,custom_val\n"
    rows, ignored = parse_csv_upload(content, "test.csv")
    assert "my_custom_field" in ignored


def test_parse_csv_upload_over_limit():
    headers = "listing_id,title\n"
    rows = "".join(f"id{i},Title{i}\n" for i in range(5001))
    with pytest.raises(CSVToolsError) as exc_info:
        parse_csv_upload((headers + rows).encode(), "big.csv")
    assert exc_info.value.status_code == 400


# ── API tests — auth ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_requires_auth(client):
    r = await client.get(EXPORT_URL)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_import_requires_auth(client):
    content = b"listing_id,title\n"
    r = await client.post(IMPORT_URL, files={"file": ("test.csv", content, "text/csv")})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_template_requires_auth(client):
    r = await client.get(TEMPLATE_URL)
    assert r.status_code == 403


# ── API tests — export ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_returns_csv_content_type(client, db_session):
    token = await _register_and_login(client, {"email": "csv1@test.com", "password": "Pw12345!", "full_name": "CSV1"})
    r = await client.get(EXPORT_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


@pytest.mark.asyncio
async def test_export_includes_expected_headers(client, db_session):
    token = await _register_and_login(client, {"email": "csv2@test.com", "password": "Pw12345!", "full_name": "CSV2"})
    r = await client.get(EXPORT_URL, headers={"Authorization": f"Bearer {token}"})
    text = r.text
    reader = csv.DictReader(io.StringIO(text))
    for h in ["listing_id", "title", "price_amount", "tags"]:
        assert h in (reader.fieldnames or [])


@pytest.mark.asyncio
async def test_export_only_org_listings(client, db_session):
    token_a = await _register_and_login(client, {"email": "csv3a@test.com", "password": "Pw12345!", "full_name": "CSV3A"})
    token_b = await _register_and_login(client, {"email": "csv3b@test.com", "password": "Pw12345!", "full_name": "CSV3B"})
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).offset(1).limit(1)
    )
    org_a = result.scalar_one().organization_id
    listing_a = await _setup_listing(db_session, org_a, "CSVEXP001")
    r_a = await client.get(EXPORT_URL, headers={"Authorization": f"Bearer {token_a}"})
    r_b = await client.get(EXPORT_URL, headers={"Authorization": f"Bearer {token_b}"})
    assert listing_a.etsy_listing_id in r_a.text
    assert listing_a.etsy_listing_id not in r_b.text


@pytest.mark.asyncio
async def test_template_returns_headers(client, db_session):
    token = await _register_and_login(client, {"email": "csv4@test.com", "password": "Pw12345!", "full_name": "CSV4"})
    r = await client.get(TEMPLATE_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    reader = csv.DictReader(io.StringIO(r.text))
    assert "listing_id" in (reader.fieldnames or [])


# ── API tests — import ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_rejects_empty_file(client, db_session):
    token = await _register_and_login(client, {"email": "csv5@test.com", "password": "Pw12345!", "full_name": "CSV5"})
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", b"", "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_import_rejects_non_csv_extension(client, db_session):
    token = await _register_and_login(client, {"email": "csv6@test.com", "password": "Pw12345!", "full_name": "CSV6"})
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.xlsx", b"data", "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_import_rejects_over_max_rows(client, db_session):
    token = await _register_and_login(client, {"email": "csv7@test.com", "password": "Pw12345!", "full_name": "CSV7"})
    headers = "listing_id,title\n"
    rows = "".join(f"id{i},T{i}\n" for i in range(5001))
    r = await client.post(
        IMPORT_URL,
        files={"file": ("big.csv", (headers + rows).encode(), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_import_creates_csv_job(client, db_session):
    token = await _register_and_login(client, {"email": "csv8@test.com", "password": "Pw12345!", "full_name": "CSV8"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "CSV_IMP01")
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "Updated Title"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert "job_id" in data
    assert data["row_count"] == 1


@pytest.mark.asyncio
async def test_import_creates_csv_rows(client, db_session):
    token = await _register_and_login(client, {"email": "csv9@test.com", "password": "Pw12345!", "full_name": "CSV9"})
    org_id = await _get_org_id(db_session)
    l1 = await _setup_listing(db_session, org_id, "CSV_IMP02")
    l2 = await _setup_listing(db_session, org_id, "CSV_IMP03")
    csv_bytes = _make_csv([
        {"listing_id": l1.id, "title": "Title One"},
        {"listing_id": l2.id, "title": "Title Two"},
    ])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["row_count"] == 2


@pytest.mark.asyncio
async def test_import_validates_listing_id_match(client, db_session):
    token = await _register_and_login(client, {"email": "csv10@test.com", "password": "Pw12345!", "full_name": "CSV10"})
    csv_bytes = _make_csv([{"listing_id": "00000000-0000-0000-0000-000000000000", "title": "New"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["invalid_row_count"] == 1


@pytest.mark.asyncio
async def test_import_rejects_other_org_listing_id(client, db_session):
    token_a = await _register_and_login(client, {"email": "csv11a@test.com", "password": "Pw12345!", "full_name": "CSV11A"})
    token_b = await _register_and_login(client, {"email": "csv11b@test.com", "password": "Pw12345!", "full_name": "CSV11B"})
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).offset(1).limit(1)
    )
    org_a = result.scalar_one().organization_id
    listing_a = await _setup_listing(db_session, org_a, "CSV_IMP04")
    csv_bytes = _make_csv([{"listing_id": listing_a.id, "title": "Hacked"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 201
    assert r.json()["invalid_row_count"] == 1


@pytest.mark.asyncio
async def test_import_matches_by_etsy_listing_id(client, db_session):
    token = await _register_and_login(client, {"email": "csv12@test.com", "password": "Pw12345!", "full_name": "CSV12"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "ETSYID999")
    csv_bytes = _make_csv([{"etsy_listing_id": "ETSYID999", "title": "Title via Etsy ID"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["invalid_row_count"] == 0


@pytest.mark.asyncio
async def test_import_invalid_when_listing_id_etsy_id_mismatch(client, db_session):
    token = await _register_and_login(client, {"email": "csv13@test.com", "password": "Pw12345!", "full_name": "CSV13"})
    org_id = await _get_org_id(db_session)
    l1 = await _setup_listing(db_session, org_id, "MISMATCH01")
    l2 = await _setup_listing(db_session, org_id, "MISMATCH02")
    csv_bytes = _make_csv([{"listing_id": l1.id, "etsy_listing_id": "MISMATCH02", "title": "Wrong"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["invalid_row_count"] == 1


@pytest.mark.asyncio
async def test_import_parses_pipe_tags(client, db_session):
    token = await _register_and_login(client, {"email": "csv14@test.com", "password": "Pw12345!", "full_name": "CSV14"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "PIPE001")
    csv_bytes = _make_csv([{"listing_id": listing.id, "tags": "handmade|gift|unique"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    job_id = r.json()["job_id"]
    r2 = await client.get(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    items = r2.json()["items"]
    assert len(items) == 1
    diff = items[0]["diff"]
    if diff:
        assert "tags" in diff
        assert diff["tags"]["after"] == ["handmade", "gift", "unique"]


@pytest.mark.asyncio
async def test_import_parses_booleans(client, db_session):
    token = await _register_and_login(client, {"email": "csv15@test.com", "password": "Pw12345!", "full_name": "CSV15"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "BOOL001")
    csv_bytes = _make_csv([{"listing_id": listing.id, "is_personalizable": "yes", "is_customizable": "1"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["invalid_row_count"] == 0


@pytest.mark.asyncio
async def test_import_parses_integers(client, db_session):
    token = await _register_and_login(client, {"email": "csv16@test.com", "password": "Pw12345!", "full_name": "CSV16"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "INT001")
    csv_bytes = _make_csv([{"listing_id": listing.id, "price_amount": "2500", "quantity": "5"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["invalid_row_count"] == 0


@pytest.mark.asyncio
async def test_import_invalid_negative_price(client, db_session):
    token = await _register_and_login(client, {"email": "csv17@test.com", "password": "Pw12345!", "full_name": "CSV17"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "NEG001")
    csv_bytes = _make_csv([{"listing_id": listing.id, "price_amount": "-100"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["invalid_row_count"] == 1


@pytest.mark.asyncio
async def test_import_invalid_negative_quantity(client, db_session):
    token = await _register_and_login(client, {"email": "csv18@test.com", "password": "Pw12345!", "full_name": "CSV18"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "NEG002")
    csv_bytes = _make_csv([{"listing_id": listing.id, "quantity": "-5"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["invalid_row_count"] == 1


@pytest.mark.asyncio
async def test_import_unchanged_row_status(client, db_session):
    token = await _register_and_login(client, {"email": "csv19@test.com", "password": "Pw12345!", "full_name": "CSV19"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "UNCHANGED01", title="Same Title")
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "Same Title"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["unchanged_row_count"] == 1


@pytest.mark.asyncio
async def test_import_changed_row_has_diff(client, db_session):
    token = await _register_and_login(client, {"email": "csv20@test.com", "password": "Pw12345!", "full_name": "CSV20"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "DIFF001", title="Old Title")
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "New Title for Real"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    job_id = r.json()["job_id"]
    r2 = await client.get(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    items = r2.json()["items"]
    assert items[0]["diff"]["title"]["before"] == "Old Title"
    assert items[0]["diff"]["title"]["after"] == "New Title for Real"


@pytest.mark.asyncio
async def test_import_unknown_columns_tracked(client, db_session):
    token = await _register_and_login(client, {"email": "csv21@test.com", "password": "Pw12345!", "full_name": "CSV21"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "UNKNOWN01")
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "T", "my_special_col": "val"}])
    r = await client.post(
        IMPORT_URL,
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert "my_special_col" in r.json()["ignored_columns"]


# ── API tests — preview ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_preview_paginates(client, db_session):
    token = await _register_and_login(client, {"email": "csv22@test.com", "password": "Pw12345!", "full_name": "CSV22"})
    org_id = await _get_org_id(db_session)
    listings = [await _setup_listing(db_session, org_id, f"PAG{i:03d}") for i in range(5)]
    rows = [{"listing_id": l.id, "title": f"Title {i}"} for i, l in enumerate(listings)]
    csv_bytes = _make_csv(rows)
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    r2 = await client.get(f"{JOBS_URL}/{job_id}/preview?per_page=2", headers={"Authorization": f"Bearer {token}"})
    data = r2.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_preview_filters_by_status(client, db_session):
    token = await _register_and_login(client, {"email": "csv23@test.com", "password": "Pw12345!", "full_name": "CSV23"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "FILT001", title="Same")
    csv_bytes = _make_csv([
        {"listing_id": listing.id, "title": "Same"},
        {"listing_id": "00000000-0000-0000-0000-000000000099", "title": "Bad"},
    ])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    r2 = await client.get(f"{JOBS_URL}/{job_id}/preview?status=invalid", headers={"Authorization": f"Bearer {token}"})
    assert all(item["status"] == "invalid" for item in r2.json()["items"])


# ── API tests — convert ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_convert_blocks_invalid_rows(client, db_session):
    token = await _register_and_login(client, {"email": "csv24@test.com", "password": "Pw12345!", "full_name": "CSV24"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "CONV001")
    csv_bytes = _make_csv([
        {"listing_id": listing.id, "title": "Good Title"},
        {"listing_id": "00000000-0000-0000-0000-000000000088", "title": "Bad"},
    ])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    r2 = await client.post(
        f"{JOBS_URL}/{job_id}/convert",
        json={"ignore_invalid": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_convert_creates_bulk_edit_session(client, db_session):
    token = await _register_and_login(client, {"email": "csv25@test.com", "password": "Pw12345!", "full_name": "CSV25"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "CONV002", title="Old")
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "Converted New Title"}])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    r2 = await client.post(
        f"{JOBS_URL}/{job_id}/convert",
        json={"ignore_invalid": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert "bulk_edit_session_id" in data
    assert data["bulk_edit_session_id"]


@pytest.mark.asyncio
async def test_convert_creates_bulk_edit_changes(client, db_session):
    token = await _register_and_login(client, {"email": "csv26@test.com", "password": "Pw12345!", "full_name": "CSV26"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "CONV003", title="Old", quantity=5)
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "Brand New Title", "quantity": "20"}])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    r2 = await client.post(
        f"{JOBS_URL}/{job_id}/convert",
        json={"ignore_invalid": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["created_changes"] >= 2


@pytest.mark.asyncio
async def test_convert_does_not_write_to_etsy(client, db_session):
    """Convert creates BulkEditSession only — no Etsy calls should be made."""
    token = await _register_and_login(client, {"email": "csv27@test.com", "password": "Pw12345!", "full_name": "CSV27"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "CONV004", title="Safe")
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "Converted Safe New Title"}])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    r2 = await client.post(
        f"{JOBS_URL}/{job_id}/convert",
        json={"ignore_invalid": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    # BulkEditSession should be draft (not applied)
    from app.models.bulk_edit_session import BulkEditSession
    session_id = r2.json()["bulk_edit_session_id"]
    result = await db_session.execute(select(BulkEditSession).where(BulkEditSession.id == session_id))
    session = result.scalar_one()
    assert session.status == "draft"


@pytest.mark.asyncio
async def test_convert_marks_job_converted(client, db_session):
    token = await _register_and_login(client, {"email": "csv28@test.com", "password": "Pw12345!", "full_name": "CSV28"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "CONV005", title="Before")
    csv_bytes = _make_csv([{"listing_id": listing.id, "title": "After Conversion Title"}])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    await client.post(f"{JOBS_URL}/{job_id}/convert", json={}, headers={"Authorization": f"Bearer {token}"})
    r2 = await client.get(f"{JOBS_URL}/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert r2.json()["status"] == "converted"


# ── API tests — org isolation ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_isolation_job_detail(client, db_session):
    token_a = await _register_and_login(client, {"email": "csv29a@test.com", "password": "Pw12345!", "full_name": "CSV29A"})
    token_b = await _register_and_login(client, {"email": "csv29b@test.com", "password": "Pw12345!", "full_name": "CSV29B"})
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).offset(1).limit(1)
    )
    org_a = result.scalar_one().organization_id
    listing_a = await _setup_listing(db_session, org_a, "ISO001")
    csv_bytes = _make_csv([{"listing_id": listing_a.id, "title": "Title"}])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token_a}"})
    job_id = r.json()["job_id"]
    r2 = await client.get(f"{JOBS_URL}/{job_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_org_isolation_preview(client, db_session):
    token_a = await _register_and_login(client, {"email": "csv30a@test.com", "password": "Pw12345!", "full_name": "CSV30A"})
    token_b = await _register_and_login(client, {"email": "csv30b@test.com", "password": "Pw12345!", "full_name": "CSV30B"})
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).offset(1).limit(1)
    )
    org_a = result.scalar_one().organization_id
    listing_a = await _setup_listing(db_session, org_a, "ISO002")
    csv_bytes = _make_csv([{"listing_id": listing_a.id, "title": "Title"}])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token_a}"})
    job_id = r.json()["job_id"]
    r2 = await client.get(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_org_isolation_convert(client, db_session):
    token_a = await _register_and_login(client, {"email": "csv31a@test.com", "password": "Pw12345!", "full_name": "CSV31A"})
    token_b = await _register_and_login(client, {"email": "csv31b@test.com", "password": "Pw12345!", "full_name": "CSV31B"})
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).offset(1).limit(1)
    )
    org_a = result.scalar_one().organization_id
    listing_a = await _setup_listing(db_session, org_a, "ISO003", title="Old")
    csv_bytes = _make_csv([{"listing_id": listing_a.id, "title": "New Hacker Title"}])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token_a}"})
    job_id = r.json()["job_id"]
    r2 = await client.post(f"{JOBS_URL}/{job_id}/convert", json={}, headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


# ── target_listing_ids / bulk edit backward compat ────────────────────────────

@pytest.mark.asyncio
async def test_existing_bulk_edit_changes_apply_to_all(client, db_session):
    """Changes without target_listing_ids still apply to all selected listings."""
    token = await _register_and_login(client, {"email": "csv32@test.com", "password": "Pw12345!", "full_name": "CSV32"})
    org_id = await _get_org_id(db_session)
    l1 = await _setup_listing(db_session, org_id, "BKWD001", title="Old One")
    l2 = await _setup_listing(db_session, org_id, "BKWD002", title="Old Two")
    r = await client.post(
        "/api/v1/bulk-edit/sessions",
        json={"listing_ids": [l1.id, l2.id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = r.json()["id"]
    await client.post(
        f"/api/v1/bulk-edit/sessions/{session_id}/changes",
        json={"field_name": "sku", "operation": "set", "operation_value": "NEW-SKU"},
        headers={"Authorization": f"Bearer {token}"},
    )
    r2 = await client.post(
        f"/api/v1/bulk-edit/sessions/{session_id}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["summary"]["preview_items"] == 2
    assert data["summary"]["invalid"] == 0


@pytest.mark.asyncio
async def test_csv_generated_changes_apply_per_listing(client, db_session):
    """CSV-generated changes with target_listing_ids apply only to their target."""
    token = await _register_and_login(client, {"email": "csv33@test.com", "password": "Pw12345!", "full_name": "CSV33"})
    org_id = await _get_org_id(db_session)
    l1 = await _setup_listing(db_session, org_id, "TGT001", title="Old A")
    l2 = await _setup_listing(db_session, org_id, "TGT002", title="Old B")
    csv_bytes = _make_csv([
        {"listing_id": l1.id, "title": "New Title A For L1 Only"},
        {"listing_id": l2.id, "title": "New Title B For L2 Only"},
    ])
    r = await client.post(IMPORT_URL, files={"file": ("t.csv", csv_bytes, "text/csv")}, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["job_id"]
    r2 = await client.post(
        f"{JOBS_URL}/{job_id}/convert",
        json={"ignore_invalid": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    session_id = r2.json()["bulk_edit_session_id"]
    r3 = await client.post(
        f"/api/v1/bulk-edit/sessions/{session_id}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 200
    from app.models.bulk_edit_preview_item import BulkEditPreviewItem
    items_r = await db_session.execute(
        select(BulkEditPreviewItem).where(BulkEditPreviewItem.bulk_edit_session_id == session_id)
    )
    items = {item.listing_id: item for item in items_r.scalars().all()}
    assert items[l1.id].after_data["title"] == "New Title A For L1 Only"
    assert items[l2.id].after_data["title"] == "New Title B For L2 Only"
