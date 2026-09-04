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


@pytest.mark.anyio
async def test_list_renders_all_statuses_powers_history_view(client: AsyncClient, db_session):
    """M13.05: the default (all_statuses=False, unchanged) still hides
    pending/failed renders for the replace_video picker; all_statuses=True
    (used by the Video Generator's own render history) must include them."""
    from app.models.video_render import VideoRender
    from sqlalchemy import select
    from app.models.organization_member import OrganizationMember

    token = await _register_and_login(client, "vid_list_all@test.com", "VidListAll")
    org_id = (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id

    db_session.add(VideoRender(organization_id=org_id, template_id="clean_zoom", status="completed", is_etsy_ready=True, file_path="/tmp/done.mp4"))
    db_session.add(VideoRender(organization_id=org_id, template_id="clean_zoom", status="pending"))
    db_session.add(VideoRender(organization_id=org_id, template_id="clean_zoom", status="failed", error_message="Render error"))
    await db_session.commit()

    resp_default = await client.get(
        "/api/v1/video-generator/renders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(resp_default.json()) == 1

    resp_all = await client.get(
        "/api/v1/video-generator/renders?all_statuses=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_all.status_code == 200
    statuses = {r["status"] for r in resp_all.json()}
    assert statuses == {"completed", "pending", "failed"}
    failed = next(r for r in resp_all.json() if r["status"] == "failed")
    assert failed["error_message"] == "Render error"


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


# --- Download endpoint (M13.05: "Download to your computer") ---

@pytest.mark.anyio
async def test_download_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/video-generator/renders/some-id/download")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_download_completed_render_succeeds(client: AsyncClient, db_session, tmp_path):
    from app.models.video_render import VideoRender
    from sqlalchemy import select
    from app.models.organization_member import OrganizationMember

    token = await _register_and_login(client, "vid_dl_ok@test.com", "VidDlOk")
    org_id = (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id

    mp4 = tmp_path / "done.mp4"
    mp4.write_bytes(b"\x00\x00\x00\x18ftypmp42fake")
    render = VideoRender(organization_id=org_id, template_id="clean_zoom", status="completed",
                         is_etsy_ready=True, file_path=str(mp4))
    db_session.add(render)
    await db_session.commit()
    await db_session.refresh(render)

    resp = await client.get(
        f"/api/v1/video-generator/renders/{render.id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "video/mp4"
    # Safe filename derived from the render id only — no user input, no secrets.
    assert f"product_video_{render.id[:8]}.mp4" in resp.headers.get("content-disposition", "")


@pytest.mark.anyio
async def test_download_rejects_non_completed_render(client: AsyncClient, db_session):
    from app.models.video_render import VideoRender
    from sqlalchemy import select
    from app.models.organization_member import OrganizationMember

    token = await _register_and_login(client, "vid_dl_pending@test.com", "VidDlPending")
    org_id = (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id

    render = VideoRender(organization_id=org_id, template_id="clean_zoom", status="rendering")
    db_session.add(render)
    await db_session.commit()
    await db_session.refresh(render)

    resp = await client.get(
        f"/api/v1/video-generator/renders/{render.id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_download_missing_file_returns_410(client: AsyncClient, db_session):
    from app.models.video_render import VideoRender
    from sqlalchemy import select
    from app.models.organization_member import OrganizationMember

    token = await _register_and_login(client, "vid_dl_gone@test.com", "VidDlGone")
    org_id = (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id

    render = VideoRender(organization_id=org_id, template_id="clean_zoom", status="completed",
                         file_path="/tmp/does-not-exist-xyz.mp4")
    db_session.add(render)
    await db_session.commit()
    await db_session.refresh(render)

    resp = await client.get(
        f"/api/v1/video-generator/renders/{render.id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 410


@pytest.mark.anyio
async def test_download_isolated_across_orgs(client: AsyncClient, db_session, tmp_path):
    """A render belonging to org A must not be downloadable by org B."""
    from app.models.video_render import VideoRender
    from sqlalchemy import select
    from app.models.organization_member import OrganizationMember

    token_a = await _register_and_login(client, "vid_dl_a@test.com", "VidDlOrgA")
    token_b = await _register_and_login(client, "vid_dl_b@test.com", "VidDlOrgB")
    org_a = (await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id

    mp4 = tmp_path / "a.mp4"
    mp4.write_bytes(b"fake")
    render = VideoRender(organization_id=org_a, template_id="clean_zoom", status="completed", file_path=str(mp4))
    db_session.add(render)
    await db_session.commit()
    await db_session.refresh(render)

    resp = await client.get(
        f"/api/v1/video-generator/renders/{render.id}/download",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


# --- No-auto-upload guarantee (M13.05 hard product rule) ---

@pytest.mark.anyio
async def test_generate_render_does_not_create_media_upload_job(client: AsyncClient, db_session, monkeypatch):
    """Creating a render must NEVER create a media job or otherwise queue an
    Etsy upload. Upload to Etsy is an explicit, separate user action."""
    from app.models.bulk_edit_media_job import BulkEditMediaJob
    from sqlalchemy import select, func

    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))

    # Neutralize the background render task — it opens its own DB/HTTP clients
    # against real services; we only care that the render *endpoint* never
    # queues an Etsy upload / media job.
    async def _noop_render(**kwargs):
        return None
    monkeypatch.setattr("app.api.v1.video_generator._run_render", _noop_render)

    token = await _register_and_login(client, "vid_noauto@test.com", "VidNoAuto")
    before = (await db_session.execute(select(func.count()).select_from(BulkEditMediaJob))).scalar()

    resp = await client.post(
        "/api/v1/video-generator/render",
        json={"template_id": "clean_zoom", "image_urls": ["https://example.com/a.jpg"],
              "aspect_ratio": "9:16", "duration_seconds": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202

    after = (await db_session.execute(select(func.count()).select_from(BulkEditMediaJob))).scalar()
    assert after == before, "Generating a video must not create any media upload job."


# --- Branding overlay (M13.05C) ---

@pytest.mark.anyio
async def test_render_rejects_invalid_logo_position(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))
    token = await _register_and_login(client, "brand_pos@test.com", "BrandPos")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={"template_id": "clean_zoom", "image_urls": ["https://e/a.jpg"],
              "aspect_ratio": "9:16", "duration_seconds": 10,
              "branding": {"logo_position": "middle"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_render_rejects_invalid_text_placement(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))
    token = await _register_and_login(client, "brand_place@test.com", "BrandPlace")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={"template_id": "clean_zoom", "image_urls": ["https://e/a.jpg"],
              "aspect_ratio": "9:16", "duration_seconds": 10,
              "branding": {"text_placement": "diagonal"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_render_rejects_bad_brand_color(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))
    token = await _register_and_login(client, "brand_color@test.com", "BrandColor")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={"template_id": "clean_zoom", "image_urls": ["https://e/a.jpg"],
              "aspect_ratio": "9:16", "duration_seconds": 10,
              "branding": {"brand_color": "notacolor"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_render_rejects_too_long_headline(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))
    token = await _register_and_login(client, "brand_long@test.com", "BrandLong")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={"template_id": "clean_zoom", "image_urls": ["https://e/a.jpg"],
              "aspect_ratio": "9:16", "duration_seconds": 10,
              "branding": {"headline": "x" * 61}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_render_accepts_valid_branding_and_stores_it(client: AsyncClient, db_session, monkeypatch):
    from app.models.video_render import VideoRender
    from sqlalchemy import select

    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))
    async def _noop_render(**kwargs):
        return None
    monkeypatch.setattr("app.api.v1.video_generator._run_render", _noop_render)

    token = await _register_and_login(client, "brand_ok@test.com", "BrandOk")
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={"template_id": "clean_zoom", "image_urls": ["https://e/a.jpg"],
              "aspect_ratio": "9:16", "duration_seconds": 10,
              "branding": {"headline": "Handmade Mug", "cta_text": "Shop now",
                           "text_placement": "bottom", "brand_color": "#123456"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    rid = resp.json()["id"]
    row = (await db_session.execute(select(VideoRender).where(VideoRender.id == rid))).scalar_one()
    assert row.branding_json is not None
    assert "Handmade Mug" in row.branding_json


@pytest.mark.anyio
async def test_render_with_branding_does_not_create_media_job(client: AsyncClient, db_session, monkeypatch):
    """No-auto-upload guarantee holds with branding present."""
    from app.models.bulk_edit_media_job import BulkEditMediaJob
    from sqlalchemy import select, func

    monkeypatch.setattr("app.api.v1.video_generator.check_ffmpeg", lambda path=None: ("working", "ok"))
    async def _noop_render(**kwargs):
        return None
    monkeypatch.setattr("app.api.v1.video_generator._run_render", _noop_render)

    token = await _register_and_login(client, "brand_noauto@test.com", "BrandNoAuto")
    before = (await db_session.execute(select(func.count()).select_from(BulkEditMediaJob))).scalar()
    resp = await client.post(
        "/api/v1/video-generator/render",
        json={"template_id": "clean_zoom", "image_urls": ["https://e/a.jpg"],
              "aspect_ratio": "9:16", "duration_seconds": 10,
              "branding": {"headline": "Hello"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    after = (await db_session.execute(select(func.count()).select_from(BulkEditMediaJob))).scalar()
    assert after == before


# --- M13.03 gated Etsy video-upload intent + media gate ---

async def _org_id_for(db_session):
    from sqlalchemy import select as _sel
    from app.models.organization_member import OrganizationMember
    return (await db_session.execute(
        _sel(OrganizationMember).order_by(OrganizationMember.created_at.asc()).limit(1)
    )).scalar_one().organization_id


def _completed_render(org_id, tmp_path):
    from app.models.video_render import VideoRender
    p = tmp_path / "r.mp4"; p.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    return VideoRender(organization_id=org_id, template_id="clean_zoom", status="completed",
                       is_etsy_ready=True, file_path=str(p))


def _listing(org_id, etsy_listing_id="111", title="Test Listing"):
    from app.models.listing import Listing
    return Listing(organization_id=org_id, etsy_shop_id="shop-x",
                   etsy_listing_id=etsy_listing_id, title=title, state="active")


@pytest.mark.anyio
async def test_upload_intent_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/video-generator/renders/x/etsy-upload-intent", json={})
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_upload_intent_completed_render_is_gated_no_listing(client: AsyncClient, db_session, tmp_path):
    token = await _register_and_login(client, "intent_ok@test.com", "IntentOk")
    org = await _org_id_for(db_session)
    r = _completed_render(org, tmp_path); db_session.add(r); await db_session.commit(); await db_session.refresh(r)
    resp = await client.post(f"/api/v1/video-generator/renders/{r.id}/etsy-upload-intent",
                             json={}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    d = resp.json()
    assert d["enabled"] is False
    assert d["allowed"] is False
    assert d["no_auto_upload"] is True
    assert d["operation"] is None  # no listing selected


@pytest.mark.anyio
async def test_upload_intent_pending_render_rejected(client: AsyncClient, db_session):
    from app.models.video_render import VideoRender
    token = await _register_and_login(client, "intent_pending@test.com", "IntentPending")
    org = await _org_id_for(db_session)
    r = VideoRender(organization_id=org, template_id="clean_zoom", status="rendering")
    db_session.add(r); await db_session.commit(); await db_session.refresh(r)
    resp = await client.post(f"/api/v1/video-generator/renders/{r.id}/etsy-upload-intent",
                             json={}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_upload_intent_cross_org_render_404(client: AsyncClient, db_session, tmp_path):
    await _register_and_login(client, "intent_a@test.com", "IntentOrgA")
    token_b = await _register_and_login(client, "intent_b@test.com", "IntentOrgB")
    org_a = await _org_id_for(db_session)  # earliest = A
    r = _completed_render(org_a, tmp_path); db_session.add(r); await db_session.commit(); await db_session.refresh(r)
    resp = await client.post(f"/api/v1/video-generator/renders/{r.id}/etsy-upload-intent",
                             json={}, headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_upload_intent_add_vs_replace(client: AsyncClient, db_session, tmp_path):
    from app.models.listing_video import ListingVideo
    token = await _register_and_login(client, "intent_slot@test.com", "IntentSlot")
    org = await _org_id_for(db_session)
    r = _completed_render(org, tmp_path)
    l_novideo = _listing(org, "1001", "No Video Listing")
    l_hasvideo = _listing(org, "1002", "Has Video Listing")
    db_session.add_all([r, l_novideo, l_hasvideo]); await db_session.commit()
    await db_session.refresh(r); await db_session.refresh(l_novideo); await db_session.refresh(l_hasvideo)
    db_session.add(ListingVideo(listing_id=l_hasvideo.id, etsy_video_id="v1", video_url="https://cdn/x.mp4"))
    await db_session.commit()

    # listing with no video → add_video
    resp1 = await client.post(f"/api/v1/video-generator/renders/{r.id}/etsy-upload-intent",
                              json={"listing_id": l_novideo.id}, headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["operation"] == "add_video"
    assert d1["video_slot_synced"] is True
    assert d1["has_existing_video"] is False
    assert d1["allowed"] is False  # flag still off
    assert d1["enabled"] is False

    # listing with a video → replace_video, not supported
    resp2 = await client.post(f"/api/v1/video-generator/renders/{r.id}/etsy-upload-intent",
                              json={"listing_id": l_hasvideo.id}, headers={"Authorization": f"Bearer {token}"})
    d2 = resp2.json()
    assert d2["operation"] == "replace_video"
    assert d2["has_existing_video"] is True
    assert d2["replace_supported"] is False
    assert d2["allowed"] is False


@pytest.mark.anyio
async def test_upload_intent_cross_org_listing_rejected(client: AsyncClient, db_session, tmp_path):
    token = await _register_and_login(client, "intent_xlist_a@test.com", "IntentXA")
    org_a = await _org_id_for(db_session)
    r = _completed_render(org_a, tmp_path)
    other_listing = _listing("some-other-org", "2001")
    db_session.add_all([r, other_listing]); await db_session.commit()
    await db_session.refresh(r); await db_session.refresh(other_listing)
    resp = await client.post(f"/api/v1/video-generator/renders/{r.id}/etsy-upload-intent",
                             json={"listing_id": other_listing.id}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_media_add_video_gated_by_flag(db_session):
    """add_video / replace_video media jobs are refused while
    ETSY_VIDEO_UPLOAD_ENABLED is off (default)."""
    from fastapi import HTTPException
    from app.services.bulk_edit_media import create_media_job
    from app.core.config import settings
    assert settings.ETSY_VIDEO_UPLOAD_ENABLED is False
    # The video-upload flag gate is checked before org/listing validation, so a
    # literal org id + listing id is enough to prove the gate blocks the op.
    for op in ("add_video", "replace_video"):
        with pytest.raises(HTTPException) as exc:
            await create_media_job(db_session, "org-x", "u1", op, ["listing-x"], {"video_render_id": "x"})
        assert exc.value.status_code == 403
        assert "video upload" in exc.value.detail.lower() or "disabled" in exc.value.detail.lower()
