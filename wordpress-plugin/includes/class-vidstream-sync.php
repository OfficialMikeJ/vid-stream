<?php
/**
 * VidStream Sync Handler
 *
 * @package VidStream_Connector
 */

if (!defined('ABSPATH')) {
    exit;
}

class VidStream_Sync {
    
    /**
     * API instance
     */
    private $api;
    
    /**
     * Constructor
     */
    public function __construct($api) {
        $this->api = $api;
        
        // Auto sync cron
        add_action('vidstream_auto_sync_cron', array($this, 'auto_sync'));
        
        // AJAX handlers
        add_action('wp_ajax_vidstream_manual_sync', array($this, 'ajax_manual_sync'));
        add_action('wp_ajax_vidstream_sync_single', array($this, 'ajax_sync_single'));
    }
    
    /**
     * Auto sync (triggered by cron)
     */
    public function auto_sync() {
        if (get_option('vidstream_auto_sync') !== 'yes') {
            return;
        }
        
        $this->sync_all_videos();
    }
    
    /**
     * Manual sync via AJAX
     */
    public function ajax_manual_sync() {
        check_ajax_referer('vidstream_ajax_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }
        
        $result = $this->sync_all_videos();
        wp_send_json_success($result);
    }
    
    /**
     * Sync single video via AJAX
     */
    public function ajax_sync_single() {
        check_ajax_referer('vidstream_ajax_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }
        
        $video_id = isset($_POST['video_id']) ? sanitize_text_field($_POST['video_id']) : '';
        
        if (!$video_id) {
            wp_send_json_error(array('message' => 'Video ID required'));
        }
        
        $result = $this->sync_video($video_id);
        wp_send_json_success($result);
    }
    
    /**
     * Sync all videos
     */
    public function sync_all_videos() {
        $videos_response = $this->api->get_videos();
        
        if (!$videos_response['success']) {
            return array(
                'success' => false,
                'message' => $videos_response['message']
            );
        }
        
        $videos = $videos_response['data'];
        $synced = 0;
        $failed = 0;
        $skipped = 0;
        
        foreach ($videos as $video) {
            // Skip if not ready
            if (isset($video['processing_status']) && $video['processing_status'] !== 'ready') {
                $skipped++;
                continue;
            }
            
            $result = $this->sync_video($video['id'], $video);
            
            if ($result['success']) {
                $synced++;
            } else {
                $failed++;
            }
        }
        
        return array(
            'success' => true,
            'synced' => $synced,
            'failed' => $failed,
            'skipped' => $skipped,
            'total' => count($videos)
        );
    }
    
    /**
     * Sync single video
     */
    public function sync_video($video_id, $video_data = null) {
        // Get video data if not provided
        if (!$video_data) {
            $video_response = $this->api->get_video($video_id);
            
            if (!$video_response['success']) {
                $this->log_sync($video_id, null, 'failed', $video_response['message']);
                return array(
                    'success' => false,
                    'message' => $video_response['message']
                );
            }
            
            $video_data = $video_response['data'];
        }
        
        // Check if video already exists
        $existing_post_id = $this->get_post_by_video_id($video_id);
        
        if ($existing_post_id) {
            // Update existing post
            $post_id = $this->update_video_post($existing_post_id, $video_data);
        } else {
            // Create new post
            $post_id = $this->create_video_post($video_data);
        }
        
        if (is_wp_error($post_id)) {
            $this->log_sync($video_id, null, 'failed', $post_id->get_error_message());
            return array(
                'success' => false,
                'message' => $post_id->get_error_message()
            );
        }
        
        // Sync thumbnail
        $this->sync_thumbnail($post_id, $video_id);
        
        // Save video metadata
        $this->save_video_metadata($post_id, $video_data);
        
        $this->log_sync($video_id, $post_id, 'success', 'Video synced successfully');
        
        return array(
            'success' => true,
            'post_id' => $post_id,
            'message' => 'Video synced successfully'
        );
    }
    
    /**
     * Create video post
     */
    private function create_video_post($video_data) {
        // Prepare post data
        $post_data = array(
            'post_title' => sanitize_text_field($video_data['title']),
            'post_content' => !empty($video_data['description']) ? wp_kses_post($video_data['description']) : '',
            'post_status' => 'publish',
            'post_type' => 'video', // MAS Videos custom post type
            'post_author' => get_current_user_id() ?: 1
        );
        
        $post_id = wp_insert_post($post_data);
        
        if (!is_wp_error($post_id)) {
            // Save VidStream video ID for reference
            update_post_meta($post_id, '_vidstream_video_id', $video_data['id']);
            update_post_meta($post_id, '_vidstream_synced', current_time('mysql'));
        }
        
        return $post_id;
    }
    
    /**
     * Update video post
     */
    private function update_video_post($post_id, $video_data) {
        $post_data = array(
            'ID' => $post_id,
            'post_title' => sanitize_text_field($video_data['title']),
            'post_content' => !empty($video_data['description']) ? wp_kses_post($video_data['description']) : ''
        );
        
        $result = wp_update_post($post_data);
        
        if (!is_wp_error($result)) {
            update_post_meta($post_id, '_vidstream_synced', current_time('mysql'));
        }
        
        return $result;
    }
    
    /**
     * Save video metadata
     */
    private function save_video_metadata($post_id, $video_data) {
        // Video duration
        if (isset($video_data['duration'])) {
            update_post_meta($post_id, '_video_duration', intval($video_data['duration']));
        }
        
        // Video URL (HLS stream)
        $stream_url = $this->api->get_stream_url($video_data['id']);
        update_post_meta($post_id, '_video_url', $stream_url);
        update_post_meta($post_id, '_video_url_type', 'hls');
        
        // Video source
        update_post_meta($post_id, '_video_source', 'vidstream');
        update_post_meta($post_id, '_vidstream_original_url', isset($video_data['file_path']) ? $video_data['file_path'] : '');
        
        // Video dimensions
        if (isset($video_data['width'])) {
            update_post_meta($post_id, '_video_width', intval($video_data['width']));
        }
        if (isset($video_data['height'])) {
            update_post_meta($post_id, '_video_height', intval($video_data['height']));
        }
        if (isset($video_data['aspect_ratio'])) {
            update_post_meta($post_id, '_video_aspect_ratio', sanitize_text_field($video_data['aspect_ratio']));
        }
        
        // File size
        if (isset($video_data['file_size'])) {
            update_post_meta($post_id, '_video_file_size', intval($video_data['file_size']));
        }
        
        // Format
        if (isset($video_data['format'])) {
            update_post_meta($post_id, '_video_format', sanitize_text_field($video_data['format']));
        }
        
        // Processing status
        if (isset($video_data['processing_status'])) {
            update_post_meta($post_id, '_vidstream_status', sanitize_text_field($video_data['processing_status']));
        }
    }
    
    /**
     * Sync thumbnail
     */
    private function sync_thumbnail($post_id, $video_id) {
        // Check if thumbnail already exists
        if (has_post_thumbnail($post_id)) {
            return;
        }
        
        $upload_dir = wp_upload_dir();
        $filename = 'vidstream-' . $video_id . '.jpg';
        $file_path = $upload_dir['path'] . '/' . $filename;
        
        // Download thumbnail
        if ($this->api->download_thumbnail($video_id, $file_path)) {
            // Insert as attachment
            $attachment = array(
                'post_mime_type' => 'image/jpeg',
                'post_title' => sanitize_file_name($filename),
                'post_content' => '',
                'post_status' => 'inherit'
            );
            
            $attach_id = wp_insert_attachment($attachment, $file_path, $post_id);
            
            if (!is_wp_error($attach_id)) {
                require_once(ABSPATH . 'wp-admin/includes/image.php');
                $attach_data = wp_generate_attachment_metadata($attach_id, $file_path);
                wp_update_attachment_metadata($attach_id, $attach_data);
                set_post_thumbnail($post_id, $attach_id);
            }
        }
    }
    
    /**
     * Get post by video ID
     */
    private function get_post_by_video_id($video_id) {
        $args = array(
            'post_type' => 'video',
            'meta_key' => '_vidstream_video_id',
            'meta_value' => $video_id,
            'posts_per_page' => 1,
            'fields' => 'ids'
        );
        
        $posts = get_posts($args);
        
        return !empty($posts) ? $posts[0] : false;
    }
    
    /**
     * Log sync operation
     */
    private function log_sync($video_id, $post_id, $status, $message) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'vidstream_sync_log';
        
        $wpdb->insert(
            $table_name,
            array(
                'video_id' => $video_id,
                'post_id' => $post_id,
                'status' => $status,
                'message' => $message,
                'synced_at' => current_time('mysql')
            ),
            array('%s', '%d', '%s', '%s', '%s')
        );
    }
    
    /**
     * Get sync log
     */
    public function get_sync_log($limit = 50) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'vidstream_sync_log';
        
        return $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM $table_name ORDER BY synced_at DESC LIMIT %d",
                $limit
            )
        );
    }
}