# VidStream - Video Hosting Service

A powerful, self-hosted video hosting platform with FFmpeg processing, HLS streaming, and customizable embed options. Upload, process, organize, and stream videos with ease.

![VidStream Dashboard](https://img.shields.io/badge/Status-Production%20Ready-success)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-19.0-61dafb)

## 🎯 Features

### Video Management
- **Multi-format Support** - Upload any FFmpeg-compatible video format (MP4, MOV, AVI, MKV, WebM, FLV, WMV, MPEG, etc.)
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
- **Modern Dark Theme** - Beautiful glassmorphism design with gradient accents
- **Responsive Layout** - Works seamlessly on desktop and mobile devices
- **Drag & Drop Upload** - Intuitive file upload with progress tracking
- **Video Grid Library** - Organized video display with thumbnails
- **Inline Video Player** - Play videos directly in the dashboard

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
git clone https://github.com/yourusername/vidstream.git
cd vidstream
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

#### Production Deployment

**Essential Files for Production:**

```
📦 VidStream Production Files
├── backend/
│   ├── server.py              ✅ Core backend application
│   ├── requirements.txt       ✅ Python dependencies
│   ├── .env                   ✅ Environment variables (configure for production)
│   └── video_storage/         ✅ Created automatically (stores uploads)
│
├── frontend/
│   ├── package.json           ✅ Node dependencies
│   ├── src/                   ✅ React application source
│   ├── public/                ✅ Static assets
│   └── .env                   ✅ Frontend config (set REACT_APP_BACKEND_URL)
│
└── .gitignore                 ✅ Exclude video_storage, node_modules, .env
```

**Production Setup (Supervisor - Recommended):**

Create `/etc/supervisor/conf.d/vidstream.conf`:

```ini
[program:vidstream-backend]
command=/path/to/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
directory=/path/to/vidstream/backend
autostart=true
autorestart=true
user=www-data
environment=PATH="/path/to/venv/bin"
stdout_logfile=/var/log/vidstream/backend.log
stderr_logfile=/var/log/vidstream/backend-error.log

[program:vidstream-frontend]
command=/usr/bin/yarn start
directory=/path/to/vidstream/frontend
autostart=true
autorestart=true
user=www-data
environment=NODE_ENV="production"
stdout_logfile=/var/log/vidstream/frontend.log
stderr_logfile=/var/log/vidstream/frontend-error.log
```

**Start Services:**
```bash
# Create log directory
sudo mkdir -p /var/log/vidstream

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start services
sudo supervisorctl start vidstream-backend
sudo supervisorctl start vidstream-frontend

# Check status
sudo supervisorctl status
```

## ⚙️ Configuration

### Backend Environment Variables (`backend/.env`)

```bash
# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="vidstream_db"

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

## 📖 Usage Guide

### First Time Login

1. Navigate to `http://localhost:3000` (or your configured URL)
2. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `admin123`
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
  "username": "admin",
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
vidstream/
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
│   │       └── EmbedSettingsDialog.jsx
│   ├── package.json           # Node dependencies
│   └── .env                   # Frontend configuration
│
├── tests/                     # Test files
├── README.md                  # This file
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

    client_max_body_size 2G;

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
- Reset admin password using backend script
- Clear browser cache and cookies

### Streaming Not Working

**Issue:** Videos won't play in browser

**Solutions:**
- Verify video status is "ready"
- Check HLS files exist in `video_storage/hls/`
- Test HLS URL directly in browser
- Check browser console for errors

### High Server Load

**Issue:** Server slow during video processing

**Solutions:**
- Process videos one at a time
- Increase server resources (CPU/RAM)
- Optimize FFmpeg settings
- Use queue system for batch processing

## 🚦 Performance Optimization

### Video Processing
- Use hardware acceleration if available: `-hwaccel cuda`
- Adjust HLS segment size (default: 10 seconds)
- Lower transcoding quality for faster processing
- Implement background job queue (Celery/Redis)

### Database
- Create indexes on frequently queried fields
- Use MongoDB aggregation for complex queries
- Implement caching layer (Redis)
- Regular database maintenance

### Frontend
- Enable production build for React
- Implement lazy loading for video thumbnails
- Use CDN for static assets
- Enable gzip compression

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

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript
- Write meaningful commit messages
- Add tests for new features
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FFmpeg** - The backbone of video processing
- **Shadcn/UI** - Beautiful React components
- **HLS.js** - Seamless video streaming
- **FastAPI** - Modern Python web framework

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@your-domain.com
- Documentation: https://docs.your-domain.com

## 🗺️ Roadmap

### Upcoming Features
- [ ] Multiple quality transcoding (480p, 720p, 1080p)
- [ ] Video analytics and watch statistics
- [ ] Subtitle support (.srt, .vtt)
- [ ] Video trimming and editing
- [ ] Batch upload support
- [ ] User roles and permissions
- [ ] API webhooks for processing events
- [ ] Cloud storage integration (S3, Google Cloud)
- [ ] Video compression optimization
- [ ] Mobile app (React Native)

---

**Made with ❤️ using FastAPI, React, and FFmpeg**

⭐ Star this repo if you find it useful!
