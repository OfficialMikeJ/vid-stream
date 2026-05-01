# StreamHost - Video Hosting Service

A powerful, self-hosted video hosting platform with FFmpeg processing, HLS streaming, and customizable embed options. Upload, process, organize, and stream videos with ease.

![StreamHost Dashboard](https://img.shields.io/badge/Status-Production%20Ready-success)
![Version](https://img.shields.io/badge/Version-2025.12.17-blue)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-19.0-61dafb)

## 🎯 Features

### Video Management
- **Multi-format Support** - Upload any FFmpeg-compatible video format (MP4, MOV, AVI, MKV, WebM, FLV, WMV, MPEG, etc.)
- **Large File Support** - Upload videos up to 56GB
- **Automatic Processing Pipeline**
  - Metadata extraction (duration, resolution, aspect ratio)
  - Automatic thumbnail generation from video content
  - HLS transcoding for adaptive streaming
  - Real-time processing status tracking
- **Folder Organization** - Create custom folders to organize your video library
- **Video Metadata** - Edit titles, descriptions, and organize into folders

### Streaming & Embed
- **HLS Streaming** - Adaptive bitrate streaming for optimal playback on any device
- **Custom Embed Codes** - Generate embed codes for external websites
- **Domain Restrictions** - Whitelist specific domains for video embeds
- **Player Customization**
  - Custom player colors
  - Toggle controls visibility
  - Autoplay and loop options
  - Custom CSS support

### Security
- **JWT Authentication** - Secure token-based authentication
- **Admin Access Control** - Single admin user with secure credentials
- **Password Management** - Forced password change on first login
- **Bcrypt Hashing** - Industry-standard password security

### User Interface
- **Modern Dark Theme** - Black/Gray backgrounds with colored button accents
- **Responsive Layout** - Works seamlessly on desktop and mobile devices
- **Drag & Drop Upload** - Intuitive file upload with progress tracking
- **Video Grid Library** - Organized video display with thumbnails
- **Inline Video Player** - Play videos directly in the dashboard

### Desktop Application
- **Cross-Platform** - Python Tkinter-based desktop client
- **Full Feature Parity** - Login, upload, manage videos, folders
- **Windows Batch Scripts** - Double-click to install and run

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database for flexible data storage
- **FFmpeg** - Industry-standard video processing
- **Motor** - Async MongoDB driver
- **Python-Jose** - JWT token handling
- **Passlib + Bcrypt** - Secure password hashing

### Frontend
- **React 19** - Latest React with concurrent features
- **React Router** - Client-side routing
- **Shadcn/UI** - Beautiful, accessible UI components
- **TailwindCSS** - Utility-first CSS framework
- **HLS.js** - HTTP Live Streaming library
- **Axios** - HTTP client for API calls
- **Sonner** - Toast notifications

### Desktop App
- **Python 3.8+** - Cross-platform compatibility
- **Tkinter + ttkbootstrap** - Modern dark-themed UI
- **Requests** - API communication

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+ and Yarn
- MongoDB 5.0+
- FFmpeg 5.0+
- 2GB+ RAM (4GB+ recommended for processing)
- 10GB+ storage (depending on video library size)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/streamhost.git
cd streamhost
```

### 2. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg mongodb
```

#### macOS
```bash
brew install ffmpeg mongodb-community
brew services start mongodb-community
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

### 4. Frontend Setup

```bash
cd frontend

# Install Node dependencies
yarn install

# Configure environment variables
cp .env.example .env
# Edit .env with your backend URL
```

### 5. Start the Application

> **📘 For Production Deployment:** See [PRODUCTION-GUIDE.md](PRODUCTION-GUIDE.md) for complete production setup with Nginx, Supervisor, SSL, and security configuration.

#### Development Mode

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Frontend:**
```bash
cd frontend
yarn start
```

## 🐳 Docker Deployment (recommended for production)

The easiest way to deploy StreamHost to any server (aaPanel, plain Ubuntu, a VPS, etc.) is with pre-built Docker images from **GitHub Container Registry (GHCR)**. You only need **two files** on the server — no source code.

### How it works

```
 ┌────────────────┐   push to main    ┌─────────────────────────────┐
 │  Your GitHub   │ ───────────────▶  │  GitHub Actions builds and  │
 │  repository    │                    │  pushes backend + frontend  │
 └────────────────┘                    │  images to ghcr.io          │
                                       └──────────────┬──────────────┘
                                                      │ docker compose pull
                                                      ▼
                                       ┌─────────────────────────────┐
                                       │  Your server (aaPanel/VPS)  │
                                       │  runs docker-compose.yml +  │
                                       │  .env — nothing else needed │
                                       └─────────────────────────────┘
```

### ⚠️ Common error

> `unable to prepare context: path ".../frontend" not found`

This means you uploaded `docker-compose.yml` that uses `build: ./frontend` but didn't put the source on the server. **Use the pre-built image flow below instead.**

### Step 1 — Publish images (one-time setup on GitHub)

The repo ships with `.github/workflows/build-images.yml`. It builds and pushes both images to GHCR on every push to `main`/`master`, every tag, and every Release.

1. Push the repo to GitHub (use **"Save to GitHub"** in chat, or plain `git push`).
2. Go to **Actions** tab → **Build & Push Docker Images** → **Run workflow** (first run).
3. Once finished, check your GitHub profile → **Packages** — you should see:
   - `<repo>-backend`
   - `<repo>-frontend`
4. (Optional) Make packages public: profile → each package → Package settings → Change visibility → Public. If you keep them private, you'll need to `docker login ghcr.io` on the server.

### Step 2 — Prepare the server

On the server (aaPanel compose folder or `/opt/streamhost/`):

1. Upload **only these two files** from the repo:
   - `docker-compose.deploy.yml` → rename to `docker-compose.yml`
   - `.env.example` → rename to `.env`
2. Edit `.env` and fill in real values:
   ```bash
   # Replace with your GitHub namespace (lowercase!)
   IMAGE_BACKEND=ghcr.io/yourname/streamhost-backend:latest
   IMAGE_FRONTEND=ghcr.io/yourname/streamhost-frontend:latest

   # Strong random string used to sign JWTs
   JWT_SECRET=a-long-random-secret-string-change-this

   # Public URL where the backend is reachable
   BACKEND_URL=https://yourdomain.com

   # CORS allow-list (use * only for testing)
   CORS_ORIGINS=https://yourdomain.com

   # Host ports (change if these are taken)
   BACKEND_PORT=8001
   FRONTEND_PORT=3000
   ```

### Step 3 — Private images (skip if you made them public)

If the packages are private, log in on the server with a GitHub Personal Access Token that has `read:packages` scope:

```bash
echo "YOUR_PAT" | docker login ghcr.io -u your-github-username --password-stdin
```

### Step 4 — Run it

```bash
docker compose pull
docker compose up -d
docker compose ps
docker compose logs -f backend   # optional — watch startup
```

Open `http://your-server:3000` and log in with the default credentials (you'll be forced to change the password on first login).

### Updating to the latest version

```bash
docker compose pull && docker compose up -d
```

### File reference

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Local-dev compose that **builds** images from source (needs repo cloned). |
| `docker-compose.deploy.yml` | Production compose using **pre-built images** from GHCR. Ship this to the server. |
| `.env.example` | Template for the env file that sits next to the deploy compose. |
| `.github/workflows/build-images.yml` | Builds + pushes backend and frontend images to GHCR on push/tag/release. |
| `.github/workflows/build-desktop.yml` | Builds the Windows `.exe` of the desktop app via PyInstaller on push/tag/release. |

### Using a plain Linux box (no aaPanel)

```bash
mkdir -p /opt/streamhost && cd /opt/streamhost
# Upload docker-compose.deploy.yml as docker-compose.yml and .env alongside it
docker compose pull
docker compose up -d
```

Put Nginx in front of `:3000` and `:8001` for HTTPS — see the Nginx example further down in this README.

## 🖥️ Desktop Application

The StreamHost Desktop Application provides the same features as the web interface in a native desktop experience.

### Installation (Windows)

1. Navigate to the `desktop-app` folder
2. Double-click `StreamHost.bat`
3. The script will:
   - Check Python installation
   - Create a virtual environment
   - Install dependencies
   - Launch the application

### Files

| File | Purpose |
|------|---------|
| `StreamHost.bat` | Main launcher (first-time setup + run) |
| `StreamHost_QuickStart.bat` | Fast launcher (skips setup) |
| `Install_Dependencies.bat` | Install only (no launch) |
| `streamhost_desktop.py` | Main application |
| `requirements.txt` | Python dependencies |

### Running Manually

```bash
cd desktop-app

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python streamhost_desktop.py
```

## ⚙️ Configuration

### Backend Environment Variables (`backend/.env`)

```bash
# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="streamhost_db"

# Security
JWT_SECRET="your-super-secret-jwt-key-change-this"
CORS_ORIGINS="*"  # In production, specify your frontend domain

# Server Configuration (optional)
BACKEND_URL="http://localhost:8001"
```

### Frontend Environment Variables (`frontend/.env`)

```bash
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Optional
WDS_SOCKET_PORT=3000
```

### Desktop App Configuration (`desktop-app/.env`)

```bash
# StreamHost API URL
STREAMHOST_API_URL=http://localhost:8001
```

## 📖 Usage Guide

### First Time Login

1. Navigate to `http://localhost:3000` (or your configured URL)
2. Login with default credentials:
   - **Username:** `StreamHost`
   - **Password:** `password1234!@#`
3. You'll be prompted to change your password (security requirement)
4. Set a new secure password and access the dashboard

### Uploading Videos

1. Click **"Upload"** in the sidebar
2. Drag & drop a video file or click to browse
3. Enter video details:
   - Title (required)
   - Description (optional)
   - Folder (optional - organize your videos)
4. Click **"Upload Video"**
5. Processing begins automatically (status visible in Video Library)

### Managing Folders

1. Click **"Folders"** in the sidebar
2. Click **"Create Folder"** button
3. Enter folder name and save
4. Use folders when uploading or editing videos

### Video Embedding

1. Go to **Video Library**
2. Click **"Embed"** on any processed video
3. Configure embed settings:
   - **Allowed Domains** - Restrict playback to specific domains
   - **Player Color** - Customize the player accent color
   - **Show Controls** - Toggle video controls
   - **Autoplay** - Auto-play on load
   - **Loop** - Repeat video continuously
4. Click **"Save & Get Embed Code"**
5. Copy the generated HTML code
6. Paste into your website

### Example Embed Code

```html
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
  <video id="video-abc123" 
         style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
         controls>
    <source src="https://your-domain.com/api/stream/hls/abc123/playlist.m3u8" type="application/x-mpegURL">
  </video>
</div>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
  var video = document.getElementById('video-abc123');
  if (Hls.isSupported()) {
    var hls = new Hls();
    hls.loadSource('https://your-domain.com/api/stream/hls/abc123/playlist.m3u8');
    hls.attachMedia(video);
  }
</script>
```

## 🔌 API Documentation

### Authentication

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "StreamHost",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "must_change_password": false
}
```

#### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer {token}
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

### Videos

#### Upload Video
```http
POST /api/videos/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

Form Data:
- file: (video file)
- title: "Video Title"
- description: "Optional description"
- folder_id: "optional-folder-id"
```

#### Get All Videos
```http
GET /api/videos
Authorization: Bearer {token}

Response:
[
  {
    "id": "video-id",
    "title": "Video Title",
    "duration": 120.5,
    "width": 1920,
    "height": 1080,
    "aspect_ratio": "16:9",
    "processing_status": "ready",
    ...
  }
]
```

#### Get Video Details
```http
GET /api/videos/{video_id}
Authorization: Bearer {token}
```

#### Update Video
```http
PATCH /api/videos/{video_id}?title=New Title&description=New Description
Authorization: Bearer {token}
```

#### Delete Video
```http
DELETE /api/videos/{video_id}
Authorization: Bearer {token}
```

### Streaming

#### Get Thumbnail
```http
GET /api/stream/thumbnail/{video_id}
```

#### Get HLS Playlist
```http
GET /api/stream/hls/{video_id}/playlist.m3u8
```

#### Get HLS Segment
```http
GET /api/stream/hls/{video_id}/{segment_name}
```

### Folders

#### Create Folder
```http
POST /api/folders
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Folder Name",
  "parent_id": null
}
```

#### Get All Folders
```http
GET /api/folders
Authorization: Bearer {token}
```

#### Delete Folder
```http
DELETE /api/folders/{folder_id}
Authorization: Bearer {token}
```

### Embed Settings

#### Create Embed Settings
```http
POST /api/embed-settings
Authorization: Bearer {token}
Content-Type: application/json

