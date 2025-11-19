<?php
/**
 * Invite Code Manager
 *
 * @package StreamLab_Invites
 */

if (!defined('ABSPATH')) {
    exit;
}

class StreamLab_Invite_Code_Manager {
    
    /**
     * Constructor
     */
    public function __construct() {
        // AJAX handlers
        add_action('wp_ajax_streamlab_generate_code', array($this, 'ajax_generate_code'));
        add_action('wp_ajax_streamlab_verify_code', array($this, 'ajax_verify_code'));
        add_action('wp_ajax_streamlab_delete_code', array($this, 'ajax_delete_code'));
        add_action('wp_ajax_streamlab_revoke_code', array($this, 'ajax_revoke_code'));
        
        // Frontend AJAX (no auth required)
        add_action('wp_ajax_nopriv_streamlab_verify_code', array($this, 'ajax_verify_code_frontend'));
    }
    
    /**
     * Generate invite code
     */
    public function generate_code($created_by = null, $notes = '') {
        $code_length = get_option('streamlab_invites_code_length', 12);
        $code_format = get_option('streamlab_invites_code_format', 'alphanumeric');
        
        // Generate unique code
        $code = $this->create_unique_code($code_length, $code_format);
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $result = $wpdb->insert(
            $table_name,
            array(
                'code' => $code,
                'uses' => 0,
                'max_uses' => 2,
                'status' => 'active',
                'created_by' => $created_by ?: get_current_user_id(),
                'notes' => $notes
            ),
            array('%s', '%d', '%d', '%s', '%d', '%s')
        );
        
        if ($result) {
            $this->log_action($wpdb->insert_id, $code, null, null, 'generated');
            return array(
                'success' => true,
                'code' => $code,
                'id' => $wpdb->insert_id
            );
        }
        
        return array(
            'success' => false,
            'message' => 'Failed to generate code'
        );
    }
    
    /**
     * Create unique code
     */
    private function create_unique_code($length, $format) {
        $attempts = 0;
        $max_attempts = 10;
        
        do {
            $code = $this->generate_random_code($length, $format);
            $exists = $this->code_exists($code);
            $attempts++;
        } while ($exists && $attempts < $max_attempts);
        
        return $code;
    }
    
    /**
     * Generate random code
     */
    private function generate_random_code($length, $format) {
        switch ($format) {
            case 'numeric':
                $characters = '0123456789';
                break;
            case 'alpha':
                $characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'; // Exclude confusing letters
                break;
            case 'alphanumeric':
            default:
                $characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789';
                break;
        }
        
        $code = '';
        $max = strlen($characters) - 1;
        
        for ($i = 0; $i < $length; $i++) {
            $code .= $characters[random_int(0, $max)];
        }
        
        // Format as XXX-XXX-XXX for readability
        if ($length >= 9) {
            $formatted = substr($code, 0, 3) . '-' . substr($code, 3, 3) . '-' . substr($code, 6);
            return $formatted;
        }
        
        return $code;
    }
    
    /**
     * Check if code exists
     */
    private function code_exists($code) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $count = $wpdb->get_var(
            $wpdb->prepare(
                "SELECT COUNT(*) FROM $table_name WHERE code = %s",
                $code
            )
        );
        
