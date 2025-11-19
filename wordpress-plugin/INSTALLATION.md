# VidStream Connector - Installation Guide

Complete guide to integrate VidStream with your StreamLab WordPress theme.

## Prerequisites

Before installing, ensure you have:

✅ WordPress 5.8 or higher
✅ PHP 7.4 or higher  
✅ StreamLab theme installed and activated
✅ MAS Videos plugin installed and activated
✅ VidStream hosting service running

## Step 1: Install Required Plugins

### MAS Videos Plugin

The StreamLab theme requires the MAS Videos plugin for video functionality.

1. Download MAS Videos from the plugin folder included with your theme
2. In WordPress admin, go to **Plugins > Add New**
3. Click **Upload Plugin** and select the MAS Videos zip file
4. Click **Install Now** and then **Activate**

### StreamLab Core Plugin

1. Navigate to the plugin folder in your theme package
2. Find `streamlab-core.zip`
3. In WordPress admin, go to **Plugins > Add New**
4. Click **Upload Plugin** and select the StreamLab Core zip file
5. Click **Install Now** and then **Activate**

## Step 2: Install VidStream Connector

### Upload Plugin

1. Download the `vidstream-connector.zip` file
2. In WordPress admin, go to **Plugins > Add New**
3. Click **Upload Plugin**
4. Choose the `vidstream-connector.zip` file
5. Click **Install Now**
6. Click **Activate Plugin**

### Verify Installation

After activation, you should see:
- **VidStream** menu item in WordPress admin sidebar
- Green success message confirming activation

## Step 3: Configure VidStream Connector

### Access Settings

1. In WordPress admin, go to **VidStream > Settings**
2. You'll see a configuration form

### Enter Your VidStream Credentials

**VidStream API URL:**
```
https://your-vidstream-domain.com
```
⚠️ **Important:** Enter the URL WITHOUT `/api` at the end

**Username:**
```
admin
```
(or your VidStream admin username)

**Password:**
```
your-password
```
(your VidStream admin password)

**Auto Sync:**
- ☑️ Check this to enable automatic video syncing
- Videos will sync based on your chosen interval

**Sync Interval:**
- Choose: Hourly, Twice Daily, or Daily
- Recommended: **Hourly** for active video libraries

### Save Settings

Click **Save Settings** button

## Step 4: Test Connection

After saving settings:

1. Scroll down to **Test Connection** section
2. Click **Test Connection** button
3. You should see:
   - ✅ **Connection successful**
   - Number of videos found in your VidStream library

**If connection fails:**
- Verify your API URL is correct (no /api at end)
- Check username and password
- Ensure your VidStream service is running
- Check that VidStream is accessible from your WordPress server

## Step 5: Sync Your Videos

### Manual Sync

1. Go to **VidStream > Sync Videos**
2. Click **Sync All Videos Now** button
3. Watch the progress bar as videos are imported
4. You'll see a summary:
   - Total videos
   - Successfully synced
   - Failed
   - Skipped (not ready)

### View Synced Videos

1. Go to **Videos > All Videos** in WordPress admin
2. You'll see all synced videos with:
   - Thumbnails
   - VidStream status
   - Duration
   - Title and description

### Video Information

Click **Edit** on any video to see:
- Video ID from VidStream
- Processing status
- Resolution and aspect ratio
- File size and format
- HLS stream URL
- Last sync time
- **Re-sync** button to update from VidStream

## Step 6: Display Videos on Frontend

### Using StreamLab Theme

Your synced videos will automatically appear in:

**Video Archive Page:**
```
https://your-site.com/videos/
```

**Single Video Page:**
```
https://your-site.com/video/video-title/
```

### Video Player

Videos will play using:
- HLS.js for adaptive streaming
- Custom StreamLab video player
- Responsive design
- Mobile-friendly controls

## Step 7: Configure Auto Sync (Optional)

### Enable Auto Sync

If you haven't already:
1. Go to **VidStream > Settings**
2. Check **Auto Sync** checkbox
3. Select sync interval
4. Click **Save Settings**

### How Auto Sync Works

- WordPress will check VidStream for new/updated videos
- Runs automatically based on your interval
- Only syncs videos with status "ready"
- Creates new posts for new videos
- Updates existing posts for changed videos

