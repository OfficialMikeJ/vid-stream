# StreamHost — Product Requirements Document

**Last Updated:** 2026-04-29

## Original Problem Statement
Build a video hosting service named "StreamHost" with:
- Upload videos (chunked for up to 56GB), process via FFmpeg (thumbnails, aspect ratio, HLS)
- Custom folder management and embedded streaming
- Local storage via filesystem
- Multi-user authentication (admin / viewer roles); forced first-login password change
- Custom global player theme & per-video embed settings (domain restriction, colors)
- Desktop Application (Python Tkinter) for Windows
- "PlayLab" PHP integration: serve video files + bulk reverse import + webhook auto-sync
- Storage Mesh: pool storage from multiple StreamHost servers
- UI/UX: Dark theme (Black/Gray), colored buttons (Green/Red/Gray/Black/Blue/Orange)
- Footer: "Copyright 2026 StreamHost | StreamHost Ver: 2025.12.17"
- *(Removed by user: Docker E2E deployment tests, WordPress plugin testing.)*

## Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn UI, hls.js
- **Backend:** FastAPI (modular routers), Python, Motor (async MongoDB), FFmpeg, JWT, slowapi (rate limiting)
- **Database:** MongoDB
- **Desktop:** Python Tkinter + ttkbootstrap

## Default Credentials
See `/app/memory/test_credentials.md` for current admin/viewer accounts.

## Code Architecture
```
/app/
├── backend/
│   ├── server.py            # Entry point, router registration, startup admin seed
│   ├── database.py          # Motor client + storage paths
│   ├── models.py            # Pydantic models
│   ├── security.py          # JWT, hashing, get_current_user, require_admin
│   ├── services.py          # Background: process_video (ffmpeg+HLS), webhook delivery
│   ├── transcoding.py       # Preset definitions (source, 1080p, 720p, 480p)
│   ├── rate_limit.py        # slowapi limiter, XFF-aware client_key
│   ├── routes/
│   │   ├── auth.py          # /auth/login, /auth/change-password (rate-limited)
│   │   ├── videos.py        # /videos, /folders, /stream/*, /embed-*, /settings/{player,transcoding}, /reprocess
│   │   ├── upload.py        # /upload/init, /upload/chunk, /upload/status (chunked + resume)
│   │   ├── mesh.py          # /mesh/* — storage mesh
│   │   ├── playlab.py       # /playlab/* — webhook + bulk import
│   │   ├── users.py         # /users — admin user CRUD
│   │   ├── analytics.py     # /analytics/{overview,timeline,videos,video/{id}}
│   │   ├── comments.py      # /videos/{id}/comments + /comments (mod list)
│   │   ├── captions.py      # /videos/{id}/captions, /captions/{id} (public VTT)
│   │   └── share.py         # /videos/{id}/share, /share/{token} (public)
│   └── tests/
└── frontend/src/
    ├── pages/
    │   ├── Dashboard.jsx
    │   ├── LoginPage.jsx
    │   └── SharedVideoPage.jsx     # Public /watch/:token
    └── components/
        ├── VideoLibrary.jsx
        ├── UploadVideo.jsx          # Chunked upload + transcoding preset selector
        ├── VideoPlayer.jsx          # HLS + caption tracks
        ├── VideoSettings.jsx        # Player theme + Transcoding tab + Users tab
        ├── FolderManagement.jsx
        ├── EmbedSettingsDialog.jsx
        ├── MeshNetwork.jsx
        ├── PlayLabIntegration.jsx
        ├── AnalyticsDashboard.jsx   # Stats cards + timeline + top videos
        ├── VideoComments.jsx        # Per-video comment thread
        ├── VideoCaptions.jsx        # Caption upload + list (admin)
        ├── ShareLinksDialog.jsx     # Admin share-link manager
        └── Footer.jsx
```

## Key API Endpoints
### Auth (rate-limited 10/min login, 5/min password)
- `POST /api/auth/login`, `POST /api/auth/change-password`

### Videos / Streaming
- `POST /api/videos/upload` (with `transcoding_preset`)
- `POST /api/upload/init`, `POST /api/upload/chunk`, `GET /api/upload/status/{id}`
- `GET /api/videos` (search, status, sort), `GET /api/videos/{id}`, `DELETE /api/videos/{id}`, `PATCH /api/videos/{id}`
- `POST /api/videos/{id}/reprocess?preset=`
- `GET /api/stream/hls/{id}/playlist.m3u8` (auto-records analytics view)
- `GET /api/stream/hls/{id}/{segment}`, `GET /api/stream/thumbnail/{id}`

### Folders, Embed, Player
- `POST/GET/DELETE /api/folders`
- `POST/GET/PATCH /api/embed-settings`, `GET /api/embed-code/{id}`
- `GET/PATCH /api/settings/player`, `GET/PATCH /api/settings/transcoding`

### Multi-user (admin only)
- `GET/POST /api/users`, `PATCH /api/users/{id}`, `DELETE /api/users/{id}`

