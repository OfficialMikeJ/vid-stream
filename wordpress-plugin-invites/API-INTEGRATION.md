# StreamLab Invites - API Integration Guide

Guide for integrating the invite system with Desktop and Android applications.

## 🎯 Overview

The invite system uses a **2-use code system**:
1. **First use:** Verify invite code and grant access to registration
2. **Second use:** Complete registration and activate account

This same flow works across:
- ✅ WordPress Website
- ✅ Desktop Application (Electron, etc.)
- ✅ Android Application

---

## 📱 User Flow (All Platforms)

### Display Message to User

Show this exact message on your invite gate screen:

```
Please paste your invite code and click "Submit", 
paste your invite code once more to finish registration 
for full access.
```

### Visual Steps (Optional)

Display these 3 steps:
1. **Paste your invite code**
2. **Click Submit to verify**
3. **Paste code again to complete registration**

---

## 🔌 API Endpoints

### Base URL
```
https://your-wordpress-site.com/wp-json/streamlab-invites/v1/
```

Or use WordPress AJAX:
```
https://your-wordpress-site.com/wp-admin/admin-ajax.php
```

---

## 1️⃣ Step 1: Verify Invite Code (First Use)

### Endpoint
```http
POST /wp-admin/admin-ajax.php
```

### Request
```json
{
  "action": "streamlab_verify_code",
  "nonce": "wp_nonce_here",
  "code": "ABC-123-XYZ"
}
```

### Success Response
```json
{
  "success": true,
  "code": {
    "id": "123",
    "code": "ABC-123-XYZ",
    "uses": 1,
    "max_uses": 2,
    "status": "active"
  },
  "remaining_uses": 1
}
```

### Error Response
```json
{
  "success": false,
  "message": "Invalid invite code"
}
```

### Desktop/Android Implementation

**Android (Kotlin):**
```kotlin
data class VerifyCodeRequest(
    val action: String = "streamlab_verify_code",
    val nonce: String,
    val code: String
)

data class VerifyCodeResponse(
    val success: Boolean,
    val message: String?,
    val remaining_uses: Int?
)

suspend fun verifyInviteCode(code: String): VerifyCodeResponse {
    val response = retrofitClient.post<VerifyCodeResponse>(
        url = "https://your-site.com/wp-admin/admin-ajax.php",
        body = VerifyCodeRequest(
            nonce = getNonce(),
            code = code
        )
    )
    
    if (response.success) {
        // Store code in SharedPreferences for registration
        storeInviteCode(code)
        // Navigate to registration screen
        navigateToRegistration()
    }
    
    return response
}
```

**Desktop (JavaScript/Electron):**
```javascript
async function verifyInviteCode(code) {
    const response = await fetch('https://your-site.com/wp-admin/admin-ajax.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            action: 'streamlab_verify_code',
            nonce: getNonce(),
            code: code
        })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Store code in localStorage/session
        sessionStorage.setItem('invite_code', code);
        sessionStorage.setItem('invite_verified', Date.now());
        // Navigate to registration
        window.location.href = '/register';
    } else {
        showError(data.message);
    }
    
    return data;
}
```

---

## 2️⃣ Step 2: Register User (Second Use)

### Endpoint
```http
POST /wp-json/wp/v2/users
```

Or custom registration:
```http
POST /wp-admin/admin-ajax.php
```

### Request
```json
{
  "action": "streamlab_register",
  "nonce": "wp_nonce_here",
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "invite_code": "ABC-123-XYZ"
}
```

### Success Response
```json
{
  "success": true,
  "user_id": 456,
  "message": "Registration successful",
  "token": "jwt_token_here"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Email already exists"
}
```

### Desktop/Android Implementation

**Android (Kotlin):**
```kotlin
data class RegisterRequest(
    val username: String,
    val email: String,
    val password: String,
    val invite_code: String
)

suspend fun registerUser(username: String, email: String, password: String): Boolean {
    // Get stored invite code
    val inviteCode = getStoredInviteCode()
    
    if (inviteCode == null) {
        showError("No valid invite code found")
        return false
    }
    
    val response = retrofitClient.post<RegisterResponse>(
        url = "https://your-site.com/wp-json/streamlab/v1/register",
        body = RegisterRequest(
            username = username,
            email = email,
            password = password,
            invite_code = inviteCode
        )
    )
    
    if (response.success) {
        // Save auth token
        saveAuthToken(response.token)
        // Clear invite code
        clearInviteCode()
        // Navigate to main app
        navigateToMainApp()
        return true
    }
    
    return false
}
```

