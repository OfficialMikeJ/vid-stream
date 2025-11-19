<?php
/**
 * VidStream Admin Interface
 *
 * @package VidStream_Connector
 */

if (!defined('ABSPATH')) {
    exit;
}

class VidStream_Admin {
    
    /**
     * API instance
     */
    private $api;
    
    /**
     * Sync instance
     */
    private $sync;
    
    /**
     * Constructor
     */
    public function __construct($api, $sync) {
        $this->api = $api;
        $this->sync = $sync;
        
        add_action('admin_menu', array($this, 'add_menu_pages'));
        add_action('admin_init', array($this, 'register_settings'));
        add_action('admin_notices', array($this, 'admin_notices'));
    }
    
    /**
     * Add menu pages
     */
    public function add_menu_pages() {
        add_menu_page(
            __('VidStream Connector', 'vidstream-connector'),
            __('VidStream', 'vidstream-connector'),
            'manage_options',
            'vidstream-connector',
            array($this, 'settings_page'),
            'dashicons-video-alt3',
            30
        );
        
        add_submenu_page(
            'vidstream-connector',
            __('Settings', 'vidstream-connector'),
            __('Settings', 'vidstream-connector'),
            'manage_options',
            'vidstream-connector'
        );
        
        add_submenu_page(
            'vidstream-connector',
            __('Sync Videos', 'vidstream-connector'),
            __('Sync Videos', 'vidstream-connector'),
            'manage_options',
            'vidstream-sync',
            array($this, 'sync_page')
        );
        
        add_submenu_page(
            'vidstream-connector',
            __('Sync Log', 'vidstream-connector'),
            __('Sync Log', 'vidstream-connector'),
            'manage_options',
            'vidstream-log',
            array($this, 'log_page')
        );
    }
    
    /**
     * Register settings
     */
    public function register_settings() {
        register_setting('vidstream_settings', 'vidstream_api_url', array(
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw'
        ));
        
        register_setting('vidstream_settings', 'vidstream_username', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field'
        ));
        
        register_setting('vidstream_settings', 'vidstream_password', array(
            'type' => 'string'
        ));
        
        register_setting('vidstream_settings', 'vidstream_auto_sync', array(
            'type' => 'string',
            'default' => 'no'
        ));
        
