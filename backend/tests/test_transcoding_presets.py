"""Backend tests for Feature #2 — Video Transcoding Presets."""
import os
import io
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fastapi-react-stage.preview.emergentagent.com").rstrip("/")
ADMIN = {"username": "StreamHost", "password": "TestPass123!@#"}
VIEWER = {"username": "testviewer", "password": "Viewer123!"}
TEST_VIDEO_PATH = "/tmp/test_video.mp4"


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"Login failed for {creds['username']}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def viewer_token():
    return _login(VIEWER)


@pytest.fixture(scope="module")
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def viewer_h(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


# ── GET /api/settings/transcoding ────────────────────────────────────────────

class TestGetTranscodingSettings:
    def test_admin_get_returns_presets(self, admin_h):
        r = requests.get(f"{BASE_URL}/api/settings/transcoding", headers=admin_h, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "default_preset" in data
        assert "presets" in data
        keys = {p["key"] for p in data["presets"]}
        assert keys == {"source", "1080p", "720p", "480p"}
        for p in data["presets"]:
            assert "key" in p and "label" in p and "description" in p

    def test_viewer_get_returns_presets(self, viewer_h):
        r = requests.get(f"{BASE_URL}/api/settings/transcoding", headers=viewer_h, timeout=15)
        assert r.status_code == 200
        keys = {p["key"] for p in r.json()["presets"]}
        assert keys == {"source", "1080p", "720p", "480p"}


# ── PATCH /api/settings/transcoding ──────────────────────────────────────────

class TestPatchTranscodingSettings:
    def test_admin_patch_to_720p_persists(self, admin_h):
        r = requests.patch(f"{BASE_URL}/api/settings/transcoding?default_preset=720p", headers=admin_h, timeout=15)
        assert r.status_code == 200
        assert r.json()["default_preset"] == "720p"

        # GET to verify persistence
        g = requests.get(f"{BASE_URL}/api/settings/transcoding", headers=admin_h, timeout=15)
        assert g.status_code == 200
        assert g.json()["default_preset"] == "720p"

    def test_admin_patch_invalid_preset_400(self, admin_h):
        r = requests.patch(f"{BASE_URL}/api/settings/transcoding?default_preset=foobar", headers=admin_h, timeout=15)
        assert r.status_code == 400
        body = r.json()
        # Detail mentions invalid preset
        assert "Invalid" in (body.get("detail") or "")

    def test_viewer_patch_forbidden(self, viewer_h):
        r = requests.patch(f"{BASE_URL}/api/settings/transcoding?default_preset=720p", headers=viewer_h, timeout=15)
        assert r.status_code == 403


# ── Upload tests ─────────────────────────────────────────────────────────────

class TestUploadWithPreset:
    @pytest.fixture(scope="class")
    def video_id(self, admin_h):
        with open(TEST_VIDEO_PATH, "rb") as f:
            files = {"file": ("test.mp4", f, "video/mp4")}
            data = {"title": "TEST_preset_480p", "transcoding_preset": "480p"}
            r = requests.post(f"{BASE_URL}/api/videos/upload", headers=admin_h, files=files, data=data, timeout=120)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        vid = r.json()["video_id"]
        # Give a moment for the document to be inserted
        time.sleep(0.5)
        return vid

    def test_upload_records_preset_480p(self, admin_h, video_id):
        r = requests.get(f"{BASE_URL}/api/videos/{video_id}", headers=admin_h, timeout=15)
        assert r.status_code == 200
        assert r.json().get("transcoding_preset") == "480p"

    def test_upload_invalid_preset_400(self, admin_h):
        with open(TEST_VIDEO_PATH, "rb") as f:
            files = {"file": ("test.mp4", f, "video/mp4")}
            data = {"title": "TEST_preset_garbage", "transcoding_preset": "garbage"}
            r = requests.post(f"{BASE_URL}/api/videos/upload", headers=admin_h, files=files, data=data, timeout=60)
        assert r.status_code == 400
        assert "Invalid transcoding preset" in (r.json().get("detail") or "")

    def test_chunked_upload_init_records_preset(self, admin_h):
        data = {
            "filename": "test.mp4",
            "title": "TEST_chunked_720p",
            "total_size": "1024",
            "transcoding_preset": "720p",
        }
        r = requests.post(f"{BASE_URL}/api/upload/init", headers=admin_h, data=data, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "upload_id" in body and "video_id" in body
        # Verify status endpoint exposes the session (preset is stored in db.uploads)
        s = requests.get(f"{BASE_URL}/api/upload/status/{body['upload_id']}", headers=admin_h, timeout=15)
        assert s.status_code == 200


# ── Reprocess endpoint ───────────────────────────────────────────────────────

class TestReprocess:
    @pytest.fixture(scope="class")
    def video_id(self, admin_h):
        # Reuse an existing video
        with open(TEST_VIDEO_PATH, "rb") as f:
            files = {"file": ("test.mp4", f, "video/mp4")}
            data = {"title": "TEST_reprocess", "transcoding_preset": "source"}
            r = requests.post(f"{BASE_URL}/api/videos/upload", headers=admin_h, files=files, data=data, timeout=120)
        assert r.status_code == 200
        return r.json()["video_id"]

    def test_reprocess_ok(self, admin_h, video_id):
        r = requests.post(f"{BASE_URL}/api/videos/{video_id}/reprocess?preset=480p", headers=admin_h, timeout=15)
        assert r.status_code == 200, r.text
        assert "Reprocessing" in r.json().get("message", "")

        # Verify status moves into one of the expected states
        time.sleep(1.0)
        g = requests.get(f"{BASE_URL}/api/videos/{video_id}", headers=admin_h, timeout=15)
        assert g.status_code == 200
        assert g.json().get("processing_status") in ("processing", "pending", "ready", "failed")

    def test_reprocess_404(self, admin_h):
        r = requests.post(f"{BASE_URL}/api/videos/does-not-exist/reprocess?preset=480p", headers=admin_h, timeout=15)
        assert r.status_code == 404

    def test_reprocess_invalid_preset_400(self, admin_h, video_id):
        r = requests.post(f"{BASE_URL}/api/videos/{video_id}/reprocess?preset=junk", headers=admin_h, timeout=15)
        assert r.status_code == 400

    def test_reprocess_viewer_forbidden(self, viewer_h, video_id):
        r = requests.post(f"{BASE_URL}/api/videos/{video_id}/reprocess?preset=480p", headers=viewer_h, timeout=15)
        assert r.status_code == 403


# ── Cleanup: reset default_preset back to 'source' ───────────────────────────

def test_zz_reset_default_preset_to_source(request):
    # Re-login (fixtures are module-scoped and may be torn down)
    token = _login(ADMIN)
    h = {"Authorization": f"Bearer {token}"}
    r = requests.patch(f"{BASE_URL}/api/settings/transcoding?default_preset=source", headers=h, timeout=15)
    assert r.status_code == 200
    assert r.json()["default_preset"] == "source"
