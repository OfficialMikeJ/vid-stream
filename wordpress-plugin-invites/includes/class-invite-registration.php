<?php
/**
 * Invite Registration Handler
 *
 * @package StreamLab_Invites
 */

if (!defined('ABSPATH')) {
    exit;
}

class StreamLab_Invite_Registration {
    
    /**
     * Constructor
     */
    public function __construct() {
        // Registration hooks
        add_action('user_register', array($this, 'on_user_register'));
        add_filter('registration_errors', array($this, 'validate_registration'), 10, 3);
        
        // Custom registration page
        add_action('init', array($this, 'handle_custom_registration'));
        add_shortcode('streamlab_register', array($this, 'registration_shortcode'));
    }
    
    /**
     * Validate registration with invite code
     */
    public function validate_registration($errors, $sanitized_user_login, $user_email) {
        // Check if invites are enabled
        if (get_option('streamlab_invites_enabled', 'yes') !== 'yes') {
            return $errors;
        }
        
        // Start session if not started
        if (!session_id()) {
            session_start();
        }
        
        // Check if code is verified in session
        if (!isset($_SESSION['streamlab_invite_code']) || !isset($_SESSION['streamlab_invite_verified'])) {
            $errors->add('invite_required', __('A valid invite code is required to register.', 'streamlab-invites'));
            return $errors;
        }
        
        // Verify code is still valid (within 1 hour)
        $verified_time = intval($_SESSION['streamlab_invite_verified']);
        if (time() - $verified_time > 3600) {
            $errors->add('invite_expired', __('Your invite code has expired. Please verify again.', 'streamlab-invites'));
            unset($_SESSION['streamlab_invite_code']);
            unset($_SESSION['streamlab_invite_verified']);
            return $errors;
        }
        
        return $errors;
    }
    
    /**
     * Process registration - use invite code
     */
    public function on_user_register($user_id) {
        // Check if invites are enabled
        if (get_option('streamlab_invites_enabled', 'yes') !== 'yes') {
            return;
        }
        
        // Start session if not started
        if (!session_id()) {
            session_start();
        }
        
        // Get invite code from session
        if (!isset($_SESSION['streamlab_invite_code'])) {
            return;
        }
        
        $code = $_SESSION['streamlab_invite_code'];
        $user = get_userdata($user_id);
        
        // Use the invite code (second use - registration)
        $code_manager = new StreamLab_Invite_Code_Manager();
        $result = $code_manager->use_code($code, $user_id, $user->user_email);
        
        if ($result['success']) {
            // Mark user as invited
            update_user_meta($user_id, '_streamlab_invited', 'yes');
            update_user_meta($user_id, '_streamlab_invite_code', $code);
            
            // Set custom role if configured
            $default_role = get_option('streamlab_invites_default_role', 'subscriber');
            if ($default_role && $default_role !== 'subscriber') {
                $user = new WP_User($user_id);
                $user->set_role($default_role);
            }
            
            // Clear session
            unset($_SESSION['streamlab_invite_code']);
            unset($_SESSION['streamlab_invite_verified']);
        }
    }
    
    /**
     * Handle custom registration
     */
    public function handle_custom_registration() {
        if (!isset($_POST['streamlab_register_submit'])) {
            return;
        }
        
        // Verify nonce
        if (!isset($_POST['streamlab_register_nonce']) || !wp_verify_nonce($_POST['streamlab_register_nonce'], 'streamlab_register')) {
            return;
        }
        
        $username = isset($_POST['username']) ? sanitize_user($_POST['username']) : '';
        $email = isset($_POST['email']) ? sanitize_email($_POST['email']) : '';
        $password = isset($_POST['password']) ? $_POST['password'] : '';
        
        $errors = array();
        
        // Validate
        if (empty($username)) {
            $errors[] = __('Username is required', 'streamlab-invites');
        }
        if (username_exists($username)) {
            $errors[] = __('Username already exists', 'streamlab-invites');
        }
        if (!is_email($email)) {
            $errors[] = __('Invalid email address', 'streamlab-invites');
        }
        if (email_exists($email)) {
            $errors[] = __('Email already registered', 'streamlab-invites');
        }
        if (strlen($password) < 6) {
            $errors[] = __('Password must be at least 6 characters', 'streamlab-invites');
        }
        
        // Check invite code
        if (!session_id()) {
            session_start();
        }
        if (!isset($_SESSION['streamlab_invite_code'])) {
            $errors[] = __('No valid invite code found', 'streamlab-invites');
        }
        
        if (empty($errors)) {
            // Create user
            $user_id = wp_create_user($username, $password, $email);
            
            if (!is_wp_error($user_id)) {
                // Auto login
                wp_set_auth_cookie($user_id);
                
                // Redirect to home or custom page
                $redirect = get_option('streamlab_invites_redirect_url', home_url());
                wp_redirect($redirect);
                exit;
            } else {
                $errors[] = $user_id->get_error_message();
            }
        }
        
        // Store errors for display
        set_transient('streamlab_register_errors_' . session_id(), $errors, 60);
    }
    
    /**
     * Registration shortcode
     */
    public function registration_shortcode($atts) {
        // Check if user is logged in
        if (is_user_logged_in()) {
            return '<p>' . __('You are already registered and logged in.', 'streamlab-invites') . '</p>';
        }
        
        // Check for invite code in session
        if (!session_id()) {
            session_start();
        }
        
        if (!isset($_SESSION['streamlab_invite_code'])) {
            return '<p>' . __('Please enter a valid invite code first.', 'streamlab-invites') . '</p>';
        }
        
        // Get errors if any
        $errors = get_transient('streamlab_register_errors_' . session_id());
        if ($errors) {
            delete_transient('streamlab_register_errors_' . session_id());
        }
        
        ob_start();
        ?>
        <div class="streamlab-register-form" data-testid="registration-form">
            <h2><?php _e('Create Your Account', 'streamlab-invites'); ?></h2>
            
            <?php if (!empty($errors)) : ?>
                <div class="streamlab-errors" data-testid="registration-errors">
                    <?php foreach ($errors as $error) : ?>
                        <p class="error"><?php echo esc_html($error); ?></p>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
            
            <form method="post" action="">
                <?php wp_nonce_field('streamlab_register', 'streamlab_register_nonce'); ?>
                
                <p class="streamlab-form-field">
                    <label for="username"><?php _e('Username', 'streamlab-invites'); ?> *</label>
                    <input type="text" name="username" id="username" required data-testid="registration-username">
                </p>
                
                <p class="streamlab-form-field">
                    <label for="email"><?php _e('Email', 'streamlab-invites'); ?> *</label>
                    <input type="email" name="email" id="email" required data-testid="registration-email">
                </p>
                
                <p class="streamlab-form-field">
                    <label for="password"><?php _e('Password', 'streamlab-invites'); ?> *</label>
                    <input type="password" name="password" id="password" required data-testid="registration-password">
                    <small><?php _e('Minimum 6 characters', 'streamlab-invites'); ?></small>
                </p>
                
                <p class="streamlab-form-field">
                    <button type="submit" name="streamlab_register_submit" class="streamlab-submit-button" data-testid="registration-submit">
                        <?php _e('Register', 'streamlab-invites'); ?>
                    </button>
                </p>
            </form>
        </div>
        <?php
        return ob_get_clean();
    }
}