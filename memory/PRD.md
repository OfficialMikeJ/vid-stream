# StreamHost — Product Requirements Document

**Last Updated:** 2026-04-28

## Original Problem Statement
Build a video hosting service named "StreamHost" with:
- Upload videos (chunked for up to 56GB), process via FFmpeg (thumbnails, aspect ratio, HLS)
- Custom folder management and embedded streaming
- Local storage via filesystem (not GridFS)
- Single admin authentication with forced first-login password change
- Custom global player theme settings and embed settings (domain restriction, player colors)
- Desktop Application (Python Tkinter) for Windows with `.bat` quick-start scripts
- WordPress Integration: StreamHost Connector plugin + StreamLab Invites plugin
- UI/UX: Dark theme (Black/Gray), colored buttons (Green/Red/Gray/Black/Blue/Orange)
- Footer: "Copyright 2026 StreamHost | StreamHost Ver: 2025.12.17"
- Production Docker Compose setup for Ubuntu 20.4+ with Nginx

## Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Python, Motor (Async MongoDB), FFmpeg, JWT
- **Database:** MongoDB (filesystem storage for videos)
- **Desktop:** Python Tkinter + ttkbootstrap
- **Deployment:** Docker Compose, Nginx

## Default Credentials
- Username: `StreamHost`
- Password: `password1234!@#` (forces password change on first login)

## Key API Endpoints
- `POST /api/auth/login`
- `POST /api/auth/change-password`
- `POST /api/upload/init` — initialize chunked upload session
- `POST /api/upload/chunk` — send individual 5MB chunk
- `GET /api/videos` — list videos
- `GET /api/videos/{id}` — video detail
- `DELETE /api/videos/{id}` — delete
- `POST /api/folders` / `GET /api/folders` / `DELETE /api/folders/{id}`
- `GET /api/stream/hls/{id}/playlist.m3u8` — HLS streaming
- `GET /api/stream/thumbnail/{id}` — thumbnail
- `POST /api/embed-settings` / `GET /api/embed-settings/{id}` / `PATCH /api/embed-settings/{id}`
- `GET /api/embed-code/{id}` — get embed HTML
- `GET /api/health` — health check

## DB Schema
- **users:** `{id, username, password_hash, must_change_password, created_at}`
- **videos:** `{id, title, description, folder_id, original_filename, file_path, thumbnail_path, hls_path, duration, width, height, aspect_ratio, file_size, format, processing_status, created_at}`
- **folders:** `{id, name, parent_id, created_at}`
- **embed_settings:** `{id, video_id, allowed_domains, player_color, show_controls, autoplay, loop, custom_css, created_at, updated_at}`
- **uploads:** `{upload_id, video_id, filename, title, description, folder_id, total_size, chunks_received, status, created_at}` ← chunked upload tracking

## Code Architecture
```
/app/
├── backend/
│   ├── server.py           # All API routes
│   ├── video_storage/
│   │   ├── originals/
│   │   ├── thumbnails/
│   │   ├── hls/
│   │   └── temp/           # Chunked upload temp storage
│   └── tests/
│       └── test_chunked_upload.py
├── desktop-app/
│   ├── streamhost_desktop.py  # Tkinter desktop client
│   ├── StreamHost.bat
│   └── README.md
├── docker/
│   ├── docker-compose.prod.yml
│   ├── ubuntu-setup.sh
│   └── nginx/nginx.conf
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── UploadVideo.jsx     # True chunked upload
│       │   ├── VideoLibrary.jsx
│       │   ├── FolderManagement.jsx
│       │   ├── EmbedSettingsDialog.jsx
│       │   ├── VideoPlayer.jsx
│       │   ├── VideoSettings.jsx
│       │   └── Footer.jsx
│       └── pages/
├── wordpress-plugin/
└── wordpress-plugin-invites/
```

---

## What's Been Implemented

### 2026-04-28 (This Session)
- **True File Chunk Uploading (P0 COMPLETE)**
  - Backend: `POST /api/upload/init` + `POST /api/upload/chunk`
  - 5MB chunks, sequential, MongoDB state tracking, auto-reassemble on final chunk
  - Frontend: `UploadVideo.jsx` uses `File.slice()` for ALL file sizes
  - Desktop App: `_upload_thread` uses chunked upload with determinate progress bar
  - Test: 100% pass rate (10/10 backend + all frontend UI tests)

### Previous Sessions
- Fixed admin login persistence bug (self-healing `initialize_admin_user()`)
- Rebranded from VidStream to StreamHost
- Dark/Gray theme + colored buttons (Green/Red/Orange/Blue)
- Footer: "Copyright 2026 StreamHost | StreamHost Ver: 2025.12.17"
- Default credentials: StreamHost / password1234!@#
- Python Tkinter desktop app with Windows .bat scripts
- Docker Compose + Nginx + Ubuntu deployment scripts
- Two WordPress plugins created (pending user testing)

---

## Prioritized Backlog

### P0 (Done)
- [x] True File Chunk Uploading

### P1 (Done)
- [x] Python Desktop App API wiring (login, video library, upload, folders all connected)

### P2 — Upcoming
- [ ] E2E Docker deployment test on live Ubuntu (pending user environment)
- [ ] WordPress plugin testing (BLOCKED — user needs WP environment)

### Future / Backlog
- [ ] Player theme settings UI (global theme colors)
- [ ] Embed settings per-video UI improvements
- [ ] Upload resume on network failure (retry failed chunks)
- [ ] Video search / filter in library
- [ ] Multi-user support (currently single admin)