### Mesh / PlayLab
- `GET/POST/DELETE /api/mesh/nodes`, `POST /api/mesh/nodes/{id}/ping`, `GET /api/mesh/status`
- `GET/PATCH /api/playlab/settings`, `POST /api/playlab/regenerate-key`
- `GET /api/playlab/videos`, `GET /api/playlab/video/{id}`
- `POST /api/playlab/import`, `PATCH /api/playlab/webhook`, `POST /api/playlab/test-webhook`

### Analytics (admin)
- `GET /api/analytics/overview` — total videos/views/storage/duration/24h
- `GET /api/analytics/timeline?days=N` — daily view series
- `GET /api/analytics/videos?sort=views|unique|recent` — top videos
- `GET /api/analytics/video/{id}` — single-video stats (admin + viewer)

### Comments
- `GET/POST /api/videos/{id}/comments` (any user; rate-limited POST 30/min)
- `DELETE /api/videos/{id}/comments/{cid}` (admin or own)
- `GET /api/comments` — admin moderation list

### Captions
- `GET /api/videos/{id}/captions`, `POST /api/videos/{id}/captions` (admin)
- `GET /api/captions/{cid}` — PUBLIC (used by `<track>`)
- `DELETE /api/videos/{id}/captions/{cid}` (admin)

### Share Links
- `POST /api/videos/{id}/share` (admin) — body: `{label?, password?, expires_at?}`
- `GET /api/videos/{id}/share` (admin) — list links
- `DELETE /api/share/{token}` (admin)
- `GET /api/share/{token}` — PUBLIC, rate-limited 120/min, returns `{requires_password}` then full payload after `?password=`

## DB Schema
- **users**: `{id, username, password_hash, role, is_active, must_change_password, created_at}`
- **videos**: `{id, title, description, folder_id, original_filename, file_path, thumbnail_path, hls_path, duration, width, height, aspect_ratio, file_size, format, processing_status, transcoding_preset, created_at}`
- **folders**: `{id, name, parent_id, created_at}`
- **embed_settings**: `{id, video_id, allowed_domains, player_color, show_controls, autoplay, loop, custom_css}`
- **uploads**: `{upload_id, video_id, filename, title, description, folder_id, transcoding_preset, total_size, chunks_received, status}`
- **global_settings**: `{type:'player'|'transcoding', ...}`
- **mesh_nodes**, **playlab_settings**: as before
- **video_views**: `{video_id, visitor (hash), referrer, timestamp}` — analytics
- **comments**: `{id, video_id, username, user_role, body, created_at}`
- **captions**: `{id, video_id, language, label, is_default, file_path, size_bytes, created_at}`
- **share_links**: `{id, token, video_id, label, expires_at, password_hash, view_count, created_by, created_at}`

---

## What's Been Implemented

### 2026-04-29 Session — All 6 Optional Features (DONE, fully tested)
- **Analytics Dashboard** — view tracking (de-duped per visitor 30min) + admin dashboard with 6 stat cards, daily-views chart, top-videos table. Iteration 6: 18 backend + frontend tests green.
- **Transcoding Presets** — 4 presets (source/1080p/720p/480p) selectable per-upload + global default. New `/api/settings/transcoding` and per-video `/reprocess`. Iteration 7: 13 tests green.
- **Video Comments** — per-video threads with admin moderation. Both roles post; admins delete any, viewers delete own. Iteration 8: 16 tests green.
- **Captions / Subtitles** — WebVTT upload + automatic SRT→VTT conversion. Public `/api/captions/{id}` for `<track>` element. Default-track flag is mutually exclusive. Iteration 9: 14 tests green.
- **Video Sharing Links** — public tokenized URLs with optional password & expiration; standalone `/watch/:token` page (no auth). Iteration 10: 19 tests green.
- **API Rate Limiting** — slowapi with XFF-aware key. Login 10/min, change-password 5/min, comments 30/min, share 120/min. Iteration 11: 8 tests green.

### 2026-04-29 Earlier in session
- Modular backend split, multi-user roles, player theme UI, embed-settings UI, PlayLab bulk import.

### Previous sessions
- Storage Mesh, PlayLab base integration, webhook auto-sync, chunked upload + resume, video search/filter, Python desktop app.

---

## Prioritized Backlog

### Done (this session)
- [x] Analytics Dashboard
- [x] Video Transcoding Presets
- [x] Comments
- [x] Captions / Subtitles
- [x] Video Sharing Links
- [x] API Rate Limiting

### P2 / Future
- [ ] Desktop App E2E verification (chunked upload + new endpoints)
- [ ] Storage Mesh peer-to-peer file transfer (currently only stats pooling)
- [ ] Redis-backed rate limiter for multi-pod deployments (currently in-memory)
- [ ] Email notifications (e.g., new comment, share-link viewed)
- [ ] Adaptive bitrate HLS (multiple ladder rungs in one playlist)

### Removed by user
- ~~Docker E2E deployment tests~~
- ~~WordPress plugin testing~~
