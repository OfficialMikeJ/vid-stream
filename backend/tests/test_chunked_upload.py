"""
Tests for StreamHost chunked upload flow and related endpoints.
Covers: health, auth, upload/init, upload/chunk, and video retrieval.
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Credentials (original and potentially changed)
ADMIN_USERNAME = "StreamHost"
ADMIN_ORIGINAL_PASSWORD = "password1234!@#"
ADMIN_NEW_PASSWORD = "TestPass123!@#"


# ---------- Helpers ----------

def get_token(username: str, password: str) -> dict:
    """Login and return the full response json."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": username, "password": password},
    )
    return response


def do_login() -> str:
    """
    Login with original password. If must_change_password is True, change the
    password to ADMIN_NEW_PASSWORD and re-login. Returns a valid JWT token.
    """
    # Try original password first
    resp = get_token(ADMIN_USERNAME, ADMIN_ORIGINAL_PASSWORD)
    if resp.status_code == 200:
        data = resp.json()
        token = data["access_token"]
        if data.get("must_change_password"):
            # Change password
            change_resp = requests.post(
                f"{BASE_URL}/api/auth/change-password",
                json={
                    "current_password": ADMIN_ORIGINAL_PASSWORD,
                    "new_password": ADMIN_NEW_PASSWORD,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert change_resp.status_code == 200, (
                f"Password change failed: {change_resp.text}"
            )
            # Re-login with new password
            resp2 = get_token(ADMIN_USERNAME, ADMIN_NEW_PASSWORD)
            assert resp2.status_code == 200, f"Re-login failed: {resp2.text}"
            return resp2.json()["access_token"]
        return token

    # Try new password (already changed in a previous run)
    resp2 = get_token(ADMIN_USERNAME, ADMIN_NEW_PASSWORD)
    assert resp2.status_code == 200, (
        f"Login failed with both passwords. Last error: {resp2.text}"
    )
    return resp2.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- Tests ----------

class TestHealth:
    """Health check endpoint"""

    def test_health_returns_healthy(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        data = resp.json()
        assert data.get("status") == "healthy", f"Unexpected status: {data}"
        assert "database" in data
        assert data["database"] == "connected"
        print("PASS: /api/health returns healthy")


class TestAuth:
    """Authentication flow"""

    def test_login_with_original_or_new_password(self):
        """Login works with StreamHost credentials (either original or changed password)."""
        # Try original password first
        resp = get_token(ADMIN_USERNAME, ADMIN_ORIGINAL_PASSWORD)
        if resp.status_code == 200:
            data = resp.json()
            assert "access_token" in data
            assert isinstance(data["access_token"], str)
            assert len(data["access_token"]) > 0
            assert "must_change_password" in data
            print(
                f"PASS: Login with original password OK (must_change_password={data['must_change_password']})"
            )
            return

        # Try new password
        resp2 = get_token(ADMIN_USERNAME, ADMIN_NEW_PASSWORD)
        assert resp2.status_code == 200, (
            f"Login failed with both passwords. Status: {resp2.status_code}, Body: {resp2.text}"
        )
        data = resp2.json()
        assert "access_token" in data
        print("PASS: Login with new password OK")

    def test_login_invalid_credentials_rejected(self):
        resp = get_token(ADMIN_USERNAME, "totally-wrong-password")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: Invalid credentials return 401")

    def test_full_login_flow_with_password_change_if_needed(self):
        """Full flow: login → change password if needed → re-login."""
        token = do_login()
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 10
        print("PASS: Full login flow (with optional password change) successful")


class TestChunkedUpload:
    """Chunked upload: init → chunks → verify video record"""

    @pytest.fixture(scope="class")
    def token(self):
        return do_login()

    def _make_test_file(self, size_bytes: int = 11 * 1024 * 1024) -> bytes:
        """Create a small fake binary payload of given size."""
        # Use repeating bytes to simulate a small file
        return bytes(range(256)) * (size_bytes // 256 + 1)[:size_bytes]

    def test_upload_init_returns_ids(self, token):
        """POST /api/upload/init should return upload_id and video_id."""
        form_data = {
            "filename": "test_video.mp4",
            "title": "TEST_ChunkedUpload",
            "total_size": str(11 * 1024 * 1024),  # 11MB
        }
        resp = requests.post(
            f"{BASE_URL}/api/upload/init",
            data=form_data,
            headers=auth_headers(token),
        )
        assert resp.status_code == 200, f"Upload init failed: {resp.text}"
        data = resp.json()
        assert "upload_id" in data, f"Missing upload_id in response: {data}"
        assert "video_id" in data, f"Missing video_id in response: {data}"
        assert isinstance(data["upload_id"], str) and len(data["upload_id"]) > 0
        assert isinstance(data["video_id"], str) and len(data["video_id"]) > 0
        print(
            f"PASS: /api/upload/init returned upload_id={data['upload_id']}, video_id={data['video_id']}"
        )

    def test_full_chunked_upload_flow(self, token):
        """
        Full E2E: init → send 2 chunks → verify video record exists.
        Chunk 0: status should be in_progress.
        Chunk 1 (final): status should be complete with video_id.
        """
        CHUNK_SIZE = 5 * 1024 * 1024  # 5MB
        file_data = bytes(range(256)) * (CHUNK_SIZE * 2 // 256 + 1)
        file_data = file_data[: CHUNK_SIZE * 2]  # exactly 10MB (2 chunks)
        total_size = len(file_data)
        total_chunks = 2

        # --- Init ---
        form_data = {
            "filename": "test_video.mp4",
            "title": "TEST_FullChunkedFlow",
            "total_size": str(total_size),
        }
        init_resp = requests.post(
            f"{BASE_URL}/api/upload/init",
            data=form_data,
            headers=auth_headers(token),
        )
        assert init_resp.status_code == 200, f"Init failed: {init_resp.text}"
        init_data = init_resp.json()
        upload_id = init_data["upload_id"]
        video_id = init_data["video_id"]
        print(f"Init OK: upload_id={upload_id}, video_id={video_id}")

        # --- Chunk 0 (not final) ---
        chunk0_data = file_data[:CHUNK_SIZE]
        chunk_form = {
            "upload_id": (None, upload_id),
            "chunk_index": (None, "0"),
            "total_chunks": (None, str(total_chunks)),
            "chunk": ("chunk_0", io.BytesIO(chunk0_data), "application/octet-stream"),
        }
        chunk0_resp = requests.post(
            f"{BASE_URL}/api/upload/chunk",
            files=chunk_form,
            headers=auth_headers(token),
        )
        assert chunk0_resp.status_code == 200, f"Chunk 0 failed: {chunk0_resp.text}"
        chunk0_result = chunk0_resp.json()
        assert chunk0_result.get("status") == "in_progress", (
            f"Expected status=in_progress, got: {chunk0_result}"
        )
        assert chunk0_result.get("chunk_index") == 0
        assert chunk0_result.get("chunks_received") == 1
        print(f"PASS: Chunk 0 status=in_progress, chunks_received=1")

        # --- Chunk 1 (final) ---
        chunk1_data = file_data[CHUNK_SIZE:]
        chunk1_form = {
            "upload_id": (None, upload_id),
            "chunk_index": (None, "1"),
            "total_chunks": (None, str(total_chunks)),
            "chunk": ("chunk_1", io.BytesIO(chunk1_data), "application/octet-stream"),
        }
        chunk1_resp = requests.post(
            f"{BASE_URL}/api/upload/chunk",
            files=chunk1_form,
            headers=auth_headers(token),
        )
        assert chunk1_resp.status_code == 200, f"Chunk 1 (final) failed: {chunk1_resp.text}"
        chunk1_result = chunk1_resp.json()
        assert chunk1_result.get("status") == "complete", (
            f"Expected status=complete, got: {chunk1_result}"
        )
        assert "video_id" in chunk1_result, f"Missing video_id in final chunk response: {chunk1_result}"
        returned_video_id = chunk1_result["video_id"]
        assert returned_video_id == video_id, (
            f"video_id mismatch: init={video_id}, final={returned_video_id}"
        )
        print(f"PASS: Final chunk status=complete, video_id={returned_video_id}")

        # --- Verify video record exists ---
        video_resp = requests.get(
            f"{BASE_URL}/api/videos/{video_id}",
            headers=auth_headers(token),
        )
        assert video_resp.status_code == 200, (
            f"GET /api/videos/{video_id} failed: {video_resp.text}"
        )
        video_data = video_resp.json()
        assert video_data.get("id") == video_id
        assert video_data.get("title") == "TEST_FullChunkedFlow"
        assert video_data.get("processing_status") in ("pending", "processing", "ready", "failed"), (
            f"Unexpected processing_status: {video_data.get('processing_status')}"
        )
        print(
            f"PASS: GET /api/videos/{video_id} returned status={video_data.get('processing_status')}"
        )

    def test_chunk_upload_session_not_found(self, token):
        """Sending a chunk for a non-existent upload_id should return 404."""
        chunk_form = {
            "upload_id": (None, "non-existent-upload-id"),
            "chunk_index": (None, "0"),
            "total_chunks": (None, "2"),
            "chunk": ("chunk_0", io.BytesIO(b"hello world"), "application/octet-stream"),
        }
        resp = requests.post(
            f"{BASE_URL}/api/upload/chunk",
            files=chunk_form,
            headers=auth_headers(token),
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("PASS: Non-existent upload_id returns 404")

    def test_upload_requires_auth(self):
        """Upload init without auth should return 403."""
        form_data = {
            "filename": "test.mp4",
            "title": "NoAuth",
            "total_size": "1024",
        }
        resp = requests.post(f"{BASE_URL}/api/upload/init", data=form_data)
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )
        print("PASS: Upload init without auth rejected")


class TestVideoLibrary:
    """Basic video library endpoint checks"""

    @pytest.fixture(scope="class")
    def token(self):
        return do_login()

    def test_get_videos_list(self, token):
        """GET /api/videos should return a list."""
        resp = requests.get(
            f"{BASE_URL}/api/videos",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200, f"GET /api/videos failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"PASS: GET /api/videos returned {len(data)} videos")

    def test_get_nonexistent_video_returns_404(self, token):
        """GET /api/videos/<bad-id> should return 404."""
        resp = requests.get(
            f"{BASE_URL}/api/videos/definitely-not-a-real-video-id",
            headers=auth_headers(token),
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("PASS: Non-existent video returns 404")