        register_setting('vidstream_settings', 'vidstream_sync_interval', array(
            'type' => 'string',
            'default' => 'hourly'
        ));
    }
    
    /**
     * Admin notices
     */
    public function admin_notices() {
        if (!get_option('vidstream_api_url')) {
            echo '<div class="notice notice-warning"><p>';
            echo __('VidStream Connector: Please configure your API settings.', 'vidstream-connector');
            echo ' <a href="' . admin_url('admin.php?page=vidstream-connector') . '">' . __('Go to Settings', 'vidstream-connector') . '</a>';
            echo '</p></div>';
        }
    }
    
    /**
     * Settings page
     */
    public function settings_page() {
        if (isset($_POST['test_connection'])) {
            check_admin_referer('vidstream_test_connection');
            $test_result = $this->api->test_connection();
        }
        
        ?>
        <div class="wrap vidstream-admin">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            
            <?php if (isset($test_result)) : ?>
                <div class="notice notice-<?php echo $test_result['success'] ? 'success' : 'error'; ?> is-dismissible">
                    <p><strong><?php echo esc_html($test_result['message']); ?></strong></p>
                    <?php if ($test_result['success'] && isset($test_result['video_count'])) : ?>
                        <p><?php printf(__('Found %d videos in your VidStream library.', 'vidstream-connector'), $test_result['video_count']); ?></p>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
            
            <form method="post" action="options.php">
                <?php settings_fields('vidstream_settings'); ?>
                
                <table class="form-table">
                    <tr>
                        <th scope="row">
                            <label for="vidstream_api_url"><?php _e('VidStream API URL', 'vidstream-connector'); ?></label>
                        </th>
                        <td>
                            <input type="url" 
                                   id="vidstream_api_url" 
                                   name="vidstream_api_url" 
                                   value="<?php echo esc_attr(get_option('vidstream_api_url')); ?>" 
                                   class="regular-text" 
                                   placeholder="https://your-vidstream-domain.com" 
                                   required>
                            <p class="description"><?php _e('Enter your VidStream API URL (without /api)', 'vidstream-connector'); ?></p>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row">
                            <label for="vidstream_username"><?php _e('Username', 'vidstream-connector'); ?></label>
                        </th>
                        <td>
                            <input type="text" 
                                   id="vidstream_username" 
                                   name="vidstream_username" 
                                   value="<?php echo esc_attr(get_option('vidstream_username')); ?>" 
                                   class="regular-text" 
                                   required>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row">
                            <label for="vidstream_password"><?php _e('Password', 'vidstream-connector'); ?></label>
                        </th>
                        <td>
                            <input type="password" 
                                   id="vidstream_password" 
                                   name="vidstream_password" 
                                   value="<?php echo esc_attr(get_option('vidstream_password')); ?>" 
                                   class="regular-text" 
                                   required>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row">
                            <label for="vidstream_auto_sync"><?php _e('Auto Sync', 'vidstream-connector'); ?></label>
                        </th>
                        <td>
                            <label>
                                <input type="checkbox" 
                                       id="vidstream_auto_sync" 
                                       name="vidstream_auto_sync" 
                                       value="yes" 
                                       <?php checked(get_option('vidstream_auto_sync'), 'yes'); ?>>
                                <?php _e('Automatically sync videos from VidStream', 'vidstream-connector'); ?>
                            </label>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row">
                            <label for="vidstream_sync_interval"><?php _e('Sync Interval', 'vidstream-connector'); ?></label>
                        </th>
                        <td>
                            <select id="vidstream_sync_interval" name="vidstream_sync_interval">
                                <option value="hourly" <?php selected(get_option('vidstream_sync_interval'), 'hourly'); ?>><?php _e('Hourly', 'vidstream-connector'); ?></option>
                                <option value="twicedaily" <?php selected(get_option('vidstream_sync_interval'), 'twicedaily'); ?>><?php _e('Twice Daily', 'vidstream-connector'); ?></option>
                                <option value="daily" <?php selected(get_option('vidstream_sync_interval'), 'daily'); ?>><?php _e('Daily', 'vidstream-connector'); ?></option>
                            </select>
                        </td>
                    </tr>
                </table>
                
                <?php submit_button(__('Save Settings', 'vidstream-connector')); ?>
            </form>
            
            <hr>
            
            <h2><?php _e('Test Connection', 'vidstream-connector'); ?></h2>
            <form method="post">
                <?php wp_nonce_field('vidstream_test_connection'); ?>
                <p><?php _e('Test your VidStream API connection before syncing.', 'vidstream-connector'); ?></p>
                <button type="submit" name="test_connection" class="button button-secondary"><?php _e('Test Connection', 'vidstream-connector'); ?></button>
            </form>
        </div>
        <?php
    }
    
    /**
     * Sync page
     */
    public function sync_page() {
        ?>
        <div class="wrap vidstream-admin">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            
            <div class="vidstream-sync-section">
                <h2><?php _e('Manual Sync', 'vidstream-connector'); ?></h2>
                <p><?php _e('Click the button below to sync all videos from your VidStream library.', 'vidstream-connector'); ?></p>
                
                <button type="button" id="vidstream-sync-btn" class="button button-primary button-large">
                    <?php _e('Sync All Videos Now', 'vidstream-connector'); ?>
                </button>
                
                <div id="vidstream-sync-progress" style="display:none; margin-top: 20px;">
                    <div class="vidstream-progress-bar">
                        <div class="vidstream-progress-fill"></div>
                    </div>
                    <p class="vidstream-progress-text"></p>
                </div>
                
                <div id="vidstream-sync-result" style="display:none; margin-top: 20px;"></div>
            </div>
            
            <hr>
            
            <div class="vidstream-info-section">
                <h2><?php _e('Sync Information', 'vidstream-connector'); ?></h2>
                
                <table class="widefat">
                    <tr>
                        <td><strong><?php _e('Last Sync:', 'vidstream-connector'); ?></strong></td>
                        <td><?php echo esc_html($this->get_last_sync_time()); ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('Total Synced Videos:', 'vidstream-connector'); ?></strong></td>
                        <td><?php echo esc_html($this->get_synced_video_count()); ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('Auto Sync:', 'vidstream-connector'); ?></strong></td>
                        <td><?php echo get_option('vidstream_auto_sync') === 'yes' ? __('Enabled', 'vidstream-connector') : __('Disabled', 'vidstream-connector'); ?></td>
                    </tr>
                </table>
            </div>
        </div>
        <?php
    }
    
    /**
     * Log page
     */
    public function log_page() {
        $logs = $this->sync->get_sync_log(100);
        
        ?>
        <div class="wrap vidstream-admin">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            
            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th><?php _e('Video ID', 'vidstream-connector'); ?></th>
                        <th><?php _e('Post ID', 'vidstream-connector'); ?></th>
                        <th><?php _e('Status', 'vidstream-connector'); ?></th>
                        <th><?php _e('Message', 'vidstream-connector'); ?></th>
                        <th><?php _e('Date', 'vidstream-connector'); ?></th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (!empty($logs)) : ?>
                        <?php foreach ($logs as $log) : ?>
                            <tr>
                                <td><?php echo esc_html($log->video_id); ?></td>
                                <td>
                                    <?php if ($log->post_id) : ?>
                                        <a href="<?php echo get_edit_post_link($log->post_id); ?>" target="_blank">
                                            <?php echo esc_html($log->post_id); ?>
                                        </a>
                                    <?php else : ?>
                                        —
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <span class="vidstream-status vidstream-status-<?php echo esc_attr($log->status); ?>">
                                        <?php echo esc_html(ucfirst($log->status)); ?>
                                    </span>
                                </td>
                                <td><?php echo esc_html($log->message); ?></td>
                                <td><?php echo esc_html($log->synced_at); ?></td>
                            </tr>
                        <?php endforeach; ?>
                    <?php else : ?>
                        <tr>
                            <td colspan="5"><?php _e('No sync logs found.', 'vidstream-connector'); ?></td>
                        </tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
        <?php
    }
    
    /**
     * Get last sync time
     */
    private function get_last_sync_time() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'vidstream_sync_log';
        
        $last_sync = $wpdb->get_var(
            "SELECT synced_at FROM $table_name WHERE status = 'success' ORDER BY synced_at DESC LIMIT 1"
        );
        
        return $last_sync ? $last_sync : __('Never', 'vidstream-connector');
    }
    
    /**
     * Get synced video count
     */
    private function get_synced_video_count() {
        $args = array(
            'post_type' => 'video',
            'meta_key' => '_vidstream_video_id',
            'posts_per_page' => -1,
            'fields' => 'ids'
        );
        
        $posts = get_posts($args);
        return count($posts);
    }
}