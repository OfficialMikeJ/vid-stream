<?php
/**
 * Invite Access Control
 *
 * @package StreamLab_Invites
 */

if (!defined('ABSPATH')) {
    exit;
}

class StreamLab_Invite_Access_Control {
    
    /**
     * Constructor
     */
    public function __construct() {
        // Template redirect - check access
        add_action('template_redirect', array($this, 'check_access'), 1);
        
        // Add body class
        add_filter('body_class', array($this, 'add_body_class'));
    }
    
    /**
     * Check if invites are enabled
     */
    private function is_enabled() {
        return get_option('streamlab_invites_enabled', 'yes') === 'yes';
    }
    
    /**
     * Check if user has access
     */
    public function user_has_access() {
        // Admins always have access
        if (current_user_can('manage_options')) {
            return true;
        }
        
        // Logged in users with invite codes have access
        if (is_user_logged_in()) {
            $user_id = get_current_user_id();
            $has_invite = get_user_meta($user_id, '_streamlab_invited', true);
            return $has_invite === 'yes';
        }
        
        // Check session for verified code
        if (!session_id()) {
            session_start();
        }
        
        if (isset($_SESSION['streamlab_invite_verified'])) {
            // Code is valid for 1 hour
            $verified_time = intval($_SESSION['streamlab_invite_verified']);
            if (time() - $verified_time < 3600) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Check if page should be locked
     */
    private function should_lock_page() {
        // Don't lock admin pages
        if (is_admin()) {
            return false;
        }
        
        // Don't lock login/register pages
        if ($GLOBALS['pagenow'] === 'wp-login.php') {
            return false;
        }
        
        // Check if homepage should be accessible
        $allow_homepage = get_option('streamlab_invites_allow_homepage', 'no');
        if ($allow_homepage === 'yes' && is_front_page()) {
            return false;
        }
        
        // Check custom unlocked pages
        $unlocked_pages = get_option('streamlab_invites_unlocked_pages', array());
        $current_page_id = get_queried_object_id();
        
        if (in_array($current_page_id, $unlocked_pages)) {
            return false;
        }
        
        // Check if specific pages should be locked
        $locked_pages = get_option('streamlab_invites_locked_pages', array());
        if (!empty($locked_pages) && !in_array($current_page_id, $locked_pages)) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Check access on template redirect
     */
    public function check_access() {
        // Skip if not enabled
        if (!$this->is_enabled()) {
            return;
        }
        
        // Skip if user has access
        if ($this->user_has_access()) {
            return;
        }
        
        // Skip if page shouldn't be locked
        if (!$this->should_lock_page()) {
            return;
        }
        
        // Show invite gate
        $this->show_invite_gate();
        exit;
    }
    
    /**
     * Show invite gate
     */
    private function show_invite_gate() {
        // Get custom message
        $message = get_option('streamlab_invites_message', 'Please contact us for an invite access code.');
        $custom_css = get_option('streamlab_invites_custom_css', '');
        
        // Load theme header
        get_header();
        
        ?>
        <div class="streamlab-invite-gate" data-testid="invite-gate">
            <div class="streamlab-invite-container">
                <div class="streamlab-invite-content">
                    <div class="streamlab-invite-icon">
                        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="currentColor"/>
                        </svg>
                    </div>
                    
                    <h1 class="streamlab-invite-title"><?php _e('Invite Only Access', 'streamlab-invites'); ?></h1>
                    
                    <p class="streamlab-invite-message" data-testid="invite-message"><?php echo nl2br(esc_html($message)); ?></p>
                    
                    <div class="streamlab-invite-steps">
                        <div class="step-item">
                            <span class="step-number">1</span>
                            <span class="step-text"><?php _e('Paste your invite code', 'streamlab-invites'); ?></span>
                        </div>
                        <div class="step-item">
                            <span class="step-number">2</span>
                            <span class="step-text"><?php _e('Click Submit to verify', 'streamlab-invites'); ?></span>
                        </div>
                        <div class="step-item">
                            <span class="step-number">3</span>
                            <span class="step-text"><?php _e('Paste code again to complete registration', 'streamlab-invites'); ?></span>
                        </div>
                    </div>
                    
                    <form id="streamlab-invite-form" class="streamlab-invite-form" data-testid="invite-form">
                        <div class="streamlab-invite-input-group">
                            <label for="invite-code" class="streamlab-invite-label"><?php _e('Invite Code', 'streamlab-invites'); ?></label>
                            <input 
                                type="text" 
                                id="invite-code" 
                                name="invite_code" 
                                class="streamlab-invite-input" 
                                placeholder="XXX-XXX-XXX"
                                data-testid="invite-code-input"
                                required
                            >
                        </div>
                        
                        <div class="streamlab-invite-error" id="invite-error" style="display:none;" data-testid="invite-error"></div>
                        
                        <button type="submit" class="streamlab-invite-button" data-testid="verify-invite-button">
                            <span class="button-text"><?php _e('Submit', 'streamlab-invites'); ?></span>
                            <span class="button-loader" style="display:none;">
                                <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25"/>
                                    <path d="M12 2 A10 10 0 0 1 22 12" stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="round">
                                        <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                                    </path>
                                </svg>
                            </span>
                        </button>
                    </form>
                </div>
            </div>
        </div>
        
        <?php if ($custom_css) : ?>
        <style type="text/css">
            <?php echo wp_strip_all_tags($custom_css); ?>
        </style>
        <?php endif; ?>
        
        <?php
        // Load theme footer
        get_footer();
    }
    
    /**
     * Add body class
     */
    public function add_body_class($classes) {
        if ($this->is_enabled() && !$this->user_has_access() && $this->should_lock_page()) {
            $classes[] = 'streamlab-invite-locked';
        }
        return $classes;
    }
}