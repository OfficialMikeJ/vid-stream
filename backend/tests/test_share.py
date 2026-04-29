"""Feature #5 — Video Sharing Links (public tokenized URLs).

Covers POST/GET/DELETE /api/videos/{id}/share + public GET /api/share/{token}.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fastapi-react-stage.preview.emergentagent.com").rstrip("/")
ADMIN = {"username": "StreamHost", "password": "TestPass123!@#"}
VIEWER = {"username": "testviewer", "password": "Viewer123!"}


# ─── fixtures ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def viewer_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=VIEWER, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def viewer_client(viewer_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {viewer_token}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def video_id(admin_client):
    r = admin_client.get(f"{BASE_URL}/api/videos")
    assert r.status_code == 200
    items = r.json()
    if isinstance(items, dict):
        items = items.get("videos") or items.get("items") or []
    assert items, "No videos exist — cannot test share"
    return items[0]["id"]


# Track tokens for cleanup
_tokens_created = []


@pytest.fixture(scope="module", autouse=True)
def _cleanup(admin_client):
    yield
    for tok in _tokens_created:
        try:
            admin_client.delete(f"{BASE_URL}/api/share/{tok}")
        except Exception:
            pass


# ─── create ────────────────────────────────────────────────────────────────
class TestCreateShare:
    def test_create_basic(self, admin_client, video_id):
        r = admin_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"label": "X"})
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("id", "token", "video_id", "label", "expires_at", "view_count", "has_password", "created_by", "created_at"):
            assert k in d, f"missing {k}"
        assert "password_hash" not in d
        assert d["label"] == "X"
        assert d["video_id"] == video_id
        assert d["expires_at"] is None
        assert d["view_count"] == 0
        assert d["has_password"] is False
        _tokens_created.append(d["token"])

    def test_create_with_password(self, admin_client, video_id):
        r = admin_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"password": "hunter2", "label": "VIP"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["has_password"] is True
        assert "password_hash" not in d
        _tokens_created.append(d["token"])
        # save for later use
        TestCreateShare.pw_token = d["token"]

    def test_create_already_expired(self, admin_client, video_id):
        r = admin_client.post(
            f"{BASE_URL}/api/videos/{video_id}/share",
            json={"expires_at": "2020-01-01T00:00:00+00:00"},
        )
        assert r.status_code == 200, r.text
        _tokens_created.append(r.json()["token"])
        TestCreateShare.expired_token = r.json()["token"]

    def test_create_invalid_expires(self, admin_client, video_id):
        r = admin_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"expires_at": "not-a-date"})
        assert r.status_code == 400
        assert "Invalid expires_at" in r.json().get("detail", "")

    def test_create_nonexistent_video(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/videos/does-not-exist/share", json={})
        assert r.status_code == 404

    def test_create_viewer_forbidden(self, viewer_client, video_id):
        r = viewer_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"label": "nope"})
        assert r.status_code == 403


# ─── list ──────────────────────────────────────────────────────────────────
class TestListShare:
    def test_list_admin(self, admin_client, video_id):
        r = admin_client.get(f"{BASE_URL}/api/videos/{video_id}/share")
        assert r.status_code == 200
        d = r.json()
        assert d["video_id"] == video_id
        assert d["count"] == len(d["items"])
        for it in d["items"]:
            assert "has_password" in it
            assert "password_hash" not in it

    def test_list_viewer_forbidden(self, viewer_client, video_id):
        r = viewer_client.get(f"{BASE_URL}/api/videos/{video_id}/share")
        assert r.status_code == 403


# ─── public resolve ────────────────────────────────────────────────────────
class TestResolveShare:
    """Public endpoint — no auth header should be sent."""

    @pytest.fixture(scope="class")
    def public(self):
        # bare requests session (no auth)
        return requests.Session()

    @pytest.fixture(scope="class")
    def unprotected_token(self, admin_client, video_id):
        r = admin_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"label": "PublicTest"})
        tok = r.json()["token"]
        _tokens_created.append(tok)
        return tok

    def test_resolve_unprotected(self, public, unprotected_token):
        r = public.get(f"{BASE_URL}/api/share/{unprotected_token}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["requires_password"] is False
        assert "video" in d
        assert d["hls_url"].startswith("/api/stream/hls/") and d["hls_url"].endswith("/playlist.m3u8")
        assert "thumbnail_url" in d
        assert "captions" in d and isinstance(d["captions"], list)
        assert d["label"] == "PublicTest"

    def test_resolve_protected_no_password(self, public):
        tok = TestCreateShare.pw_token
        r = public.get(f"{BASE_URL}/api/share/{tok}")
        assert r.status_code == 200
        d = r.json()
        assert d["requires_password"] is True
        assert d["label"] == "VIP"
        assert "video" not in d
        assert "hls_url" not in d

    def test_resolve_wrong_password(self, public):
        tok = TestCreateShare.pw_token
        r = public.get(f"{BASE_URL}/api/share/{tok}", params={"password": "wrong"})
        assert r.status_code == 401
        assert "Incorrect password" in r.json().get("detail", "")

    def test_resolve_correct_password(self, public):
        tok = TestCreateShare.pw_token
        r = public.get(f"{BASE_URL}/api/share/{tok}", params={"password": "hunter2"})
        assert r.status_code == 200
        d = r.json()
        assert d["requires_password"] is False
        assert "video" in d

    def test_resolve_expired(self, public):
        r = public.get(f"{BASE_URL}/api/share/{TestCreateShare.expired_token}")
        assert r.status_code == 410
        assert "expired" in r.json().get("detail", "").lower()

    def test_resolve_nonexistent(self, public):
        r = public.get(f"{BASE_URL}/api/share/nonexistent-token-zzz")
        assert r.status_code == 404

    def test_view_counter_increments(self, public, admin_client, video_id, unprotected_token):
        # call resolve twice
        r1 = public.get(f"{BASE_URL}/api/share/{unprotected_token}")
        r2 = public.get(f"{BASE_URL}/api/share/{unprotected_token}")
        assert r1.status_code == 200 and r2.status_code == 200
        time.sleep(0.5)
        listing = admin_client.get(f"{BASE_URL}/api/videos/{video_id}/share").json()
        match = [i for i in listing["items"] if i["token"] == unprotected_token]
        assert match
        assert match[0]["view_count"] >= 2


# ─── revoke ────────────────────────────────────────────────────────────────
class TestRevokeShare:
    def test_viewer_cannot_revoke(self, viewer_client, admin_client, video_id):
        r = admin_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"label": "ToRevoke"})
        tok = r.json()["token"]
        _tokens_created.append(tok)
        rv = viewer_client.delete(f"{BASE_URL}/api/share/{tok}")
        assert rv.status_code == 403

    def test_admin_revoke_then_404(self, admin_client, video_id):
        r = admin_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"label": "ToRevoke2"})
        tok = r.json()["token"]
        rv = admin_client.delete(f"{BASE_URL}/api/share/{tok}")
        assert rv.status_code == 200
        assert "revoked" in rv.json().get("message", "").lower()
        # Resolve should now 404
        r404 = requests.get(f"{BASE_URL}/api/share/{tok}")
        assert r404.status_code == 404

    def test_revoke_nonexistent(self, admin_client):
        r = admin_client.delete(f"{BASE_URL}/api/share/totally-fake-token-xyz")
        assert r.status_code == 404


# ─── public endpoint must NOT require auth ─────────────────────────────────
def test_resolve_no_auth_header(admin_client, video_id):
    r = admin_client.post(f"{BASE_URL}/api/videos/{video_id}/share", json={"label": "NoAuth"})
    tok = r.json()["token"]
    _tokens_created.append(tok)
    # Use bare requests (no Authorization)
    rr = requests.get(f"{BASE_URL}/api/share/{tok}", timeout=15)
    assert rr.status_code == 200, rr.text
    assert rr.json().get("requires_password") is False
