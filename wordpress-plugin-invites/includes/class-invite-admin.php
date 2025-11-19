<?php
/**
 * Invite Admin Interface
 *
 * @package StreamLab_Invites
 */

if (!defined('ABSPATH')) {
    exit;
}

class StreamLab_Invite_Admin {
    
    /**
     * Code manager instance
     */
    private $code_manager;
    
    /**
     * Constructor
     */
    public function __construct() {
        $this->code_manager = new StreamLab_Invite_Code_Manager();
        
        add_action('admin_menu', array($this, 'add_menu_pages'));
        add_action('admin_init', array($this, 'register_settings'));
    }
    
    /**
     * Add menu pages
     */
    public function add_menu_pages() {
        add_menu_page(
            __('StreamLab Invites', 'streamlab-invites'),
            __('Invites', 'streamlab-invites'),
            'manage_options',
            'streamlab-invites',
            array($this, 'admin_page'),
            'dashicons-tickets-alt',
            30
        );
    }
    
    /**
     * Register settings
     */
    public function register_settings() {
        // General settings
        register_setting('streamlab_invites_general', 'streamlab_invites_enabled');
        register_setting('streamlab_invites_general', 'streamlab_invites_message');
        register_setting('streamlab_invites_general', 'streamlab_invites_allow_homepage');
        register_setting('streamlab_invites_general', 'streamlab_invites_redirect_url');
        register_setting('streamlab_invites_general', 'streamlab_invites_default_role');
        
        // Code settings
        register_setting('streamlab_invites_codes', 'streamlab_invites_code_length');
        register_setting('streamlab_invites_codes', 'streamlab_invites_code_format');
        
        // Page settings
        register_setting('streamlab_invites_pages', 'streamlab_invites_locked_pages');
        register_setting('streamlab_invites_pages', 'streamlab_invites_unlocked_pages');
        
        // Style settings
        register_setting('streamlab_invites_style', 'streamlab_invites_custom_css');
    }
    
    /**
     * Main admin page
     */
    public function admin_page() {
        $active_tab = isset($_GET['tab']) ? sanitize_text_field($_GET['tab']) : 'generate';
        
        ?>
        <div class="wrap streamlab-invites-admin">
            <h1><?php _e('StreamLab Invites', 'streamlab-invites'); ?></h1>
            
            <nav class="nav-tab-wrapper">
                <a href="?page=streamlab-invites&tab=generate" class="nav-tab <?php echo $active_tab === 'generate' ? 'nav-tab-active' : ''; ?>" data-testid="tab-generate">
                    <?php _e('Generate Codes', 'streamlab-invites'); ?>
                </a>
                <a href="?page=streamlab-invites&tab=manage" class="nav-tab <?php echo $active_tab === 'manage' ? 'nav-tab-active' : ''; ?>" data-testid="tab-manage">
                    <?php _e('Manage Codes', 'streamlab-invites'); ?>
                </a>
                <a href="?page=streamlab-invites&tab=settings" class="nav-tab <?php echo $active_tab === 'settings' ? 'nav-tab-active' : ''; ?>" data-testid="tab-settings">
                    <?php _e('Settings', 'streamlab-invites'); ?>
                </a>
                <a href="?page=streamlab-invites&tab=logs" class="nav-tab <?php echo $active_tab === 'logs' ? 'nav-tab-active' : ''; ?>" data-testid="tab-logs">
                    <?php _e('Activity Log', 'streamlab-invites'); ?>
                </a>
                <a href="?page=streamlab-invites&tab=roles" class="nav-tab <?php echo $active_tab === 'roles' ? 'nav-tab-active' : ''; ?>" data-testid="tab-roles">
                    <?php _e('Roles & Permissions', 'streamlab-invites'); ?>
                </a>
            </nav>
            
            <div class="streamlab-invites-content">
                <?php
                switch ($active_tab) {
                    case 'generate':
                        $this->render_generate_tab();
                        break;
                    case 'manage':
                        $this->render_manage_tab();
                        break;
                    case 'settings':
                        $this->render_settings_tab();
                        break;
                    case 'logs':
                        $this->render_logs_tab();
                        break;
                    case 'roles':
                        $this->render_roles_tab();
                        break;
                }
                ?>
            </div>
        </div>
        <?php
    }
    