        return $count > 0;
    }
    
    /**
     * Verify invite code
     */
    public function verify_code($code) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $invite = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE code = %s",
                $code
            ),
            ARRAY_A
        );
        
        if (!$invite) {
            return array(
                'success' => false,
                'message' => 'Invalid invite code'
            );
        }
        
        if ($invite['status'] !== 'active') {
            return array(
                'success' => false,
                'message' => 'This invite code is no longer active'
            );
        }
        
        if ($invite['uses'] >= $invite['max_uses']) {
            return array(
                'success' => false,
                'message' => 'This invite code has been fully used'
            );
        }
        
        return array(
            'success' => true,
            'code' => $invite,
            'remaining_uses' => $invite['max_uses'] - $invite['uses']
        );
    }
    
    /**
     * Use invite code (increment usage)
     */
    public function use_code($code, $user_id = null, $user_email = null) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        // Verify code first
        $verification = $this->verify_code($code);
        if (!$verification['success']) {
            return $verification;
        }
        
        $invite = $verification['code'];
        
        // Increment uses
        $new_uses = $invite['uses'] + 1;
        $new_status = $new_uses >= $invite['max_uses'] ? 'used' : 'active';
        
        $update_data = array(
            'uses' => $new_uses,
            'status' => $new_status
        );
        
        // If fully used, record final user
        if ($new_status === 'used') {
            $update_data['used_at'] = current_time('mysql');
            $update_data['used_by'] = $user_id;
            $update_data['user_email'] = $user_email;
        }
        
        $result = $wpdb->update(
            $table_name,
            $update_data,
            array('id' => $invite['id']),
            array('%d', '%s', '%s', '%d', '%s'),
            array('%d')
        );
        
        if ($result !== false) {
            $this->log_action($invite['id'], $code, $user_id, $user_email, 'used');
            
            return array(
                'success' => true,
                'remaining_uses' => $invite['max_uses'] - $new_uses,
                'fully_used' => $new_status === 'used'
            );
        }
        
        return array(
            'success' => false,
            'message' => 'Failed to use code'
        );
    }
    
    /**
     * Get all invite codes
     */
    public function get_all_codes($status = 'all', $limit = 100, $offset = 0) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $where = '';
        if ($status !== 'all') {
            $where = $wpdb->prepare(" WHERE status = %s", $status);
        }
        
        $query = "SELECT * FROM $table_name{$where} ORDER BY created_at DESC LIMIT %d OFFSET %d";
        
        return $wpdb->get_results(
            $wpdb->prepare($query, $limit, $offset),
            ARRAY_A
        );
    }
    
    /**
     * Get code by ID
     */
    public function get_code_by_id($id) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        return $wpdb->get_row(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE id = %d",
                $id
            ),
            ARRAY_A
        );
    }
    
    /**
     * Delete invite code
     */
    public function delete_code($id) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $code_data = $this->get_code_by_id($id);
        if (!$code_data) {
            return false;
        }
        
        $result = $wpdb->delete(
            $table_name,
            array('id' => $id),
            array('%d')
        );
        
        if ($result) {
            $this->log_action($id, $code_data['code'], null, null, 'deleted');
        }
        
        return $result !== false;
    }
    
    /**
     * Revoke invite code
     */
    public function revoke_code($id) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $code_data = $this->get_code_by_id($id);
        if (!$code_data) {
            return false;
        }
        
        $result = $wpdb->update(
            $table_name,
            array('status' => 'revoked'),
            array('id' => $id),
            array('%s'),
            array('%d')
        );
        
        if ($result !== false) {
            $this->log_action($id, $code_data['code'], null, null, 'revoked');
        }
        
        return $result !== false;
    }
    
    /**
     * Get code statistics
     */
    public function get_statistics() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'streamlab_invite_codes';
        
        $stats = $wpdb->get_row(
            "SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'used' THEN 1 ELSE 0 END) as used,
                SUM(CASE WHEN status = 'revoked' THEN 1 ELSE 0 END) as revoked,
                SUM(uses) as total_uses
            FROM $table_name",
            ARRAY_A
        );
        
        return $stats;
    }
    
    /**
     * Log action
     */
    private function log_action($code_id, $code, $user_id, $user_email, $action) {
        global $wpdb;
        $log_table = $wpdb->prefix . 'streamlab_invite_log';
        
        $wpdb->insert(
            $log_table,
            array(
                'code_id' => $code_id,
                'code' => $code,
                'user_id' => $user_id,
                'user_email' => $user_email,
                'action' => $action,
                'ip_address' => $_SERVER['REMOTE_ADDR'] ?? null,
                'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? null
            ),
            array('%d', '%s', '%d', '%s', '%s', '%s', '%s')
        );
    }
    
    /**
     * AJAX: Generate code
     */
    public function ajax_generate_code() {
        check_ajax_referer('streamlab_invites_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }
        
        $notes = isset($_POST['notes']) ? sanitize_textarea_field($_POST['notes']) : '';
        $result = $this->generate_code(get_current_user_id(), $notes);
        
        if ($result['success']) {
            wp_send_json_success($result);
        } else {
            wp_send_json_error($result);
        }
    }
    
    /**
     * AJAX: Verify code (admin)
     */
    public function ajax_verify_code() {
        check_ajax_referer('streamlab_invites_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }
        
        $code = isset($_POST['code']) ? sanitize_text_field($_POST['code']) : '';
        $result = $this->verify_code($code);
        
        wp_send_json($result);
    }
    
    /**
     * AJAX: Verify code (frontend)
     */
    public function ajax_verify_code_frontend() {
        check_ajax_referer('streamlab_invites_nonce', 'nonce');
        
        $code = isset($_POST['code']) ? sanitize_text_field($_POST['code']) : '';
        $result = $this->verify_code($code);
        
        if ($result['success']) {
            // Store code in session for registration
            if (!session_id()) {
                session_start();
            }
            $_SESSION['streamlab_invite_code'] = $code;
            $_SESSION['streamlab_invite_verified'] = time();
        }
        
        wp_send_json($result);
    }
    
    /**
     * AJAX: Delete code
     */
    public function ajax_delete_code() {
        check_ajax_referer('streamlab_invites_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }
        
        $id = isset($_POST['id']) ? intval($_POST['id']) : 0;
        $result = $this->delete_code($id);
        
        if ($result) {
            wp_send_json_success(array('message' => 'Code deleted successfully'));
        } else {
            wp_send_json_error(array('message' => 'Failed to delete code'));
        }
    }
    
    /**
     * AJAX: Revoke code
     */
    public function ajax_revoke_code() {
        check_ajax_referer('streamlab_invites_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }
        
        $id = isset($_POST['id']) ? intval($_POST['id']) : 0;
        $result = $this->revoke_code($id);
        
        if ($result) {
            wp_send_json_success(array('message' => 'Code revoked successfully'));
        } else {
            wp_send_json_error(array('message' => 'Failed to revoke code'));
        }
    }
}