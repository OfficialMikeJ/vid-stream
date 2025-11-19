# StreamLab Invites - Testing Guide

Complete testing checklist for local WordPress setup.

## Prerequisites

✅ Local WordPress installation (XAMPP, Local by Flywheel, or Docker)  
✅ WordPress 5.8 or higher  
✅ PHP 7.4 or higher  
✅ Fresh database or test site

## Installation Testing

### Test 1: Plugin Installation
1. Upload `streamlab-invites.zip` to WordPress
2. Install and activate plugin
3. **Expected:** Plugin activates successfully
4. **Verify:** "Invites" menu appears in admin sidebar

### Test 2: Database Tables
1. Go to phpMyAdmin or database tool
2. Check for tables:
   - `wp_streamlab_invite_codes`
   - `wp_streamlab_invite_log`
3. **Expected:** Both tables created with correct structure

### Test 3: Default Options
1. Go to **Invites** → **Settings**
2. **Expected:** Default values loaded:
   - Invite system enabled
   - Message: "Please contact us for an invite access code."
   - Code length: 12
   - Format: Alphanumeric

## Admin Interface Testing

### Test 4: Generate Codes Tab
1. Go to **Invites** → **Generate Codes**
2. **Verify:** Statistics dashboard shows 0/0/0/0
3. Click **Generate Invite Code**
4. **Expected:** 
   - Code generated in XXX-XXX-XXX format
   - Code displayed with copy button
   - Statistics update to show 1 total, 1 active

### Test 5: Code Generation with Notes
1. Enter notes: "Test user invite"
2. Generate code
3. Go to **Manage Codes** tab
4. **Expected:** Code shows with notes in table

### Test 6: Manage Codes Tab
1. Go to **Invites** → **Manage Codes**
2. **Verify:**
   - Generated codes appear in table
   - Status shows "Active"
   - Uses shows "0/2"
   - Actions: Revoke and Delete buttons visible

### Test 7: Filter Codes
1. In Manage Codes, click filters:
   - All
   - Active
   - Used
   - Revoked
2. **Expected:** Table filters correctly

### Test 8: Settings Tab
1. Go to **Settings** tab
2. Change settings:
   - Modify invite message
   - Change code length to 9
   - Change format to "Letters Only"
3. Save changes
4. Generate new code
5. **Expected:** New code follows new format (XXX-XXX-XXX letters only)

### Test 9: Activity Log Tab
1. Go to **Activity Log** tab
2. **Expected:** Shows all code generation activities
3. **Verify:** Timestamp, code, action, IP address logged

### Test 10: Roles Tab
1. Go to **Roles & Permissions** tab
2. **Expected:** 
   - Shows current default role
   - Lists all WordPress roles
   - Shows invited user count per role

## Access Control Testing

### Test 11: Logged Out Access
1. Open site in incognito/private window
2. Try to access homepage
3. **Expected:** Invite gate appears with:
   - Theme visible
   - Custom message displayed
   - Invite code input box
   - "Verify Code" button

### Test 12: Invalid Code Entry
1. At invite gate, enter: "INVALID-CODE"
2. Click "Verify Code"
3. **Expected:** Error message "Invalid invite code"

### Test 13: Valid Code Entry
1. Copy code from admin panel
2. Paste in invite gate
3. Click "Verify Code"
4. **Expected:**
   - Button shows loader
   - Redirects to registration page (/wp-login.php?action=register)

### Test 14: Code Usage Tracking (1st Use)
1. After verifying code, go back to admin
2. **Manage Codes** → Find the code
3. **Expected:** Uses shows "1/2"
4. **Activity Log** → Shows "used" action

## Registration Testing

### Test 15: Registration with Verified Code
1. After code verification, on registration page
2. Fill form:
   - Username: testuser1
   - Email: test@example.com
   - Password: TestPass123!
3. Submit registration
4. **Expected:**
   - User created successfully
   - Auto-logged in
   - Redirected to configured URL

### Test 16: Code Usage Tracking (2nd Use)
1. Check **Manage Codes** for the code
2. **Expected:**
   - Uses shows "2/2"
   - Status changed to "Used"
   - Registered User column shows testuser1 email

### Test 17: User Meta
1. Go to **Users** → Edit testuser1
2. Check custom fields (with plugin or directly in DB)
3. **Expected:**
   - `_streamlab_invited`: yes
   - `_streamlab_invite_code`: [the code]

### Test 18: Logged In Access
1. Stay logged in as testuser1
2. Navigate around site
3. **Expected:** Full access, no invite gate

### Test 19: Registration Without Code
1. Log out
2. Go directly to /wp-login.php?action=register
3. Try to register
4. **Expected:** Error "A valid invite code is required to register"

### Test 20: Expired Session
1. Verify a code
2. Wait 65 minutes (or modify code to 1 minute for testing)
3. Try to register
4. **Expected:** Error "Your invite code has expired"

## Code Management Testing

### Test 21: Revoke Code
1. Generate a new code
2. Go to **Manage Codes**
3. Click **Revoke** on the code
4. **Expected:**
   - Status changes to "Revoked"
   - Revoke button disappears
5. Try to use code at invite gate
6. **Expected:** Error "This invite code is no longer active"

### Test 22: Delete Code
1. Generate a new code
2. Go to **Manage Codes**
3. Click **Delete** on the code
4. Confirm deletion
5. **Expected:**
   - Code removed from table
   - Shows in Activity Log as "deleted"