    /**
     * Render Generate tab
     */
    private function render_generate_tab() {
        $stats = $this->code_manager->get_statistics();
        ?>
        <div class="streamlab-tab-content">
            <div class="streamlab-stats-grid">
                <div class="streamlab-stat-card">
                    <div class="stat-icon" style="background: #4f46e5;">
                        <span class="dashicons dashicons-tickets-alt"></span>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label"><?php _e('Total Codes', 'streamlab-invites'); ?></div>
                        <div class="stat-value" data-testid="stat-total"><?php echo esc_html($stats['total'] ?: 0); ?></div>
                    </div>
                </div>
                
                <div class="streamlab-stat-card">
                    <div class="stat-icon" style="background: #10b981;">
                        <span class="dashicons dashicons-yes-alt"></span>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label"><?php _e('Active Codes', 'streamlab-invites'); ?></div>
                        <div class="stat-value" data-testid="stat-active"><?php echo esc_html($stats['active'] ?: 0); ?></div>
                    </div>
                </div>
                
                <div class="streamlab-stat-card">
                    <div class="stat-icon" style="background: #f59e0b;">
                        <span class="dashicons dashicons-admin-users"></span>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label"><?php _e('Used Codes', 'streamlab-invites'); ?></div>
                        <div class="stat-value" data-testid="stat-used"><?php echo esc_html($stats['used'] ?: 0); ?></div>
                    </div>
                </div>
                
                <div class="streamlab-stat-card">
                    <div class="stat-icon" style="background: #ef4444;">
                        <span class="dashicons dashicons-dismiss"></span>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label"><?php _e('Revoked', 'streamlab-invites'); ?></div>
                        <div class="stat-value" data-testid="stat-revoked"><?php echo esc_html($stats['revoked'] ?: 0); ?></div>
                    </div>
                </div>
            </div>
            
            <div class="streamlab-generate-section">
                <h2><?php _e('Generate New Invite Code', 'streamlab-invites'); ?></h2>
                <p class="description"><?php _e('Generate a new invite code that can be used twice: once to access the registration page and once to complete registration.', 'streamlab-invites'); ?></p>
                
                <div class="streamlab-generate-form">
                    <div class="form-field">
                        <label for="code-notes"><?php _e('Notes (Optional)', 'streamlab-invites'); ?></label>
                        <textarea id="code-notes" rows="3" placeholder="<?php _e('e.g., Code for John Doe', 'streamlab-invites'); ?>" data-testid="code-notes"></textarea>
                    </div>
                    
                    <button type="button" id="generate-code-btn" class="button button-primary button-hero" data-testid="generate-code-button">
                        <span class="dashicons dashicons-plus-alt"></span>
                        <?php _e('Generate Invite Code', 'streamlab-invites'); ?>
                    </button>
                </div>
                
                <div id="generated-code-display" class="streamlab-code-display" style="display:none;" data-testid="generated-code-display">
                    <div class="code-success-icon">
                        <span class="dashicons dashicons-yes-alt"></span>
                    </div>
                    <h3><?php _e('Invite Code Generated!', 'streamlab-invites'); ?></h3>
                    <div class="generated-code" id="generated-code-value" data-testid="generated-code-value"></div>
                    <button type="button" class="button" id="copy-code-btn" data-testid="copy-code-button">
                        <span class="dashicons dashicons-clipboard"></span>
                        <?php _e('Copy Code', 'streamlab-invites'); ?>
                    </button>
                    <p class="code-info"><?php _e('Share this code with the person you want to invite. The code can be used twice.', 'streamlab-invites'); ?></p>
                </div>
            </div>
        </div>
        <?php
    }
    
