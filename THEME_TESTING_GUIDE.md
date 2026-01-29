# Theme Management Testing Guide

**Phase 6: Theme Management Foundation**
Test the new dark mode feature with persistent preferences across platforms.

**⚠️ IMPORTANT:** You must be **logged in** (Google or Microsoft OAuth) before accessing Settings. The `/settings` route is protected by authentication.

**🔧 BUG FIX (2026-01-29):** Fixed critical bug where navigating to `/settings` would log users out. If you pulled before commit `4be4c74`, please `git pull` to get the fix.

---

## Quick Setup (Another PC)

### 1. Clone Repository

```bash
git clone https://github.com/itsvetkov1/XtraSkill.git
cd XtraSkill
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Or (macOS/Linux)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python run.py
```

Backend runs at: `http://localhost:8000`

**Keep this terminal open** - backend must run during testing.

### 3. Frontend Setup

Open a **new terminal** in the project root:

```bash
cd frontend

# Install Flutter dependencies
flutter pub get

# Run on Chrome (recommended for quick testing)
flutter run -d chrome
```

**Alternative platforms:**
- Windows: `flutter run -d windows`
- macOS: `flutter run -d macos`
- Android: `flutter run -d android` (requires device/emulator)
- iOS: `flutter run -d ios` (requires macOS + device/simulator)

---

## Testing Theme Features

### Test 0: Login First (REQUIRED)

**What:** Authenticate before accessing Settings

1. App launches and shows **Splash Screen** → automatically redirects to **Login Screen**
2. Click either **"Continue with Google"** or **"Continue with Microsoft"** button
3. Complete OAuth flow in browser popup/redirect
4. **Verify:** You're redirected back to app and see **Home Screen**
5. **Verify:** You're now logged in (authenticated)

**Expected:** Successful login, Home screen displays

**Note:** Backend must be running (`python run.py` in backend folder) for OAuth to work.

---

### Test 1: Navigate to Settings

**What:** Access the new Settings page with theme toggle

1. **Ensure you're logged in** (see Test 0 above)
2. App is in **light theme** (white background)
3. In the URL bar, type: `/settings` and press Enter
4. **Verify:** Settings page displays with "Appearance" section
5. **Verify:** "Dark Mode" toggle switch is visible and OFF

**Expected:** Settings screen loads, toggle is OFF (light theme default)

---

### Test 2: Toggle to Dark Mode (SET-03)

**What:** Switch to dark theme instantly

