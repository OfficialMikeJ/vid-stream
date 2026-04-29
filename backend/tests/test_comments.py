"""Backend tests for Feature #3 — Video Comments.

Covers:
- GET /api/videos/{id}/comments  (admin & viewer)
- POST /api/videos/{id}/comments  (admin & viewer; validations)
- DELETE /api/videos/{id}/comments/{cid}  (ownership + admin override)
- GET /api/comments  (admin moderation list; viewer 403)
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = {"username": "StreamHost", "password": "TestPass123!@#"}
VIEWER = {"username": "testviewer", "password": "Viewer123!"}


# ── Auth helpers ─────────────────────────────────────────────────────────────

def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"Login failed for {creds['username']}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_h():
    return {"Authorization": f"Bearer {_login(ADMIN)}"}


@pytest.fixture(scope="module")
def viewer_h():
    return {"Authorization": f"Bearer {_login(VIEWER)}"}


@pytest.fixture(scope="module")
def video_id(admin_h):
    """Pick any existing video (status doesn't matter for comment endpoints)."""
    r = requests.get(f"{BASE_URL}/api/videos", headers=admin_h, timeout=15)
    assert r.status_code == 200, f"Cannot list videos: {r.text}"
    items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
    assert items, "No videos available — seed one before running comments tests"
    return items[0]["id"]


@pytest.fixture(scope="module")
def created_comment_ids():
    """Track comments created during the run so we can clean up admin-side."""
    return []


# ── GET /api/videos/{id}/comments ────────────────────────────────────────────

class TestListVideoComments:
    def test_admin_list_returns_shape(self, admin_h, video_id):
        r = requests.get(f"{BASE_URL}/api/videos/{video_id}/comments", headers=admin_h, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["video_id"] == video_id
        assert isinstance(d["count"], int)
        assert isinstance(d["items"], list)

    def test_viewer_can_list(self, viewer_h, video_id):
        r = requests.get(f"{BASE_URL}/api/videos/{video_id}/comments", headers=viewer_h, timeout=15)
        assert r.status_code == 200
        assert "items" in r.json()

    def test_list_nonexistent_video_404(self, admin_h):
        r = requests.get(
            f"{BASE_URL}/api/videos/{uuid.uuid4()}/comments", headers=admin_h, timeout=15
        )
        assert r.status_code == 404
        assert r.json()["detail"] == "Video not found"


# ── POST /api/videos/{id}/comments ───────────────────────────────────────────

class TestCreateComment:
    def test_admin_can_post(self, admin_h, video_id, created_comment_ids):
        r = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=admin_h,
            json={"body": "TEST_admin top-level comment"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        c = r.json()
        for k in ("id", "video_id", "username", "user_role", "body", "created_at"):
            assert k in c, f"Missing key {k}"
        assert c["video_id"] == video_id
        assert c["username"] == "StreamHost"
        assert c["user_role"] == "admin"
        assert c["body"] == "TEST_admin top-level comment"
        created_comment_ids.append(("admin", c["id"]))

        # Verify persistence via list
        lst = requests.get(
            f"{BASE_URL}/api/videos/{video_id}/comments", headers=admin_h, timeout=15
        ).json()["items"]
        assert any(it["id"] == c["id"] for it in lst)

    def test_viewer_can_post(self, viewer_h, video_id, created_comment_ids):
        r = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=viewer_h,
            json={"body": "TEST_viewer comment"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        c = r.json()
        assert c["username"] == "testviewer"
        assert c["user_role"] == "viewer"
        created_comment_ids.append(("viewer", c["id"]))

    def test_whitespace_body_rejected_400(self, admin_h, video_id):
        r = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=admin_h,
            json={"body": "    "},
            timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "empty" in r.json()["detail"].lower()

    def test_too_long_body_422(self, admin_h, video_id):
        r = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=admin_h,
            json={"body": "x" * 2001},
            timeout=15,
        )
        assert r.status_code == 422, r.text

    def test_post_to_nonexistent_video_404(self, admin_h):
        r = requests.post(
            f"{BASE_URL}/api/videos/{uuid.uuid4()}/comments",
            headers=admin_h,
            json={"body": "ghost"},
            timeout=15,
        )
        assert r.status_code == 404

    def test_post_unauth_401(self, video_id):
        r = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            json={"body": "no auth"},
            timeout=15,
        )
        assert r.status_code in (401, 403)


# ── DELETE permissions ───────────────────────────────────────────────────────

class TestDeleteComment:
    def test_viewer_cannot_delete_admin_comment(self, viewer_h, admin_h, video_id):
        # admin posts
        c = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=admin_h,
            json={"body": "TEST_admin-only-target"},
            timeout=15,
        ).json()
        # viewer tries to delete
        r = requests.delete(
            f"{BASE_URL}/api/videos/{video_id}/comments/{c['id']}",
            headers=viewer_h,
            timeout=15,
        )
        assert r.status_code == 403
        assert "your own" in r.json()["detail"].lower()
        # cleanup as admin
        requests.delete(
            f"{BASE_URL}/api/videos/{video_id}/comments/{c['id']}",
            headers=admin_h,
            timeout=15,
        )

    def test_viewer_can_delete_own(self, viewer_h, video_id):
        c = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=viewer_h,
            json={"body": "TEST_viewer-self-delete"},
            timeout=15,
        ).json()
        r = requests.delete(
            f"{BASE_URL}/api/videos/{video_id}/comments/{c['id']}",
            headers=viewer_h,
            timeout=15,
        )
        assert r.status_code == 200
        # confirm gone
        lst = requests.get(
            f"{BASE_URL}/api/videos/{video_id}/comments", headers=viewer_h, timeout=15
        ).json()["items"]
        assert not any(it["id"] == c["id"] for it in lst)

    def test_admin_can_delete_viewer_comment(self, admin_h, viewer_h, video_id):
        c = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=viewer_h,
            json={"body": "TEST_admin-overrides-viewer"},
            timeout=15,
        ).json()
        r = requests.delete(
            f"{BASE_URL}/api/videos/{video_id}/comments/{c['id']}",
            headers=admin_h,
            timeout=15,
        )
        assert r.status_code == 200

    def test_delete_nonexistent_404(self, admin_h, video_id):
        r = requests.delete(
            f"{BASE_URL}/api/videos/{video_id}/comments/{uuid.uuid4()}",
            headers=admin_h,
            timeout=15,
        )
        assert r.status_code == 404