### Test 23: Fully Used Code
1. Use a code through complete registration
2. Try to use same code again
3. **Expected:** Error "This invite code has been fully used"

## Security Testing

### Test 24: Admin Access
1. Log in as administrator
2. Try to access site
3. **Expected:** Full access, no invite gate (admins bypass)

### Test 25: Non-Admin Logged User Without Invite
1. Create user manually (without invite)
2. Log in as that user
3. Try to access content
4. **Expected:** Blocked by invite gate

### Test 26: Direct Database Manipulation
1. Try to manually change code in database
2. Use manipulated code
3. **Expected:** Validation prevents usage

### Test 27: Session Hijacking
1. Verify code, save session ID
2. Clear cookies
3. Try to inject saved session
4. **Expected:** Proper security prevents abuse

### Test 28: AJAX Security
1. Try AJAX requests without nonce
2. **Expected:** Request blocked with "nonce verification failed"

### Test 29: SQL Injection
1. Enter code: `' OR 1=1 --`
2. **Expected:** Sanitized, no SQL injection

### Test 30: XSS Testing
1. Enter notes: `<script>alert('xss')</script>`
2. **Expected:** Properly escaped in display

## Settings Testing

### Test 31: Enable/Disable System
1. **Settings** → Uncheck "Enable Invite System"
2. Save settings
3. Access site logged out
4. **Expected:** Normal access, no invite gate
5. Re-enable system
6. **Expected:** Invite gate returns

### Test 32: Allow Homepage Access
1. **Settings** → Check "Allow Homepage Access"
2. Save settings
3. Access homepage logged out
4. **Expected:** Homepage accessible
5. Try other pages
6. **Expected:** Other pages show invite gate

### Test 33: Custom Redirect URL
1. **Settings** → Change redirect to /thank-you/
2. Save settings
3. Complete registration with code
4. **Expected:** Redirected to /thank-you/ page

### Test 34: Default Role Assignment
1. **Settings** → Change default role to "Editor"
2. Save settings
3. Register new user with code
4. Check user in admin
5. **Expected:** User has "Editor" role

### Test 35: Code Format Changes
1. **Settings** → Change to "Numbers Only", length 8
2. Generate code
3. **Expected:** Code is 8 digits: XXX-XXX-XX

## Frontend UX Testing

### Test 36: Responsive Design
1. Open invite gate on:
   - Desktop (1920px)
   - Tablet (768px)
   - Mobile (375px)
2. **Expected:** Proper responsive layout

### Test 37: Code Input Formatting
1. Type code in input: "abc123xyz"
2. **Expected:** Auto-formats to "ABC-123-XYZ"

### Test 38: Copy Code Button
1. Generate code in admin
2. Click "Copy Code" button
3. **Expected:** Code copied to clipboard, button shows "Copied!"

### Test 39: Loading States
1. Enter code, click verify
2. **Expected:** Button shows loader during verification

### Test 40: Error Display
1. Enter invalid code
2. **Expected:** Error box appears with red styling

## Performance Testing

### Test 41: Multiple Codes
1. Generate 100 codes (bulk test)
2. Check page load time
3. **Expected:** Manage page loads < 1 second

### Test 42: Large Activity Log
1. Generate and use many codes
2. Check Activity Log performance
3. **Expected:** Displays 100 most recent, paginated

### Test 43: Frontend Load Time
1. Measure time for invite gate to appear
2. **Expected:** < 500ms

## Edge Cases

### Test 44: Duplicate Code Check
1. Manually insert duplicate code in DB
2. Try to use both
3. **Expected:** System handles gracefully

### Test 45: Special Characters
1. Try code with special chars: @#$%
2. **Expected:** Properly sanitized

### Test 46: Very Long Notes
1. Enter 5000 character note
2. Generate code
3. **Expected:** Note truncated in display, full in database

### Test 47: Concurrent Usage
1. Two users verify same code simultaneously
2. **Expected:** Both tracked, uses = 2

### Test 48: Browser Back Button
1. Verify code
2. Hit browser back
3. **Expected:** Session maintained, can proceed

### Test 49: Multiple Browser Tabs
1. Open invite gate in 2 tabs
2. Verify in one tab
3. **Expected:** Both tabs can access registration

### Test 50: Plugin Deactivation
1. Deactivate plugin
2. Access site
3. **Expected:** Normal WordPress access
4. Reactivate
5. **Expected:** Invite system returns, data preserved

## Checklist Summary

Print this checklist and mark each test:

- [ ] Tests 1-10: Installation & Admin Interface
- [ ] Tests 11-20: Access Control & Registration
- [ ] Tests 21-23: Code Management
- [ ] Tests 24-30: Security
- [ ] Tests 31-35: Settings
- [ ] Tests 36-40: Frontend UX
- [ ] Tests 41-43: Performance
- [ ] Tests 44-50: Edge Cases

## Bug Reporting

If you find issues:

1. Note test number
2. Record expected vs actual result
3. Include browser, PHP, WordPress versions
4. Check console for JavaScript errors
5. Check PHP error log

## Success Criteria

✅ All 50 tests pass  
✅ No security vulnerabilities  
✅ Performance within limits  
✅ Proper error handling  
✅ Clean code, no warnings

---

**Happy Testing!** 🧪✨