**Desktop (JavaScript/Electron):**
```javascript
async function registerUser(username, email, password) {
    // Get stored invite code
    const inviteCode = sessionStorage.getItem('invite_code');
    
    if (!inviteCode) {
        showError('No valid invite code found');
        return false;
    }
    
    const response = await fetch('https://your-site.com/wp-json/streamlab/v1/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            email: email,
            password: password,
            invite_code: inviteCode
        })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Save auth token
        localStorage.setItem('auth_token', data.token);
        // Clear invite session
        sessionStorage.removeItem('invite_code');
        sessionStorage.removeItem('invite_verified');
        // Navigate to main app
        window.location.href = '/dashboard';
        return true;
    }
    
    showError(data.message);
    return false;
}
```

---

## 🔐 Security Considerations

### Session Management

**Web/Desktop:**
- Store invite code in `sessionStorage` (1 hour validity)
- Clear after successful registration
- Re-verify if session expired

**Android:**
- Store in `SharedPreferences` with timestamp
- Clear after successful registration
- Check expiry (1 hour max)

### Nonce Generation

**WordPress Nonce:**
```php
// In your WordPress theme/plugin
wp_localize_script('your-script', 'streamlabInvites', array(
    'ajax_url' => admin_url('admin-ajax.php'),
    'nonce' => wp_create_nonce('streamlab_invites_nonce')
));
```

**For Native Apps:**
You may need to implement a REST API endpoint that provides nonces:

```php
// In functions.php or custom plugin
add_action('rest_api_init', function () {
    register_rest_route('streamlab/v1', '/get-nonce', array(
        'methods' => 'GET',
        'callback' => function() {
            return array(
                'nonce' => wp_create_nonce('streamlab_invites_nonce')
            );
        },
        'permission_callback' => '__return_true'
    ));
});
```

---

## 📋 Implementation Checklist

### Desktop App
- [ ] Display invite gate with 3-step instructions
- [ ] Implement code verification API call
- [ ] Store verified code in sessionStorage
- [ ] Show registration form
- [ ] Implement registration API call with invite code
- [ ] Handle session expiry (1 hour)
- [ ] Clear invite code after successful registration

### Android App
- [ ] Design invite gate screen with steps
- [ ] Implement code verification with Retrofit/OkHttp
- [ ] Store verified code in SharedPreferences
- [ ] Create registration screen
- [ ] Implement registration API call
- [ ] Handle token storage
- [ ] Clear invite code after registration

---

## 🎨 UI/UX Guidelines

### Invite Gate Screen

**Layout:**
```
┌─────────────────────────────────┐
│      [App Logo/Icon]            │
│                                 │
│   Invite Only Access            │
│                                 │
│ Please paste your invite code   │
│ and click "Submit", paste your  │
│ invite code once more to finish │
│ registration for full access.   │
│                                 │
│  ┌───┐                          │
│  │ 1 │ Paste your invite code   │
│  └───┘                          │
│  ┌───┐                          │
│  │ 2 │ Click Submit to verify   │
│  └───┘                          │
│  ┌───┐                          │
│  │ 3 │ Paste code again to      │
│  └───┘   complete registration  │
│                                 │
│  [  Invite Code Input  ]        │
│  [     Submit Button    ]       │
│                                 │
└─────────────────────────────────┘
```

### Registration Screen

Show reminder:
```
✓ Invite code verified!
Now paste your code again to complete registration.
```

---

## 🧪 Testing

### Test Flow

1. **Generate invite code** in WordPress admin
2. **Desktop/Android:** Enter code → Verify
3. **Check:** Code uses should be 1/2
4. **Desktop/Android:** Complete registration
5. **Check:** Code uses should be 2/2, status "used"
6. **Verify:** User can login and access app

### Test Cases

- [ ] Valid code verification
- [ ] Invalid code error handling
- [ ] Expired session (wait 61 minutes)
- [ ] Registration without code (should fail)
- [ ] Registration with verified code (should succeed)
- [ ] Code reuse attempt (should fail)
- [ ] Network error handling

---

## 📞 Support

**Issues:**
- Check WordPress site is accessible
- Verify nonce generation is working
- Check invite code hasn't been fully used (2/2)
- Ensure session hasn't expired (1 hour limit)
- Check Activity Log in WordPress admin

**API Debugging:**
```javascript
// Enable verbose logging
console.log('Verifying code:', code);
console.log('Response:', response);
console.log('Session:', sessionStorage.getItem('invite_code'));
```

---

## ✅ Summary

**Key Points:**
- Always display the complete 3-step instruction message
- Use 2-step verification: verify → register
- Store code in session/preferences between steps
- Code expires after 1 hour in session
- Code is tied to user email after registration
- Same API works for web, desktop, and mobile

**User Experience:**
1. User sees clear instructions (paste twice)
2. First paste: verify and unlock registration
3. Second paste: complete registration
4. Full access granted

---

*Consistent invite experience across all platforms.* 📱💻🌐
