"""
Sprint 7 tests: bulk edit session CRUD, change management, preview generation,
validation logic, apply stub, org isolation.
No Etsy API calls. No Listing rows modified by apply stub.
"""
import pytest
import uuid
from sqlalchemy import select

from app.services.bulk_edit import (
    apply_change_to_listing_data,
    validate_listing_data,
    compute_diff,
    build_before_data,
)
from app.models.bulk_edit_change import BulkEditChange

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
SESSIONS_URL = "/api/v1/bulk-edit/sessions"


async def _register_and_login(client, user: dict) -> str:
    await client.post(REGISTER_URL, json={**user, "terms_accepted": True})
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _setup_listing(db_session, org_id: str, etsy_id: str = "10001", **kwargs):
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"bulk_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(organization_id=org_id, etsy_shop_id=shop_etsy_id, shop_name="Bulk Shop", is_connected=True)
        db_session.add(shop)
        await db_session.flush()
        token = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake"),
            refresh_token_enc=encrypt_token("fake_r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scopes="listings_r",
        )
        db_session.add(token)

    listing = Listing(
        organization_id=org_id,
        etsy_shop_id=shop.id,
        etsy_listing_id=etsy_id,
        title=kwargs.get("title", f"Test Listing {etsy_id}"),
        state="active",
        price_amount=kwargs.get("price_amount", 1000),
        quantity=kwargs.get("quantity", 5),
        tags=kwargs.get("tags", ["handmade"]),
        **{k: v for k, v in kwargs.items() if k not in ("title", "price_amount", "quantity", "tags")},
    )
    db_session.add(listing)
    await db_session.commit()
    return listing


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    return member.organization_id


# ── pure-function unit tests ───────────────────────────────────────────────────

def _make_change(field_name: str, operation: str, operation_value=None) -> BulkEditChange:
    c = BulkEditChange()
    c.field_name = field_name
    c.operation = operation
    c.operation_value = operation_value
    return c


def test_apply_set_title():
    before = {"title": "Old Title", "tags": []}
    change = _make_change("title", "set", "New Title")
    after = apply_change_to_listing_data(before, change)
    assert after["title"] == "New Title"
    assert before["title"] == "Old Title"  # no mutation


def test_apply_append_title():
    before = {"title": "Handmade Mug", "tags": []}
    change = _make_change("title", "append", " — Blue Edition")
    after = apply_change_to_listing_data(before, change)
    assert after["title"] == "Handmade Mug — Blue Edition"


def test_apply_prepend_title():
    before = {"title": "Mug", "tags": []}
    change = _make_change("title", "prepend", "Handmade ")
    after = apply_change_to_listing_data(before, change)
    assert after["title"] == "Handmade Mug"


def test_apply_replace_title():
    before = {"title": "Blue Mug for Kids", "tags": []}
    change = _make_change("title", "replace", {"find": "Blue", "replace": "Red"})
    after = apply_change_to_listing_data(before, change)
    assert after["title"] == "Red Mug for Kids"


def test_apply_add_tag():
    before = {"title": "X", "tags": ["handmade"]}
    change = _make_change("tags", "add_tag", "gift")
    after = apply_change_to_listing_data(before, change)
    assert "gift" in after["tags"]
    assert "handmade" in after["tags"]


def test_apply_add_tag_no_duplicate():
    before = {"title": "X", "tags": ["handmade"]}
    change = _make_change("tags", "add_tag", "handmade")
    after = apply_change_to_listing_data(before, change)
    assert after["tags"].count("handmade") == 1


def test_apply_remove_tag():
    before = {"title": "X", "tags": ["handmade", "gift"]}
    change = _make_change("tags", "remove_tag", "gift")
    after = apply_change_to_listing_data(before, change)
    assert "gift" not in after["tags"]
    assert "handmade" in after["tags"]


def test_apply_percentage_change_price():
    before = {"title": "X", "tags": [], "price_amount": 1000}
    change = _make_change("price_amount", "percentage_change", 10)
    after = apply_change_to_listing_data(before, change)
    assert after["price_amount"] == 1100


def test_apply_fixed_amount_change_price():
    before = {"title": "X", "tags": [], "price_amount": 1000}
    change = _make_change("price_amount", "fixed_amount_change", 200)
    after = apply_change_to_listing_data(before, change)
    assert after["price_amount"] == 1200


def test_apply_unknown_field_is_noop():
    before = {"title": "X", "tags": []}
    change = _make_change("nonexistent_field", "set", "value")
    after = apply_change_to_listing_data(before, change)
    assert after == before


def test_validate_empty_title_invalid():
    result = validate_listing_data({"title": "", "tags": []})
    assert result["status"] == "invalid"
    fields = [m["field"] for m in result["messages"]]
    assert "title" in fields


