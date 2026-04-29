"""Backend tests for Feature #4 — Captions / Subtitles (WebVTT + SRT auto-convert).

Endpoints under test (routes/captions.py):
  - GET    /api/videos/{video_id}/captions       (auth, no file_path leakage)
  - POST   /api/videos/{video_id}/captions       (admin only, multipart)
  - GET    /api/captions/{caption_id}            (PUBLIC, returns text/vtt + CORS *)
  - DELETE /api/videos/{video_id}/captions/{id}  (admin only)
"""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fastapi-react-stage.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"username": "StreamHost", "password": "TestPass123!@#"}
VIEWER = {"username": "testviewer", "password": "Viewer123!"}

VIDEO_ID = "2ff9939e-53da-41eb-9edc-e9a9e602b4ca"  # PlayLab Test (existing seed)
NONEXISTENT_VIDEO = "00000000-0000-0000-0000-000000000000"
NONEXISTENT_CAPTION = "11111111-1111-1111-1111-111111111111"

VTT_SAMPLE = (
    "WEBVTT\n\n"
    "00:00:00.000 --> 00:00:02.000\nHello world\n\n"
)
SRT_SAMPLE = (
    "1\n00:00:00,000 --> 00:00:02,000\nHello\n\n"
    "2\n00:00:02,000 --> 00:00:04,000\nWorld\n"
)


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def viewer_token():
    r = requests.post(f"{API}/auth/login", json=VIEWER, timeout=15)
    assert r.status_code == 200, f"viewer login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def viewer_h(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture(scope="session", autouse=True)
def _cleanup(admin_token):
    """Sweep any stray captions on the test video before & after the run."""
    h = {"Authorization": f"Bearer {admin_token}"}
    def _sweep():
        try:
            r = requests.get(f"{API}/videos/{VIDEO_ID}/captions", headers=h, timeout=10)
            if r.status_code == 200:
                for it in r.json().get("items", []):
                    requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{it['id']}", headers=h, timeout=10)
        except Exception:
            pass
    _sweep()
    yield
    _sweep()


