=== VidStream Connector ===
Contributors: yourusername
Tags: video, streaming, mas-videos, vidstream, video-hosting
Requires at least: 5.8
Tested up to: 6.7
Stable tag: 1.0.0
Requires PHP: 7.4
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Automatically sync videos from your VidStream hosting service to WordPress with MAS Videos integration.

== Description ==

VidStream Connector seamlessly integrates your self-hosted VidStream video platform with WordPress. Automatically import and sync your video library, complete with thumbnails, metadata, and HLS streaming support.

**Key Features:**

* **Automatic Video Sync** - Set it and forget it with scheduled automatic syncing
* **MAS Videos Integration** - Works perfectly with the MAS Videos plugin and StreamLab theme
* **HLS Streaming** - Full support for adaptive bitrate streaming
* **Thumbnail Sync** - Automatically imports video thumbnails
* **Metadata Sync** - Duration, resolution, aspect ratio, and more
* **Manual & Auto Sync** - Choose when to sync your videos
* **Sync Logs** - Track all sync operations
* **Admin Dashboard** - Easy-to-use admin interface

**Requirements:**

* WordPress 5.8 or higher
* PHP 7.4 or higher
* MAS Videos plugin (for video post type support)
* VidStream hosting service

== Installation ==

1. Upload the plugin files to `/wp-content/plugins/vidstream-connector/`
2. Activate the plugin through the 'Plugins' menu in WordPress
3. Install and activate the MAS Videos plugin if not already installed
4. Go to VidStream > Settings to configure your API credentials
5. Test your connection and start syncing!

== Frequently Asked Questions ==

= What is VidStream? =

VidStream is a self-hosted video hosting platform with FFmpeg processing and HLS streaming capabilities.

= Do I need MAS Videos plugin? =

Yes, this plugin creates videos using the MAS Videos custom post type format.

= How often does auto-sync run? =

You can choose between hourly, twice daily, or daily sync intervals.

= Can I manually sync specific videos? =

Yes, you can manually sync all videos or re-sync individual videos from the video edit page.

= What video formats are supported? =

VidStream supports all FFmpeg-compatible formats, and videos are automatically transcoded to HLS for streaming.

== Screenshots ==

1. Settings page - Configure your VidStream API connection
2. Sync page - Manually sync videos with progress tracking
3. Sync log - View detailed sync history
4. Video edit page - VidStream metadata display

== Changelog ==

= 1.0.0 =
* Initial release
* Auto sync functionality
* Manual sync with progress tracking
* Thumbnail synchronization
* Metadata synchronization
* HLS streaming URL support
* Sync logging
* Admin dashboard

== Upgrade Notice ==

= 1.0.0 =
Initial release of VidStream Connector.

== Support ==

For support, please visit https://github.com/yourusername/vidstream-connector

== Credits ==

Developed with ❤️ for the VidStream community.