def test_validate_short_title_warning():
    result = validate_listing_data({"title": "Hi", "tags": []})
    assert result["status"] == "warning"


def test_validate_title_too_long_invalid():
    result = validate_listing_data({"title": "A" * 141, "tags": []})
    assert result["status"] == "invalid"


def test_validate_tags_too_many_invalid():
    tags = [str(i) for i in range(14)]
    result = validate_listing_data({"title": "Good Title Long Enough Here", "tags": tags})
    assert result["status"] == "invalid"
    fields = [m["field"] for m in result["messages"]]
    assert "tags" in fields


def test_validate_tag_too_long_invalid():
    result = validate_listing_data({"title": "Good Title Long Enough Here", "tags": ["a" * 21]})
    assert result["status"] == "invalid"


def test_validate_negative_price_invalid():
    result = validate_listing_data({"title": "Good Title Long Enough Here", "tags": [], "price_amount": -1})
    assert result["status"] == "invalid"
    fields = [m["field"] for m in result["messages"]]
    assert "price_amount" in fields


def test_validate_zero_price_warning():
    result = validate_listing_data({"title": "Good Title Long Enough Here", "tags": [], "price_amount": 0})
    assert result["status"] == "warning"


def test_validate_negative_quantity_invalid():
    result = validate_listing_data({"title": "Good Title Long Enough Here", "tags": [], "quantity": -1})
    assert result["status"] == "invalid"


def test_validate_processing_min_gt_max_invalid():
    result = validate_listing_data({
        "title": "Good Title Long Enough Here", "tags": [],
        "processing_min": 5, "processing_max": 2
    })
    assert result["status"] == "invalid"
    fields = [m["field"] for m in result["messages"]]
    assert "processing_min" in fields


def test_validate_personalizable_required_without_enabled_warning():
    result = validate_listing_data({
        "title": "Good Title Long Enough Here", "tags": [],
        "personalization_is_required": True,
        "is_personalizable": False,
    })
    assert result["status"] == "warning"


def test_compute_diff_basic():
    before = {"title": "Old", "price_amount": 1000, "tags": ["a"]}
    after = {"title": "New", "price_amount": 1000, "tags": ["a"]}
    diff = compute_diff(before, after)
    assert "title" in diff
    assert diff["title"]["before"] == "Old"
    assert diff["title"]["after"] == "New"
    assert "price_amount" not in diff


def test_compute_diff_empty_when_no_changes():
    data = {"title": "Same", "price_amount": 500}
    diff = compute_diff(data, data.copy())
    assert diff == {}


# ── API integration tests ──────────────────────────────────────────────────────

async def test_create_session_requires_auth(client):
    r = await client.post(SESSIONS_URL, json={"listing_ids": ["x"]})
    assert r.status_code == 403


async def test_create_session_rejects_empty_listing_ids(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_empty@example.com", "password": "password123",
        "full_name": "E", "organization_name": "Empty Org",
    })
    r = await client.post(SESSIONS_URL, json={"listing_ids": []}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (400, 422)


async def test_create_session_rejects_listing_from_another_org(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "be_iso_a@example.com", "password": "password123",
        "full_name": "A", "organization_name": "Iso A",
    })
    await _register_and_login(client, {
        "email": "be_iso_b@example.com", "password": "password123",
        "full_name": "B", "organization_name": "Iso B",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "iso_b_01")

    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [listing.id]},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 400