1. Click the "Dark Mode" toggle switch
2. **Verify:** All screens immediately switch to dark theme
   - Background: Dark gray (#121212)
   - No animation or transition
   - Change happens instantly
3. Navigate to Home screen (`/`)
4. **Verify:** Home screen is in dark theme
5. Navigate to Projects screen (`/projects`)
6. **Verify:** Projects screen is in dark theme
7. Return to Settings (`/settings`)
8. **Verify:** Toggle switch is still ON

**Expected:** Instant theme switching, all screens dark, no lag

---

### Test 3: Theme Persistence (SET-04)

**What:** Theme preference survives app restart

1. With dark mode ON, close the browser/app completely
2. Reopen the browser/app
3. Navigate back to the app URL
4. **CRITICAL:** Watch the startup carefully
   - **Verify:** App opens directly in dark theme
   - **Verify:** NO white flash during startup
5. Navigate to Settings (`/settings`)
6. **Verify:** Toggle switch is still ON

**Expected:** Dark theme persists, no white flash on startup

---

### Test 4: No White Flash on Dark Mode Startup (SET-06 CRITICAL)

**What:** Async initialization prevents white flash

1. Ensure dark mode is ON
2. Close and reopen app **5 times**
3. Each time, watch the first frame carefully
4. **Verify:** Zero white flash, app starts dark immediately
5. **Verify:** Background is dark gray from first pixel

**Expected:** Perfect dark startup, no flicker, no white flash

**If you see white flash:** This is a CRITICAL failure - report it

---

### Test 5: Toggle Back to Light Mode

**What:** Switch back to light theme

1. Navigate to Settings (`/settings`)
2. Click "Dark Mode" toggle to turn it OFF
3. **Verify:** All screens immediately switch to light theme
4. Navigate between Home, Projects, Settings
5. **Verify:** All screens remain in light theme
6. Close and reopen app
7. **Verify:** App opens in light theme, no dark flash

**Expected:** Instant switch to light, persistence works both directions

---

### Test 6: First Launch Defaults to Light (SET-07)

**What:** New users see light theme first

**Web (Chrome):**
1. Press F12 (open DevTools)
2. Go to: Application → Storage → Local Storage
3. Find entry for your app URL (e.g., `http://localhost:xxxxx`)
4. Delete all keys
5. Close DevTools, refresh page (F5)
6. **Verify:** App opens in LIGHT theme (not dark)

**Windows Desktop:**
1. Close app
2. Navigate to: `%APPDATA%\...\shared_preferences`
3. Delete preference files
4. Reopen app
5. **Verify:** App opens in LIGHT theme

**Expected:** Fresh install always starts with light theme

---

### Test 7: Rapid Toggle Stress Test

**What:** Ensure no lag or crashes with rapid switching

1. Navigate to Settings (`/settings`)
2. Toggle dark mode switch ON and OFF rapidly 10 times
3. **Verify:** No lag, no crashes, no error messages
4. Final state (ON or OFF) persists after restart
5. **Verify:** App doesn't freeze or slow down

**Expected:** Smooth toggling, no performance issues

---

### Test 8: Cross-Platform Persistence (if available)

**What:** Theme persists on different platforms

1. Test on Chrome: Set dark mode, restart → persists
2. Test on Windows desktop: Set dark mode, restart → persists
3. Test on Android: Set dark mode, force-close app, reopen → persists
4. Test on iOS: Set dark mode, force-close app, reopen → persists

**Expected:** Each platform independently persists theme preference

**Note:** Theme preference is local to each device (not synced across devices)

---

## Success Criteria Checklist

- [ ] Settings page accessible at `/settings` route
- [ ] Dark Mode toggle visible and functional
- [ ] Theme switches instantly with no animation
- [ ] Dark theme uses dark gray background (#121212)
- [ ] Light theme uses white background
- [ ] Theme preference persists across app restarts
- [ ] **CRITICAL:** No white flash when starting app in dark mode
- [ ] New users see light theme on first launch
- [ ] Rapid toggling works smoothly with no lag
- [ ] All screens (Home, Projects, Settings) reflect theme change
- [ ] Toggle switch state matches current theme

---

## Known Issues (Ignore These)

1. **No sidebar link to Settings yet:** Phase 7 work. Use URL bar: `/settings`
2. **Placeholder sections in Settings:** "Account" section is Phase 8 work
3. **Pre-existing analyzer warnings:** Unrelated to theme changes

---

## Troubleshooting

### Backend Not Running
**Symptom:** Frontend crashes or shows connection errors
**Fix:** Ensure backend terminal shows: `Uvicorn running on http://127.0.0.1:8000`

### White Flash Still Occurs
**Symptom:** Brief white screen when starting in dark mode
**This is a CRITICAL bug** - report immediately with:
- Platform (Chrome/Windows/macOS/Android/iOS)
- Steps to reproduce
- Screenshot/recording if possible

### Theme Doesn't Persist
**Symptom:** Dark mode resets to light after restart
**Check:**
- Browser not in incognito/private mode (can't save preferences)
- No browser extensions blocking localStorage
- SharedPreferences writes not failing (check console for errors)

### Toggle Switch Not Visible
**Symptom:** Settings page loads but no toggle
**Check:**
- Run `flutter pub get` again
- Restart Flutter (stop and `flutter run` again)
- Check URL is exactly `/settings` (case sensitive)

---

## What Was Built

**Phase 6 delivered these capabilities:**

1. **ThemeProvider** (`frontend/lib/providers/theme_provider.dart`)
   - ChangeNotifier pattern for reactive theme state
   - Immediate persistence (saves before notifyListeners)
   - Static load() factory for async initialization
   - Graceful error handling for storage failures

2. **AppTheme Updates** (`frontend/lib/core/theme.dart`)
   - Professional blue accent: #1976D2
   - Dark gray background: #121212 (reduces eye strain vs pure black)
   - Material 3 design system

3. **Settings Screen** (`frontend/lib/screens/settings_screen.dart`)
   - Dark Mode toggle switch
   - Clean sectioned layout
   - Placeholder for Phase 8 features

4. **Async Initialization** (`frontend/lib/main.dart`)
   - SharedPreferences loaded before MaterialApp
   - Prevents white flash on dark mode startup
   - ThemeProvider wired to MaterialApp.themeMode

---

## Requirements Tested

- **SET-03:** Settings page includes light/dark theme toggle ✓
- **SET-04:** Theme preference persists across app restarts ✓
- **SET-06:** Theme loads before MaterialApp (prevent white flash) ✓
- **SET-07:** Theme defaults to light for new users ✓

---

## Reporting Results

After testing, reply with:

**"approved"** if all tests pass

**OR describe specific failures:**
- Which test failed (Test 1, 2, 3, etc.)
- Platform tested (Chrome/Windows/macOS/Android/iOS)
- What happened vs what was expected
- Screenshots if helpful

---

## Next Steps After Approval

Once theme management is verified, Phase 7 will add:
- Persistent sidebar navigation (no more URL typing)
- Settings link in sidebar
- Breadcrumb navigation
- Back arrows with context

**Phase 6 → Phase 7 → Phase 8 (full Settings page with profile/logout/token usage)**
