# Phase 8: Settings Page & User Preferences - Research

**Researched:** 2026-01-29
**Domain:** Flutter Settings page with user profile display, logout confirmation, and token usage visualization
**Confidence:** HIGH

## Summary

Phase 8 completes the Settings page by adding user profile display (SET-01), logout with confirmation (SET-02), and token budget visualization (SET-05). The current `settings_screen.dart` already implements the theme toggle (SET-03) and uses the content-only pattern established in Phase 7 where ResponsiveScaffold provides all navigation UI.

The implementation requires:
1. **Enhancing the /auth/me endpoint** to return display name from OAuth providers (currently only returns email)
2. **Creating a new /auth/usage endpoint** to expose monthly token usage statistics
3. **Enhancing AuthProvider** to store display name and provide a logout method with confirmation flow
4. **Creating a TokenUsageProvider** (or expanding AuthProvider) to fetch and display usage data
5. **Expanding the Settings screen** with profile section, logout button, and token usage visualization

The backend already has `get_monthly_usage()` in `token_tracking.py` but no API endpoint exposes it. The OAuth services already fetch display names from Google and Microsoft APIs but don't persist them to the database.

**Primary recommendation:** Add display name to User model, expose /auth/usage endpoint, implement confirmation dialog pattern for logout, use LinearProgressIndicator with percentage display for token budget visualization.

## Standard Stack

The established libraries/tools for this phase are already in the project:

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `provider` | 6.x | State management | Already used for ThemeProvider, AuthProvider |
| `dio` | 5.x | HTTP client | Already used for all API services |
| `flutter_secure_storage` | 9.x | Token storage | Already used for JWT storage |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Material 3 widgets | Built-in | UI components | ListTile, SwitchListTile, AlertDialog, LinearProgressIndicator |

### No New Dependencies Required
This phase uses only existing packages. Key widgets from Flutter's material library:
- `AlertDialog` - Logout confirmation dialog
- `LinearProgressIndicator` - Token budget visualization
- `ListTile` - Settings sections (profile, logout)
- `CircleAvatar` - User avatar placeholder (initials-based)

## Architecture Patterns

### Recommended Project Structure (Additions)
```
lib/
├── providers/
│   ├── auth_provider.dart      # ADD: displayName, logout confirmation
│   └── usage_provider.dart     # NEW: Token usage data fetching
├── services/
│   └── auth_service.dart       # ADD: getUsage() method
├── models/
│   └── token_usage.dart        # NEW: Usage data model
└── screens/
    └── settings_screen.dart    # EXPAND: Profile section, logout, usage

backend/app/
├── routes/
│   └── auth.py                 # ADD: /auth/usage endpoint
├── models.py                   # ADD: display_name to User
└── services/
    └── auth_service.py         # ADD: Store display_name from OAuth
```

### Pattern 1: Settings Page Section Structure
**What:** Organize settings into semantic sections with headers
**When to use:** Always - Material 3 design pattern for settings pages
**Example:**
```dart
// Source: Material Design 3 Settings patterns
ListView(
  children: [
    // Account Section
    _buildSectionHeader(context, 'Account'),
    ListTile(
      leading: CircleAvatar(child: Text(initials)),
      title: Text(displayName ?? email),
      subtitle: Text(email),
    ),
    const Divider(),

    // Appearance Section
    _buildSectionHeader(context, 'Appearance'),
    SwitchListTile(
      title: const Text('Dark Mode'),
      value: isDarkMode,
      onChanged: (_) => toggleTheme(),
    ),
    const Divider(),

    // Usage Section
    _buildSectionHeader(context, 'Usage'),
    _TokenUsageListTile(),
    const Divider(),

    // Actions Section
    _buildSectionHeader(context, 'Actions'),
    ListTile(
      leading: const Icon(Icons.logout, color: Colors.red),
      title: const Text('Log Out', style: TextStyle(color: Colors.red)),
      onTap: () => _showLogoutConfirmation(context),
    ),
  ],
)
```

### Pattern 2: Logout Confirmation Dialog
**What:** AlertDialog with destructive action confirmation
**When to use:** Always before logout (SET-02 requirement)
**Example:**
```dart
// Source: https://api.flutter.dev/flutter/material/AlertDialog-class.html
Future<void> _showLogoutConfirmation(BuildContext context) async {
  final confirmed = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (BuildContext context) {
      return AlertDialog(
        title: const Text('Log Out'),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Log Out'),
          ),
        ],
      );
    },
  );

  if (confirmed == true && context.mounted) {
    await context.read<AuthProvider>().logout();
    // GoRouter redirect handles navigation to login
  }
}
```