# ── Admin moderation list ────────────────────────────────────────────────────

class TestAdminModerationList:
    def test_admin_list_all_with_titles(self, admin_h, video_id):
        # ensure at least one
        c = requests.post(
            f"{BASE_URL}/api/videos/{video_id}/comments",
            headers=admin_h,
            json={"body": "TEST_moderation-row"},
            timeout=15,
        ).json()
        r = requests.get(f"{BASE_URL}/api/comments", headers=admin_h, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["count"], int)
        assert isinstance(d["items"], list)
        if d["items"]:
            sample = d["items"][0]
            for k in ("id", "body", "video_id", "video_title", "username", "user_role", "created_at"):
                assert k in sample, f"Moderation row missing {k}"
        # cleanup
        requests.delete(
            f"{BASE_URL}/api/videos/{video_id}/comments/{c['id']}",
            headers=admin_h,
            timeout=15,
        )

    def test_viewer_forbidden_on_moderation_list(self, viewer_h):
        r = requests.get(f"{BASE_URL}/api/comments", headers=viewer_h, timeout=15)
        assert r.status_code == 403


# ── Final cleanup (TEST_ data) ───────────────────────────────────────────────

def test_cleanup_test_comments(admin_h, video_id, created_comment_ids):
    """Sweep any TEST_ comments still on the seed video."""
    r = requests.get(f"{BASE_URL}/api/videos/{video_id}/comments", headers=admin_h, timeout=15)
    for it in r.json().get("items", []):
        if it["body"].startswith("TEST_"):
            requests.delete(
                f"{BASE_URL}/api/videos/{video_id}/comments/{it['id']}",
                headers=admin_h,
                timeout=15,
            )
    # tracked ones too
    for _, cid in created_comment_ids:
        requests.delete(
            f"{BASE_URL}/api/videos/{video_id}/comments/{cid}",
            headers=admin_h,
            timeout=15,
        )
