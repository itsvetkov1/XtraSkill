# Phase 13: Auth Provider Display - Research

**Researched:** 2026-01-30
**Domain:** Flutter AuthProvider state management with settings page profile display
**Confidence:** HIGH

## Summary

Phase 13 adds authentication provider display to the Settings page profile section. This is a minimal feature that requires surfacing data already available from the backend but not currently exposed in the frontend.

The backend `/auth/me` endpoint already returns `oauth_provider` as a string ("google" or "microsoft"). The frontend `AuthProvider` currently fetches this data but discards it. The Settings page profile section exists but only shows email and display name.

The implementation requires:
1. **Adding `authProvider` field to AuthProvider** - Store the `oauth_provider` value from `/auth/me` response
2. **Updating profile tile in settings_screen.dart** - Add a subtitle showing "Signed in with Google" or "Signed in with Microsoft"

No backend changes required. No new dependencies. Estimated: 20-30 minutes of implementation.

**Primary recommendation:** Add `_authProvider` String field to AuthProvider, populate from existing API response, display in profile tile as formatted string.

## Standard Stack

No new libraries required. All implementation uses existing infrastructure.

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `provider` | 6.x | State management | Already used for AuthProvider |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Material 3 widgets | Built-in | UI components | ListTile subtitle text |

### No New Dependencies Required
This phase is purely additive to existing code. Uses only:
- `AuthProvider` existing fetch patterns
- `ListTile` widget already in use in settings_screen.dart

## Architecture Patterns

### Existing Project Structure (No Changes)
```
frontend/lib/
├── providers/
│   └── auth_provider.dart      # MODIFY: Add authProvider field
└── screens/
    └── settings_screen.dart    # MODIFY: Add provider display to profile tile
```

### Pattern 1: AuthProvider Field Addition
**What:** Add nullable string field for OAuth provider
**When to use:** Storing simple string data from API response
**Example:**
```dart
// Source: Existing pattern in auth_provider.dart
class AuthProvider extends ChangeNotifier {
  // Existing fields
  String? _userId;
  String? _email;
  String? _displayName;
  String? _errorMessage;

  // NEW: Auth provider field
  String? _authProvider;  // "google" or "microsoft"

  // NEW: Getter
  String? get authProvider => _authProvider;

  // In checkAuthStatus():
  final user = await _authService.getCurrentUser();
  _userId = user['id'] as String?;
  _email = user['email'] as String?;
  _displayName = user['display_name'] as String?;
  _authProvider = user['oauth_provider'] as String?;  // NEW

  // In handleCallback():
  _authProvider = user['oauth_provider'] as String?;  // NEW

  // In logout():
  _authProvider = null;  // NEW
}
```

### Pattern 2: Profile Tile with Provider Display
**What:** Extend profile ListTile to show authentication method
**When to use:** SETTINGS-01, SETTINGS-02 requirements
**Example:**
```dart
// Source: Existing _buildProfileTile in settings_screen.dart
Widget _buildProfileTile(BuildContext context, AuthProvider authProvider) {
  final email = authProvider.email ?? 'Unknown';
  final displayName = authProvider.displayName;
  final provider = authProvider.authProvider;
  final initials = _getInitials(displayName ?? email);

  return ListTile(
    leading: CircleAvatar(
      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      child: Text(
        initials,
        style: TextStyle(
          color: Theme.of(context).colorScheme.onPrimaryContainer,
          fontWeight: FontWeight.bold,
        ),
      ),
    ),
    title: Text(displayName ?? email),
    subtitle: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (displayName != null) Text(email),
        if (provider != null)
          Text(
            'Signed in with ${_formatProviderName(provider)}',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
      ],
    ),
    isThreeLine: displayName != null && provider != null,
  );
}

String _formatProviderName(String provider) {
  switch (provider.toLowerCase()) {
    case 'google':
      return 'Google';
    case 'microsoft':
      return 'Microsoft';
    default:
      return provider;
  }
}
```

### Anti-Patterns to Avoid
- **Calling API again to get provider:** The data is already fetched in `/auth/me`, just not stored
- **Storing provider in separate storage:** Provider state belongs in AuthProvider with other user data
- **Using icons instead of text for provider:** Requirements specify text format "Signed in with X"
- **Hardcoding provider detection:** Let backend provide canonical provider value

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Provider name formatting | Complex provider detection | Backend-provided `oauth_provider` string | Backend is source of truth |
| Multi-line ListTile | Custom layout widget | ListTile with isThreeLine | Built-in support for 3-line tiles |
| Provider icons | Icon mapping logic | Text-only per requirements | Requirements specify text display |

