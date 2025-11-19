<?php
/**
 * Plugin Name: StreamLab Invites
 * Plugin URI: https://github.com/yourusername/streamlab-invites
 * Description: Secure invite-only access system for your streaming platform with code generation, registration control, and customizable permissions
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://your-domain.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: streamlab-invites
 * Requires at least: 5.8
 * Requires PHP: 7.4
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('STREAMLAB_INVITES_VERSION', '1.0.0');
define('STREAMLAB_INVITES_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('STREAMLAB_INVITES_PLUGIN_URL', plugin_dir_url(__FILE__));
define('STREAMLAB_INVITES_PLUGIN_FILE', __FILE__);

/**
 * Main StreamLab Invites Class
 */
class StreamLab_Invites {
    
    /**
     * Instance of this class
     */
    private static $instance = null;
    
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
        require_once STREAMLAB_INVITES_PLUGIN_DIR . 'includes/class-invite-code-manager.php';
        require_once STREAMLAB_INVITES_PLUGIN_DIR . 'includes/class-invite-access-control.php';
        require_once STREAMLAB_INVITES_PLUGIN_DIR . 'includes/class-invite-registration.php';
        require_once STREAMLAB_INVITES_PLUGIN_DIR . 'includes/class-invite-admin.php';
        require_once STREAMLAB_INVITES_PLUGIN_DIR . 'includes/class-invite-roles.php';
    }
    
    /**
     * Initialize hooks
     */
    private function init_hooks() {
        add_action('init', array($this, 'init'));
        add_action('admin_enqueue_scripts', array($this, 'admin_scripts'));
        add_action('wp_enqueue_scripts', array($this, 'frontend_scripts'));
        
        // Initialize classes
        new StreamLab_Invite_Code_Manager();
        new StreamLab_Invite_Access_Control();
        new StreamLab_Invite_Registration();
        new StreamLab_Invite_Admin();
        new StreamLab_Invite_Roles();
        
        // Register activation/deactivation hooks
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
    }
    
    /**
     * Initialize plugin
     */
    public function init() {
        load_plugin_textdomain('streamlab-invites', false, dirname(plugin_basename(__FILE__)) . '/languages');
    }
    
    /**
     * Enqueue admin scripts
     */
    public function admin_scripts($hook) {
        if (strpos($hook, 'streamlab-invites') === false) {
            return;
        }
        
        wp_enqueue_style(
            'streamlab-invites-admin',
            STREAMLAB_INVITES_PLUGIN_URL . 'assets/css/admin.css',
            array(),
            STREAMLAB_INVITES_VERSION
        );
        
        wp_enqueue_script(
            'streamlab-invites-admin',
            STREAMLAB_INVITES_PLUGIN_URL . 'assets/js/admin.js',
            array('jquery'),
            STREAMLAB_INVITES_VERSION,
            true
        );
        
        wp_localize_script('streamlab-invites-admin', 'streamlabInvites', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('streamlab_invites_nonce'),
            'confirm_delete' => __('Are you sure you want to delete this invite code?', 'streamlab-invites'),
            'confirm_revoke' => __('Are you sure you want to revoke this invite code?', 'streamlab-invites'),
        ));
    }
    
    /**
     * Enqueue frontend scripts
     */
    public function frontend_scripts() {
        wp_enqueue_style(
            'streamlab-invites-frontend',
            STREAMLAB_INVITES_PLUGIN_URL . 'assets/css/frontend.css',
            array(),
            STREAMLAB_INVITES_VERSION
        );
        
        wp_enqueue_script(
            'streamlab-invites-frontend',
            STREAMLAB_INVITES_PLUGIN_URL . 'assets/js/frontend.js',
            array('jquery'),
            STREAMLAB_INVITES_VERSION,
            true
        );
        
        wp_localize_script('streamlab-invites-frontend', 'streamlabInvites', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('streamlab_invites_nonce'),
            'errors' => array(
                'empty_code' => __('Please enter an invite code', 'streamlab-invites'),
                'invalid_code' => __('Invalid invite code', 'streamlab-invites'),
            )
        ));
    }
    
    /**
     * Plugin activation
     */
    public function activate() {
        global $wpdb;
        $charset_collate = $wpdb->get_charset_collate();
        
        // Create invite codes table
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $sql = "CREATE TABLE IF NOT EXISTS $table_name (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            code varchar(32) NOT NULL UNIQUE,
            uses int(11) DEFAULT 0,
            max_uses int(11) DEFAULT 2,
            status varchar(20) DEFAULT 'active',
            created_by bigint(20) DEFAULT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            used_at datetime DEFAULT NULL,
            used_by bigint(20) DEFAULT NULL,
            user_email varchar(255) DEFAULT NULL,
            notes text,
            PRIMARY KEY  (id),
            UNIQUE KEY code (code),
            KEY status (status),
            KEY used_by (used_by)
        ) $charset_collate;";
        
        // Create invite usage log table
        $log_table = $wpdb->prefix . 'streamlab_invite_log';
        
        $log_sql = "CREATE TABLE IF NOT EXISTS $log_table (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            code_id bigint(20) NOT NULL,
            code varchar(32) NOT NULL,
            user_id bigint(20) DEFAULT NULL,
            user_email varchar(255) DEFAULT NULL,
            action varchar(50) NOT NULL,
            ip_address varchar(45) DEFAULT NULL,
            user_agent text,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY code_id (code_id),
            KEY user_id (user_id),
            KEY action (action)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
        dbDelta($log_sql);
        
        // Set default options
        if (!get_option('streamlab_invites_enabled')) {
            add_option('streamlab_invites_enabled', 'yes');
            add_option('streamlab_invites_message', 'Please contact us for an invite access code.');
            add_option('streamlab_invites_locked_pages', array());
            add_option('streamlab_invites_allow_homepage', 'no');
            add_option('streamlab_invites_redirect_url', home_url());
            add_option('streamlab_invites_default_role', 'subscriber');
            add_option('streamlab_invites_code_length', 12);
            add_option('streamlab_invites_code_format', 'alphanumeric');
        }
        
        // Flush rewrite rules
        flush_rewrite_rules();
    }
    
    /**
     * Plugin deactivation
     */
    public function deactivate() {
        flush_rewrite_rules();
    }
}

/**
 * Initialize the plugin
 */
function streamlab_invites() {
    return StreamLab_Invites::get_instance();
}

// Start the plugin
streamlab_invites();
