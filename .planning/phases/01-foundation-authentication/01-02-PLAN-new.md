---
ph
ase: 01-foundation-authentication
plan: 02
type: execute
wave: 2
depends_on: ["01-01"]
files_modified:
  - backend/app/services/auth_service.py
  - backend/app/routes/auth.py
  - backend/main.py
  - frontend/lib/services/auth_service.dart
  - frontend/lib/providers/auth_provider.dart
  - frontend/lib/screens/auth/login_screen.dart
  - android/app/src/main/AndroidManifest.xml
  - ios/Runner/Info.plist

autonomous: false

user_setup:
  - service: "Google OAuth"
    why: "User authentication via Google accounts"
    env_vars:
      - name: GOOGLE_CLIENT_ID
        source: "Google Cloud Console → APIs & Services → Credentials → Create OAuth 2.0 Client ID"
      - name: GOOGLE_CLIENT_SECRET
        source: "Same location as Client ID"
    dashboard_config:
      - task: "Create OAuth 2.0 credentials"
        location: "Google Cloud Console → APIs & Services → Credentials"
      - task: "Add authorized redirect URI: http://localhost:8000/auth/google/callback"
        location: "OAuth 2.0 Client ID settings"
      - task: "Add authorized JavaScript origin: http://localhost:8080"
        location: "OAuth 2.0 Client ID settings"

  - service: "Microsoft OAuth"
    why: "User authentication via Microsoft accounts"
    env_vars:
      - name: MICROSOFT_CLIENT_ID
        source: "Azure Portal → App Registrations → New registration → Application (client) ID"
      - name: MICROSOFT_CLIENT_SECRET
        source: "Azure Portal → App Registrations → Certificates & secrets → New client secret"
    dashboard_config:
      - task: "Register application"
        location: "Azure Portal → App Registrations → New registration"
      - task: "Add redirect URI: http://localhost:8000/auth/microsoft/callback"
        location: "App Registration → Authentication → Add a platform → Web"
      - task: "Add API permission: Microsoft Graph → User.Read"
        location: "App Registration → API permissions"

must_haves:
  truths:
    - "User can click Google OAuth button and be redirected to Google login"
    - "User can complete Google OAuth and receive JWT token"
    - "User can click Microsoft OAuth button and be redirected to Microsoft login"
    - "User can complete Microsoft OAuth and receive JWT token"
    - "JWT token is stored securely on device"
    - "User remains logged in across app restarts"
    - "User can log out from the home screen"
  artifacts:
    - path: "backend/app/services/auth_service.py"
      provides: "OAuth flow implementation and JWT generation"
      min_lines: 100
    - path: "backend/app/routes/auth.py"
      provides: "Auth endpoints (initiate, callback, logout)"
      exports: ["router"]
    - path: "frontend/lib/services/auth_service.dart"
      provides: "OAuth flow and token management"
      min_lines: 80
    - path: "frontend/lib/screens/home_screen.dart"
      provides: "Home screen with logout button"
      contains: "logout"
  key_links:
    - from: "frontend/lib/screens/auth/login_screen.dart"
      to: "frontend/lib/services/auth_service.dart"
      via: "OAuth button click handlers"
      pattern: "onPressed.*authService\\.login"
    - from: "backend/app/routes/auth.py"
      to: "backend/app/services/auth_service.py"
      via: "OAuth callback processing"
      pattern: "auth_service\\.process_callback"
    - from: "backend/app/services/auth_service.py"
      to: "backend/app/models.py"
      via: "User creation/retrieval"
      pattern: "db\\.query\\(User\\)"
---

<objective>
Implement production-ready OAuth 2.0 authentication with Google and Microsoft providers.