**Key insight:** The backend already provides the exact data needed. This phase is purely about surfacing it in the UI.

## Common Pitfalls

### Pitfall 1: Forgetting to Clear Provider on Logout
**What goes wrong:** Provider value persists after logout, shown to next user
**Why it happens:** New fields added but logout() not updated
**How to avoid:** Set `_authProvider = null` in logout() alongside other user fields
**Warning signs:** Previous user's provider shown after re-login with different provider

### Pitfall 2: Not Handling Null Provider
**What goes wrong:** "Signed in with null" displayed or null pointer exception
**Why it happens:** API response might not include oauth_provider in edge cases
**How to avoid:**
- Check for null before displaying
- Use conditional rendering: `if (provider != null)`
**Warning signs:** Ugly "null" text or crash on settings page

### Pitfall 3: Case Sensitivity in Provider Name
**What goes wrong:** "Signed in with google" instead of "Signed in with Google"
**Why it happens:** Backend returns lowercase, displayed directly
**How to avoid:** Format provider name with proper capitalization
**Warning signs:** Inconsistent capitalization in UI

### Pitfall 4: ListTile Height Issues with Extra Line
**What goes wrong:** ListTile truncates or clips text
**Why it happens:** Adding subtitle line without setting isThreeLine
**How to avoid:** Set `isThreeLine: true` when both email and provider are shown
**Warning signs:** Ellipsis in subtitle or clipped text

## Code Examples

Verified patterns from existing codebase and official documentation.

### Complete AuthProvider Enhancement
```dart
// Source: Enhancement to existing auth_provider.dart
// File: frontend/lib/providers/auth_provider.dart

class AuthProvider extends ChangeNotifier {
  final AuthService _authService;

  AuthState _state = AuthState.loading;
  String? _userId;
  String? _email;
  String? _displayName;
  String? _errorMessage;
  String? _authProvider;  // NEW: "google" or "microsoft"

  // ... existing constructor ...

  // Existing getters...
  AuthState get state => _state;
  bool get isAuthenticated => _state == AuthState.authenticated;
  bool get isLoading => _state == AuthState.loading;
  String? get userId => _userId;
  String? get email => _email;
  String? get displayName => _displayName;
  String? get errorMessage => _errorMessage;

  // NEW: Auth provider getter
  String? get authProvider => _authProvider;

  Future<void> checkAuthStatus() async {
    _state = AuthState.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      final isValid = await _authService.isTokenValid();

      if (isValid) {
        final user = await _authService.getCurrentUser();
        _userId = user['id'] as String?;
        _email = user['email'] as String?;
        _displayName = user['display_name'] as String?;
        _authProvider = user['oauth_provider'] as String?;  // NEW
        _state = AuthState.authenticated;
      } else {
        _state = AuthState.unauthenticated;
      }
    } catch (e) {
      _state = AuthState.unauthenticated;
      _userId = null;
      _email = null;
      _displayName = null;
      _authProvider = null;  // NEW
    }

    Future.microtask(() => notifyListeners());
  }

  Future<void> handleCallback(String token) async {
    _state = AuthState.loading;
    notifyListeners();

    try {
      await _authService.storeToken(token);
      final user = await _authService.getCurrentUser();

      _userId = user['id'] as String?;
      _email = user['email'] as String?;
      _displayName = user['display_name'] as String?;
      _authProvider = user['oauth_provider'] as String?;  // NEW

      _state = AuthState.authenticated;
      _errorMessage = null;
    } catch (e) {
      _state = AuthState.error;
      _errorMessage = 'Authentication failed: ${e.toString()}';
    }

    Future.microtask(() => notifyListeners());
  }

  Future<void> logout() async {
    _state = AuthState.loading;
    notifyListeners();

    try {
      await _authService.logout();

      _userId = null;
      _email = null;
      _displayName = null;
      _authProvider = null;  // NEW
      _state = AuthState.unauthenticated;
      _errorMessage = null;
    } catch (e) {
      _userId = null;
      _email = null;
      _displayName = null;
      _authProvider = null;  // NEW
      _state = AuthState.unauthenticated;
    }

    Future.microtask(() => notifyListeners());
  }
}
```

