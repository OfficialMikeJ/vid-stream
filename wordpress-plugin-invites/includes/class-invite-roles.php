<?php
/**
 * Invite Roles Manager
 *
 * @package StreamLab_Invites
 */

if (!defined('ABSPATH')) {
    exit;
}

class StreamLab_Invite_Roles {
    
    /**
     * Constructor
     */
    public function __construct() {
        // Add role management hooks if needed
        add_action('init', array($this, 'init_roles'));
    }
    
    /**
     * Initialize roles
     */
    public function init_roles() {
        // Can add custom role on plugin activation if needed
        // For now, using WordPress default roles
    }
    
    /**
     * Get invited users by role
     */
    public function get_invited_users_by_role($role) {
        return get_users(array(
            'role' => $role,
            'meta_key' => '_streamlab_invited',
            'meta_value' => 'yes'
        ));
    }
    
    /**
     * Check if user is invited
     */
    public function is_invited_user($user_id) {
        return get_user_meta($user_id, '_streamlab_invited', true) === 'yes';
    }
    
    /**
     * Get user's invite code
     */
    public function get_user_invite_code($user_id) {
        return get_user_meta($user_id, '_streamlab_invite_code', true);
    }
}