<?php
/**
 * Plugin Name: VidStream Connector
 * Plugin URI: https://github.com/yourusername/vidstream-connector
 * Description: Automatically sync videos from your VidStream hosting service to WordPress with MAS Videos integration
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://your-domain.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: vidstream-connector
 * Requires at least: 5.8
 * Requires PHP: 7.4
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('VIDSTREAM_CONNECTOR_VERSION', '1.0.0');
define('VIDSTREAM_CONNECTOR_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('VIDSTREAM_CONNECTOR_PLUGIN_URL', plugin_dir_url(__FILE__));
define('VIDSTREAM_CONNECTOR_PLUGIN_FILE', __FILE__);

/**
 * Main VidStream Connector Class
 */
class VidStream_Connector {
    
    /**
     * Instance of this class
     */
    private static $instance = null;
    
    /**
     * API handler instance
     */
    private $api;
    
    /**
     * Sync handler instance
     */
    private $sync;
    
    /**
     * Get instance
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Constructor
     */
    private function __construct() {
        $this->includes();
        $this->init_hooks();
    }
    
    /**
     * Include required files
     */
    private function includes() {
        require_once VIDSTREAM_CONNECTOR_PLUGIN_DIR . 'includes/class-vidstream-api.php';
        require_once VIDSTREAM_CONNECTOR_PLUGIN_DIR . 'includes/class-vidstream-sync.php';
        require_once VIDSTREAM_CONNECTOR_PLUGIN_DIR . 'includes/class-vidstream-admin.php';
        require_once VIDSTREAM_CONNECTOR_PLUGIN_DIR . 'includes/class-vidstream-video-post-type.php';
    }
    
    /**
     * Initialize hooks
     */
    private function init_hooks() {
        add_action('init', array($this, 'init'));
        add_action('admin_enqueue_scripts', array($this, 'admin_scripts'));
        
        // Initialize classes
        $this->api = new VidStream_API();
        $this->sync = new VidStream_Sync($this->api);
        new VidStream_Admin($this->api, $this->sync);
        new VidStream_Video_Post_Type();
        
        // Register activation/deactivation hooks
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
    }
    
    /**
     * Initialize plugin
     */
    public function init() {
        load_plugin_textdomain('vidstream-connector', false, dirname(plugin_basename(__FILE__)) . '/languages');
    }
    
    /**
     * Enqueue admin scripts
     */
    public function admin_scripts($hook) {
        if ('toplevel_page_vidstream-connector' !== $hook && 'vidstream_page_vidstream-sync' !== $hook) {
            return;
        }
        
        wp_enqueue_style(
            'vidstream-admin',
            VIDSTREAM_CONNECTOR_PLUGIN_URL . 'assets/css/admin.css',
            array(),
            VIDSTREAM_CONNECTOR_VERSION
        );
        
        wp_enqueue_script(
            'vidstream-admin',
            VIDSTREAM_CONNECTOR_PLUGIN_URL . 'assets/js/admin.js',
            array('jquery'),
            VIDSTREAM_CONNECTOR_VERSION,
            true
        );
        
        wp_localize_script('vidstream-admin', 'vidstreamAjax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('vidstream_ajax_nonce'),
        ));
    }
    
    /**
     * Plugin activation
     */
    public function activate() {
        // Create sync log table
        global $wpdb;
        $table_name = $wpdb->prefix . 'vidstream_sync_log';
        $charset_collate = $wpdb->get_charset_collate();
        
        $sql = "CREATE TABLE IF NOT EXISTS $table_name (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            video_id varchar(255) NOT NULL,
            post_id bigint(20) DEFAULT NULL,
            status varchar(50) NOT NULL,
            message text,
            synced_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY video_id (video_id),
            KEY post_id (post_id)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
        
        // Set default options
        if (!get_option('vidstream_api_url')) {
            add_option('vidstream_api_url', '');
            add_option('vidstream_username', '');
            add_option('vidstream_password', '');
            add_option('vidstream_auto_sync', 'no');
            add_option('vidstream_sync_interval', 'hourly');
        }
        
        // Schedule cron
        if (!wp_next_scheduled('vidstream_auto_sync_cron')) {
            wp_schedule_event(time(), 'hourly', 'vidstream_auto_sync_cron');
        }
    }
    
    /**
     * Plugin deactivation
     */
    public function deactivate() {
        wp_clear_scheduled_hook('vidstream_auto_sync_cron');
    }
}

/**
 * Initialize the plugin
 */
function vidstream_connector() {
    return VidStream_Connector::get_instance();
}

// Start the plugin
vidstream_connector();
