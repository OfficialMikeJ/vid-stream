# StreamHost Connector - Quick Start Guide

Get your StreamHost videos on WordPress in 5 minutes!

## Step 1: Install (2 minutes)

### Upload Plugin
1. Download `streamhost-connector.zip`
2. WordPress Admin → **Plugins** → **Add New**
3. Click **Upload Plugin**
4. Choose zip file → **Install Now** → **Activate**

### Verify
✅ See "StreamHost" in WordPress admin sidebar

## Step 2: Configure (1 minute)

### Enter Settings
1. Go to **StreamHost** → **Settings**
2. Fill in:
   ```
   API URL: https://your-streamhost-domain.com
   Username: admin
   Password: your-password
   ```
3. Check ☑️ **Auto Sync**
4. Click **Save Settings**

### Test Connection
1. Scroll down
2. Click **Test Connection**
3. Should show: ✅ "Connection successful"

## Step 3: Sync Videos (2 minutes)

### Import Videos
1. Go to **StreamHost** → **Sync Videos**
2. Click **Sync All Videos Now**
3. Wait for progress bar to complete

### Check Results
- Go to **Videos** → **All Videos**
- See your synced videos with thumbnails!

## Done! 🎉

Your videos are now on WordPress!

### What's Synced?
✅ Video title & description
✅ Thumbnail images
✅ Duration & resolution
✅ HLS streaming URL
✅ All metadata

### View Videos
- **Archive:** `yoursite.com/videos/`
- **Single:** `yoursite.com/video/video-title/`

### Auto Updates
Videos sync automatically based on your interval (hourly/daily).

## Need Help?

📖 **Full Guide:** See [INSTALLATION.md](INSTALLATION.md)
🐛 **Issues:** See [README.md](README.md#troubleshooting)
💬 **Support:** support@your-domain.com

---

**Pro Tips:**

💡 Enable auto-sync to keep videos updated automatically
💡 Check **StreamHost** → **Sync Log** to see sync history
💡 Use **Re-sync** button in video edit page to update individual videos
💡 Videos must be in "ready" status in StreamHost to sync
