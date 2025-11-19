# StreamLab Invites - Quick Start Guide

Get your invite-only platform running in 5 minutes!

## Step 1: Install Plugin (1 minute)

1. Upload `streamlab-invites.zip` to WordPress
2. **Plugins** → **Add New** → **Upload Plugin**
3. Click **Install Now** → **Activate**
4. See **Invites** menu in sidebar ✅

## Step 2: Configure (2 minutes)

### Enable Invites
1. Go to **Invites** → **Settings**
2. Check ☑️ **Enable Invite System**
3. Customize message: "Please contact us for an invite access code."
4. Click **Save Changes**

### Your Site is Now Locked! 🔒

Non-invited users will see:
- Your theme (preserved)
- Invite gate overlay
- "Enter Invite Code" box
- Cannot access content

## Step 3: Generate Codes (1 minute)

1. Go to **Invites** → **Generate Codes**
2. Add note (optional): "Code for John Doe"
3. Click **Generate Invite Code**
4. Copy the code: `ABC-123-XYZ`
5. Share with your user!

## Step 4: Test It! (1 minute)

### As Non-Logged User:
1. Open site in incognito/private window
2. See invite gate 👍
3. Enter code → Verify
4. Redirected to registration
5. Register → Full access!

### Check Dashboard:
1. **Manage Codes** → See used code
2. **Activity Log** → See all actions
3. Stats updated automatically

## Done! 🎉

Your invite-only platform is ready!

---

## Common Tasks

### Generate More Codes
**Invites** → **Generate Codes** → Click button → Share

### Revoke a Code
**Invites** → **Manage Codes** → Find code → Click **Revoke**

### Check Who Registered
**Invites** → **Manage Codes** → See "Registered User" column

### View All Activity
**Invites** → **Activity Log** → See timestamps, IPs, actions

### Allow Homepage Access
**Invites** → **Settings** → Check **Allow Homepage Access**

---

## Pro Tips

💡 **Generate codes ahead of time** - Create multiple codes for batch invites  
💡 **Add notes to codes** - Track who each code is for  
💡 **Monitor Activity Log** - Watch for suspicious activity  
💡 **Revoke leaked codes** - Immediately disable compromised codes  
💡 **Use strong codes** - Keep 12+ character alphanumeric format

---

## Need Help?

📖 **Full Documentation:** See [README.md](README.md)  
🐛 **Issues:** Check troubleshooting section  
💬 **Support:** support@your-domain.com

---

## How It Works

### Code Lifecycle

1. **Generate** → Admin creates code (0/2 uses)
2. **Verify** → User enters code (1/2 uses)
3. **Register** → User completes registration (2/2 uses)
4. **Used** → Code status changes to "Used"

### User Journey

```
Visit Site → Invite Gate → Enter Code → Verify → 
Register Page → Create Account → Login → Full Access
```

### Security Flow

- Code verified via AJAX
- Stored in session (1-hour validity)
- Second use on registration
- User marked as invited
- Code tied to user account

---

**Your platform is now invite-only!** 🔐✨
