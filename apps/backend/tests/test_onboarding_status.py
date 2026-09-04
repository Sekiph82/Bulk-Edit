"""Tests for the durable dashboard onboarding signal (Phase C).

GET /api/v1/bulk-edit/onboarding-status returns has_completed_bulk_edit based
on all-time apply-job evidence (success_count > 0), NOT the monthly usage
counter that regressed the dashboard to unchecked after a billing rollover.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.organization_member import OrganizationMember
from app.models.bulk_edit_apply_job import BulkEditApplyJob

URL = "/api/v1/bulk-edit/onboarding-status"


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post("/api/v1/auth/register", json={
        "email": email, "password": "Test1234!", "full_name": "Test",
        "organization_name": org, "terms_accepted": True,
    })
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


async def _first_org_id(db_session) -> str:
    return (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id


def _job(org_id: str, *, success=0, failed=0, skipped=0, status="completed") -> BulkEditApplyJob:
    return BulkEditApplyJob(
        id=str(uuid.uuid4()), organization_id=org_id,
        bulk_edit_session_id=str(uuid.uuid4()), status=status,
        total_items=success + failed + skipped,
        success_count=success, failure_count=failed, skipped_count=skipped,
    )


@pytest.mark.anyio
async def test_onboarding_requires_auth(client: AsyncClient):
    resp = await client.get(URL)
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_no_apply_job_is_incomplete(client: AsyncClient):
    token = await _register_and_login(client, "onb_none@test.com", "OnbNone")
    resp = await client.get(URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["has_completed_bulk_edit"] is False


@pytest.mark.anyio
async def test_succeeded_apply_completes(client: AsyncClient, db_session):
    token = await _register_and_login(client, "onb_ok@test.com", "OnbOk")
    org_id = await _first_org_id(db_session)
    db_session.add(_job(org_id, success=3, status="completed"))
    await db_session.commit()
    resp = await client.get(URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["has_completed_bulk_edit"] is True


@pytest.mark.anyio
async def test_partially_failed_with_success_completes(client: AsyncClient, db_session):
    token = await _register_and_login(client, "onb_partial@test.com", "OnbPartial")
    org_id = await _first_org_id(db_session)
    db_session.add(_job(org_id, success=1, failed=2, status="completed_with_errors"))
    await db_session.commit()
    resp = await client.get(URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["has_completed_bulk_edit"] is True


@pytest.mark.anyio
async def test_reverted_successful_job_still_completes(client: AsyncClient, db_session):
    """A revert is a separate RevertJob and never lowers the apply job's
    success_count, so a reverted successful bulk edit still counts."""
    token = await _register_and_login(client, "onb_revert@test.com", "OnbRevert")
    org_id = await _first_org_id(db_session)
    # status could read "reverted" via canonical mapping, but success_count stays > 0
    db_session.add(_job(org_id, success=2, status="completed"))
    await db_session.commit()
    resp = await client.get(URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["has_completed_bulk_edit"] is True


@pytest.mark.anyio
async def test_skipped_only_does_not_complete(client: AsyncClient, db_session):
    token = await _register_and_login(client, "onb_skip@test.com", "OnbSkip")
    org_id = await _first_org_id(db_session)
    db_session.add(_job(org_id, skipped=3, status="completed"))
    await db_session.commit()
    resp = await client.get(URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["has_completed_bulk_edit"] is False


@pytest.mark.anyio
async def test_failed_only_does_not_complete(client: AsyncClient, db_session):
    token = await _register_and_login(client, "onb_fail@test.com", "OnbFail")
    org_id = await _first_org_id(db_session)
    db_session.add(_job(org_id, failed=4, status="failed"))
    await db_session.commit()
    resp = await client.get(URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["has_completed_bulk_edit"] is False


@pytest.mark.anyio
async def test_cross_org_job_not_counted(client: AsyncClient, db_session):
    token = await _register_and_login(client, "onb_a@test.com", "OnbOrgA")
    await _register_and_login(client, "onb_b@test.com", "OnbOrgB")
    # Attribute a successful job to some OTHER org, not org A's.
    other_org = str(uuid.uuid4())
    db_session.add(_job(other_org, success=5, status="completed"))
    await db_session.commit()
    resp = await client.get(URL, headers={"Authorization": f"Bearer {token}"})
    # org A (the token's org) has no jobs of its own
    assert resp.json()["has_completed_bulk_edit"] is False