{
  "video_id": "video-id",
  "allowed_domains": ["example.com", "mysite.com"],
  "player_color": "#3b82f6",
  "show_controls": true,
  "autoplay": false,
  "loop": false
}
```

#### Get Embed Settings
```http
GET /api/embed-settings/{video_id}
Authorization: Bearer {token}
```

#### Update Embed Settings
```http
PATCH /api/embed-settings/{video_id}
Authorization: Bearer {token}
```

#### Get Embed Code
```http
GET /api/embed-code/{video_id}
Authorization: Bearer {token}
```

## 📁 Project Structure

```
streamhost/
├── backend/
│   ├── server.py              # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment configuration
│   └── video_storage/         # Video files storage
│       ├── originals/         # Original uploaded files
│       ├── thumbnails/        # Generated thumbnails
│       └── hls/               # HLS streaming segments
│
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main application component
│   │   ├── App.css            # Global styles
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   └── Dashboard.jsx
│   │   └── components/
│   │       ├── VideoLibrary.jsx
│   │       ├── UploadVideo.jsx
│   │       ├── VideoPlayer.jsx
│   │       ├── FolderManagement.jsx
│   │       ├── VideoSettings.jsx
│   │       ├── EmbedSettingsDialog.jsx
│   │       └── Footer.jsx
│   ├── package.json           # Node dependencies
│   └── .env                   # Frontend configuration
│
├── desktop-app/
│   ├── streamhost_desktop.py  # Desktop application
│   ├── requirements.txt       # Python dependencies
│   ├── StreamHost.bat         # Windows launcher
│   ├── StreamHost_QuickStart.bat
│   ├── Install_Dependencies.bat
│   └── README.md              # Desktop app documentation
│
├── .github/workflows/
│   ├── build-images.yml       # Publishes backend+frontend images to GHCR
│   └── build-desktop.yml      # Builds Windows .exe via PyInstaller
│
├── docker-compose.yml         # Local dev (builds from source)
├── docker-compose.deploy.yml  # Production (uses pre-built GHCR images)
├── .env.example               # Deployment env template
├── README.md                  # This file
├── PRODUCTION-GUIDE.md        # Production deployment guide
└── LICENSE                    # License information
```

## 🎬 Video Processing Pipeline

1. **Upload** - File received and saved to `video_storage/originals/`
2. **Metadata Extraction** - FFmpeg probe extracts video information
3. **Thumbnail Generation** - Frame captured at 10% of video duration
4. **HLS Transcoding** - Video converted to HLS format with segments
5. **Status Update** - Video marked as "ready" and available for streaming

## 🔒 Security Considerations

### Production Deployment

1. **Change Default Credentials** - Always change the default admin password
2. **Secure JWT Secret** - Use a strong, random JWT_SECRET
3. **HTTPS Only** - Deploy behind HTTPS with valid SSL certificates
4. **CORS Configuration** - Restrict CORS_ORIGINS to your specific domain
5. **Domain Restrictions** - Use embed domain restrictions for public videos
6. **Regular Updates** - Keep dependencies up to date
7. **File Size Limits** - Configure nginx/server file upload limits
8. **Rate Limiting** - Implement rate limiting on API endpoints

### Recommended Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    client_max_body_size 60G;

    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_request_buffering off;
        proxy_http_version 1.1;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 Troubleshooting

### Video Processing Fails

**Issue:** Videos stuck in "processing" status

**Solutions:**
- Check FFmpeg is installed: `ffmpeg -version`
- Check backend logs: `tail -f /var/log/supervisor/backend.log`
- Verify video format is valid
- Ensure sufficient disk space

### Login Issues

**Issue:** Cannot login with credentials

**Solutions:**
- Verify MongoDB is running: `systemctl status mongodb`
- Check admin user exists in database
- Default credentials: `StreamHost` / `password1234!@#`
- Clear browser cache and cookies