### Pattern 3: Token Usage Progress Indicator
**What:** LinearProgressIndicator with percentage label for budget visualization
**When to use:** SET-05 requirement for token budget display
**Example:**
```dart
// Source: https://api.flutter.dev/flutter/material/LinearProgressIndicator-class.html
class _TokenUsageListTile extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<UsageProvider>(
      builder: (context, usageProvider, _) {
        if (usageProvider.isLoading) {
          return const ListTile(
            title: Text('Token Usage'),
            subtitle: LinearProgressIndicator(),
          );
        }

        final usage = usageProvider.usage;
        if (usage == null) {
          return const ListTile(
            title: Text('Token Usage'),
            subtitle: Text('Unable to load usage data'),
          );
        }

        final usedTokens = usage.totalInputTokens + usage.totalOutputTokens;
        final budgetTokens = 10000; // Or from usage.budgetTokens
        final percentage = (usedTokens / budgetTokens).clamp(0.0, 1.0);
        final percentText = (percentage * 100).toStringAsFixed(1);

        return ListTile(
          title: const Text('Token Usage'),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: percentage,
                backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
                color: percentage > 0.8
                    ? Colors.orange
                    : Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 4),
              Text(
                '${_formatNumber(usedTokens)} / ${_formatNumber(budgetTokens)} tokens ($percentText%)',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        );
      },
    );
  }

  String _formatNumber(int number) {
    if (number >= 1000) {
      return '${(number / 1000).toStringAsFixed(1)}K';
    }
    return number.toString();
  }
}
```

### Pattern 4: User Profile Display with Initials Avatar
**What:** Show user email and display name with initials-based avatar
**When to use:** SET-01 requirement
**Example:**
```dart
// Source: Material 3 design patterns
Widget _buildProfileTile(BuildContext context, AuthProvider authProvider) {
  final email = authProvider.email ?? 'Unknown';
  final displayName = authProvider.displayName;
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
    subtitle: displayName != null ? Text(email) : null,
  );
}

String _getInitials(String name) {
  final parts = name.split(RegExp(r'[\s@]+')).where((p) => p.isNotEmpty).toList();
  if (parts.isEmpty) return '?';
  if (parts.length == 1) return parts[0][0].toUpperCase();
  return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
}
```

### Anti-Patterns to Avoid
- **Navigating after async without context.mounted check:** Always verify context is still valid after await
- **Using BuildContext across async gaps:** Store provider reference before await, not after
- **Hardcoding budget values:** Fetch from backend, allow for per-user customization later
- **Blocking UI during logout:** Show loading state but don't prevent cancellation
- **Missing error handling on usage fetch:** Always provide fallback UI for failed API calls

## Don't Hand-Roll

Problems with existing solutions that should NOT be custom-built:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Confirmation dialogs | Custom modal/bottom sheet | AlertDialog with showDialog | Standard Material pattern, keyboard accessible, handles barrier taps |
| Progress visualization | Custom painted progress bar | LinearProgressIndicator | Built-in Material 3 styling, accessibility, animation |
| Number formatting | Manual string building | NumberFormat from intl package (if needed) | Locale-aware, handles edge cases |
| Avatar generation | Image loading/fallback logic | CircleAvatar with initials | Built-in, handles sizing, theming |

**Key insight:** All UI components for this phase exist in Flutter's material library. The complexity is in backend API additions and proper state management integration.

## Common Pitfalls

### Pitfall 1: BuildContext After Async
**What goes wrong:** Navigator or Provider call fails with "deactivated widget" error
**Why it happens:** Widget disposed during async operation
**How to avoid:**
- Check `context.mounted` before using context after await
- Store provider reference before async operation
- Use callback pattern for dialog results
**Warning signs:** Random crashes on logout or navigation

### Pitfall 2: Logout State Race Condition
**What goes wrong:** User sees partial UI or error after logout
**Why it happens:** Auth state changes while screens still building
**How to avoid:**
- GoRouter redirect handles navigation automatically
- Don't manually navigate after logout()
- AuthProvider.logout() clears state atomically
**Warning signs:** Flash of authenticated content after logout

### Pitfall 3: Token Usage Stale Data
**What goes wrong:** Usage shows outdated values after AI conversation
**Why it happens:** Usage fetched once on settings page open, not refreshed
**How to avoid:**
- Fetch on page open (WidgetsBinding.addPostFrameCallback)
- Consider periodic refresh or pull-to-refresh
- Show "as of" timestamp
**Warning signs:** Usage appears lower than expected after heavy AI use

