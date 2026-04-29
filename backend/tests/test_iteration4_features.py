"""
Iteration 4 backend tests:
- Video search/filter/sort (GET /api/videos with params)
- Upload resume (GET /api/upload/status/{id})
- PlayLab webhook (PATCH /api/playlab/webhook, POST /api/playlab/test-webhook)
- Regression: health, auth, base video list
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token using known credentials."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "StreamHost", "password": "TestPass123!@#"},
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Login failed ({response.status_code}): {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Authorization header for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


# ── Health ───────────────────────────────────────────────────────────────────

class TestHealth:
    """GET /api/health"""

    def test_health_returns_healthy(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"
        assert data.get("service") == "StreamHost API"
        print("PASS: GET /api/health returns healthy")


# ── Auth ─────────────────────────────────────────────────────────────────────

class TestAuth:
    """POST /api/auth/login"""

    def test_login_with_valid_credentials(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "StreamHost", "password": "TestPass123!@#"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        print("PASS: POST /api/auth/login returns access_token")

    def test_login_with_wrong_password_fails(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "StreamHost", "password": "wrongpassword"},
        )
        assert resp.status_code in (401, 403)
        print(f"PASS: Wrong password returns {resp.status_code}")


# ── Videos (search/filter/sort) ───────────────────────────────────────────

class TestVideoSearchFilter:
    """GET /api/videos with search/status/sort params."""

    def test_get_videos_returns_list(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/videos", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: GET /api/videos returns list of {len(data)} videos")

    def test_get_videos_search_param(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/videos?search=test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # All returned videos should match "test" in title or description
        for v in data:
            title = v.get("title", "").lower()
            desc = (v.get("description") or "").lower()
            assert "test" in title or "test" in desc, (
                f"Video '{v['title']}' doesn't match search 'test'"
            )
        print(f"PASS: GET /api/videos?search=test returns {len(data)} filtered results")

    def test_get_videos_status_filter_ready(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/videos?status=ready", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # All returned videos should have status "ready"
        for v in data:
            assert v.get("processing_status") == "ready", (
                f"Video '{v['title']}' has status '{v.get('processing_status')}', expected 'ready'"
            )
        print(f"PASS: GET /api/videos?status=ready returns {len(data)} ready videos")

    def test_get_videos_status_filter_failed(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/videos?status=failed", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for v in data:
            assert v.get("processing_status") == "failed"
        print(f"PASS: GET /api/videos?status=failed returns {len(data)} failed videos")

    def test_get_videos_sort_oldest(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/videos?sort=oldest", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # Verify ascending date order
        if len(data) >= 2:
            dates = [v.get("created_at") for v in data]
            assert dates == sorted(dates), "Videos not in ascending order when sort=oldest"
        print(f"PASS: GET /api/videos?sort=oldest returns {len(data)} videos in ascending order")

    def test_get_videos_sort_newest(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/videos?sort=newest", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if len(data) >= 2:
            dates = [v.get("created_at") for v in data]
            assert dates == sorted(dates, reverse=True), "Videos not in descending order when sort=newest"
        print(f"PASS: GET /api/videos?sort=newest returns {len(data)} videos in descending order")

    def test_get_videos_search_no_match_returns_empty_list(self, auth_headers):
        resp = requests.get(
            f"{BASE_URL}/api/videos?search=zzz_no_match_xyz_99999",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0
        print("PASS: Search with no-match returns empty list")

    def test_get_videos_requires_auth(self):
        resp = requests.get(f"{BASE_URL}/api/videos")
        # FastAPI's HTTPBearer returns 403 when no Authorization header is present
        assert resp.status_code in (401, 403)
        print(f"PASS: GET /api/videos without auth returns {resp.status_code}")


# ── Upload Status (resume support) ───────────────────────────────────────────

class TestUploadStatus:
    """GET /api/upload/status/{upload_id}"""

    def test_upload_status_nonexistent_returns_404(self, auth_headers):
        resp = requests.get(
            f"{BASE_URL}/api/upload/status/nonexistent-upload-id-xyz",
            headers=auth_headers,
        )
        assert resp.status_code == 404
        print("PASS: GET /api/upload/status/nonexistent returns 404")

    def test_upload_init_creates_session(self, auth_headers):
        data = {
            "filename": "TEST_resume_video.mp4",
            "title": "TEST_Resume Upload Test",
            "total_size": 10485760,  # 10MB
            "description": "Test upload for resume testing",
        }
        resp = requests.post(
            f"{BASE_URL}/api/upload/init",
            data=data,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert "upload_id" in result
        assert "video_id" in result
        assert isinstance(result["upload_id"], str)
        assert len(result["upload_id"]) > 0
        print(f"PASS: POST /api/upload/init creates session {result['upload_id']}")
        return result

    def test_upload_status_returns_chunks_received(self, auth_headers):
        # First init a session
        data = {
            "filename": "TEST_status_check.mp4",
            "title": "TEST_Status Check Upload",
            "total_size": 5242880,  # 5MB
        }
        init_resp = requests.post(
            f"{BASE_URL}/api/upload/init",
            data=data,
            headers=auth_headers,
        )
        assert init_resp.status_code == 200
        upload_id = init_resp.json()["upload_id"]

        # Now get status
        status_resp = requests.get(
            f"{BASE_URL}/api/upload/status/{upload_id}",
            headers=auth_headers,
        )
        assert status_resp.status_code == 200
        result = status_resp.json()
        assert result["upload_id"] == upload_id
        assert result["status"] == "in_progress"
        assert "chunks_received" in result
        assert isinstance(result["chunks_received"], list)
        assert result["chunks_received"] == []  # No chunks uploaded yet
        assert result["total_size"] == 5242880
        assert result["title"] == "TEST_Status Check Upload"
        print(f"PASS: GET /api/upload/status/{upload_id} returns chunks_received=[] for new session")

    def test_upload_status_requires_auth(self):
        resp = requests.get(
            f"{BASE_URL}/api/upload/status/some-upload-id",
        )
        # FastAPI's HTTPBearer returns 403 when no Authorization header is present
        assert resp.status_code in (401, 403)
        print(f"PASS: GET /api/upload/status/{{id}} without auth returns {resp.status_code}")


# ── PlayLab Webhook ───────────────────────────────────────────────────────────

class TestPlayLabWebhook:
    """PATCH /api/playlab/webhook, POST /api/playlab/test-webhook"""

    def test_get_settings_includes_webhook_fields(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/playlab/settings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Check webhook_url field exists (may be None)
        assert "webhook_url" in data
        assert "api_key" in data
        assert "enabled" in data
        print(f"PASS: GET /api/playlab/settings has webhook_url field = {data.get('webhook_url')!r}")

    def test_patch_webhook_sets_url_and_secret(self, auth_headers):
        resp = requests.patch(
            f"{BASE_URL}/api/playlab/webhook",
            params={
                "webhook_url": "https://httpbin.org/post",
                "webhook_secret": "test-secret-123",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "updated" in data["message"].lower() or "webhook" in data["message"].lower()
        print("PASS: PATCH /api/playlab/webhook sets url and secret")

    def test_get_settings_shows_updated_webhook_url(self, auth_headers):
        # Set webhook URL first
        requests.patch(
            f"{BASE_URL}/api/playlab/webhook",
            params={"webhook_url": "https://httpbin.org/post"},
            headers=auth_headers,
        )
        # Check it persisted
        resp = requests.get(f"{BASE_URL}/api/playlab/settings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("webhook_url") == "https://httpbin.org/post"
        print("PASS: GET /api/playlab/settings shows updated webhook_url")

    def test_test_webhook_with_no_url_returns_400(self, auth_headers):
        # First clear the webhook URL
        requests.patch(
            f"{BASE_URL}/api/playlab/webhook",
            params={"webhook_url": ""},
            headers=auth_headers,
        )
        # Now test webhook should fail with 400
        resp = requests.post(f"{BASE_URL}/api/playlab/test-webhook", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.json()
        assert "detail" in data
        print(f"PASS: POST /api/playlab/test-webhook with no URL returns 400: {data['detail']}")

    def test_test_webhook_with_httpbin_returns_success(self, auth_headers):
        # Set webhook URL to httpbin
        requests.patch(
            f"{BASE_URL}/api/playlab/webhook",
            params={"webhook_url": "https://httpbin.org/post"},
            headers=auth_headers,
        )
        # Now test webhook should succeed
        resp = requests.post(
            f"{BASE_URL}/api/playlab/test-webhook",
            headers=auth_headers,
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        assert data.get("status_code") == 200
        assert "response" in data
        print(f"PASS: POST /api/playlab/test-webhook with httpbin URL returns success: HTTP {data.get('status_code')}")

    def test_patch_webhook_clear_url(self, auth_headers):
        """Clear webhook URL after test."""
        resp = requests.patch(
            f"{BASE_URL}/api/playlab/webhook",
            params={"webhook_url": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        print("PASS: PATCH /api/playlab/webhook with empty url clears it")


# ── Regression: existing routes ───────────────────────────────────────────────

class TestRegression:
    """Regression tests for all previously working features after module split."""

    def test_auth_routes_still_work(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "StreamHost", "password": "TestPass123!@#"},
        )
        assert resp.status_code == 200
        print("PASS: Regression - auth route works")

    def test_folders_route_still_works(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/folders", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        print("PASS: Regression - GET /api/folders works")

    def test_mesh_status_still_works(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/mesh/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        print("PASS: Regression - GET /api/mesh/status works")

    def test_mesh_nodes_still_works(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/mesh/nodes", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Mesh nodes returns {local_node: {...}, remote_nodes: [...]}
        assert "local_node" in data or isinstance(data, list)
        print("PASS: Regression - GET /api/mesh/nodes works")

    def test_playlab_videos_still_works(self, auth_headers):
        # Get API key first
        settings_resp = requests.get(f"{BASE_URL}/api/playlab/settings", headers=auth_headers)
        assert settings_resp.status_code == 200
        api_key = settings_resp.json().get("api_key")

        resp = requests.get(
            f"{BASE_URL}/api/playlab/videos",
            headers={"X-PlayLab-Key": api_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "videos" in data
        print(f"PASS: Regression - GET /api/playlab/videos works, {data['count']} ready videos")

    def test_upload_init_still_works(self, auth_headers):
        resp = requests.post(
            f"{BASE_URL}/api/upload/init",
            data={
                "filename": "TEST_regression.mp4",
                "title": "TEST_Regression Upload",
                "total_size": 1048576,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "upload_id" in data
        print("PASS: Regression - POST /api/upload/init works")