### Monitor Sync Activity

Go to **VidStream > Sync Log** to see:
- All sync operations
- Success/failure status
- Error messages
- Timestamps

## Advanced Configuration

### Custom Video Display

The plugin integrates with MAS Videos, so you can use:

**Shortcodes:**
```
[mas_videos limit="12" columns="4"]
```

**Widgets:**
- Recent Videos
- Popular Videos
- Video Categories

**Elementor Widgets:**
- StreamLab includes custom Elementor widgets for videos

### Video Metadata

Synced from VidStream:
- ✅ Title
- ✅ Description
- ✅ Thumbnail
- ✅ Duration
- ✅ Resolution (width x height)
- ✅ Aspect ratio
- ✅ File size
- ✅ Format
- ✅ HLS stream URL

### Folder Support

If you organize videos in folders on VidStream:
- Plugin syncs folder information
- Can be mapped to WordPress categories/tags (future feature)

## Troubleshooting

### Connection Failed

**Problem:** "Authentication failed" or "Not authenticated"

**Solutions:**
1. Verify API URL format: `https://domain.com` (no /api)
2. Check username and password are correct
3. Ensure VidStream admin user is active
4. Test VidStream login directly in browser

### Videos Not Syncing

**Problem:** Sync completes but no videos appear

**Solutions:**
1. Check **VidStream > Sync Log** for errors
2. Verify videos are in "ready" status in VidStream
3. Check WordPress user permissions
4. Ensure MAS Videos plugin is active

### Thumbnails Not Showing

**Problem:** Videos sync but thumbnails are missing

**Solutions:**
1. Check WordPress uploads directory is writable
2. Verify thumbnail exists in VidStream
3. Check PHP memory limit (recommended: 256M)
4. Try re-syncing specific video

### Slow Sync Performance

**Problem:** Syncing takes very long time

**Solutions:**
1. Increase PHP max execution time
2. Sync smaller batches manually
3. Use scheduled auto-sync instead of manual
4. Check VidStream server response time

### Videos Won't Play

**Problem:** Video player shows error or doesn't load

**Solutions:**
1. Verify HLS stream URL is accessible
2. Check browser console for errors
3. Ensure HLS.js is loading (included in StreamLab)
4. Test stream URL directly in browser

## Support

### Plugin Issues

For VidStream Connector plugin issues:
- Check **VidStream > Sync Log** for error details
- GitHub: https://github.com/yourusername/vidstream-connector

### Theme Issues

For StreamLab theme issues:
- Theme documentation included in theme package
- Support: https://gentechtreedesign.com

### VidStream Issues

For VidStream service issues:
- Check VidStream backend logs
- Verify FFmpeg is working
- Ensure MongoDB is running

## Best Practices

### Regular Syncing

- Enable auto-sync for active video libraries
- Use hourly interval if adding videos frequently
- Run manual sync after batch uploads

### Video Management

- Edit videos in VidStream, not WordPress
- Use Re-sync button to update WordPress after changes
- Keep VidStream as single source of truth

### Performance

- Optimize WordPress database regularly
- Use caching plugin (WP Super Cache, W3 Total Cache)
- Enable CDN for static assets
- Consider video CDN for high traffic

### Backup

- Backup WordPress database regularly
- VidStream videos are stored on VidStream server
- WordPress only stores metadata and references

## Next Steps

After successful installation:

1. ✅ Customize video display using StreamLab theme options
2. ✅ Add videos to navigation menus
3. ✅ Create video categories and tags
4. ✅ Configure SEO settings for video pages
5. ✅ Set up video analytics
6. ✅ Customize video player colors in theme

## Updates

### Checking for Updates

1. Go to **Plugins** in WordPress admin
2. Look for update notifications
3. Click **Update Now** when available

### Auto-Updates

Enable auto-updates:
1. Go to **Plugins**
2. Find VidStream Connector
3. Click **Enable auto-updates**

---

**Congratulations!** 🎉

Your VidStream video hosting service is now integrated with your StreamLab WordPress theme!

Upload videos to VidStream, and they'll automatically appear on your WordPress site.