# ---------- list ----------
class TestList:
    def test_admin_list_ok(self, admin_h):
        r = requests.get(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["video_id"] == VIDEO_ID
        assert "count" in body and "items" in body
        assert isinstance(body["items"], list)
        for it in body["items"]:
            # file_path must NOT leak
            assert "file_path" not in it
            assert "_id" not in it

    def test_viewer_list_ok(self, viewer_h):
        r = requests.get(f"{API}/videos/{VIDEO_ID}/captions", headers=viewer_h, timeout=10)
        assert r.status_code == 200
        for it in r.json().get("items", []):
            assert "file_path" not in it

    def test_list_nonexistent_video_404(self, admin_h):
        r = requests.get(f"{API}/videos/{NONEXISTENT_VIDEO}/captions", headers=admin_h, timeout=10)
        assert r.status_code == 404


# ---------- upload ----------
class TestUpload:
    def test_upload_vtt_admin_ok(self, admin_h):
        files = {"file": ("tiny.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        data = {"language": "en", "label": "English", "is_default": "true"}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files, data=data, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["language"] == "en"
        assert body["label"] == "English"
        assert body["is_default"] is True
        assert body["video_id"] == VIDEO_ID
        assert "id" in body
        assert "file_path" not in body  # must not leak
        # Verify persistence + public fetch
        cid = body["id"]
        gr = requests.get(f"{API}/captions/{cid}", timeout=10)
        assert gr.status_code == 200
        assert gr.headers.get("content-type", "").startswith("text/vtt")
        assert gr.headers.get("access-control-allow-origin") == "*"
        assert "WEBVTT" in gr.text
        # Cleanup this one
        requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{cid}", headers=admin_h, timeout=10)

    def test_upload_srt_auto_converts(self, admin_h):
        files = {"file": ("tiny.srt", io.BytesIO(SRT_SAMPLE.encode()), "application/x-subrip")}
        data = {"language": "fr", "label": "French"}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files, data=data, timeout=15)
        assert r.status_code == 200, r.text
        cid = r.json()["id"]
        gr = requests.get(f"{API}/captions/{cid}", timeout=10)
        assert gr.status_code == 200
        text = gr.text
        assert text.lstrip().startswith("WEBVTT"), f"not vtt: {text[:100]}"
        # comma -> dot in cue timing line
        assert "00:00:00.000 --> 00:00:02.000" in text
        assert "00:00:00,000 --> 00:00:02,000" not in text
        requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{cid}", headers=admin_h, timeout=10)

    def test_upload_garbage_400(self, admin_h):
        files = {"file": ("x.txt", io.BytesIO(b"this is not subtitles at all"), "text/plain")}
        data = {"language": "en"}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files, data=data, timeout=10)
        assert r.status_code == 400
        assert "Unsupported caption format" in r.text

    def test_upload_empty_language_400(self, admin_h):
        files = {"file": ("tiny.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        data = {"language": ""}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files, data=data, timeout=10)
        # Empty form value may trigger 400 (custom check) or 422 (pydantic min_length); accept both, but verify message
        assert r.status_code in (400, 422)
        if r.status_code == 400:
            assert "Language code is required" in r.text

    def test_upload_default_unsets_previous(self, admin_h):
        # First default upload
        files1 = {"file": ("a.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        r1 = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files1,
                           data={"language": "en", "label": "First", "is_default": "true"}, timeout=15)
        assert r1.status_code == 200
        first_id = r1.json()["id"]
        assert r1.json()["is_default"] is True

        # Second default upload
        files2 = {"file": ("b.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        r2 = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files2,
                           data={"language": "es", "label": "Second", "is_default": "true"}, timeout=15)
        assert r2.status_code == 200
        second_id = r2.json()["id"]
        assert r2.json()["is_default"] is True

        # GET list and verify
        listing = requests.get(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, timeout=10).json()
        by_id = {c["id"]: c for c in listing["items"]}
        assert by_id[first_id]["is_default"] is False, "first default should have been unset"
        assert by_id[second_id]["is_default"] is True

        # cleanup
        requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{first_id}", headers=admin_h, timeout=10)
        requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{second_id}", headers=admin_h, timeout=10)

    def test_upload_viewer_403(self, viewer_h):
        files = {"file": ("t.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        data = {"language": "en"}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=viewer_h, files=files, data=data, timeout=10)
        assert r.status_code == 403


# ---------- public fetch ----------
class TestPublicFetch:
    def test_public_fetch_no_auth(self, admin_h):
        files = {"file": ("p.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files,
                          data={"language": "en"}, timeout=15)
        assert r.status_code == 200
        cid = r.json()["id"]
        # NO Authorization header
        gr = requests.get(f"{API}/captions/{cid}", timeout=10)
        assert gr.status_code == 200
        assert gr.headers.get("content-type", "").startswith("text/vtt")
        assert gr.headers.get("access-control-allow-origin") == "*"
        requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{cid}", headers=admin_h, timeout=10)

    def test_public_fetch_nonexistent_404(self):
        r = requests.get(f"{API}/captions/{NONEXISTENT_CAPTION}", timeout=10)
        assert r.status_code == 404


# ---------- delete ----------
class TestDelete:
    def test_delete_admin_ok_removes_file(self, admin_h):
        files = {"file": ("d.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files,
                          data={"language": "en"}, timeout=15)
        assert r.status_code == 200
        cid = r.json()["id"]

        d = requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{cid}", headers=admin_h, timeout=10)
        assert d.status_code == 200

        # File on disk removed -> public fetch must return 404
        gr = requests.get(f"{API}/captions/{cid}", timeout=10)
        assert gr.status_code == 404

    def test_delete_viewer_403(self, admin_h, viewer_h):
        files = {"file": ("dv.vtt", io.BytesIO(VTT_SAMPLE.encode()), "text/vtt")}
        r = requests.post(f"{API}/videos/{VIDEO_ID}/captions", headers=admin_h, files=files,
                          data={"language": "en"}, timeout=15)
        assert r.status_code == 200
        cid = r.json()["id"]

        d = requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{cid}", headers=viewer_h, timeout=10)
        assert d.status_code == 403

        # cleanup
        requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{cid}", headers=admin_h, timeout=10)

    def test_delete_nonexistent_404(self, admin_h):
        r = requests.delete(f"{API}/videos/{VIDEO_ID}/captions/{NONEXISTENT_CAPTION}",
                            headers=admin_h, timeout=10)
        assert r.status_code == 404
