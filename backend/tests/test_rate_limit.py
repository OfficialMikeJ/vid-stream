"""Rate limiting (slowapi) — Feature #6 backend tests.

Tests are designed to NOT brick each other:
  * Each test uses a UNIQUE X-Forwarded-For value so they go into different
    rate-limit buckets (the limiter keys on XFF first hop).
  * Tests verify both the ENFORCEMENT (Nth+1 = 429) and the CONTRACT
    (JSON body shape, Retry-After header).
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN = {"username": "StreamHost", "password": "TestPass123!@#"}
VIEWER = {"username": "testviewer", "password": "Viewer123!"}


def _xff() -> str:
    """Unique fake source IP for this test invocation."""
    return f"10.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}"


def _login_with_xff(xff: str, creds=ADMIN) -> str:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=creds,
        headers={"X-Forwarded-For": xff},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


# ── 1. /api/auth/login limited to 10/minute ─────────────────────────────────

class TestLoginRateLimit:
    def test_login_429_after_10_attempts(self):
        xff = _xff()
        statuses = []
        for i in range(11):
            r = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": "StreamHost", "password": "wrong-on-purpose"},
                headers={"X-Forwarded-For": xff},
                timeout=15,
            )
            statuses.append(r.status_code)
            if r.status_code == 429:
                break
        # First 10 should be 401 (wrong creds), 11th should be 429
        assert statuses[:10].count(401) == 10, f"first 10 should be 401, got {statuses[:10]}"
        assert statuses[-1] == 429, f"11th should be 429, full = {statuses}"

    def test_login_429_body_and_headers(self):
        xff = _xff()
        last = None
        for _ in range(11):
            last = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": "x", "password": "y"},
                headers={"X-Forwarded-For": xff},
                timeout=15,
            )
            if last.status_code == 429:
                break
        assert last.status_code == 429
        # Must be JSON, not HTML
        assert "application/json" in last.headers.get("content-type", "").lower()
        body = last.json()
        assert "detail" in body and "Too many" in body["detail"]
        assert body.get("limit") == "10 per 1 minute"
        assert last.headers.get("Retry-After") == "60"

    def test_login_mix_right_and_wrong_counts_together(self):
        """Right + wrong creds from same IP share the same bucket."""
        xff = _xff()
        seq = []
        # 5 right, 5 wrong, then one more — should 429
        for i in range(11):
            creds = ADMIN if i % 2 == 0 else {"username": "StreamHost", "password": "bad"}
            r = requests.post(
                f"{BASE_URL}/api/auth/login",
                json=creds,
                headers={"X-Forwarded-For": xff},
                timeout=15,
            )
            seq.append(r.status_code)
        assert 429 in seq, f"expected a 429 in mixed sequence, got {seq}"
        assert seq.index(429) == 10, f"429 should be exactly the 11th, got {seq}"


# ── 2. XFF bucket isolation ─────────────────────────────────────────────────

class TestXForwardedForIsolation:
    def test_different_xff_have_separate_buckets(self):
        xff_a = _xff()
        xff_b = _xff()
        # Burn 10 on A so A is at the edge
        for _ in range(10):
            requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": "x", "password": "y"},
                headers={"X-Forwarded-For": xff_a},
                timeout=15,
            )
        # 11th from A — should 429
        r_a = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "x", "password": "y"},
            headers={"X-Forwarded-For": xff_a},
            timeout=15,
        )
        assert r_a.status_code == 429
        # First request from B — should NOT be 429 (separate bucket)
        r_b = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "x", "password": "y"},
            headers={"X-Forwarded-For": xff_b},
            timeout=15,
        )
        assert r_b.status_code == 401, f"B should be unaffected, got {r_b.status_code}"


# ── 3. /api/auth/change-password limited to 5/minute ────────────────────────

class TestChangePasswordRateLimit:
    def test_change_password_429_after_5(self):
        xff = _xff()
        token = _login_with_xff(xff, ADMIN)
        headers = {"Authorization": f"Bearer {token}", "X-Forwarded-For": xff}
        statuses = []
        for i in range(6):
            r = requests.post(
                f"{BASE_URL}/api/auth/change-password",
                json={"current_password": "definitely-wrong", "new_password": "Whatever123!"},
                headers=headers,
                timeout=15,
            )
            statuses.append(r.status_code)
            if r.status_code == 429:
                break
        # First 5 = 400 (wrong current pw), 6th = 429
        assert statuses[:5] == [400, 400, 400, 400, 400], f"got {statuses}"
        assert statuses[-1] == 429, f"6th should be 429, full = {statuses}"

        # Verify body shape on the 429
        r = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": "x", "new_password": "y"},
            headers=headers,
            timeout=15,
        )
        assert r.status_code == 429
        body = r.json()
        assert body.get("limit") == "5 per 1 minute"
        assert r.headers.get("Retry-After") == "60"


# ── 4. /api/videos/{id}/comments limited to 30/minute ──────────────────────

class TestCommentRateLimit:
    @pytest.fixture(scope="class")
    def video_and_token(self):
        # Login (separate XFF so it doesn't pollute other tests)
        token = _login_with_xff(_xff(), ADMIN)
        # Find a video the comment endpoint will accept
        r = requests.get(
            f"{BASE_URL}/api/videos",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        videos = body if isinstance(body, list) else body.get("items", [])
        if not videos:
            pytest.skip("No videos available to test comment rate limit")
        return videos[0]["id"], token

    def test_comment_429_after_30(self, video_and_token):
        video_id, token = video_and_token
        xff = _xff()
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Forwarded-For": xff,
            "Content-Type": "application/json",
        }
        created_ids = []
        statuses = []
        for i in range(31):
            r = requests.post(
                f"{BASE_URL}/api/videos/{video_id}/comments",
                json={"body": f"TEST_ratelimit_{i}_{uuid.uuid4().hex[:6]}"},
                headers=headers,
                timeout=15,
            )
            statuses.append(r.status_code)
            if r.status_code == 200:
                try:
                    created_ids.append(r.json().get("id"))
                except Exception:
                    pass
            if r.status_code == 429:
                break
        try:
            success_count = statuses[:30].count(200)
            assert success_count == 30, f"first 30 should be 200, got {statuses[:30]}"
            assert statuses[-1] == 429, f"31st should be 429, full = {statuses}"
        finally:
            # Cleanup created comments
            for cid in created_ids:
                if cid:
                    requests.delete(
                        f"{BASE_URL}/api/videos/{video_id}/comments/{cid}",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=15,
                    )


# ── 5. /api/share/{token} limited to 120/minute ────────────────────────────

class TestShareResolveRateLimit:
    @pytest.fixture(scope="class")
    def share_token(self):
        admin_token = _login_with_xff(_xff(), ADMIN)
        # Pick a video
        r = requests.get(
            f"{BASE_URL}/api/videos",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        body = r.json()
        videos = body if isinstance(body, list) else body.get("items", [])
        ready = [v for v in videos if v.get("processing_status") in ("ready", "external")]
        if not ready:
            pytest.skip("No ready video for share-link rate-limit test")
        vid = ready[0]["id"]
        # Create a share link
        r = requests.post(
            f"{BASE_URL}/api/videos/{vid}/share",
            json={"label": "TEST_ratelimit"},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        yield token, admin_token
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/share/{token}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )

    def test_share_resolve_429_after_120(self, share_token):
        from concurrent.futures import ThreadPoolExecutor
        token, _ = share_token
        xff = _xff()

        def _hit(_i):
            return requests.get(
                f"{BASE_URL}/api/share/{token}",
                headers={"X-Forwarded-For": xff},
                timeout=15,
            ).status_code

        # Fire 140 requests in parallel — must complete well within 60s,
        # so the 120/min limit fires deterministically.
        with ThreadPoolExecutor(max_workers=20) as ex:
            statuses = list(ex.map(_hit, range(140)))

        ok = statuses.count(200)
        too_many = statuses.count(429)
        assert too_many > 0, f"expected at least one 429, distribution = {sorted(set(statuses))}, counts: 200={ok}, 429={too_many}"
        assert ok <= 120, f"more than 120 succeeded: ok={ok}"
        assert ok + too_many == 140, f"unexpected statuses: {set(statuses)}"
        # Verify body shape — wait briefly to ensure XFF bucket still saturated
        r = requests.get(
            f"{BASE_URL}/api/share/{token}",
            headers={"X-Forwarded-For": xff},
            timeout=15,
        )
        assert r.status_code == 429, f"follow-up request expected 429, got {r.status_code}"
        body = r.json()
        assert body.get("limit") == "120 per 1 minute"
        assert r.headers.get("Retry-After") == "60"


# ── 6. Non-rate-limited endpoints stay open ────────────────────────────────

class TestUnlimitedEndpoints:
    def test_get_videos_not_rate_limited(self):
        token = _login_with_xff(_xff(), ADMIN)
        xff = _xff()
        headers = {"Authorization": f"Bearer {token}", "X-Forwarded-For": xff}
        statuses = []
        for _ in range(50):
            r = requests.get(f"{BASE_URL}/api/videos", headers=headers, timeout=15)
            statuses.append(r.status_code)
        assert 429 not in statuses, f"GET /api/videos should not rate-limit, got {set(statuses)}"
        # All should be 200
        assert all(s == 200 for s in statuses), f"unexpected statuses: {set(statuses)}"