### Enhanced Profile Tile
```dart
// Source: Enhancement to existing settings_screen.dart
// File: frontend/lib/screens/settings_screen.dart

Widget _buildProfileTile(BuildContext context, AuthProvider authProvider) {
  final email = authProvider.email ?? 'Unknown';
  final displayName = authProvider.displayName;
  final provider = authProvider.authProvider;
  final initials = _getInitials(displayName ?? email);

  // Determine if we need three lines
  // Line 1: displayName (or email if no displayName)
  // Line 2: email (only if displayName exists)
  // Line 3: "Signed in with X" (if provider exists)
  final hasDisplayName = displayName != null;
  final hasProvider = provider != null;
  final isThreeLine = hasDisplayName && hasProvider;

  return ListTile(
    leading: CircleAvatar(
      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      child: Text(
        initials,
        style: TextStyle(
          color: Theme.of(context).colorScheme.onPrimaryContainer,
          fontWeight: FontWeight.bold,
        ),
      ),
    ),
    title: Text(displayName ?? email),
    subtitle: _buildProfileSubtitle(context, email, displayName, provider),
    isThreeLine: isThreeLine,
  );
}

Widget? _buildProfileSubtitle(
  BuildContext context,
  String email,
  String? displayName,
  String? provider,
) {
  final lines = <Widget>[];

  // Show email if we have a display name (email becomes secondary)
  if (displayName != null) {
    lines.add(Text(email));
  }

  // Show provider if available
  if (provider != null) {
    lines.add(
      Text(
        'Signed in with ${_formatProviderName(provider)}',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      ),
    );
  }

  if (lines.isEmpty) return null;
  if (lines.length == 1) return lines.first;

  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: lines,
  );
}

String _formatProviderName(String provider) {
  switch (provider.toLowerCase()) {
    case 'google':
      return 'Google';
    case 'microsoft':
      return 'Microsoft';
    default:
      return provider;
  }
}
```

## Backend API Reference

The backend already provides the required data. No backend changes needed.

### GET /auth/me Response
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "display_name": "John Doe",
  "oauth_provider": "google",
  "created_at": "2026-01-30T12:00:00Z"
}
```

**oauth_provider values:**
- `"google"` - User authenticated with Google OAuth
- `"microsoft"` - User authenticated with Microsoft OAuth

Source: `backend/app/routes/auth.py` lines 247-253

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Multi-line ListTile with custom padding | ListTile.isThreeLine property | Always available | Cleaner code, consistent spacing |
| Provider icons next to text | Text-only display | Material 3 guidance | Simpler, more accessible |

**Deprecated/outdated:**
- N/A - This is a simple feature addition

## Implementation Checklist

### Pre-Implementation Verification
- [x] Backend `/auth/me` returns `oauth_provider` - VERIFIED in auth.py line 251
- [x] OAuthProvider enum has GOOGLE and MICROSOFT values - VERIFIED in models.py lines 23-26
- [x] Settings page profile section exists - VERIFIED in settings_screen.dart

### Implementation Steps
1. **AuthProvider enhancement** (~10 min)
   - Add `_authProvider` private field
   - Add `authProvider` getter
   - Update `checkAuthStatus()` to store provider
   - Update `handleCallback()` to store provider
   - Update `logout()` to clear provider

2. **Settings screen enhancement** (~15 min)
   - Update `_buildProfileTile()` to show provider
   - Add `_formatProviderName()` helper
   - Handle isThreeLine logic
   - Test both Google and Microsoft displays

### Testing
- Login with Google, verify "Signed in with Google" displays
- Login with Microsoft, verify "Signed in with Microsoft" displays
- Logout, verify no provider persists
- Re-login, verify correct provider shown

## Open Questions

None. Requirements are clear and implementation path is straightforward.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `auth_provider.dart` - AuthProvider pattern
- Existing codebase: `settings_screen.dart` - Profile tile implementation
- Existing codebase: `backend/app/routes/auth.py` - API response format
- Existing codebase: `backend/app/models.py` - OAuthProvider enum values

### Secondary (MEDIUM confidence)
- [Flutter ListTile API](https://api.flutter.dev/flutter/material/ListTile-class.html) - isThreeLine property

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new packages, existing patterns only
- Architecture: HIGH - Simple field addition to existing provider
- UI changes: HIGH - Minor enhancement to existing tile
- Pitfalls: HIGH - Well-understood edge cases

**Research date:** 2026-01-30
**Valid until:** 2026-04-30 (90 days - very stable, no external dependencies)
