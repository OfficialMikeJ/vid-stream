"""
Tests for StreamHost Storage Mesh and PlayLab Integration endpoints.
Covers: health, auth, mesh nodes CRUD + ping, playlab settings/key/videos.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_USERNAME = "StreamHost"
ADMIN_PASSWORD = "TestPass123!@#"


# ─── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def auth_token():
    """Get a valid JWT for the admin user."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def authed(auth_token):
    """Requests session with Authorization header."""
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"})
    return s


# ─── Health ─────────────────────────────────────────────────────────────────

class TestHealth:
    """Sanity-check: service must be up."""

    def test_health_ok(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"
        print("PASS: /api/health returns healthy")


# ─── Mesh Status ─────────────────────────────────────────────────────────────

class TestMeshStatus:
    """GET /api/mesh/status — public endpoint (no auth required)."""

    def test_mesh_status_returns_storage_stats(self):
        resp = requests.get(f"{BASE_URL}/api/mesh/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "storage_total_gb" in data, "Missing storage_total_gb"
        assert "storage_used_gb" in data, "Missing storage_used_gb"
        assert "video_count" in data, "Missing video_count"
        assert data.get("status") == "online"
        assert isinstance(data["storage_total_gb"], (int, float))
        assert isinstance(data["video_count"], int)
        print(f"PASS: /api/mesh/status returns stats: total={data['storage_total_gb']}GB used={data['storage_used_gb']}GB videos={data['video_count']}")


# ─── Mesh Nodes ──────────────────────────────────────────────────────────────

class TestMeshNodes:
    """CRUD + ping for /api/mesh/nodes — authenticated endpoints."""

    _created_node_id = None  # shared across test methods in class

    def test_get_mesh_nodes_structure(self, authed):
        resp = authed.get(f"{BASE_URL}/api/mesh/nodes")
        assert resp.status_code == 200
        data = resp.json()
        assert "local_node" in data, "Missing local_node"
        assert "remote_nodes" in data, "Missing remote_nodes"
        assert isinstance(data["remote_nodes"], list)
        local = data["local_node"]
        assert local.get("status") == "online"
        assert "storage_total_gb" in local
        assert "video_count" in local
        print(f"PASS: GET /api/mesh/nodes returns local_node + remote_nodes (count={len(data['remote_nodes'])})")

    def test_get_mesh_nodes_no_auth_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/mesh/nodes")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"
        print("PASS: GET /api/mesh/nodes without auth returns 401/403")

    def test_add_mesh_node(self, authed):
        payload = {
            "name": "TEST_StorageNode2",
            "url": "https://fake-node2.example.com",
            "api_key": "fake-api-key-for-testing-purposes",
        }
        resp = authed.post(f"{BASE_URL}/api/mesh/nodes", json=payload)
        assert resp.status_code == 200, f"Add node failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "TEST_StorageNode2"
        assert data["url"] == "https://fake-node2.example.com"
        assert "node_id" in data
        assert data["status"] in ("online", "offline", "unknown"), f"Unexpected status: {data['status']}"
        # Since fake URL, it should be offline
        assert data["status"] == "offline", f"Expected offline for fake URL, got {data['status']}"
        TestMeshNodes._created_node_id = data["node_id"]
        print(f"PASS: POST /api/mesh/nodes added node_id={data['node_id']} status={data['status']}")

    def test_add_duplicate_node_returns_400(self, authed):
        payload = {
            "name": "TEST_DuplicateNode",
            "url": "https://fake-node2.example.com",  # same URL as above
            "api_key": "another-key",
        }
        resp = authed.post(f"{BASE_URL}/api/mesh/nodes", json=payload)
        assert resp.status_code == 400, f"Expected 400 for duplicate, got {resp.status_code}"
        print("PASS: Duplicate node URL returns 400")

    def test_ping_mesh_node(self, authed):
        node_id = TestMeshNodes._created_node_id
        assert node_id, "No node created in previous test"
        resp = authed.post(f"{BASE_URL}/api/mesh/nodes/{node_id}/ping")
        assert resp.status_code == 200, f"Ping failed: {resp.text}"
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("online", "offline")
        # Fake URL → should be offline
        assert data["status"] == "offline"
        assert "last_seen" in data
        print(f"PASS: POST /api/mesh/nodes/{node_id}/ping returns status={data['status']}")

    def test_ping_nonexistent_node_returns_404(self, authed):
        resp = authed.post(f"{BASE_URL}/api/mesh/nodes/nonexistent-node-id/ping")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("PASS: Ping nonexistent node returns 404")

    def test_delete_mesh_node(self, authed):
        node_id = TestMeshNodes._created_node_id
        assert node_id, "No node created in previous test"
        resp = authed.delete(f"{BASE_URL}/api/mesh/nodes/{node_id}")
        assert resp.status_code == 200, f"Delete failed: {resp.text}"
        data = resp.json()
        assert "message" in data
        print(f"PASS: DELETE /api/mesh/nodes/{node_id} removed node")

    def test_delete_nonexistent_node_returns_404(self, authed):
        resp = authed.delete(f"{BASE_URL}/api/mesh/nodes/nonexistent-node-id")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("PASS: Delete nonexistent node returns 404")

    def test_node_not_in_list_after_delete(self, authed):
        node_id = TestMeshNodes._created_node_id
        assert node_id, "No node created in previous test"
        resp = authed.get(f"{BASE_URL}/api/mesh/nodes")
        assert resp.status_code == 200
        remote = resp.json()["remote_nodes"]
        ids = [n["node_id"] for n in remote]
        assert node_id not in ids, f"Node {node_id} still in list after delete"
        print(f"PASS: Deleted node {node_id} no longer in mesh node list")


# ─── PlayLab Settings ────────────────────────────────────────────────────────

class TestPlayLabSettings:
    """GET/PATCH /api/playlab/settings and key regeneration."""

    _api_key = None  # shared

    def test_get_playlab_settings(self, authed):
        resp = authed.get(f"{BASE_URL}/api/playlab/settings")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "api_key" in data
        assert "enabled" in data
        assert "videos_endpoint" in data
        assert "video_detail_endpoint" in data
        assert isinstance(data["api_key"], str) and len(data["api_key"]) > 0
        TestPlayLabSettings._api_key = data["api_key"]
        print(f"PASS: GET /api/playlab/settings returns api_key and endpoints (enabled={data['enabled']})")

    def test_regenerate_playlab_key(self, authed):
        old_key = TestPlayLabSettings._api_key
        resp = authed.post(f"{BASE_URL}/api/playlab/regenerate-key")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "api_key" in data
        new_key = data["api_key"]
        assert new_key != old_key, "New key should differ from old key"
        TestPlayLabSettings._api_key = new_key
        print(f"PASS: POST /api/playlab/regenerate-key returns new key (different from old)")

    def test_patch_playlab_disabled(self, authed):
        resp = authed.patch(f"{BASE_URL}/api/playlab/settings?enabled=false")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "message" in data and "disabled" in data["message"].lower()
        print("PASS: PATCH /api/playlab/settings?enabled=false disables integration")

    def test_patch_playlab_enabled(self, authed):
        resp = authed.patch(f"{BASE_URL}/api/playlab/settings?enabled=true")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "message" in data and "enabled" in data["message"].lower()
        print("PASS: PATCH /api/playlab/settings?enabled=true re-enables integration")


# ─── PlayLab Videos ──────────────────────────────────────────────────────────

class TestPlayLabVideos:
    """GET /api/playlab/videos — key-based auth."""

    def test_get_videos_without_key_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/playlab/videos")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("PASS: GET /api/playlab/videos without key returns 401")

    def test_get_videos_with_wrong_key_returns_403(self):
        resp = requests.get(f"{BASE_URL}/api/playlab/videos", headers={"X-PlayLab-Key": "wrong-key"})
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("PASS: GET /api/playlab/videos with wrong key returns 403")

    def test_get_videos_with_valid_key(self, authed):
        # First fetch current API key
        settings_resp = authed.get(f"{BASE_URL}/api/playlab/settings")
        assert settings_resp.status_code == 200
        api_key = settings_resp.json()["api_key"]

        resp = requests.get(
            f"{BASE_URL}/api/playlab/videos",
            headers={"X-PlayLab-Key": api_key},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "count" in data
        assert "videos" in data
        assert isinstance(data["videos"], list)
        assert data["count"] == len(data["videos"])
        print(f"PASS: GET /api/playlab/videos returns count={data['count']} videos")

    def test_get_videos_via_query_param(self, authed):
        settings_resp = authed.get(f"{BASE_URL}/api/playlab/settings")
        api_key = settings_resp.json()["api_key"]
        resp = requests.get(f"{BASE_URL}/api/playlab/videos?api_key={api_key}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "videos" in data
        print("PASS: GET /api/playlab/videos?api_key= also works")

    def test_get_videos_when_disabled_returns_403(self, authed):
        # Disable PlayLab
        authed.patch(f"{BASE_URL}/api/playlab/settings?enabled=false")

        settings_resp = authed.get(f"{BASE_URL}/api/playlab/settings")
        api_key = settings_resp.json()["api_key"]

        resp = requests.get(
            f"{BASE_URL}/api/playlab/videos",
            headers={"X-PlayLab-Key": api_key},
        )
        assert resp.status_code == 403, f"Expected 403 when disabled, got {resp.status_code}: {resp.text}"
        print("PASS: GET /api/playlab/videos returns 403 when integration is disabled")

        # Re-enable for cleanup
        authed.patch(f"{BASE_URL}/api/playlab/settings?enabled=true")
        print("PASS: Re-enabled PlayLab integration after test")


# ─── PlayLab Video Detail ─────────────────────────────────────────────────────

class TestPlayLabVideoDetail:
    """GET /api/playlab/video/{id}."""

    def test_get_video_detail_nonexistent_returns_404(self, authed):
        settings_resp = authed.get(f"{BASE_URL}/api/playlab/settings")
        api_key = settings_resp.json()["api_key"]

        resp = requests.get(
            f"{BASE_URL}/api/playlab/video/nonexistent-video-id",
            headers={"X-PlayLab-Key": api_key},
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("PASS: GET /api/playlab/video/nonexistent returns 404")


# ─── Regression: Existing Endpoints ──────────────────────────────────────────

class TestRegression:
    """Ensure pre-existing endpoints still work after new additions."""

    def test_videos_list_still_works(self, authed):
        resp = authed.get(f"{BASE_URL}/api/videos")
        assert resp.status_code == 200
        data = resp.json()
        # /api/videos returns a plain list
        assert isinstance(data, list)
        print(f"PASS: GET /api/videos still works (count={len(data)})")

    def test_upload_init_still_works(self, auth_token):
        # upload/init uses multipart Form fields (not JSON) — must NOT send Content-Type: application/json
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = requests.post(
            f"{BASE_URL}/api/upload/init",
            data={
                "filename": "regression_test.mp4",
                "title": "Regression Test",
                "total_size": 1024,
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Upload init failed: {resp.text}"
        data = resp.json()
        assert "upload_id" in data
        assert "video_id" in data
        print(f"PASS: POST /api/upload/init still works upload_id={data['upload_id']}")