    /**
     * Render Manage tab
     */
    private function render_manage_tab() {
        $status = isset($_GET['status']) ? sanitize_text_field($_GET['status']) : 'all';
        $codes = $this->code_manager->get_all_codes($status);
        
        ?>
        <div class="streamlab-tab-content">
            <div class="streamlab-manage-header">
                <h2><?php _e('Manage Invite Codes', 'streamlab-invites'); ?></h2>
                
                <div class="filter-buttons">
                    <a href="?page=streamlab-invites&tab=manage&status=all" class="button <?php echo $status === 'all' ? 'button-primary' : ''; ?>"><?php _e('All', 'streamlab-invites'); ?></a>
                    <a href="?page=streamlab-invites&tab=manage&status=active" class="button <?php echo $status === 'active' ? 'button-primary' : ''; ?>"><?php _e('Active', 'streamlab-invites'); ?></a>
                    <a href="?page=streamlab-invites&tab=manage&status=used" class="button <?php echo $status === 'used' ? 'button-primary' : ''; ?>"><?php _e('Used', 'streamlab-invites'); ?></a>
                    <a href="?page=streamlab-invites&tab=manage&status=revoked" class="button <?php echo $status === 'revoked' ? 'button-primary' : ''; ?>"><?php _e('Revoked', 'streamlab-invites'); ?></a>
                </div>
            </div>
            
            <table class="wp-list-table widefat fixed striped" data-testid="codes-table">
                <thead>
                    <tr>
                        <th><?php _e('Code', 'streamlab-invites'); ?></th>
                        <th><?php _e('Status', 'streamlab-invites'); ?></th>
                        <th><?php _e('Uses', 'streamlab-invites'); ?></th>
                        <th><?php _e('Registered User', 'streamlab-invites'); ?></th>
                        <th><?php _e('Created', 'streamlab-invites'); ?></th>
                        <th><?php _e('Notes', 'streamlab-invites'); ?></th>
                        <th><?php _e('Actions', 'streamlab-invites'); ?></th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($codes)) : ?>
                        <tr>
                            <td colspan="7" style="text-align:center;"><?php _e('No invite codes found.', 'streamlab-invites'); ?></td>
                        </tr>
                    <?php else : ?>
                        <?php foreach ($codes as $code) : ?>
                            <tr data-code-id="<?php echo esc_attr($code['id']); ?>">
                                <td>
                                    <code class="streamlab-code" data-testid="code-value"><?php echo esc_html($code['code']); ?></code>
                                </td>
                                <td>
                                    <span class="status-badge status-<?php echo esc_attr($code['status']); ?>" data-testid="code-status">
                                        <?php echo esc_html(ucfirst($code['status'])); ?>
                                    </span>
                                </td>
                                <td>
                                    <span class="uses-indicator" data-testid="code-uses">
                                        <?php echo esc_html($code['uses'] . '/' . $code['max_uses']); ?>
                                    </span>
                                </td>
                                <td>
                                    <?php if ($code['user_email']) : ?>
                                        <span data-testid="code-user"><?php echo esc_html($code['user_email']); ?></span>
                                    <?php else : ?>
                                        <span style="color: #999;">&mdash;</span>
                                    <?php endif; ?>
                                </td>
                                <td><?php echo esc_html(date_i18n(get_option('date_format'), strtotime($code['created_at']))); ?></td>
                                <td>
                                    <?php if ($code['notes']) : ?>
                                        <span title="<?php echo esc_attr($code['notes']); ?>" data-testid="code-notes">
                                            <?php echo esc_html(wp_trim_words($code['notes'], 5)); ?>
                                        </span>
                                    <?php else : ?>
                                        <span style="color: #999;">&mdash;</span>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <?php if ($code['status'] === 'active') : ?>
                                        <button class="button button-small revoke-code" data-code-id="<?php echo esc_attr($code['id']); ?>" data-testid="revoke-code-button">
                                            <?php _e('Revoke', 'streamlab-invites'); ?>
                                        </button>
                                    <?php endif; ?>
                                    <button class="button button-small button-link-delete delete-code" data-code-id="<?php echo esc_attr($code['id']); ?>" data-testid="delete-code-button">
                                        <?php _e('Delete', 'streamlab-invites'); ?>
                                    </button>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
        <?php
    }
    
    /**
     * Render Settings tab
     */
    private function render_settings_tab() {
        ?>
        <div class="streamlab-tab-content">
            <form method="post" action="options.php">
                <?php settings_fields('streamlab_invites_general'); ?>
                
                <h2><?php _e('General Settings', 'streamlab-invites'); ?></h2>
                
                <table class="form-table">
                    <tr>
                        <th scope="row"><?php _e('Enable Invite System', 'streamlab-invites'); ?></th>
                        <td>
                            <label>
                                <input type="checkbox" name="streamlab_invites_enabled" value="yes" <?php checked(get_option('streamlab_invites_enabled', 'yes'), 'yes'); ?> data-testid="enable-invites">
                                <?php _e('Lock the website and require invite codes', 'streamlab-invites'); ?>
                            </label>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row"><?php _e('Invite Gate Message', 'streamlab-invites'); ?></th>
                        <td>
                            <textarea name="streamlab_invites_message" class="large-text" rows="3" data-testid="invite-message"><?php echo esc_textarea(get_option('streamlab_invites_message', 'Please paste your invite code and click "Submit", paste your invite code once more to finish registration for full access.')); ?></textarea>
                            <p class="description"><?php _e('Message displayed to users without an invite code (supports multi-line)', 'streamlab-invites'); ?></p>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row"><?php _e('Allow Homepage Access', 'streamlab-invites'); ?></th>
                        <td>
                            <label>
                                <input type="checkbox" name="streamlab_invites_allow_homepage" value="yes" <?php checked(get_option('streamlab_invites_allow_homepage', 'no'), 'yes'); ?> data-testid="allow-homepage">
                                <?php _e('Allow access to homepage without invite code', 'streamlab-invites'); ?>
                            </label>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row"><?php _e('Redirect After Registration', 'streamlab-invites'); ?></th>
                        <td>
                            <input type="url" name="streamlab_invites_redirect_url" value="<?php echo esc_attr(get_option('streamlab_invites_redirect_url', home_url())); ?>" class="large-text" data-testid="redirect-url">
                            <p class="description"><?php _e('URL to redirect users after successful registration', 'streamlab-invites'); ?></p>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row"><?php _e('Default User Role', 'streamlab-invites'); ?></th>
                        <td>
                            <select name="streamlab_invites_default_role" data-testid="default-role">
                                <?php
                                $roles = wp_roles()->get_names();
                                $current_role = get_option('streamlab_invites_default_role', 'subscriber');
                                foreach ($roles as $role_key => $role_name) :
                                ?>
                                    <option value="<?php echo esc_attr($role_key); ?>" <?php selected($current_role, $role_key); ?>>
                                        <?php echo esc_html($role_name); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                            <p class="description"><?php _e('Role assigned to users who register with invite code', 'streamlab-invites'); ?></p>
                        </td>
                    </tr>
                </table>
                
                <h2><?php _e('Code Settings', 'streamlab-invites'); ?></h2>
                
                <table class="form-table">
                    <tr>
                        <th scope="row"><?php _e('Code Length', 'streamlab-invites'); ?></th>
                        <td>
                            <input type="number" name="streamlab_invites_code_length" value="<?php echo esc_attr(get_option('streamlab_invites_code_length', 12)); ?>" min="6" max="32" data-testid="code-length">
                            <p class="description"><?php _e('Number of characters in invite code (6-32)', 'streamlab-invites'); ?></p>
                        </td>
                    </tr>
                    
                    <tr>
                        <th scope="row"><?php _e('Code Format', 'streamlab-invites'); ?></th>
                        <td>
                            <select name="streamlab_invites_code_format" data-testid="code-format">
                                <option value="alphanumeric" <?php selected(get_option('streamlab_invites_code_format', 'alphanumeric'), 'alphanumeric'); ?>><?php _e('Alphanumeric (Letters + Numbers)', 'streamlab-invites'); ?></option>
                                <option value="alpha" <?php selected(get_option('streamlab_invites_code_format'), 'alpha'); ?>><?php _e('Letters Only', 'streamlab-invites'); ?></option>
                                <option value="numeric" <?php selected(get_option('streamlab_invites_code_format'), 'numeric'); ?>><?php _e('Numbers Only', 'streamlab-invites'); ?></option>
                            </select>
                        </td>
                    </tr>
                </table>
                
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }
    
    /**
     * Render Logs tab
     */
    private function render_logs_tab() {
        global $wpdb;
        $log_table = $wpdb->prefix . 'streamlab_invite_log';
        
        $logs = $wpdb->get_results(
            "SELECT * FROM $log_table ORDER BY created_at DESC LIMIT 100",
            ARRAY_A
        );
        
        ?>
        <div class="streamlab-tab-content">
            <h2><?php _e('Activity Log', 'streamlab-invites'); ?></h2>
            <p class="description"><?php _e('Recent invite code activity and usage history', 'streamlab-invites'); ?></p>
            
            <table class="wp-list-table widefat fixed striped" data-testid="activity-log-table">
                <thead>
                    <tr>
                        <th><?php _e('Date/Time', 'streamlab-invites'); ?></th>
                        <th><?php _e('Code', 'streamlab-invites'); ?></th>
                        <th><?php _e('Action', 'streamlab-invites'); ?></th>
                        <th><?php _e('User', 'streamlab-invites'); ?></th>
                        <th><?php _e('IP Address', 'streamlab-invites'); ?></th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($logs)) : ?>
                        <tr>
                            <td colspan="5" style="text-align:center;"><?php _e('No activity logged yet.', 'streamlab-invites'); ?></td>
                        </tr>
                    <?php else : ?>
                        <?php foreach ($logs as $log) : ?>
                            <tr>
                                <td><?php echo esc_html(date_i18n(get_option('date_format') . ' ' . get_option('time_format'), strtotime($log['created_at']))); ?></td>
                                <td><code><?php echo esc_html($log['code']); ?></code></td>
                                <td>
                                    <span class="action-badge action-<?php echo esc_attr($log['action']); ?>" data-testid="log-action">
                                        <?php echo esc_html(ucfirst($log['action'])); ?>
                                    </span>
                                </td>
                                <td>
                                    <?php if ($log['user_email']) : ?>
                                        <?php echo esc_html($log['user_email']); ?>
                                    <?php else : ?>
                                        <span style="color: #999;">&mdash;</span>
                                    <?php endif; ?>
                                </td>
                                <td><code><?php echo esc_html($log['ip_address'] ?: '—'); ?></code></td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
        <?php
    }
    
    /**
     * Render Roles tab
     */
    private function render_roles_tab() {
        ?>
        <div class="streamlab-tab-content">
            <h2><?php _e('Roles & Permissions', 'streamlab-invites'); ?></h2>
            <p class="description"><?php _e('Manage user roles and permissions for invited users', 'streamlab-invites'); ?></p>
            
            <div class="streamlab-roles-info">
                <div class="info-box">
                    <span class="dashicons dashicons-info"></span>
                    <div>
                        <h3><?php _e('Current Role Configuration', 'streamlab-invites'); ?></h3>
                        <p><?php _e('Users who register with an invite code will be assigned the role configured in Settings tab.', 'streamlab-invites'); ?></p>
                        <p><strong><?php _e('Current Default Role:', 'streamlab-invites'); ?></strong> 
                            <?php
                            $current_role = get_option('streamlab_invites_default_role', 'subscriber');
                            $roles = wp_roles()->get_names();
                            echo esc_html($roles[$current_role] ?? 'Subscriber');
                            ?>
                        </p>
                    </div>
                </div>
                
                <h3><?php _e('Available Roles', 'streamlab-invites'); ?></h3>
                <table class="wp-list-table widefat fixed striped">
                    <thead>
                        <tr>
                            <th><?php _e('Role', 'streamlab-invites'); ?></th>
                            <th><?php _e('Capabilities', 'streamlab-invites'); ?></th>
                            <th><?php _e('Invited Users', 'streamlab-invites'); ?></th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php
                        $all_roles = wp_roles()->get_names();
                        foreach ($all_roles as $role_key => $role_name) :
                            $role = get_role($role_key);
                            $user_count = count(get_users(array(
                                'role' => $role_key,
                                'meta_key' => '_streamlab_invited',
                                'meta_value' => 'yes'
                            )));
                        ?>
                            <tr>
                                <td><strong><?php echo esc_html($role_name); ?></strong></td>
                                <td>
                                    <span class="capabilities-count">
                                        <?php printf(__('%d capabilities', 'streamlab-invites'), count($role->capabilities)); ?>
                                    </span>
                                </td>
                                <td><?php echo esc_html($user_count); ?></td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
        <?php
    }
}