# StreamHost Docker Deployment Guide

Complete guide to deploy StreamHost using Docker on Ubuntu 20.04+.

## 📦 Quick Start

### Option 1: Automated Setup (Ubuntu 20.04+)

```bash
# Clone the repository
git clone https://github.com/yourusername/streamhost.git
cd streamhost

# Run the setup script
sudo chmod +x docker/ubuntu-setup.sh
sudo ./docker/ubuntu-setup.sh

# Log out and log back in for docker group changes
exit

# Start StreamHost
cp .env.docker .env
docker compose up -d
```

### Option 2: Manual Setup

If Docker is already installed:

```bash
# Clone and navigate
git clone https://github.com/yourusername/streamhost.git
cd streamhost

# Copy and configure environment
cp .env.docker .env
nano .env  # Edit as needed

# Build and start
docker compose up -d --build
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Security - CHANGE IN PRODUCTION!
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# CORS - Specify your domain in production
CORS_ORIGINS=https://yourdomain.com

# Backend URL (external URL)
BACKEND_URL=http://localhost:8001

# Frontend Backend URL
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 📂 File Structure

```
streamhost/
├── docker-compose.yml          # Development compose file
├── .env.docker                 # Environment template
├── .env                        # Your configuration (create this)
│
├── backend/
│   ├── Dockerfile              # Backend container
│   ├── .dockerignore
│   └── server.py
│
├── frontend/
│   ├── Dockerfile              # Frontend container
│   ├── .dockerignore
│   └── src/
│
└── docker/
    ├── README.md               # This file
    ├── ubuntu-setup.sh         # Ubuntu setup script
    ├── docker-compose.prod.yml # Production compose file
    └── nginx/
        └── nginx.conf          # Nginx configuration
```

## 🚀 Docker Commands

### Basic Operations

```bash
# Start all services
docker compose up -d

# Start with build
docker compose up -d --build

# Stop all services
docker compose down

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mongodb
```

### Maintenance

```bash
# Restart a service
docker compose restart backend

# Rebuild a specific service
docker compose up -d --build backend

# Remove all containers and volumes (CAUTION: deletes data)
docker compose down -v

# Check service status
docker compose ps

# Execute command in container
docker compose exec backend bash
docker compose exec mongodb mongosh
```

## 🌐 Accessing the Application

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Web interface |
| Backend API | http://localhost:8001 | REST API |
| Health Check | http://localhost:8001/api/health | API health status |

### Default Credentials

- **Username:** `StreamHost`
- **Password:** `password1234!@#`
- First login requires password change

## 🏭 Production Deployment

### Using Production Compose File

```bash
# Copy production compose file
cp docker/docker-compose.prod.yml docker-compose.yml

# Configure environment
cp .env.docker .env
nano .env  # Set production values

# Add SSL certificates
mkdir -p docker/nginx/ssl
cp /path/to/fullchain.pem docker/nginx/ssl/
cp /path/to/privkey.pem docker/nginx/ssl/

# Start services
docker compose up -d --build
```

### Production Environment Variables

```bash
# REQUIRED - Change these!
JWT_SECRET=generate-a-64-character-random-string-here

# CORS - Your domain only
CORS_ORIGINS=https://yourdomain.com

# URLs
BACKEND_URL=https://yourdomain.com
REACT_APP_BACKEND_URL=https://yourdomain.com

# MongoDB authentication (optional but recommended)
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=secure-password-here
```

### SSL/TLS Setup

1. **Using Let's Encrypt:**
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/
```

2. **Update nginx.conf** - Uncomment the HTTPS server block

### Resource Requirements

| Service | Min Memory | Recommended |
|---------|------------|-------------|
| MongoDB | 512MB | 2GB |
| Backend | 1GB | 4GB |
| Frontend | 128MB | 512MB |
| Nginx | 64MB | 128MB |

## 💾 Data Persistence

### Volumes

| Volume | Purpose |
|--------|---------|
| `mongodb_data` | Database files |
| `mongodb_config` | MongoDB configuration |
| `video_storage` | Uploaded and processed videos |

### Backup

```bash
# Backup MongoDB
docker compose exec mongodb mongodump --out /data/backup
docker cp streamhost-mongodb:/data/backup ./mongodb-backup

# Backup video storage
docker run --rm -v streamhost_video_storage:/data -v $(pwd):/backup \
    alpine tar cvf /backup/video-backup.tar /data
```

### Restore

```bash
# Restore MongoDB
docker cp ./mongodb-backup streamhost-mongodb:/data/backup
docker compose exec mongodb mongorestore /data/backup

# Restore video storage
docker run --rm -v streamhost_video_storage:/data -v $(pwd):/backup \
    alpine tar xvf /backup/video-backup.tar -C /
```

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - MongoDB not ready: Wait for health check
# - Port in use: Change ports in docker-compose.yml
# - Permission issues: Check volume permissions
```

### MongoDB Connection Failed

```bash
# Check MongoDB is running
docker compose ps mongodb

# Check MongoDB logs
docker compose logs mongodb

# Test connection
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Video Processing Fails

```bash
# Check FFmpeg is installed in container
docker compose exec backend ffmpeg -version

# Check disk space
docker system df

# Check video storage permissions
docker compose exec backend ls -la /app/video_storage
```

### Frontend Not Loading

```bash
# Check frontend logs
docker compose logs frontend

# Verify build completed
docker compose exec frontend ls -la /app/build

# Check REACT_APP_BACKEND_URL
docker compose exec frontend env | grep REACT
```

## 🔄 Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose up -d --build

# Or rebuild specific service
docker compose up -d --build backend
```

## 📊 Monitoring

### Health Checks

```bash
# Check all service health
docker compose ps

# Check API health
curl http://localhost:8001/api/health

# Check MongoDB health
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Resource Usage

```bash
# View container stats
docker stats

# View disk usage
docker system df
```

---

**StreamHost Ver: 2025.12.17**

**Copyright 2026 StreamHost**
