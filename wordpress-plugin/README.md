# StreamHost Connector - WordPress Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![WordPress](https://img.shields.io/badge/WordPress-5.8%2B-blue)
![PHP](https://img.shields.io/badge/PHP-7.4%2B-purple)
![License](https://img.shields.io/badge/license-GPL--2.0-green)

Seamlessly integrate your StreamHost video hosting platform with WordPress. Automatically sync videos, thumbnails, and metadata with full MAS Videos and StreamLab theme support.

## 🎯 Features

### Core Functionality
- **Automatic Video Sync** - Schedule hourly, twice daily, or daily syncing
- **Manual Sync** - Sync all videos or individual videos on demand
- **Smart Updates** - Only syncs "ready" videos, updates existing posts
- **Thumbnail Management** - Automatically downloads and sets featured images
- **Metadata Sync** - Duration, resolution, aspect ratio, file size, format

### Integration
- **MAS Videos Compatible** - Creates proper video post types
- **StreamLab Theme Ready** - Works perfectly with StreamLab theme
- **HLS Streaming** - Full support for adaptive bitrate streaming
- **Custom Post Type** - Integrates with WordPress video ecosystem

### Admin Features
- **Connection Testing** - Verify API connection before syncing
- **Sync Progress** - Real-time progress bar during sync operations
- **Detailed Logging** - Track every sync operation with timestamps
- **Video Information Panel** - View StreamHost data in video edit page
- **Re-sync Individual Videos** - Update specific videos from StreamHost

### Developer Friendly
- **Clean Architecture** - Well-organized class structure
- **WordPress Standards** - Follows WordPress coding standards
- **AJAX Powered** - Smooth admin experience
- **Extensible** - Hooks and filters for customization

## 📋 Requirements

| Requirement | Version |
|------------|---------|
| WordPress | 5.8+ |
| PHP | 7.4+ |
| MAS Videos Plugin | Latest |
| StreamHost Service | Running |

## 🚀 Installation

### Quick Install

1. Download the latest release
2. Upload to `/wp-content/plugins/streamhost-connector/`
3. Activate via WordPress admin
4. Configure settings in **StreamHost > Settings**

### Detailed Installation

See [INSTALLATION.md](INSTALLATION.md) for complete setup guide.

## ⚙️ Configuration

### Basic Setup

1. Navigate to **StreamHost > Settings**
2. Enter your StreamHost API URL (e.g., `https://your-domain.com`)
3. Enter admin username and password
4. Enable auto-sync (optional)
5. Click **Save Settings**

### Test Connection

1. Click **Test Connection** button
2. Verify successful connection
3. Check video count matches StreamHost

### First Sync

1. Go to **StreamHost > Sync Videos**
2. Click **Sync All Videos Now**
3. Wait for completion
4. Check synced videos in **Videos > All Videos**

## 📖 Usage

### Automatic Syncing

When auto-sync is enabled:
- Runs automatically based on interval
- Checks for new videos
- Updates existing videos
- Logs all operations

### Manual Syncing

**Sync All Videos:**
1. Go to **StreamHost > Sync Videos**
2. Click **Sync All Videos Now**
3. View progress and results

**Re-sync Single Video:**
1. Edit any video post
2. Find **StreamHost Information** panel
3. Click **Re-sync from StreamHost**

### View Sync History

Go to **StreamHost > Sync Log** to see:
- Video ID
- WordPress Post ID
- Status (success/failed)
- Error messages
- Sync timestamp

## 🎬 Video Display

### Automatic Display

Synced videos appear in:
- `/videos/` - Video archive page
- `/video/video-title/` - Single video pages
- StreamLab theme video sections

### Shortcodes

Use MAS Videos shortcodes:

```php
// Display recent videos
[mas_videos limit="12" columns="4"]

// Display videos by category
[mas_videos category="action" limit="8"]

// Display single video
[mas_video id="123"]
```

### Template Tags

In your theme templates:

```php
// Check if video
if (is_singular('video')) {
    // Get video URL
    $video_url = get_post_meta(get_the_ID(), '_video_url', true);
    
    // Get StreamHost ID
    $streamhost_id = get_post_meta(get_the_ID(), '_streamhost_video_id', true);
    
    // Get duration
    $duration = get_post_meta(get_the_ID(), '_video_duration', true);
}
```

## 🔌 API Reference

### Hooks

**Actions:**

```php
// Before video sync
do_action('streamhost_before_sync', $video_id, $video_data);

// After video sync
do_action('streamhost_after_sync', $post_id, $video_data);

// After thumbnail sync
do_action('streamhost_after_thumbnail_sync', $post_id, $attachment_id);
```

**Filters:**

```php
// Modify video post data before creation
apply_filters('streamhost_video_post_data', $post_data, $video_data);

// Modify video metadata
apply_filters('streamhost_video_metadata', $metadata, $video_data);

// Modify sync interval
apply_filters('streamhost_sync_interval', $interval);
```

### Classes

**StreamHost_API**
```php
$api = new StreamHost_API();
$videos = $api->get_videos();
$video = $api->get_video($video_id);
```

**StreamHost_Sync**
```php
$sync = new StreamHost_Sync($api);
$result = $sync->sync_video($video_id);
$result = $sync->sync_all_videos();
```

## 📊 Database

### Custom Tables

**wp_streamhost_sync_log**
- Tracks all sync operations
- Stores video ID, post ID, status, message, timestamp
- Used for sync history and debugging

### Post Meta

| Meta Key | Description |
|----------|-------------|
| `_streamhost_video_id` | StreamHost video ID |
| `_streamhost_synced` | Last sync timestamp |
| `_streamhost_status` | Processing status |
| `_video_url` | HLS stream URL |
| `_video_duration` | Video duration (seconds) |
| `_video_width` | Video width (pixels) |
| `_video_height` | Video height (pixels) |
| `_video_aspect_ratio` | Aspect ratio (e.g., 16:9) |
| `_video_file_size` | File size (bytes) |
| `_video_format` | Video format |

## 🛠️ Development

### File Structure

```
streamhost-connector/
├── streamhost-connector.php       # Main plugin file
├── includes/
│   ├── class-streamhost-api.php           # API handler
│   ├── class-streamhost-sync.php          # Sync logic
│   ├── class-streamhost-admin.php         # Admin interface
│   └── class-streamhost-video-post-type.php # Post type handler
├── assets/
│   ├── css/
│   │   └── admin.css                     # Admin styles
│   └── js/
│       └── admin.js                      # Admin scripts
├── README.md
├── INSTALLATION.md
└── readme.txt                            # WordPress.org readme
```

### Coding Standards

- Follows WordPress Coding Standards
- PSR-4 autoloading
- Object-oriented architecture
- Proper sanitization and validation
- Nonce verification for AJAX

### Testing

**Manual Testing:**
1. Test connection with various credentials
2. Sync videos with different statuses
3. Check thumbnail downloads
4. Verify metadata accuracy
5. Test re-sync functionality

**Error Scenarios:**
- Invalid API URL
- Wrong credentials
- Network timeout
- Missing thumbnails
- Failed video processing

## 🐛 Troubleshooting

### Common Issues

**Issue:** Videos not syncing

**Solution:**
- Check sync log for errors
- Verify video status is "ready"
- Check MAS Videos plugin is active
- Increase PHP max execution time

**Issue:** Thumbnails missing

**Solution:**
- Check uploads directory is writable
- Verify thumbnail exists in StreamHost
- Check PHP memory limit
- Re-sync the video

**Issue:** Authentication fails

**Solution:**
- Verify API URL format
- Check credentials are correct
- Ensure StreamHost is accessible
- Check for firewall blocking

### Debug Mode

Enable WordPress debug mode in `wp-config.php`:

```php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

Check debug log: `/wp-content/debug.log`

## 📝 Changelog

### Version 1.0.0 (Current)

**Initial Release**
- ✨ Auto sync with configurable intervals
- ✨ Manual sync with progress tracking
- ✨ Thumbnail synchronization
- ✨ Complete metadata sync
- ✨ HLS streaming support
- ✨ Detailed sync logging
- ✨ Admin dashboard
- ✨ Connection testing
- ✨ Individual video re-sync
- ✨ MAS Videos integration
- ✨ StreamLab theme compatibility

## 🗺️ Roadmap

### Version 1.1.0 (Planned)
- [ ] Folder to category mapping
- [ ] Selective sync by folder
- [ ] Embed settings sync
- [ ] Bulk actions in video list
- [ ] Import/export settings

### Version 1.2.0 (Planned)
- [ ] Video analytics integration
- [ ] CDN support
- [ ] Advanced caching
- [ ] Webhook support
- [ ] Multi-site support

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Contribution Guidelines

- Follow WordPress coding standards
- Add PHPDoc comments
- Test thoroughly
- Update documentation
- Add to CHANGELOG.md

## 📧 Support

**Plugin Issues:**
- GitHub Issues: https://github.com/yourusername/streamhost-connector/issues
- Email: support@your-domain.com

**StreamHost Service:**
- StreamHost Documentation
- StreamHost GitHub

**WordPress/Theme:**
- WordPress Support
- StreamLab Theme Support

## 📄 License

This plugin is licensed under the GPL v2 or later.

```
Copyright (C) 2024 Your Name

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
```

## 🙏 Credits

**Developed by:** Your Name
**Contributors:** Community contributors
**Built with:** WordPress, PHP, JavaScript
**Integrates with:** StreamHost, MAS Videos, StreamLab

---

**Made with ❤️ for the WordPress community**

⭐ Star this repo if you find it useful!