### Pitfall 4: Display Name Missing for Existing Users
**What goes wrong:** Existing users see only email, no display name
**Why it happens:** User model initially didn't store display name
**How to avoid:**
- Handle null displayName gracefully (show email)
- Migration to add column with NULL default
- Display name populated on next OAuth login
**Warning signs:** Blank profile section for existing users

### Pitfall 5: Usage Endpoint Authorization
**What goes wrong:** 401 errors on usage fetch
**Why it happens:** Forgetting to add auth dependency to new endpoint
**How to avoid:**
- New endpoint uses same `Depends(get_current_user)` pattern
- Test with expired token to verify auth check
**Warning signs:** Usage section shows error even when logged in

## Code Examples

Verified patterns from the existing codebase:

### Backend: Add /auth/usage Endpoint
```python
# Source: Pattern from existing auth.py routes
@router.get("/usage")
async def get_user_usage(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current month token usage for authenticated user.

    Requires valid JWT token in Authorization header.

    Returns:
        Usage object with total_cost, total_requests, total_input_tokens,
        total_output_tokens, month_start, budget
    """
    from app.services.token_tracking import get_monthly_usage

    usage = await get_monthly_usage(db, user["user_id"])

    return {
        "total_cost": float(usage["total_cost"]),
        "total_requests": usage["total_requests"],
        "total_input_tokens": usage["total_input_tokens"],
        "total_output_tokens": usage["total_output_tokens"],
        "month_start": usage["month_start"],
        "budget": float(usage["budget"]),
    }
```

### Backend: Enhanced /auth/me with Display Name
```python
# Source: Enhanced version of existing auth.py /me endpoint
@router.get("/me")
async def get_current_user_info(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user information."""
    from sqlalchemy import select
    from app.models import User

    stmt = select(User).where(User.id == user["user_id"])
    result = await db.execute(stmt)
    user_obj = result.scalar_one_or_none()

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": user_obj.id,
        "email": user_obj.email,
        "display_name": user_obj.display_name,  # NEW
        "oauth_provider": user_obj.oauth_provider.value,
        "created_at": user_obj.created_at.isoformat(),
    }
```

### Frontend: UsageService
```dart
// Source: Pattern from existing project_service.dart
class UsageService {
  final Dio _dio;
  final FlutterSecureStorage _storage;
  final String _baseUrl;

  UsageService({
    String? baseUrl,
    Dio? dio,
    FlutterSecureStorage? storage,
  })  : _baseUrl = baseUrl ?? 'http://localhost:8000',
        _dio = dio ?? Dio(),
        _storage = storage ?? const FlutterSecureStorage();

  static const String _tokenKey = 'auth_token';

  Future<Map<String, String>> _getHeaders() async {
    final token = await _storage.read(key: _tokenKey);
    if (token == null) throw Exception('Not authenticated');
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  Future<TokenUsage> getMonthlyUsage() async {
    final headers = await _getHeaders();
    final response = await _dio.get(
      '$_baseUrl/auth/usage',
      options: Options(headers: headers),
    );
    return TokenUsage.fromJson(response.data);
  }
}
```

### Frontend: TokenUsage Model
```dart
// Source: New model following existing project.dart pattern
class TokenUsage {
  final double totalCost;
  final int totalRequests;
  final int totalInputTokens;
  final int totalOutputTokens;
  final String monthStart;
  final double budget;

  TokenUsage({
    required this.totalCost,
    required this.totalRequests,
    required this.totalInputTokens,
    required this.totalOutputTokens,
    required this.monthStart,
    required this.budget,
  });

  factory TokenUsage.fromJson(Map<String, dynamic> json) {
    return TokenUsage(
      totalCost: (json['total_cost'] as num).toDouble(),
      totalRequests: json['total_requests'] as int,
      totalInputTokens: json['total_input_tokens'] as int,
      totalOutputTokens: json['total_output_tokens'] as int,
      monthStart: json['month_start'] as String,
      budget: (json['budget'] as num).toDouble(),
    );
  }

  int get totalTokens => totalInputTokens + totalOutputTokens;

  double get costPercentage => (totalCost / budget).clamp(0.0, 1.0);
}
```

