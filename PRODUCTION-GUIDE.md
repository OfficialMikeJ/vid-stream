# VidStream - Production Deployment Guide

Complete guide to deploy VidStream in production with minimal files and maximum security.

## 📦 What You Need

### Essential Files Only

```
vidstream/
├── backend/
│   ├── server.py                    # FastAPI application (1 file)
│   ├── requirements.txt             # Python dependencies list
│   └── .env                         # Environment variables (create this)
│
└── frontend/
    ├── src/                         # React application folder
    ├── public/                      # Static assets folder
    ├── package.json                 # Node dependencies list
    └── .env                         # Frontend config (create this)
```

**That's it!** No complex setup, just 2 main files + configs.

---

## 🚀 Quick Production Setup

### Step 1: System Requirements

**Install on Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y nodejs npm ffmpeg mongodb
sudo npm install -g yarn

# Install Supervisor
sudo apt install -y supervisor

# Install Nginx
sudo apt install -y nginx
```

### Step 2: Project Setup

```bash
# Create project directory
sudo mkdir -p /var/www/vidstream
cd /var/www/vidstream

# Upload your files (via SCP, Git, or FTP)
# Only upload: server.py, requirements.txt, src/, public/, package.json

# Create directory structure
mkdir -p backend frontend
```

### Step 3: Backend Setup

```bash
cd /var/www/vidstream/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
MONGO_URL="mongodb://localhost:27017"
DB_NAME="vidstream_production"
CORS_ORIGINS="https://your-domain.com"
JWT_SECRET="change-this-to-random-secure-key-min-32-chars"
BACKEND_URL="https://your-domain.com"
EOF

# Test backend
uvicorn server:app --host 0.0.0.0 --port 8001
# Press Ctrl+C after verifying it starts
```

### Step 4: Frontend Setup

```bash
cd /var/www/vidstream/frontend

# Install dependencies
yarn install

# Create .env file
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://your-domain.com
EOF

# Build for production
yarn build

# Test frontend (optional)
yarn start
# Press Ctrl+C
```

### Step 5: Supervisor Configuration

Create `/etc/supervisor/conf.d/vidstream.conf`:

```bash
sudo nano /etc/supervisor/conf.d/vidstream.conf
```

Paste this configuration:

```ini
[program:vidstream-backend]
command=/var/www/vidstream/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
directory=/var/www/vidstream/backend
autostart=true
autorestart=true
user=www-data
environment=PATH="/var/www/vidstream/backend/venv/bin"
stdout_logfile=/var/log/vidstream/backend.log
stderr_logfile=/var/log/vidstream/backend-error.log
redirect_stderr=true

[program:vidstream-frontend]
command=/usr/bin/yarn start
directory=/var/www/vidstream/frontend
autostart=true
autorestart=true
user=www-data
environment=NODE_ENV="production",PATH="/usr/bin:/usr/local/bin"
stdout_logfile=/var/log/vidstream/frontend.log
stderr_logfile=/var/log/vidstream/frontend-error.log
redirect_stderr=true
```

**Start services:**

```bash
# Create log directory
sudo mkdir -p /var/log/vidstream
sudo chown www-data:www-data /var/log/vidstream

# Set permissions
sudo chown -R www-data:www-data /var/www/vidstream

# Reload and start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start vidstream-backend
sudo supervisorctl start vidstream-frontend

# Check status
sudo supervisorctl status
```

### Step 6: Nginx Configuration

Create `/etc/nginx/sites-available/vidstream`:

```bash
sudo nano /etc/nginx/sites-available/vidstream
```

Paste this configuration:

```nginx
# VidStream Production Configuration
upstream backend {
    server 127.0.0.1:8001;
}