async def test_create_session_deduplicates_listing_ids(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_dedup@example.com", "password": "password123",
        "full_name": "D", "organization_name": "Dedup Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "dedup_01")

    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [listing.id, listing.id, listing.id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["selected_count"] == 1


async def test_list_sessions(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_list@example.com", "password": "password123",
        "full_name": "L", "organization_name": "List Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "list_01")

    await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    r = await client.get(SESSIONS_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_add_change_accepts_title_append(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_ch_ok@example.com", "password": "password123",
        "full_name": "C", "organization_name": "Change OK Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "ch_ok_01")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    r2 = await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "append", "operation_value": " — Sale"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 201
    data = r2.json()
    assert data["field_name"] == "title"
    assert data["operation"] == "append"


async def test_add_change_rejects_unknown_field(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_bad_field@example.com", "password": "password123",
        "full_name": "X", "organization_name": "Bad Field Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "bf_01")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    r2 = await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "etsy_secret_field", "operation": "set", "operation_value": "hack"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 400


async def test_add_change_rejects_incompatible_operation(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_bad_op@example.com", "password": "password123",
        "full_name": "O", "organization_name": "Bad Op Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "bo_01")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    r2 = await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "is_personalizable", "operation": "append", "operation_value": "x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 400


async def test_generate_preview_creates_one_per_listing(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_prev@example.com", "password": "password123",
        "full_name": "P", "organization_name": "Preview Org",
    })
    org_id = await _get_org_id(db_session)
    l1 = await _setup_listing(db_session, org_id, "prev_01", title="Listing One for Preview")
    l2 = await _setup_listing(db_session, org_id, "prev_02", title="Listing Two for Preview")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [l1.id, l2.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "append", "operation_value": " — NEW"},
        headers={"Authorization": f"Bearer {token}"},
    )

    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data = r2.json()
    assert data["summary"]["selected_count"] == 2
    assert data["summary"]["preview_items"] == 2
    assert data["session"]["status"] == "preview_ready"


async def test_preview_diff_includes_before_after_title(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_diff@example.com", "password": "password123",
        "full_name": "Df", "organization_name": "Diff Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "diff_01", title="Original Title For Testing")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "set", "operation_value": "New Replaced Title Here"},
        headers={"Authorization": f"Bearer {token}"},
    )

    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})

    r2 = await client.get(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    items = r2.json()["items"]
    assert len(items) == 1
    diff = items[0]["diff"]
    assert "title" in diff
    assert diff["title"]["before"] == "Original Title For Testing"
    assert diff["title"]["after"] == "New Replaced Title Here"


async def test_get_preview_pagination(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_page@example.com", "password": "password123",
        "full_name": "Pg", "organization_name": "Page Org",
    })
    org_id = await _get_org_id(db_session)
    listings = []
    for i in range(3):
        l = await _setup_listing(db_session, org_id, f"page_{i:02d}", title=f"Pageable Listing Number {i:02d}")
        listings.append(l)

    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [l.id for l in listings]},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "append", "operation_value": " x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})

    r2 = await client.get(
        f"{SESSIONS_URL}/{session_id}/preview?page=1&per_page=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2

    r3 = await client.get(
        f"{SESSIONS_URL}/{session_id}/preview?page=2&per_page=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(r3.json()["items"]) == 1


async def test_apply_draft_session_returns_400(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_apply@example.com", "password": "password123",
        "full_name": "Ap", "organization_name": "Apply Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "apply_01", title="Apply Test Listing Here")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    # Draft session (no preview generated) must be rejected
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400
    assert "preview_ready" in r2.json()["detail"]


async def test_apply_does_not_modify_listing(client, db_session):
    from app.models.listing import Listing
    token = await _register_and_login(client, {
        "email": "be_safe@example.com", "password": "password123",
        "full_name": "Sf", "organization_name": "Safe Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "safe_01", title="Safe Original Title Now")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "set", "operation_value": "MUTATED TITLE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})
    await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    result = await db_session.execute(select(Listing).where(Listing.id == listing.id))
    db_listing = result.scalar_one()
    assert db_listing.title == "Safe Original Title Now"


async def test_canceled_session_cannot_add_changes(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_cancel@example.com", "password": "password123",
        "full_name": "Cn", "organization_name": "Cancel Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "cancel_01", title="Cancelable Listing Here Now")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    await client.delete(f"{SESSIONS_URL}/{session_id}", headers={"Authorization": f"Bearer {token}"})

    r2 = await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "set", "operation_value": "X"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 400


async def test_org_isolation_sessions(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "be_org_a@example.com", "password": "password123",
        "full_name": "OA", "organization_name": "Org A Bulk",
    })
    token_b = await _register_and_login(client, {
        "email": "be_org_b@example.com", "password": "password123",
        "full_name": "OB", "organization_name": "Org B Bulk",
    })

    org_a_id = await _get_org_id(db_session)
    listing_a = await _setup_listing(db_session, org_a_id, "org_iso_a_01", title="Org A Listing For Isolation")

    # re-login user A to get org A properly
    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing_a.id]}, headers={"Authorization": f"Bearer {token_a}"})
    if r.status_code == 400:
        # org_a_id was actually org_b's — get org for user A
        from app.models.organization_member import OrganizationMember
        from app.models.user import User
        user_a_email = "be_org_a@example.com"
        u_r = await db_session.execute(select(User).where(User.email == user_a_email))
        u = u_r.scalar_one()
        m_r = await db_session.execute(select(OrganizationMember).where(OrganizationMember.user_id == u.id).limit(1))
        m = m_r.scalar_one()
        listing_a.organization_id = m.organization_id
        await db_session.commit()
        r = await client.post(SESSIONS_URL, json={"listing_ids": [listing_a.id]}, headers={"Authorization": f"Bearer {token_a}"})

    assert r.status_code == 201
    session_id = r.json()["id"]

    r2 = await client.get(f"{SESSIONS_URL}/{session_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


async def test_delete_session_sets_canceled(client, db_session):
    token = await _register_and_login(client, {
        "email": "be_del@example.com", "password": "password123",
        "full_name": "Del", "organization_name": "Del Org",
    })
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "del_01", title="Deletable Session Listing Here")

    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]

    r2 = await client.delete(f"{SESSIONS_URL}/{session_id}", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "canceled"
