# StreamHost Desktop Application

A modern Python desktop client for the StreamHost video hosting service.

## Features

- **Login & Authentication** - Secure login with password change support
- **Video Library** - Browse, play, and manage uploaded videos
- **Video Upload** - Upload videos with progress tracking (supports up to 56GB)
- **Folder Management** - Create and organize videos into folders
- **Embed Codes** - Get embed codes for sharing videos
- **Settings** - View connection status and app information

## Requirements

- Python 3.8 or higher
- tkinter (usually included with Python)
- ttkbootstrap (for modern dark theme)

## Installation

1. **Install dependencies:**
   ```bash
   cd desktop-app
   pip install -r requirements.txt
   ```

2. **Configure API URL (Optional):**
   
   Create a `.env` file in the desktop-app folder:
   ```
   STREAMHOST_API_URL=http://your-server-url:8001
   ```
   
   If not configured, it defaults to `http://localhost:8001`

## Running the Application

```bash
python streamhost_desktop.py
```

## Default Credentials

- **Username:** StreamHost
- **Password:** password1234!@#

Note: You will be prompted to change your password on first login.

## Screenshots

### Login Screen
- Dark theme with StreamHost branding
- Username and password fields
- Footer with copyright and version

### Main Dashboard
- Sidebar navigation (Video Library, Upload, Folders, Settings)
- Video cards with metadata (duration, size, status)
- Play, Embed, and Delete actions

### Upload Screen
- File browser
- Title and description fields
- Folder selection
- Progress indicator

### Folders Screen
- Create and delete folders
- Organize videos

## Version

**StreamHost Ver: 2025.12.17**

## Copyright

Copyright 2026 StreamHost