Purpose: Enable users to securely authenticate using their work accounts (Google Workspace or Microsoft 365), establishing the authorization foundation for all user-specific features. This prevents authentication debt (Pitfall #5) by implementing enterprise-grade auth from day one.

Output: Working OAuth flows for both providers, JWT-based session management, secure token storage, persistent authentication across sessions and devices, and logout functionality.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/research/STACK.md
@.planning/research/ARCHITECTURE.md
@.planning/research/PITFALLS.md
@.planning/phases/01-foundation-authentication/01-01-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Implement OAuth 2.0 backend with Google and Microsoft providers</name>
  <files>
    backend/app/services/auth_service.py
    backend/app/routes/auth.py
    backend/app/utils/jwt.py
    backend/main.py
  </files>
  <action>
    Create backend authentication infrastructure:

    1. **JWT utilities** (app/utils/jwt.py):
       - create_access_token(user_id: UUID, email: str) → JWT string
         - Payload: sub=user_id, email=email, exp=7 days from now
         - Sign with HS256 using SECRET_KEY from config
       - verify_token(token: str) → dict or raise HTTPException
         - Decode JWT, verify signature and expiration
         - Return payload if valid
       - get_current_user dependency for FastAPI routes:
         - Extract Bearer token from Authorization header
         - Verify token and return user_id

    2. **Auth service** (app/services/auth_service.py):
       - OAuth2Service class with methods for each provider
       - **Google OAuth flow**:
         - get_google_auth_url() → authorization URL with state parameter (CSRF protection)
         - process_google_callback(code: str, state: str) → user object
           - Exchange code for tokens via Google token endpoint
           - Fetch user profile from Google userinfo endpoint
           - Create or update User in database (upsert by oauth_provider + oauth_id)
           - Return user object
       - **Microsoft OAuth flow**:
         - get_microsoft_auth_url() → authorization URL with state parameter
         - process_microsoft_callback(code: str, state: str) → user object
           - Exchange code for tokens via Microsoft token endpoint
           - Fetch user profile from Microsoft Graph API (/me endpoint)
           - Create or update User in database
           - Return user object

       Use authlib library for OAuth client:
       ```python
       from authlib.integrations.httpx_client import AsyncOAuth2Client

       google_client = AsyncOAuth2Client(
           client_id=config.GOOGLE_CLIENT_ID,
           client_secret=config.GOOGLE_CLIENT_SECRET,
           redirect_uri="http://localhost:8000/auth/google/callback"
       )
       ```

       WHY authlib: Handles OAuth 2.0 protocol details, token exchange, and PKCE for mobile.

    3. **Auth routes** (app/routes/auth.py):
       - POST /auth/google/initiate → returns {"auth_url": "https://accounts.google.com/..."}
       - GET /auth/google/callback?code=...&state=... → exchanges code, creates JWT, redirects to Flutter with token
       - POST /auth/microsoft/initiate → returns {"auth_url": "https://login.microsoftonline.com/..."}
       - GET /auth/microsoft/callback?code=...&state=... → exchanges code, creates JWT, redirects
       - POST /auth/logout → returns success (stateless, client discards token)
       - GET /auth/me → returns current user info (requires JWT)

       Callback redirect pattern:
       ```python
       # After successful OAuth
       jwt_token = create_access_token(user.id, user.email)
       # Redirect to Flutter deep link with token
       return RedirectResponse(f"http://localhost:8080/auth/callback?token={jwt_token}")
       ```

    4. **Register router** in main.py:
       ```python
       from app.routes import auth
       app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
       ```

    AVOID: Storing OAuth tokens in database (use them once to get user info, then discard), not validating state parameter (CSRF vulnerability), exposing secrets in logs.
  </action>
  <verify>
    Run verification commands:
    ```bash
    cd backend
    pytest tests/test_auth.py  # Create basic tests for JWT creation/verification

    # Manual OAuth flow test
    curl http://localhost:8000/auth/google/initiate
    # Should return: {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."}

    # Test JWT creation
    python -c "from app.utils.jwt import create_access_token; import uuid; print(create_access_token(uuid.uuid4(), 'test@example.com'))"

    # Test protected endpoint
    curl -H "Authorization: Bearer <valid_jwt>" http://localhost:8000/auth/me
    ```

    Expected results:
    - JWT creation returns valid token string
    - JWT verification accepts valid tokens, rejects invalid/expired
    - Initiate endpoints return Google/Microsoft auth URLs
    - Protected endpoint (/auth/me) requires valid JWT
  </verify>
  <done>
    - OAuth2Service class implemented with Google and Microsoft flows
    - JWT utilities create and verify tokens with 7-day expiration
    - Auth routes handle initiate and callback for both providers
    - User creation/update logic upserts by oauth_provider + oauth_id
    - State parameter used for CSRF protection
    - Protected endpoints require valid JWT via get_current_user dependency
    - /auth/me endpoint returns current user information
  </done>
</task>

<task type="auto">
  <name>Task 2: Implement OAuth flow in Flutter with secure token storage and mobile deep links</name>
  <files>
    frontend/lib/services/auth_service.dart
    frontend/lib/providers/auth_provider.dart
    frontend/lib/screens/auth/login_screen.dart
    frontend/lib/screens/auth/callback_screen.dart
    frontend/lib/main.dart
    android/app/src/main/AndroidManifest.xml
    ios/Runner/Info.plist
  </files>
  <action>
    Create Flutter authentication implementation:

    1. **Auth service** (lib/services/auth_service.dart):
       - AuthService class managing OAuth flows and token storage
       - Dependencies: dio (HTTP), flutter_secure_storage (token persistence), url_launcher (OAuth browser)

       Methods:
       - **loginWithGoogle()** → Future<String> (returns JWT token):
         - Call GET /auth/google/initiate to get auth_url
         - Launch auth_url in browser using url_launcher
         - Wait for callback with token (handled by callback screen)
         - Store token in secure storage
         - Return token

       - **loginWithMicrosoft()** → similar to Google

       - **logout()** → Future<void>:
         - Delete token from secure storage
         - Call POST /auth/logout (optional, stateless JWT)

       - **getStoredToken()** → Future<String?>:
         - Retrieve token from flutter_secure_storage
         - Return null if not found

       - **isTokenValid(String token)** → bool:
         - Decode JWT payload (base64 decode middle segment)
         - Check exp timestamp is in future
         - Return false if expired or malformed

       - **getCurrentUser()** → Future<User>:
         - Call GET /auth/me with Bearer token
         - Return User object

       Use flutter_secure_storage for token persistence:
       ```dart
       final storage = FlutterSecureStorage();
       await storage.write(key: 'auth_token', value: token);
       ```

       WHY flutter_secure_storage: Uses Keychain (iOS), KeyStore (Android), secure storage (Web), not plain SharedPreferences.

    2. **Auth provider update** (lib/providers/auth_provider.dart):
       - Implement actual login methods (replace stubs from Plan 01):
         - loginWithGoogle() → calls authService.loginWithGoogle(), updates state
         - loginWithMicrosoft() → calls authService.loginWithMicrosoft(), updates state
         - logout() → calls authService.logout(), sets state to unauthenticated
         - checkAuthStatus() → called on app startup, loads token, verifies validity

       State management:
       ```dart
       enum AuthState { unauthenticated, loading, authenticated, error }

       class AuthProvider extends ChangeNotifier {
         AuthState _state = AuthState.unauthenticated;
         User? _user;
         String? _errorMessage;

         Future<void> loginWithGoogle() async {
           _state = AuthState.loading;
           notifyListeners();
           try {
             final token = await _authService.loginWithGoogle();
             _user = await _authService.getCurrentUser();
             _state = AuthState.authenticated;
           } catch (e) {
             _state = AuthState.error;
             _errorMessage = e.toString();
           }
           notifyListeners();
         }
       }
       ```

    3. **Login screen update** (lib/screens/auth/login_screen.dart):
       - Replace placeholder buttons with functional OAuth buttons
       - Google button: Call context.read<AuthProvider>().loginWithGoogle()
       - Microsoft button: Call context.read<AuthProvider>().loginWithMicrosoft()
       - Show loading indicator when AuthState.loading
       - Show error message if AuthState.error
       - Navigate to /home when AuthState.authenticated

    4. **Callback screen** (lib/screens/auth/callback_screen.dart):
       - Handle OAuth redirect: /auth/callback?token=...
       - Extract token from URL query parameter
       - Store token using authService.storeToken()
       - Navigate to /home
       - Show loading spinner during processing

    5. **Update main.dart routing**:
       - Add /auth/callback route → CallbackScreen
       - Update splash screen logic: Check stored token, verify validity, navigate to /login or /home


    6. **Configure mobile deep links for OAuth callback**:
       - **Android** (android/app/src/main/AndroidManifest.xml):
         Add intent-filter to handle OAuth redirect URIs:
         ```xml
         <intent-filter>
             <action android:name="android.intent.action.VIEW" />
             <category android:name="android.intent.category.DEFAULT" />
             <category android:name="android.intent.category.BROWSABLE" />
             <data
                 android:scheme="com.baassistant"
                 android:host="auth"
                 android:pathPrefix="/callback" />
         </intent-filter>
         ```
         This allows `com.baassistant://auth/callback?token=...` to open the app.

       - **iOS** (ios/Runner/Info.plist):
         Add URL scheme and universal links configuration:
         ```xml
         <key>CFBundleURLTypes</key>
         <array>
             <dict>
                 <key>CFBundleTypeRole</key>
                 <string>Editor</string>
                 <key>CFBundleURLSchemes</key>
                 <array>
                     <string>com.baassistant</string>
                 </array>
             </dict>
         </array>
         ```
         This allows `com.baassistant://auth/callback?token=...` to open the app.

       - **Update backend redirect URIs** in auth_service.py to use platform-specific URIs:
         - Web: `http://localhost:8080/auth/callback`
         - Android/iOS: `com.baassistant://auth/callback`
         - Detect platform from User-Agent or use separate mobile endpoints

       WHY mobile deep links: Without proper deep link configuration, OAuth callbacks on mobile fail to return to the app, leaving users stuck in the browser.

    AVOID: Storing token in SharedPreferences (insecure), not validating token expiration, synchronous operations blocking UI, hardcoded API URLs (use config.dart), missing mobile deep link configuration (breaks mobile OAuth).
  </action>
  <verify>
    Run verification commands:
    ```bash
    cd frontend
    flutter analyze
    flutter test
    flutter run -d chrome --web-port=8080
    ```

    Manual testing checklist:
    1. Click "Sign in with Google" button
       - Browser opens to Google OAuth consent screen
       - After approval, redirects to callback screen
       - App navigates to home screen with authenticated state
    2. Restart app
       - Opens directly to home screen (token persisted)
       - User remains authenticated
    3. Click logout
       - Returns to login screen
       - Token removed from storage
    4. Test token expiration:
       - Manually create expired token, store in secure storage
       - App startup detects invalid token, redirects to login
    5. Test mobile deep links (Android/iOS):
       - Complete OAuth flow on mobile device
       - Verify callback redirects back to app (not stuck in browser)
       - Check AndroidManifest.xml has intent-filter
       - Check Info.plist has CFBundleURLTypes

    Verify with Flutter DevTools:
    - No console errors during OAuth flow
    - Token stored in secure storage (not plain text)
    - API calls include Authorization header
  </verify>
  <done>
    - AuthService class implements OAuth flows for Google and Microsoft
    - Token stored securely using flutter_secure_storage
    - Token validation checks expiration before use
    - AuthProvider updates state during login/logout
    - Login screen buttons trigger OAuth flows
    - Callback screen processes OAuth redirect and stores token
    - App checks stored token on startup and validates
    - User remains authenticated across app restarts
    - Error handling shows user-friendly messages
    - Mobile deep links configured for Android (AndroidManifest.xml intent-filter)
    - Mobile deep links configured for iOS (Info.plist URL schemes)
    - OAuth callbacks work correctly on web, Android, and iOS
  </done>
</task>

</tasks>

<verification>
**OAuth flow complete when:**
1. User clicks "Sign in with Google", completes OAuth, returns to app authenticated
2. User clicks "Sign in with Microsoft", completes OAuth, returns to app authenticated
3. User closes and reopens app, remains authenticated (token persisted)
4. User clicks logout button in home screen, token deleted, returns to login screen
5. JWT token contains correct user_id and email in payload
6. Protected backend endpoints require valid JWT, reject missing/invalid tokens
7. Mobile OAuth callbacks work correctly (app opens from browser, not stuck)

**End-to-end test:**
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Flutter web
cd frontend
flutter run -d chrome --web-port=8080

# Terminal 3: Monitor logs
tail -f backend/logs/app.log  # If logging implemented
```

Test flow:
1. Open http://localhost:8080
2. See login screen with Google and Microsoft buttons
3. Click Google → redirects to Google OAuth
4. Approve → returns to app, shows home screen
5. Close browser tab, reopen http://localhost:8080 → opens to home screen (authenticated)
6. Click logout → returns to login screen
</verification>

<success_criteria>
**Measurable completion criteria:**
1. Google OAuth flow works end-to-end (initiate → consent → callback → JWT)
2. Microsoft OAuth flow works end-to-end
3. JWT token persisted in secure storage survives app restart
4. Token expiration correctly detected (expired tokens trigger re-authentication)
5. Protected backend endpoints return 401 for missing/invalid tokens
6. User record created in database after first OAuth login
7. Subsequent logins update existing user record (upsert logic)
8. Logout removes token from storage and returns user to login screen

**Requirements coverage:**
- AUTH-01: User can create account via Google OAuth ✓
- AUTH-02: User can create account via Microsoft OAuth ✓
- AUTH-03: User can log in with Google and stay logged in across sessions ✓
- AUTH-04: User can log in with Microsoft and stay logged in across sessions ✓
- AUTH-05: User can log out from any page ✓

**Goal-backward verification:**
- Truth: "User authenticates with work account" → OAuth flows complete successfully
- Truth: "Authentication persists across sessions" → Token stored securely, survives restart
- Truth: "User can log out" → Logout clears token, returns to login screen
- Truth: "Only authenticated users access protected features" → JWT required for all user-specific endpoints
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation-authentication/01-02-SUMMARY.md` documenting:
- OAuth integration with Google and Microsoft
- JWT generation and verification implementation
- Token storage using flutter_secure_storage
- Auth routes and protected endpoint pattern
- User model creation/update logic
- Mobile deep link configuration (Android intent-filter, iOS URL schemes)
- Logout button implementation in home screen
- Testing instructions for OAuth flows
- OAuth credentials setup instructions (from user_setup)
- Any issues encountered with OAuth consent screens or redirects
</output>