### Streaming Not Working

**Issue:** Videos won't play in browser

**Solutions:**
- Verify video status is "ready"
- Check HLS files exist in `video_storage/hls/`
- Test HLS URL directly in browser
- Check browser console for errors

### Desktop App Issues

**Issue:** Desktop app won't start

**Solutions:**
- Ensure Python 3.8+ is installed
- Check "Add Python to PATH" was selected during install
- Run `Install_Dependencies.bat` first
- Check the API URL in `.env` file

## 📊 System Requirements

### Minimum
- 2 CPU cores
- 2GB RAM
- 10GB storage
- 10 Mbps network

### Recommended
- 4+ CPU cores
- 4GB+ RAM
- 100GB+ SSD storage
- 100 Mbps network

### For Large-Scale Production
- 8+ CPU cores
- 16GB+ RAM
- 1TB+ SSD storage
- Dedicated video processing server
- Load balancer
- CDN integration

## 📝 Version History

- **2025.12.17** - Current version
  - Rebranded from VidStream to StreamHost
  - New dark theme with colored buttons
  - Added Desktop Application
  - Added Player Customization settings
  - Large file upload support (56GB)
  - Copyright and version footer

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FFmpeg** - The backbone of video processing
- **Shadcn/UI** - Beautiful React components
- **HLS.js** - Seamless video streaming
- **FastAPI** - Modern Python web framework
- **ttkbootstrap** - Modern Tkinter themes

---

**StreamHost Ver: 2025.12.17**

**Copyright 2026 StreamHost**

⭐ Star this repo if you find it useful!
