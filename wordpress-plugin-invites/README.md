# StreamLab Invites - WordPress Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![WordPress](https://img.shields.io/badge/WordPress-5.8%2B-blue)
![PHP](https://img.shields.io/badge/PHP-7.4%2B-purple)
![License](https://img.shields.io/badge/license-GPL--2.0-green)

Secure invite-only access system for your WordPress streaming platform. Generate invite codes, control registration, and manage user access with full customization options.

## 🎯 Features

### Invite Code System
- **Random Code Generation** - Generate unique codes in XXX-XXX-XXX format
- **2-Use System** - First use: access registration page, Second use: complete registration
- **Configurable Format** - Alphanumeric, letters only, or numbers only
- **Custom Length** - 6-32 characters
- **Status Tracking** - Active, Used, Revoked statuses
- **Detailed Logging** - IP address and user agent tracking

### Access Control
- **Website Lock** - Lock entire site behind invite gate
- **Theme Preserved** - Site theme remains visible, only content is locked
- **Custom Message** - Configurable invite gate message
- **Selective Locking** - Choose which pages to lock/unlock
- **Homepage Control** - Optional homepage public access
- **Session Management** - 1-hour code validity window

### User Management
- **Auto-Registration** - Seamless registration with invite code
- **Role Assignment** - Configure default user role for invited users
- **User Tracking** - Track which invite code each user used
- **Custom Redirect** - Set post-registration redirect URL

### Admin Interface
- **Multi-Tab Dashboard** - Generate, Manage, Settings, Logs, Roles
- **Real-Time Stats** - Total, Active, Used, Revoked code counts
- **Code Management** - View, revoke, delete codes
- **Activity Log** - Detailed usage history with timestamps
- **Roles Overview** - View invited users by role

### Security
- **Nonce Verification** - CSRF protection on all requests
- **SQL Injection Protection** - Prepared statements
- **XSS Prevention** - Sanitization and escaping
- **Permission Checks** - Admin-only access control
- **Unique Codes** - Collision-free generation
- **IP Logging** - Track code usage by IP

## 📋 Requirements

| Requirement | Version |
|------------|---------|
| WordPress | 5.8+ |
| PHP | 7.4+ |
| MySQL | 5.6+ |

## 🚀 Installation

### Quick Install

1. Download the latest release `streamlab-invites.zip`
2. Upload to WordPress → **Plugins** → **Add New** → **Upload Plugin**
3. Click **Install Now** then **Activate**
4. Go to **Invites** in admin menu

### Manual Installation

1. Extract zip file
2. Upload `streamlab-invites` folder to `/wp-content/plugins/`
3. Activate via WordPress admin
4. Configure in **Invites** menu

## ⚙️ Configuration

### Quick Setup

1. Navigate to **Invites** → **Settings**
2. Enable invite system
3. Customize invite message
4. Configure code format
5. Save settings

### Settings Overview

**General Settings:**
- Enable/disable invite system
- Custom invite gate message
- Allow homepage access
- Post-registration redirect URL
- Default user role

**Code Settings:**
- Code length (6-32 characters)
- Code format (alphanumeric/alpha/numeric)

## 📖 Usage Guide

### 1. Generate Invite Codes

1. Go to **Invites** → **Generate Codes**
2. Optionally add notes (e.g., "Code for John")
3. Click **Generate Invite Code**
4. Copy and share the code

### 2. Share Codes

Send the generated code to users via:
- Email
- Direct message
- Social media
- Any communication method

### 3. User Experience

**Without Code:**
1. User visits site
2. Sees invite gate with clear 3-step instructions
3. Cannot access content

**With Code (2-Use System):**
1. **First Use:** User pastes invite code and clicks "Submit"
2. Code is verified → User redirected to registration page
3. **Second Use:** User pastes same code during registration
4. Account created → User gains full site access
5. Code marked as "used" and tied to user's email

### 4. Manage Codes

Go to **Invites** → **Manage Codes** to:
- View all codes
- Filter by status
- See usage statistics
- Revoke active codes
- Delete codes

### 5. Track Activity

Go to **Invites** → **Activity Log** to view:
- All code actions
- Timestamps
- User emails
- IP addresses

## 🎨 Customization

### Custom Invite Message

```php
// In Settings tab
Invite Gate Message: \"This is an exclusive platform. Please contact support@yoursite.com for access.\"
```

### Custom Styling

Add custom CSS in Settings → Custom CSS (future feature)

### Unlock Specific Pages

1. Go to **Settings** tab
2. Select pages to unlock
3. Save settings

## 🔌 Developer Reference

### Hooks

**Actions:**

```php
// Before code generation
do_action('streamlab_invite_code_generated', $code_id, $code);

// After user registers with invite
do_action('streamlab_user_invited', $user_id, $invite_code);
```

**Filters:**

```php
// Modify invite gate message
apply_filters('streamlab_invite_message', $message);

// Modify code length
apply_filters('streamlab_invite_code_length', $length);
```

### Database Tables

**wp_streamlab_invite_codes**
- Stores invite codes and metadata
- Tracks usage and status

**wp_streamlab_invite_log**
- Logs all code activities
- Stores IP and user agent

### User Meta

| Meta Key | Description |
|----------|-------------|
| `_streamlab_invited` | Marks user as invited (yes/no) |
| `_streamlab_invite_code` | Stores user's invite code |

## 🛠️ Development

### File Structure

```
streamlab-invites/
├── streamlab-invites.php              # Main plugin file
├── includes/
│   ├── class-invite-code-manager.php  # Code generation/management
│   ├── class-invite-access-control.php # Access control logic
│   ├── class-invite-registration.php   # Registration handler
│   ├── class-invite-admin.php          # Admin interface
│   └── class-invite-roles.php          # Role management
├── assets/
│   ├── css/
│   │   ├── admin.css                   # Admin styles
│   │   └── frontend.css                # Frontend styles
│   └── js/
│       ├── admin.js                    # Admin scripts
│       └── frontend.js                 # Frontend scripts
└── README.md
```

## 🐛 Troubleshooting

### Codes Not Working

**Issue:** Invite codes show as invalid

**Solutions:**
- Verify invite system is enabled in Settings
- Check code hasn't been fully used (2/2 uses)
- Ensure code hasn't been revoked
- Clear browser cache and try again

### Can't Access Admin

**Issue:** Locked out of admin area

**Solutions:**
- Admin users always have access
- Check you're logged in as administrator
- Temporarily disable plugin via FTP
- Rename plugin folder to disable

### Registration Not Working

**Issue:** Users can't register with code

**Solutions:**
- Verify WordPress registration is enabled
- Check code hasn't expired (1-hour session)
- Clear sessions and try again
- Check Activity Log for errors

### Site Completely Locked

**Issue:** No pages accessible

**Solutions:**
- Enable "Allow Homepage Access" in Settings
- Add specific pages to unlocked list
- Temporarily disable plugin
- Check Settings → Locked Pages configuration

## 📊 Statistics Dashboard

The admin dashboard shows:
- **Total Codes:** All generated codes
- **Active Codes:** Available for use
- **Used Codes:** Fully consumed (2/2 uses)
- **Revoked:** Manually disabled codes

## 🔒 Security Best Practices

### Production Deployment

1. **Use Strong Codes** - Enable alphanumeric format, 12+ characters
2. **Monitor Activity Log** - Check for suspicious usage patterns
3. **Revoke Unused Codes** - Disable codes if not shared yet
4. **Track IP Addresses** - Review Activity Log for abuse
5. **Regular Cleanup** - Delete old used/revoked codes
6. **HTTPS Only** - Always use SSL certificates
7. **Backup Database** - Regular backups including invite tables

### Code Distribution

1. **Direct Communication** - Send codes privately
2. **One-Time Use** - Generate new codes for each user
3. **Add Notes** - Track who each code is for
4. **Revoke If Compromised** - Immediately revoke leaked codes

## 🚦 Performance

### Optimization Tips

- Plugin adds minimal overhead (~0.1ms per request)
- Uses WordPress transients for caching
- Database queries are optimized with indexes
- AJAX requests are asynchronous

### Scaling

- Handles 10,000+ codes efficiently
- Activity log auto-archives old entries
- No frontend performance impact for logged-in users

## 📝 Changelog

### Version 1.0.0

**Initial Release**
- ✨ Invite code generation with customizable format
- ✨ 2-use system (access + registration)
- ✨ Website access control
- ✨ Multi-tab admin interface
- ✨ Activity logging with IP tracking
- ✨ Role assignment for invited users
- ✨ Code management (revoke/delete)
- ✨ Statistics dashboard
- ✨ Custom invite gate message
- ✨ Session-based code verification
- ✨ Responsive admin UI
- ✨ Beautiful frontend invite gate

## 🗺️ Roadmap

### Version 1.1.0 (Planned)
- [ ] Bulk code generation
- [ ] Email invite system
- [ ] Code expiration dates
- [ ] Usage analytics
- [ ] Export code list
- [ ] Custom CSS editor in admin

### Version 1.2.0 (Planned)
- [ ] Multi-code support per user
- [ ] Code categories/groups
- [ ] API for external integrations
- [ ] Webhook notifications
- [ ] Advanced role permissions
- [ ] White-label options

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📄 License

GPL v2 or later

## 🙏 Credits

**Developed by:** Your Name  
**For:** StreamLab Streaming Platform  
**Built with:** WordPress, PHP, JavaScript, Love

## 📧 Support

**Issues:** GitHub Issues  
**Email:** support@your-domain.com  
**Docs:** Full documentation included

---

**Made for exclusive communities** 🎬✨

⭐ Star this repo if you find it useful!