upstream frontend {
    server 127.0.0.1:3000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;

    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Large file uploads for videos
    client_max_body_size 2G;
    client_body_buffer_size 128k;
    client_body_timeout 300s;

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for large uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffering off for streaming
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

**Enable site:**

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/vidstream /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 7: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

### Step 8: Verify Deployment

```bash
# Check services
sudo supervisorctl status

# Check logs
sudo tail -f /var/log/vidstream/backend.log
sudo tail -f /var/log/vidstream/frontend.log

# Check Nginx
sudo systemctl status nginx

# Check MongoDB
sudo systemctl status mongodb
```

**Test in browser:**
1. Visit https://your-domain.com
2. Login with admin/admin123
3. Change password
4. Upload a test video
5. Verify processing and playback

---

## 🔒 Production Security Checklist

### Backend Security
- [ ] Change default admin password immediately
- [ ] Update JWT_SECRET to random 32+ character string
- [ ] Set strong MongoDB password
- [ ] Configure CORS_ORIGINS to your domain only
- [ ] Disable debug mode
- [ ] Set up firewall (UFW):
  ```bash
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```

### File Permissions
```bash
# Backend
sudo chown -R www-data:www-data /var/www/vidstream/backend
sudo chmod -R 750 /var/www/vidstream/backend
sudo chmod 640 /var/www/vidstream/backend/.env

# Frontend
sudo chown -R www-data:www-data /var/www/vidstream/frontend
sudo chmod -R 750 /var/www/vidstream/frontend

# Video storage
sudo mkdir -p /var/www/vidstream/backend/video_storage
sudo chown -R www-data:www-data /var/www/vidstream/backend/video_storage
sudo chmod -R 770 /var/www/vidstream/backend/video_storage
```

### MongoDB Security
```bash
# Enable authentication
sudo nano /etc/mongodb.conf

# Add:
security:
  authorization: enabled

# Create admin user
mongosh
use admin
db.createUser({
  user: "vidstream_admin",
  pwd: "strong-password-here",
  roles: [{role: "readWrite", db: "vidstream_production"}]
})
exit

# Update .env with MongoDB auth
MONGO_URL="mongodb://vidstream_admin:password@localhost:27017/vidstream_production"
```

---

## 📊 Monitoring & Maintenance

### View Logs
```bash
# Real-time backend logs
sudo tail -f /var/log/vidstream/backend.log

# Real-time frontend logs
sudo tail -f /var/log/vidstream/frontend.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart backend only
sudo supervisorctl restart vidstream-backend

# Restart frontend only
sudo supervisorctl restart vidstream-frontend

# Restart all
sudo supervisorctl restart all

# Restart Nginx
sudo systemctl restart nginx
```

### Database Backup
```bash
# Create backup script
sudo nano /usr/local/bin/backup-vidstream.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/vidstream"
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db=vidstream_production --out=$BACKUP_DIR/mongo_$DATE

# Backup video storage (optional - can be large)
# tar -czf $BACKUP_DIR/videos_$DATE.tar.gz /var/www/vidstream/backend/video_storage

# Keep only last 7 days
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and schedule:
```bash
sudo chmod +x /usr/local/bin/backup-vidstream.sh
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-vidstream.sh >> /var/log/vidstream-backup.log 2>&1
```

### Update Application
```bash
# Stop services
sudo supervisorctl stop all

# Update code
cd /var/www/vidstream
# Upload new server.py or frontend files

# Update backend dependencies if needed
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Update frontend dependencies if needed
cd ../frontend
yarn install

# Start services
sudo supervisorctl start all

# Verify
sudo supervisorctl status
```

---

## 🎯 Performance Optimization

### Backend Optimization
```bash
# Increase worker processes in supervisor config
# Edit /etc/supervisor/conf.d/vidstream.conf
command=...uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Restart
sudo supervisorctl restart vidstream-backend
```

### Nginx Caching
Add to Nginx config:
```nginx
# Cache static assets
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Cache video segments
location ~* \.(ts|m3u8)$ {
    expires 1h;
    add_header Cache-Control "public";
}
```

### MongoDB Optimization
```bash
# Enable MongoDB indexes
mongosh vidstream_production

# Create indexes
db.videos.createIndex({processing_status: 1})
db.videos.createIndex({created_at: -1})
db.folders.createIndex({parent_id: 1})
```

---

## 🆘 Troubleshooting

### Services Won't Start
```bash
# Check supervisor logs
sudo supervisorctl tail -f vidstream-backend stderr
sudo supervisorctl tail -f vidstream-frontend stderr

# Check permissions
ls -la /var/www/vidstream/backend/
ls -la /var/www/vidstream/frontend/

# Check environment
sudo -u www-data bash
cd /var/www/vidstream/backend
source venv/bin/activate
python server.py
```

### Videos Won't Upload
```bash
# Check disk space
df -h

# Check video_storage permissions
ls -la /var/www/vidstream/backend/video_storage/

# Check Nginx upload limit
sudo nginx -T | grep client_max_body_size

# Check backend logs for errors
sudo tail -f /var/log/vidstream/backend.log
```

### FFmpeg Errors
```bash
# Verify FFmpeg installation
which ffmpeg
ffmpeg -version

# Check FFmpeg can write
sudo -u www-data ffmpeg -i input.mp4 -t 1 test.mp4

# Check video_storage write permissions
sudo -u www-data touch /var/www/vidstream/backend/video_storage/test.txt
```

---

## 📞 Production Support

**System Status:**
```bash
# Quick health check
sudo supervisorctl status && \
sudo systemctl status nginx && \
sudo systemctl status mongodb && \
df -h | grep -E '^/dev' && \
free -h
```

**Resource Usage:**
```bash
# Check CPU and memory
htop

# Check disk I/O
sudo iotop

# Check network
sudo iftop
```

---

## ✅ Production Deployment Complete

Your VidStream platform is now:
- ✅ Running with Supervisor
- ✅ Secured with SSL
- ✅ Protected by Nginx
- ✅ Backed up daily
- ✅ Monitored and logged
- ✅ Optimized for performance

**Default Access:**
- URL: https://your-domain.com
- Username: admin
- Password: admin123 (change immediately!)

**Files Created:**
- Backend: `server.py` + `requirements.txt` + `.env`
- Frontend: `src/` + `public/` + `package.json` + `.env`
- Config: Supervisor + Nginx
- Logs: `/var/log/vidstream/`

**Next Steps:**
1. Change default password
2. Upload test video
3. Configure custom branding
4. Set up monitoring alerts
5. Share invite codes!

---

*Production deployment made simple.* 🚀
