"""
Tests that verify Windows .bat startup scripts meet readiness and ASCII safety requirements.
These are static content checks — no Docker or network access required.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent

BAT_FILES = [
    REPO_ROOT / "start-dev.bat",
    REPO_ROOT / "start-dev-clean.bat",
    REPO_ROOT / "setup-and-start.bat",
    REPO_ROOT / "setup-and-start-clean.bat",
]

BACKEND_HEALTH_URL = "8100/api/v1/health"
FRONTEND_URL = "localhost:3100"
BROWSER_OPEN_CMD = 'start "" "http://localhost:3100"'
DOCKER_READY_CHECK = "docker info"


def _read(bat_path: Path) -> str:
    return bat_path.read_text(encoding="ascii", errors="replace")


def test_bat_files_exist():
    for f in BAT_FILES:
        assert f.exists(), f"Expected .bat file not found: {f}"


def test_bat_files_no_chcp_65001():
    for f in BAT_FILES:
        content = _read(f)
        assert "chcp 65001" not in content, (
            f"{f.name} contains 'chcp 65001' — bat files must be ASCII-only"
        )


def test_bat_files_ascii_only():
    """No bytes outside ASCII range in any .bat file."""
    for f in BAT_FILES:
        raw = f.read_bytes()
        non_ascii = [b for b in raw if b > 127]
        assert not non_ascii, (
            f"{f.name} contains non-ASCII bytes: {non_ascii[:10]}"
        )


def test_bat_files_no_unicode_box_drawing():
    """Box drawing characters (U+2500-U+257F) must not appear."""
    for f in BAT_FILES:
        content = _read(f)
        box = [c for c in content if "─" <= c <= "╿"]
        assert not box, f"{f.name} contains box drawing characters"


def test_bat_files_wait_for_docker_before_compose():
    for f in BAT_FILES:
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
    for f in BAT_FILES:
        content = _read(f)
        assert BACKEND_HEALTH_URL in content, (
            f"{f.name} missing backend health wait for {BACKEND_HEALTH_URL}"
        )


def test_bat_files_contain_frontend_wait():
    for f in BAT_FILES:
        content = _read(f)
        # Frontend wait appears as PowerShell check against localhost:3100
        assert "localhost:3100" in content, (
            f"{f.name} missing frontend readiness check for localhost:3100"
        )
        # Must use PowerShell Invoke-WebRequest for the 3100 check
        assert "Invoke-WebRequest" in content, (
            f"{f.name} missing Invoke-WebRequest readiness polling"
        )


def test_browser_open_after_readiness_checks():
    """Browser open command must appear AFTER both health check strings."""
    for f in BAT_FILES:
        content = _read(f)
        if BROWSER_OPEN_CMD not in content:
            continue  # setup-and-start scripts use start "" "http://..." too
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
    for f in BAT_FILES:
        content = _read(f)
        assert 'timeout /t 12 /nobreak >nul && start http' not in content, (
            f"{f.name} still uses fixed-delay browser open pattern"
        )
        # Also check the subprocess variant
        assert 'timeout /t 12 /nobreak >nul' not in content or 'start http' not in content.split('timeout /t 12 /nobreak >nul')[1][:20], (
            f"{f.name} still uses fixed-delay browser open via subprocess"
        )


def test_bat_files_compose_project_name_is_bulk_edit():
    for f in BAT_FILES:
        content = _read(f)
        assert "-p bulk-edit" in content, (
            f"{f.name} missing docker compose -p bulk-edit project isolation"
        )


def test_bat_files_no_hardcoded_credentials():
    suspicious = ["password", "secret", "api_key", "token"]
    for f in BAT_FILES:
        content = _read(f).lower()
        for word in suspicious:
            # Allow the word only as part of a URL or known safe context
            # The bat files should not contain credential assignments
            matches = re.findall(rf'\b{word}\s*=\s*\S+', content)
            assert not matches, (
                f"{f.name} may contain hardcoded credentials: {matches}"
            )


def test_start_dev_bat_no_seed_prompt():
    """Dev bat files must NOT contain seed prompt or seed script invocation.
    Seeding is handled automatically by the FastAPI lifespan startup hook."""
    for f in [REPO_ROOT / "start-dev.bat", REPO_ROOT / "start-dev-clean.bat"]:
        content = _read(f)
        assert "seed_local_superusers.py" not in content, (
            f"{f.name} must not invoke seed_local_superusers.py — seeding is done by backend on startup"
        )
        assert "SEED_CHOICE" not in content, (
            f"{f.name} must not contain seed Y/N prompt (SEED_CHOICE variable)"
        )
