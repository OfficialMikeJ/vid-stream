# StreamHost - Clean Production Deployment

## 📦 Minimal File Structure

```
production-server/
├── backend/
│   ├── server.py              # 1 file - FastAPI application
│   ├── requirements.txt       # Dependencies list
│   └── .env                   # 3 lines of config
│
└── frontend/
    ├── src/                   # React app folder
    ├── public/                # Static assets
    ├── package.json           # Dependencies list
    └── .env                   # 1 line of config
```

**That's it!** Just 2 main application files + configs.

---

## 🚀 5-Minute Production Setup

### 1. Install System (Ubuntu/Debian)
```bash
sudo apt install python3.11 python3.11-venv nodejs npm ffmpeg mongodb supervisor nginx
sudo npm install -g yarn
```

### 2. Setup Backend
```bash
# Create virtual env & install
cd /var/www/streamhost/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="streamhost_production"
JWT_SECRET="your-32-char-random-secret"
EOF
```

### 3. Setup Frontend
```bash
cd /var/www/streamhost/frontend
yarn install

# Configure
echo 'REACT_APP_BACKEND_URL=https://your-domain.com' > .env
```

### 4. Configure Supervisor
```bash
# Create /etc/supervisor/conf.d/streamhost.conf
[program:streamhost-backend]
command=/var/www/streamhost/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
directory=/var/www/streamhost/backend
autostart=true
autorestart=true
user=www-data

[program:streamhost-frontend]
command=/usr/bin/yarn start
directory=/var/www/streamhost/frontend
autostart=true
autorestart=true
user=www-data
```

### 5. Configure Nginx
```bash
# Create /etc/nginx/sites-available/streamhost
server {
    listen 443 ssl;
    server_name your-domain.com;
    client_max_body_size 2G;

    # Backend /api
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Frontend /
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### 6. Start Everything
```bash
# Start services
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl start all

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/streamhost /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

**Done!** Visit https://your-domain.com

---

## 🔒 Security Checklist

- [ ] Change default admin password (admin/admin123)
- [ ] Update JWT_SECRET in backend/.env (32+ random chars)
- [ ] Configure CORS_ORIGINS to your domain only
- [ ] Enable MongoDB authentication
- [ ] Set up firewall (UFW):
  ```bash
  sudo ufw allow 22,80,443/tcp
  sudo ufw enable
  ```
- [ ] Configure automatic backups
- [ ] Set correct file permissions (www-data:www-data)
- [ ] Monitor logs in /var/log/streamhost/

---

## 📊 Management Commands

**View Status:**
```bash
sudo supervisorctl status
```

**Restart Services:**
```bash
sudo supervisorctl restart streamhost-backend
sudo supervisorctl restart streamhost-frontend
```

**View Logs:**
```bash
sudo tail -f /var/log/streamhost/backend.log
sudo tail -f /var/log/streamhost/frontend.log
```

**Update Application:**
```bash
# Stop services
sudo supervisorctl stop all

# Replace server.py or frontend files
# ...upload new files...

# Restart
sudo supervisorctl start all
```

---

## 📁 What Gets Created Automatically

```
video_storage/          # Created on first video upload
├── originals/         # Original uploaded files
├── thumbnails/        # Generated thumbnails
└── hls/               # HLS streaming segments
```

MongoDB Collections (auto-created):
- `users` - Admin and user accounts
- `videos` - Video metadata
- `folders` - Organization
- `embed_settings` - Player customization

---

## 🎯 Production URLs

- **Frontend:** https://your-domain.com
- **Backend API:** https://your-domain.com/api/*
- **Video Streams:** https://your-domain.com/api/stream/hls/{video_id}/playlist.m3u8
- **Thumbnails:** https://your-domain.com/api/stream/thumbnail/{video_id}

---

## 💾 Backup Strategy

**Daily MongoDB Backup:**
```bash
# Create backup script
cat > /usr/local/bin/backup-streamhost.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
mongodump --db=streamhost_production --out=/var/backups/streamhost/mongo_$DATE
find /var/backups/streamhost -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-streamhost.sh

# Schedule daily at 2 AM
echo "0 2 * * * /usr/local/bin/backup-streamhost.sh" | sudo crontab -
```

---

## 🆘 Quick Troubleshooting

**Services won't start?**
```bash
sudo supervisorctl tail -f streamhost-backend stderr
```

**Videos won't upload?**
```bash
# Check disk space
df -h

# Check permissions
ls -la /var/www/streamhost/backend/video_storage/

# Check Nginx upload limit
sudo nginx -T | grep client_max_body_size
```

**FFmpeg not working?**
```bash
which ffmpeg
ffmpeg -version
```

---

## ✅ Production Ready

Your deployment includes:
- ✅ Auto-restart on crash (Supervisor)
- ✅ HTTPS with SSL (Let's Encrypt)
- ✅ Reverse proxy (Nginx)
- ✅ Video processing (FFmpeg)
- ✅ Database (MongoDB)
- ✅ Logging (Supervisor + Nginx)
- ✅ Large file uploads (2GB max)
- ✅ HLS adaptive streaming

**Default Credentials:**
- Username: `admin`
- Password: `admin123` ⚠️ Change immediately!

---

## 📚 Full Documentation

- **Complete Guide:** [PRODUCTION-GUIDE.md](PRODUCTION-GUIDE.md)
- **Main README:** [README.md](README.md)
- **WordPress Plugin:** [wordpress-plugin/README.md](wordpress-plugin/README.md)
- **Invite System:** [wordpress-plugin-invites/README.md](wordpress-plugin-invites/README.md)

---

**Deployment Simplified.** 🚀

*Only essential files. Maximum performance. Production-ready security.*
