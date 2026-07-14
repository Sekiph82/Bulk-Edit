"""Tests for video generator endpoint."""

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
        "terms_accepted": True,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


# --- Auth ---

@pytest.mark.anyio
async def test_video_status_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/video-generator/status")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_video_templates_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/video-generator/templates")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_video_render_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/video-generator/render", json={
        "template_id": "clean_zoom",
        "image_urls": ["http://example.com/a.jpg"],
        "aspect_ratio": "9:16",
        "duration_seconds": 10,
    })
    assert resp.status_code in (401, 403)


# --- Status endpoint ---

@pytest.mark.anyio
async def test_video_status_not_configured(client: AsyncClient):
    token = await _register_and_login(client, "vid_u1@test.com", "VidOrg1")
    resp = await client.get(
        "/api/v1/video-generator/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "renderer_enabled" in data
    assert data["renderer_enabled"] is False
    assert "renderer_available" in data
    assert data["renderer_available"] is False
    assert "message" in data


# --- Templates endpoint ---

@pytest.mark.anyio
async def test_video_templates_returns_aspect_ratios_and_specs(client: AsyncClient):
    token = await _register_and_login(client, "vid_u2@test.com", "VidOrg2")
    resp = await client.get(
        "/api/v1/video-generator/templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "templates" in data
    assert "aspect_ratios" in data
    assert "etsy_specs" in data
    assert "renderer_enabled" in data
    assert "renderer_available" in data

    # Verify aspect ratios
    ar_values = [ar["value"] for ar in data["aspect_ratios"]]
    assert "9:16" in ar_values
    assert "1:1" in ar_values
    assert "4:5" in ar_values
    assert "16:9" in ar_values

    # Verify Etsy specs
    specs = data["etsy_specs"]
    assert specs["max_file_size_mb"] == 100
    assert specs["min_duration_seconds"] == 5
    assert specs["max_duration_seconds"] == 15
    assert specs["min_resolution_px"] == 500


@pytest.mark.anyio
async def test_video_templates_clean_zoom_implemented(client: AsyncClient):
    token = await _register_and_login(client, "vid_u3@test.com", "VidOrg3")
    resp = await client.get(
        "/api/v1/video-generator/templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    templates = resp.json()["templates"]
    clean_zoom = next((t for t in templates if t["id"] == "clean_zoom"), None)
    assert clean_zoom is not None
    assert clean_zoom["implemented"] is True


@pytest.mark.anyio
async def test_video_templates_soft_pan_not_implemented(client: AsyncClient):
    token = await _register_and_login(client, "vid_u4@test.com", "VidOrg4")
    resp = await client.get(
        "/api/v1/video-generator/templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    templates = resp.json()["templates"]
    soft_pan = next((t for t in templates if t["id"] == "soft_pan"), None)
    assert soft_pan is not None
    assert soft_pan["implemented"] is False


# --- Render endpoint validation ---

@pytest.mark.anyio
async def test_render_fails_when_renderer_disabled(client: AsyncClient):
    token = await _register_and_login(client, "vid_u5@test.com", "VidOrg5")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "clean_zoom",
            "image_urls": ["http://example.com/a.jpg"],
            "aspect_ratio": "9:16",
            "duration_seconds": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # Renderer is disabled in test env — expect 503
    assert resp.status_code == 503


@pytest.mark.anyio
async def test_render_rejects_invalid_aspect_ratio(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    token = await _register_and_login(client, "vid_u6@test.com", "VidOrg6")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "clean_zoom",
            "image_urls": ["http://example.com/a.jpg"],
            "aspect_ratio": "bad:ratio",
            "duration_seconds": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "aspect ratio" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_render_rejects_duration_below_5s(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    token = await _register_and_login(client, "vid_u7@test.com", "VidOrg7")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "clean_zoom",
            "image_urls": ["http://example.com/a.jpg"],
            "aspect_ratio": "9:16",
            "duration_seconds": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "5 seconds" in resp.json()["detail"]


@pytest.mark.anyio
async def test_render_rejects_duration_above_15s(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    token = await _register_and_login(client, "vid_u8@test.com", "VidOrg8")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "clean_zoom",
            "image_urls": ["http://example.com/a.jpg"],
            "aspect_ratio": "9:16",
            "duration_seconds": 20,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "15 seconds" in resp.json()["detail"]


@pytest.mark.anyio
async def test_render_rejects_unimplemented_template(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    token = await _register_and_login(client, "vid_u9@test.com", "VidOrg9")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "soft_pan",
            "image_urls": ["http://example.com/a.jpg"],
            "aspect_ratio": "9:16",
            "duration_seconds": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "not yet available" in resp.json()["detail"]


@pytest.mark.anyio
async def test_render_rejects_empty_image_urls(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    token = await _register_and_login(client, "vid_u10@test.com", "VidOrg10")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "clean_zoom",
            "image_urls": [],
            "aspect_ratio": "9:16",
            "duration_seconds": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# --- Response schema: no file_path / stored_filename exposure ---

@pytest.mark.anyio
async def test_render_status_does_not_expose_file_path(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    token = await _register_and_login(client, "vid_u11@test.com", "VidOrg11")
    post = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "clean_zoom",
            "image_urls": ["http://example.com/a.jpg"],
            "aspect_ratio": "9:16",
            "duration_seconds": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert post.status_code == 202
    render_id = post.json()["id"]

    resp = await client.get(
        f"/api/v1/video-generator/renders/{render_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "file_path" not in data
    assert "stored_filename" not in data
    assert "output_path" not in data


# --- Org isolation ---

@pytest.mark.anyio
async def test_render_status_isolated_across_orgs(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    token_a = await _register_and_login(client, "vid_iso_a@test.com", "VidOrgIsoA")
    token_b = await _register_and_login(client, "vid_iso_b@test.com", "VidOrgIsoB")

    post = await client.post(
        "/api/v1/video-generator/render",
        json={
            "template_id": "clean_zoom",
            "image_urls": ["http://example.com/a.jpg"],
            "aspect_ratio": "9:16",
            "duration_seconds": 10,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert post.status_code == 202
    render_id = post.json()["id"]

    resp = await client.get(
        f"/api/v1/video-generator/renders/{render_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


# --- List renders endpoint ---

@pytest.mark.anyio
async def test_list_renders_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/video-generator/renders")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_list_renders_empty_for_new_org(client: AsyncClient):
    token = await _register_and_login(client, "vid_list_empty@test.com", "VidListEmpty")
    resp = await client.get(
        "/api/v1/video-generator/renders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_list_renders_only_returns_completed_and_own_org(client: AsyncClient, db_session):
    from app.models.video_render import VideoRender

    token = await _register_and_login(client, "vid_list_a@test.com", "VidListOrgA")
    token_b = await _register_and_login(client, "vid_list_b@test.com", "VidListOrgB")

    from sqlalchemy import select
    from app.models.organization_member import OrganizationMember
    org_a = (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id

    db_session.add(VideoRender(organization_id=org_a, template_id="clean_zoom", status="completed", is_etsy_ready=True, file_path="/tmp/a.mp4"))
    db_session.add(VideoRender(organization_id=org_a, template_id="clean_zoom", status="pending"))
    await db_session.commit()

    resp_a = await client.get(
        "/api/v1/video-generator/renders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
    assert resp_a.json()[0]["status"] == "completed"

    resp_b = await client.get(
        "/api/v1/video-generator/renders",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    assert resp_b.json() == []


@pytest.mark.anyio
async def test_list_renders_etsy_ready_only_filter(client: AsyncClient, db_session):
    from app.models.video_render import VideoRender
    from sqlalchemy import select
    from app.models.organization_member import OrganizationMember

    token = await _register_and_login(client, "vid_list_filter@test.com", "VidListFilter")
    org_id = (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id

    db_session.add(VideoRender(organization_id=org_id, template_id="clean_zoom", status="completed", is_etsy_ready=True, file_path="/tmp/ready.mp4"))
    db_session.add(VideoRender(organization_id=org_id, template_id="clean_zoom", status="completed", is_etsy_ready=False, file_path="/tmp/notready.mp4"))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/video-generator/renders?etsy_ready_only=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["is_etsy_ready"] is True


# --- Upload endpoint ---

@pytest.mark.anyio
async def test_upload_video_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/video-generator/uploads",
        files={"file": ("clip.mp4", b"fake mp4 bytes", "video/mp4")},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_upload_video_rejects_unsupported_file_type(client: AsyncClient):
    token = await _register_and_login(client, "vid_upload_bad@test.com", "VidUploadBad")
    resp = await client.post(
        "/api/v1/video-generator/uploads",
        files={"file": ("clip.mov", b"fake mov bytes", "video/quicktime")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "MP4" in resp.json()["detail"]


@pytest.mark.anyio
async def test_upload_video_unavailable_when_ffprobe_missing(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.video_generator.check_ffprobe",
        lambda path=None: ("dependency_missing", "ffprobe not found."),
    )
    token = await _register_and_login(client, "vid_upload_noffprobe@test.com", "VidUploadNoFfprobe")
    resp = await client.post(
        "/api/v1/video-generator/uploads",
        files={"file": ("clip.mp4", b"fake mp4 bytes", "video/mp4")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 503


@pytest.mark.anyio
async def test_upload_video_rejects_oversized_file(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffprobe", lambda path=None: ("working", "ok"))
    monkeypatch.setattr("app.api.v1.video_generator.ETSY_MAX_FILE_SIZE_BYTES", 10)

    token = await _register_and_login(client, "vid_upload_big@test.com", "VidUploadBig")
    resp = await client.post(
        "/api/v1/video-generator/uploads",
        files={"file": ("clip.mp4", b"x" * 1000, "video/mp4")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 413


@pytest.mark.anyio
async def test_upload_video_succeeds_and_is_selectable(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffprobe", lambda path=None: ("working", "ok"))
    monkeypatch.setattr(
        "app.api.v1.video_generator.probe_video_file",
        lambda path, ffprobe_path=None: {"duration_seconds": 8.0, "width": 1080, "height": 1920},
    )

    token = await _register_and_login(client, "vid_upload_ok@test.com", "VidUploadOk")
    resp = await client.post(
        "/api/v1/video-generator/uploads",
        files={"file": ("clip.mp4", b"fake mp4 bytes", "video/mp4")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["source"] == "uploaded"
    assert data["status"] == "completed"
    assert data["aspect_ratio"] == "9:16"
    assert data["is_etsy_ready"] is True

    # Appears in the renders list used by Add Video / Replace Video selectors
    listed = await client.get(
        "/api/v1/video-generator/renders?etsy_ready_only=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    ids = [r["id"] for r in listed.json()]
    assert data["id"] in ids


@pytest.mark.anyio
async def test_upload_video_rejects_unprobeable_file(client: AsyncClient, monkeypatch):
    from app.services.video_renderer import ProbeError

    monkeypatch.setattr("app.api.v1.video_generator.check_ffprobe", lambda path=None: ("working", "ok"))

    def _raise(path, ffprobe_path=None):
        raise ProbeError("No video stream found in file.")

    monkeypatch.setattr("app.api.v1.video_generator.probe_video_file", _raise)

    token = await _register_and_login(client, "vid_upload_unprobeable@test.com", "VidUploadUnprobeable")
    resp = await client.post(
        "/api/v1/video-generator/uploads",
        files={"file": ("clip.mp4", b"not really a video", "video/mp4")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
