"""
Tests that verify Windows .bat startup scripts meet readiness and ASCII safety requirements.
These are static content checks — no Docker or network access required.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent

# All bat files — basic safety checks apply to all
ALL_BAT_FILES = [
    REPO_ROOT / "start-dev.bat",
    REPO_ROOT / "start-dev-clean.bat",
    REPO_ROOT / "setup-and-start.bat",
    REPO_ROOT / "setup-and-start-clean.bat",
]

# start-dev.bat is a thin wrapper that delegates to setup-and-start.bat.
# Full startup logic checks (health polls, docker wait, browser open) only
# apply to the scripts that contain that logic directly.
FULL_BAT_FILES = [
    REPO_ROOT / "start-dev-clean.bat",
    REPO_ROOT / "setup-and-start.bat",
    REPO_ROOT / "setup-and-start-clean.bat",
]

# Kept for backward compatibility within this module
BAT_FILES = ALL_BAT_FILES

BACKEND_HEALTH_URL = "8100/api/v1/health"
FRONTEND_URL = "localhost:3100"
BROWSER_OPEN_CMD = 'start "" "http://localhost:3100"'
DOCKER_READY_CHECK = "docker info"


def _read(bat_path: Path) -> str:
    return bat_path.read_text(encoding="ascii", errors="replace")


def test_bat_files_exist():
    for f in ALL_BAT_FILES:
        assert f.exists(), f"Expected .bat file not found: {f}"


def test_bat_files_no_chcp_65001():
    for f in ALL_BAT_FILES:
        content = _read(f)
        assert "chcp 65001" not in content, (
            f"{f.name} contains 'chcp 65001' — bat files must be ASCII-only"
        )


def test_bat_files_ascii_only():
    """No bytes outside ASCII range in any .bat file."""
    for f in ALL_BAT_FILES:
        raw = f.read_bytes()
        non_ascii = [b for b in raw if b > 127]
        assert not non_ascii, (
            f"{f.name} contains non-ASCII bytes: {non_ascii[:10]}"
        )


def test_bat_files_no_unicode_box_drawing():
    """Box drawing characters (U+2500-U+257F) must not appear."""
    for f in ALL_BAT_FILES:
        content = _read(f)
        box = [c for c in content if "─" <= c <= "╿"]
        assert not box, f"{f.name} contains box drawing characters"


def test_bat_files_wait_for_docker_before_compose():
    """Full startup scripts (not wrappers) must wait for Docker before compose."""
    for f in FULL_BAT_FILES:
        content = _read(f)
        assert DOCKER_READY_CHECK in content, (
            f"{f.name} missing docker info readiness check"
        )
        docker_pos = content.index(DOCKER_READY_CHECK)
        compose_pos = content.find("docker compose")
        assert compose_pos > docker_pos, (
            f"{f.name}: docker compose runs before docker info check"
        )


def test_bat_files_contain_backend_health_wait():
    """Full startup scripts must poll backend health endpoint."""
    for f in FULL_BAT_FILES:
        content = _read(f)
        assert BACKEND_HEALTH_URL in content, (
            f"{f.name} missing backend health wait for {BACKEND_HEALTH_URL}"
        )


def test_bat_files_contain_frontend_wait():
    """Full startup scripts must poll frontend readiness."""
    for f in FULL_BAT_FILES:
        content = _read(f)
        assert "localhost:3100" in content, (
            f"{f.name} missing frontend readiness check for localhost:3100"
        )
        assert "Invoke-WebRequest" in content, (
            f"{f.name} missing Invoke-WebRequest readiness polling"
        )


def test_browser_open_after_readiness_checks():
    """Browser open command must appear AFTER both health check strings."""
    for f in FULL_BAT_FILES:
        content = _read(f)
        if BROWSER_OPEN_CMD not in content:
            continue
        browser_pos = content.index(BROWSER_OPEN_CMD)
        backend_pos = content.index(BACKEND_HEALTH_URL)
        frontend_ps_pos = content.index("Invoke-WebRequest")
        assert browser_pos > backend_pos, (
            f"{f.name}: browser opens before backend health check"
        )
        assert browser_pos > frontend_ps_pos, (
            f"{f.name}: browser opens before frontend readiness check"
        )


def test_bat_files_no_fixed_timeout_browser_open():
    """Old pattern: 'timeout /t 12' then 'start http' — must be removed."""
    for f in ALL_BAT_FILES:
        content = _read(f)
        assert 'timeout /t 12 /nobreak >nul && start http' not in content, (
            f"{f.name} still uses fixed-delay browser open pattern"
        )
        assert 'timeout /t 12 /nobreak >nul' not in content or 'start http' not in content.split('timeout /t 12 /nobreak >nul')[1][:20], (
            f"{f.name} still uses fixed-delay browser open via subprocess"
        )


def test_bat_files_compose_project_name_is_bulk_edit():
    for f in FULL_BAT_FILES:
        content = _read(f)
        assert "-p bulk-edit" in content, (
            f"{f.name} missing docker compose -p bulk-edit project isolation"
        )


def test_bat_files_no_hardcoded_credentials():
    suspicious = ["password", "secret", "api_key", "token"]
    for f in ALL_BAT_FILES:
        content = _read(f).lower()
        for word in suspicious:
            matches = re.findall(rf'\b{word}\s*=\s*\S+', content)
            assert not matches, (
                f"{f.name} may contain hardcoded credentials: {matches}"
            )


def test_start_dev_bat_no_seed_prompt():
    """Dev bat files must NOT contain seed prompt or seed script invocation."""
    for f in [REPO_ROOT / "start-dev.bat", REPO_ROOT / "start-dev-clean.bat"]:
        content = _read(f)
        assert "seed_local_superusers.py" not in content, (
            f"{f.name} must not invoke seed_local_superusers.py"
        )
        assert "SEED_CHOICE" not in content, (
            f"{f.name} must not contain seed Y/N prompt"
        )


def test_start_dev_bat_is_thin_wrapper():
    """start-dev.bat must delegate to setup-and-start.bat, not duplicate startup logic."""
    content = _read(REPO_ROOT / "start-dev.bat")
    assert "setup-and-start.bat" in content, (
        "start-dev.bat must call setup-and-start.bat"
    )


def test_setup_bat_calls_seed_before_compose_up():
    """setup-and-start.bat must create the seed file before starting Docker Compose."""
    content = _read(REPO_ROOT / "setup-and-start.bat")
    seed_pos = content.find("create-seed.ps1")
    compose_up_pos = content.find("up -d")
    assert seed_pos != -1, "setup-and-start.bat must call create-seed.ps1"
    assert compose_up_pos != -1, "setup-and-start.bat must call compose up -d"
    assert seed_pos < compose_up_pos, (
        "create-seed.ps1 must be called BEFORE compose up -d"
    )


def test_setup_bat_verifies_login_after_readiness():
    """setup-and-start.bat must verify demo login after backend readiness."""
    content = _read(REPO_ROOT / "setup-and-start.bat")
    ready_pos = content.find("health/ready")
    login_pos = content.find("verify-demo-logins")
    assert login_pos != -1, "setup-and-start.bat must call verify-demo-logins.ps1"
    assert login_pos > ready_pos, (
        "verify-demo-logins.ps1 must be called AFTER health/ready check"
    )


def test_create_seed_ps1_has_correct_env_var_names():
    """create-seed.ps1 must write the exact env var names that local_seed.py reads."""
    path = REPO_ROOT / "scripts" / "windows" / "create-seed.ps1"
    content = path.read_text(encoding="utf-8")
    required_keys = [
        "FREE_SUPERUSER_EMAIL",
        "FREE_SUPERUSER_PASSWORD",
        "FREE_SUPERUSER_FULL_NAME",
        "FREE_SUPERUSER_ORG_NAME",
        "PAID_SUPERUSER_EMAIL",
        "PAID_SUPERUSER_PASSWORD",
        "PAID_SUPERUSER_FULL_NAME",
        "PAID_SUPERUSER_ORG_NAME",
        "PAID_SUPERUSER_PLAN",
    ]
    for key in required_keys:
        assert key in content, f"create-seed.ps1 missing required env var: {key}"


def test_create_seed_ps1_no_bom_write():
    """create-seed.ps1 must use UTF-8 no-BOM encoding (not Set-Content -Encoding UTF8)."""
    path = REPO_ROOT / "scripts" / "windows" / "create-seed.ps1"
    content = path.read_text(encoding="utf-8")
    assert "Set-Content" not in content or "UTF8" not in content.split("Set-Content")[1][:50] if "Set-Content" in content else True, (
        "create-seed.ps1 uses Set-Content -Encoding UTF8 which adds BOM. Use WriteAllLines with UTF8Encoding($false)"
    )
    assert "UTF8Encoding" in content or "WriteAllLines" in content or "WriteAllText" in content, (
        "create-seed.ps1 must use explicit no-BOM encoding (UTF8Encoding $false)"
    )