### Frontend: Enhanced AuthProvider
```dart
// Source: Addition to existing auth_provider.dart
class AuthProvider extends ChangeNotifier {
  // ... existing fields ...
  String? _displayName;

  String? get displayName => _displayName;

  Future<void> checkAuthStatus() async {
    // ... existing code ...
    if (isValid) {
      final user = await _authService.getCurrentUser();
      _userId = user['id'] as String?;
      _email = user['email'] as String?;
      _displayName = user['display_name'] as String?;  // NEW
      _state = AuthState.authenticated;
    }
    // ... rest unchanged ...
  }

  Future<void> handleCallback(String token) async {
    // ... existing code, add:
    _displayName = user['display_name'] as String?;  // NEW
    // ... rest unchanged ...
  }

  Future<void> logout() async {
    // Existing logout already works correctly
    // GoRouter redirect handles navigation
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual dialog state management | showDialog returns Future<T> | Always current | Cleaner async/await confirmation pattern |
| Custom progress bars | LinearProgressIndicator with year2023:false | Material 3 2024 | Modern appearance matches Material 3 |
| Separate settings categories on different pages | Single scrollable ListView with sections | Material 3 guidelines | Better discoverability, less navigation |

**Deprecated/outdated:**
- Using `showDialog` without `barrierDismissible` specification - always explicit about dismissability
- Legacy ProgressIndicator styling - use Material 3 defaults

## Implementation Dependencies

### Backend Changes Required
1. **Add display_name to User model** - Nullable string field
2. **Database migration** - Add column with NULL default
3. **Update OAuth services** - Store display name from provider APIs:
   - Google: `user_info["name"]` from userinfo endpoint
   - Microsoft: `user_info["displayName"]` from Graph API
4. **Enhance /auth/me endpoint** - Include display_name in response
5. **Create /auth/usage endpoint** - Expose existing get_monthly_usage()

### Frontend Changes Required
1. **Enhance AuthProvider** - Store displayName, fetch on auth check
2. **Create UsageService** - API client for /auth/usage
3. **Create UsageProvider** (optional) - Or fetch usage in SettingsScreen directly
4. **Expand settings_screen.dart** - Add profile section, logout button, usage display

### Order of Implementation
1. Backend: display_name field and migration
2. Backend: /auth/usage endpoint
3. Frontend: AuthProvider enhancement
4. Frontend: UsageService and model
5. Frontend: Settings screen expansion

## Open Questions

1. **Token Budget Display Unit**
   - What we know: SET-05 says "1,234 / 10,000 tokens used (12%)" - token count
   - What's unclear: Backend tracks cost ($), not raw token count; budget is in dollars
   - Recommendation: Display cost-based ("$0.50 / $50.00 used") OR convert to estimated tokens. Discuss with stakeholder which is more meaningful to users.

2. **Display Name Storage Strategy**
   - What we know: Google/Microsoft both provide display names
   - What's unclear: Should display_name update on every login (provider changed name) or only on first creation?
   - Recommendation: Update on every login to stay current with provider

3. **Usage Refresh Strategy**
   - What we know: Usage can change after AI conversations
   - What's unclear: How stale is acceptable? Real-time vs. on-demand refresh?
   - Recommendation: Fetch on settings page open, show "Last updated" timestamp, no auto-refresh (MVP simplicity)

## Sources

### Primary (HIGH confidence)
- [Flutter AlertDialog API](https://api.flutter.dev/flutter/material/AlertDialog-class.html) - Official confirmation dialog pattern
- [Flutter LinearProgressIndicator API](https://api.flutter.dev/flutter/material/LinearProgressIndicator-class.html) - Progress visualization
- [Material Design 3 for Flutter](https://m3.material.io/develop/flutter) - Settings page design patterns
- Existing codebase: `auth_provider.dart`, `theme_provider.dart`, `settings_screen.dart` - Established patterns

### Secondary (MEDIUM confidence)
- [Migrate to Material 3](https://docs.flutter.dev/release/breaking-changes/material-3-migration) - Current Material 3 component styling
- [Material Design Settings patterns](https://m3.material.io/components) - Section organization guidelines
- Backend `token_tracking.py` - Existing usage calculation logic

### Tertiary (LOW confidence)
- [percent_indicator package](https://pub.dev/packages/percent_indicator) - Alternative progress visualization (not recommended, built-in sufficient)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new packages required, all patterns verified from existing code
- Architecture: HIGH - Follows established provider/service patterns in codebase
- Backend changes: HIGH - Clear extension of existing endpoints and models
- Pitfalls: MEDIUM - Based on common Flutter async/state issues

**Research date:** 2026-01-29
**Valid until:** 2026-03-29 (60 days - stable patterns, no external dependencies changing)
