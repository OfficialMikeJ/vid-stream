"""
Iteration 6 backend tests: Analytics Dashboard
- GET /api/analytics/overview (admin only)
- GET /api/analytics/timeline (admin only)
- GET /api/analytics/videos (admin only)
- GET /api/analytics/video/{video_id} (both roles)
- View tracking via /api/stream/hls/{video_id}/playlist.m3u8 + de-dupe
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_USER = "StreamHost"
ADMIN_PASS = "TestPass123!@#"
VIEWER_USER = "testviewer"
VIEWER_PASS = "Viewer123!"


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"username": ADMIN_USER, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def viewer_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"username": VIEWER_USER, "password": VIEWER_PASS})
    if r.status_code != 200:
        pytest.skip(f"Viewer login failed: {r.text}")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture(scope="module")
def any_video_id(admin_headers):
    """Find any existing video for single-video stats endpoint."""
    r = requests.get(f"{BASE_URL}/api/videos", headers=admin_headers)
    if r.status_code != 200:
        pytest.skip("Cannot list videos")
    vids = r.json()
    if not vids:
        pytest.skip("No videos available")
    return vids[0]["id"]


@pytest.fixture(scope="module")
def ready_video_id(admin_headers):
    """Ready video with HLS for view-tracking; skip if none."""
    r = requests.get(f"{BASE_URL}/api/videos?status=ready", headers=admin_headers)
    if r.status_code != 200:
        pytest.skip("Cannot list videos")
    vids = [v for v in r.json() if v.get("hls_path")]
    if not vids:
        pytest.skip("No ready videos with HLS available")
    return vids[0]["id"]


# ── /api/analytics/overview ─────────────────────────────────────────────────

class TestOverview:
    def test_admin_can_get_overview(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/overview", headers=admin_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("total_videos", "ready_videos", "total_views",
                  "unique_viewers", "views_24h", "storage_bytes",
                  "total_duration_seconds"):
            assert k in d, f"Missing key {k}"
            assert isinstance(d[k], (int, float)), f"{k} not numeric: {d[k]}"

    def test_viewer_forbidden(self, viewer_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/overview", headers=viewer_headers)
        assert r.status_code == 403, r.text

    def test_unauthenticated_rejected(self):
        r = requests.get(f"{BASE_URL}/api/analytics/overview")
        assert r.status_code in (401, 403)


# ── /api/analytics/timeline ─────────────────────────────────────────────────

class TestTimeline:
    @pytest.mark.parametrize("days", [1, 7, 30, 90])
    def test_admin_timeline_valid_days(self, admin_headers, days):
        r = requests.get(f"{BASE_URL}/api/analytics/timeline?days={days}",
                         headers=admin_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["days"] == days
        assert isinstance(d["series"], list)
        assert len(d["series"]) == days, f"Expected {days} entries, got {len(d['series'])}"
        for entry in d["series"]:
            assert "date" in entry and "views" in entry
            assert isinstance(entry["views"], int)

    def test_timeline_days_zero_rejected(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/timeline?days=0",
                         headers=admin_headers)
        assert r.status_code == 400

    def test_timeline_days_too_large_rejected(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/timeline?days=400",
                         headers=admin_headers)
        assert r.status_code == 400

    def test_viewer_forbidden(self, viewer_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/timeline?days=7",
                         headers=viewer_headers)
        assert r.status_code == 403


# ── /api/analytics/videos ───────────────────────────────────────────────────

class TestVideosList:
    @pytest.mark.parametrize("sort", ["views", "unique", "recent"])
    def test_admin_videos_list_sort(self, admin_headers, sort):
        r = requests.get(f"{BASE_URL}/api/analytics/videos?sort={sort}",
                         headers=admin_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["sort"] == sort
        assert isinstance(d["items"], list)
        for item in d["items"]:
            for key in ("video_id", "views", "unique_viewers", "last_viewed"):
                assert key in item, f"Missing {key} in {item}"
            # Title may be 'Deleted video' for orphaned views
            assert "title" in item

    def test_videos_invalid_sort_falls_back(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/videos?sort=garbage",
                         headers=admin_headers)
        assert r.status_code == 200
        # Per code: invalid sort defaults to "views"
        assert r.json()["sort"] == "views"

    def test_viewer_forbidden(self, viewer_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/videos", headers=viewer_headers)
        assert r.status_code == 403


# ── /api/analytics/video/{video_id} ─────────────────────────────────────────

class TestSingleVideoStats:
    def test_admin_single_video(self, admin_headers, any_video_id):
        r = requests.get(f"{BASE_URL}/api/analytics/video/{any_video_id}",
                         headers=admin_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["video_id"] == any_video_id
        for key in ("total_views", "unique_viewers", "views_last_7d", "last_viewed"):
            assert key in d

    def test_viewer_can_see_single_video(self, viewer_headers, any_video_id):
        r = requests.get(f"{BASE_URL}/api/analytics/video/{any_video_id}",
                         headers=viewer_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["video_id"] == any_video_id

    def test_nonexistent_video_returns_404(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/video/does-not-exist-zzz",
                         headers=admin_headers)
        assert r.status_code == 404


# ── View tracking and de-dupe ───────────────────────────────────────────────

class TestViewTracking:
    def test_playlist_records_view_and_dedupes(self, admin_headers, ready_video_id):
        # Baseline overview
        r0 = requests.get(f"{BASE_URL}/api/analytics/overview", headers=admin_headers)
        assert r0.status_code == 200
        before = r0.json()["total_views"]

        # Per-video before
        r_v0 = requests.get(f"{BASE_URL}/api/analytics/video/{ready_video_id}",
                            headers=admin_headers)
        per_before = r_v0.json()["total_views"]

        # Hit playlist with same UA twice
        ua = {"User-Agent": "AnalyticsDedupeTest/1.0"}
        r1 = requests.get(f"{BASE_URL}/api/stream/hls/{ready_video_id}/playlist.m3u8",
                          headers=ua, allow_redirects=False)
        # 200 if HLS file exists; test still meaningful via overview delta
        assert r1.status_code in (200, 404), r1.status_code

        r2 = requests.get(f"{BASE_URL}/api/stream/hls/{ready_video_id}/playlist.m3u8",
                          headers=ua, allow_redirects=False)
        assert r2.status_code in (200, 404)

        # If playlist 404'd, view recording wouldn't trigger -> skip
        if r1.status_code == 404:
            pytest.skip("HLS playlist not present on disk; cannot exercise view hook")

        # Per-video after
        r_v1 = requests.get(f"{BASE_URL}/api/analytics/video/{ready_video_id}",
                            headers=admin_headers)
        per_after = r_v1.json()["total_views"]

        # Should increment by exactly 1 (de-duped)
        assert per_after - per_before == 1, (
            f"Expected +1 view (de-dupe), got {per_after - per_before}")

        # Overview should also grow by ~1 (allow >=1 in case other traffic)
        r3 = requests.get(f"{BASE_URL}/api/analytics/overview", headers=admin_headers)
        after = r3.json()["total_views"]
        assert after >= before + 1
