<?php
/**
 * VidStream Video Post Type Handler
 *
 * @package VidStream_Connector
 */

if (!defined('ABSPATH')) {
    exit;
}

class VidStream_Video_Post_Type {
    
    /**
     * Constructor
     */
    public function __construct() {
        add_filter('manage_video_posts_columns', array($this, 'add_custom_columns'));
        add_action('manage_video_posts_custom_column', array($this, 'render_custom_columns'), 10, 2);
        add_action('add_meta_boxes', array($this, 'add_meta_boxes'));
    }
    
    /**
     * Add custom columns
     */
    public function add_custom_columns($columns) {
        $new_columns = array();
        
        foreach ($columns as $key => $value) {
            $new_columns[$key] = $value;
            
            if ($key === 'title') {
                $new_columns['vidstream_thumbnail'] = __('Thumbnail', 'vidstream-connector');
                $new_columns['vidstream_status'] = __('VidStream Status', 'vidstream-connector');
                $new_columns['vidstream_duration'] = __('Duration', 'vidstream-connector');
            }
        }
        
        return $new_columns;
    }
    
    /**
     * Render custom columns
     */
    public function render_custom_columns($column, $post_id) {
        switch ($column) {
            case 'vidstream_thumbnail':
                if (has_post_thumbnail($post_id)) {
                    echo get_the_post_thumbnail($post_id, array(80, 80));
                } else {
                    echo '<span style="color: #999;">—</span>';
                }
                break;
                
            case 'vidstream_status':
                $video_id = get_post_meta($post_id, '_vidstream_video_id', true);
                $status = get_post_meta($post_id, '_vidstream_status', true);
                
                if ($video_id) {
                    $status_class = $status === 'ready' ? 'success' : 'warning';
                    echo '<span class="vidstream-badge vidstream-badge-' . esc_attr($status_class) . '">';
                    echo esc_html(ucfirst($status ?: 'synced'));
                    echo '</span>';
                } else {
                    echo '<span style="color: #999;">' . __('Not synced', 'vidstream-connector') . '</span>';
                }
                break;
                
            case 'vidstream_duration':
                $duration = get_post_meta($post_id, '_video_duration', true);
                
                if ($duration) {
                    echo esc_html($this->format_duration($duration));
                } else {
                    echo '<span style="color: #999;">—</span>';
                }
                break;
        }
    }
    
    /**
     * Add meta boxes
     */
    public function add_meta_boxes() {
        add_meta_box(
            'vidstream_info',
            __('VidStream Information', 'vidstream-connector'),
            array($this, 'render_info_meta_box'),
            'video',
            'side',
            'high'
        );
    }
    
    /**
     * Render info meta box
     */
    public function render_info_meta_box($post) {
        $video_id = get_post_meta($post->ID, '_vidstream_video_id', true);
        $synced_at = get_post_meta($post->ID, '_vidstream_synced', true);
        $stream_url = get_post_meta($post->ID, '_video_url', true);
        $status = get_post_meta($post->ID, '_vidstream_status', true);
        $width = get_post_meta($post->ID, '_video_width', true);
        $height = get_post_meta($post->ID, '_video_height', true);
        $aspect_ratio = get_post_meta($post->ID, '_video_aspect_ratio', true);
        $file_size = get_post_meta($post->ID, '_video_file_size', true);
        $format = get_post_meta($post->ID, '_video_format', true);
        
        if (!$video_id) {
            echo '<p>' . __('This video is not synced from VidStream.', 'vidstream-connector') . '</p>';
            return;
        }
        
        ?>
        <div class="vidstream-meta-info">
            <p>
                <strong><?php _e('Video ID:', 'vidstream-connector'); ?></strong><br>
                <code><?php echo esc_html($video_id); ?></code>
            </p>
            
            <?php if ($status) : ?>
            <p>
                <strong><?php _e('Status:', 'vidstream-connector'); ?></strong><br>
                <span class="vidstream-badge vidstream-badge-<?php echo $status === 'ready' ? 'success' : 'warning'; ?>">
                    <?php echo esc_html(ucfirst($status)); ?>
                </span>
            </p>
            <?php endif; ?>
            
            <?php if ($width && $height) : ?>
            <p>
                <strong><?php _e('Resolution:', 'vidstream-connector'); ?></strong><br>
                <?php echo esc_html($width . ' x ' . $height); ?>
                <?php if ($aspect_ratio) : ?>
                    (<?php echo esc_html($aspect_ratio); ?>)
                <?php endif; ?>
            </p>
            <?php endif; ?>
            
            <?php if ($file_size) : ?>
            <p>
                <strong><?php _e('File Size:', 'vidstream-connector'); ?></strong><br>
                <?php echo esc_html($this->format_bytes($file_size)); ?>
            </p>
            <?php endif; ?>
            
            <?php if ($format) : ?>
            <p>
                <strong><?php _e('Format:', 'vidstream-connector'); ?></strong><br>
                <?php echo esc_html(strtoupper($format)); ?>
            </p>
            <?php endif; ?>
            
            <?php if ($synced_at) : ?>
            <p>
                <strong><?php _e('Last Synced:', 'vidstream-connector'); ?></strong><br>
                <?php echo esc_html(date_i18n(get_option('date_format') . ' ' . get_option('time_format'), strtotime($synced_at))); ?>
            </p>
            <?php endif; ?>
            
            <?php if ($stream_url) : ?>
            <p>
                <strong><?php _e('Stream URL:', 'vidstream-connector'); ?></strong><br>
                <input type="text" value="<?php echo esc_attr($stream_url); ?>" readonly style="width: 100%; font-size: 11px;">
            </p>
            <?php endif; ?>
            
            <p style="margin-top: 15px;">
                <button type="button" class="button button-small" onclick="vidstreamResyncVideo('<?php echo esc_js($video_id); ?>', <?php echo intval($post->ID); ?>)">
                    <?php _e('Re-sync from VidStream', 'vidstream-connector'); ?>
                </button>
            </p>
        </div>
        
        <script>
        function vidstreamResyncVideo(videoId, postId) {
            if (!confirm('<?php _e('Are you sure you want to re-sync this video?', 'vidstream-connector'); ?>')) {
                return;
            }
            
            jQuery.post(ajaxurl, {
                action: 'vidstream_sync_single',
                video_id: videoId,
                nonce: '<?php echo wp_create_nonce('vidstream_ajax_nonce'); ?>'
            }, function(response) {
                if (response.success) {
                    alert('<?php _e('Video re-synced successfully!', 'vidstream-connector'); ?>');
                    location.reload();
                } else {
                    alert('<?php _e('Failed to re-sync video:', 'vidstream-connector'); ?> ' + response.data.message);
                }
            });
        }
        </script>
        <?php
    }
    
    /**
     * Format duration
     */
    private function format_duration($seconds) {
        $hours = floor($seconds / 3600);
        $minutes = floor(($seconds % 3600) / 60);
        $seconds = $seconds % 60;
        
        if ($hours > 0) {
            return sprintf('%d:%02d:%02d', $hours, $minutes, $seconds);
        } else {
            return sprintf('%d:%02d', $minutes, $seconds);
        }
    }
    
    /**
     * Format bytes
     */
    private function format_bytes($bytes) {
        $units = array('B', 'KB', 'MB', 'GB', 'TB');
        
        for ($i = 0; $bytes > 1024 && $i < count($units) - 1; $i++) {
            $bytes /= 1024;
        }
        
        return round($bytes, 2) . ' ' . $units[$i];
    }
}