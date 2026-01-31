# Phase 18: Validation - Research

**Researched:** 2026-01-31
**Domain:** End-to-end deep linking validation, edge case testing, production deployment documentation
**Confidence:** HIGH

## Summary

Phase 18 is a validation phase, not a feature implementation phase. The goal is to verify that all deep linking features from Phases 15-17 work correctly end-to-end, document edge cases, and create production deployment documentation for SPA rewrite rules.

The implementation is already complete:
1. **Phase 15:** NotFoundScreen for 404 errors, nested thread routes (`/projects/:id/threads/:threadId`)
2. **Phase 16:** UrlStorageService using sessionStorage, GoRouter redirect with returnUrl, Login/Callback integration
3. **Phase 17:** ResourceNotFoundState widget, isNotFound flags in providers, GoRouter.optionURLReflectsImperativeAPIs

The one remaining requirement (ERR-04: Invalid returnUrl after login) needs verification and potential graceful handling. The current implementation already validates returnUrl starts with `/` and falls back to `/home` for invalid URLs, but the specific case of deleted resources needs verification.

**Primary recommendation:** Create a comprehensive test plan document, execute manual tests, document results, and create production deployment guide for SPA rewrite rules.

## Standard Stack

This phase requires no new libraries - validation uses existing implementation.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| go_router | ^17.0.1 | Routing validation target | Already in use, being validated |
| sessionStorage | SDK | URL preservation target | Already implemented via UrlStorageService |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None | - | No new dependencies | Validation phase |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual testing | Integration tests | Integration tests for web deep linking are complex; manual testing is appropriate for validation phase |
| DevTools deep link validator | Manual browser testing | DevTools validator is for mobile app links, not web SPA routing |

**Installation:**
```bash
# No new packages needed - validation phase
```

## Architecture Patterns

### Recommended Project Structure
```
.planning/phases/18-validation/
|-- 18-RESEARCH.md           # This file
|-- 18-01-PLAN.md            # Test execution plan
|-- 18-01-VERIFICATION.md    # Test results (created during execution)
|-- PRODUCTION-DEPLOYMENT.md # SPA rewrite rules documentation
```

### Pattern 1: Validation Test Matrix
**What:** Systematic coverage of all deep linking scenarios
**When to use:** End-to-end validation phase
**Example:**
```markdown
| Test ID | Scenario | Input | Expected | Actual | Status |
|---------|----------|-------|----------|--------|--------|
| VAL-01 | Direct project URL | /projects/abc | Project loads | | |
| VAL-02 | Project refresh | F5 on /projects/abc | Same page | | |
| VAL-03 | Deleted project URL | /projects/deleted | Not-found state | | |
```

### Pattern 2: Edge Case Documentation
**What:** Document discovered edge cases and their handling
**When to use:** During validation when unexpected behaviors found
**Example:**
```markdown
### Edge Case: ReturnUrl to Deleted Resource
**Scenario:** User clicks shared link to deleted project while logged out
**Current behavior:** Login succeeds, navigates to /projects/deleted, shows "Project not found"
**Expected:** Graceful error state (not crash)
**Status:** PASSES
```

### Pattern 3: Production Deployment Guide
**What:** Server configuration documentation for SPA routing
**When to use:** Preparing for production deployment
**Example:**
```markdown
## Nginx Configuration

server {
    listen 80;
    server_name example.com;
    root /var/www/flutter_app;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Anti-Patterns to Avoid
- **Skipping edge cases:** Test happy path AND failure paths
- **Not documenting server config:** Production SPA issues are common; document now
- **Assuming implementation is correct:** Validation exists because bugs hide

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SPA routing | Custom 404 handlers | Server rewrite rules | Web servers handle this well |
| Deep link validation | Manual URL testing | Systematic test matrix | Ensures coverage |
| Error state detection | Ad-hoc checking | Existing isNotFound flags | Already implemented in Phase 17 |

**Key insight:** The implementation is already done. This phase validates it works correctly across all scenarios and documents production requirements.

## Common Pitfalls

### Pitfall 1: Production Server 404 on Refresh
**What goes wrong:** Browser shows server 404 (not Flutter NotFoundScreen) when refreshing deep links
**Why it happens:** Production server doesn't have SPA rewrite rules configured
**How to avoid:** Document server configuration requirements in PRODUCTION-DEPLOYMENT.md
**Warning signs:** Works in development (`flutter run`), fails in production

### Pitfall 2: Missing Test Coverage for Deleted Resources
**What goes wrong:** ERR-04 (deleted resource via returnUrl) not tested, crashes in production
**Why it happens:** Happy path tested, edge cases skipped
**How to avoid:** Include deleted resource scenarios in test matrix
**Warning signs:** Only testing with existing resources

### Pitfall 3: Not Clearing Test State Between Tests
**What goes wrong:** Test results affected by previous test state
**Why it happens:** sessionStorage, provider state, or browser history not reset
**How to avoid:** Clear sessionStorage and reload between tests; use incognito windows
**Warning signs:** Inconsistent test results

### Pitfall 4: OAuth Callback State Loss
**What goes wrong:** returnUrl lost during OAuth redirect
**Why it happens:** sessionStorage cleared, OAuth took too long, or tab closed
**How to avoid:** Test complete OAuth flow including returnUrl preservation
**Warning signs:** Always landing on /home after OAuth despite having returnUrl

### Pitfall 5: Open Redirect Vulnerability Not Validated
**What goes wrong:** Malicious returnUrl like `https://evil.com` not rejected
**Why it happens:** Security validation not tested
**How to avoid:** Include negative tests with external URLs
**Warning signs:** Only testing valid returnUrl values

## Code Examples

Verified patterns from existing codebase:

### Current returnUrl Validation (callback_screen.dart)
```dart
// Source: frontend/lib/screens/auth/callback_screen.dart lines 74-81
// Validate returnUrl (security: prevent open redirect)
String destination = '/home';
if (returnUrl != null && returnUrl.startsWith('/')) {
  destination = returnUrl;
  print('DEBUG: Using returnUrl as destination: $destination');
} else if (returnUrl != null) {
  print('DEBUG: Invalid returnUrl (not relative path), falling back to /home');
}
```

### Current Not-Found Handling (project_detail_screen.dart)
```dart
// Source: frontend/lib/screens/projects/project_detail_screen.dart lines 75-85
// Show not-found state (ERR-02) - check BEFORE generic error
if (provider.isNotFound) {
  return ResourceNotFoundState(
    icon: Icons.folder_off_outlined,
    title: 'Project not found',
    message: 'This project may have been deleted or you may not have access to it.',
    buttonLabel: 'Back to Projects',
    onPressed: () => context.go('/projects'),
  );
}
```

### Current isNotFound Detection (project_provider.dart)
```dart
// Source: frontend/lib/providers/project_provider.dart lines 124-133
// Check if it's a 404 "not found" error (from project_service.dart)
if (errorMessage.contains('not found') ||
    errorMessage.contains('404')) {
  _isNotFound = true;
  _error = null; // Not a "real" error, just not found
} else {
  _error = errorMessage;
  _isNotFound = false;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hash URLs (#/path) | Path URLs (/path) | go_router 6.0+ | Requires server rewrite rules |
| Generic 404 page | Resource-specific not-found states | Phase 17 | Better UX for deleted resources |
| In-memory returnUrl | sessionStorage returnUrl | Phase 16 | Survives OAuth redirect |

**Deprecated/outdated:**
- Hash URL strategy: Now using PathUrlStrategy
- Manual route checking: Now using GoRouter errorBuilder

## Open Questions

Things that couldn't be fully resolved:

1. **Production server platform**
   - What we know: Development uses `flutter run` which handles SPA routing automatically
   - What's unclear: What server will host production (nginx, Apache, Vercel, Firebase Hosting?)
   - Recommendation: Document common configurations; user selects appropriate one

2. **Cross-browser testing**
   - What we know: Chrome tested during development
   - What's unclear: Firefox, Safari, Edge behavior for sessionStorage and URL handling
   - Recommendation: Test in major browsers during validation

3. **Mobile web behavior**
   - What we know: Desktop web tested
   - What's unclear: Mobile browser deep link handling
   - Recommendation: Note as out of scope for v1.7; mobile web is secondary target

## Validation Test Categories

### Category 1: Route Navigation (ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04)
Tests verifying URL structure and navigation:
- Thread URLs show correct path
- Browser back/forward works on nested routes
- Invalid routes show 404 page
- ConversationScreen accepts URL parameters

### Category 2: URL Preservation (URL-01 through URL-04, AUTH-01 through AUTH-04)
Tests verifying URL survives auth flow:
- Page refresh preserves URL for authenticated users
- OAuth flow preserves returnUrl via sessionStorage
- Settings/project refresh returns to correct page
- returnUrl cleared after use

### Category 3: Error Handling (ERR-01 through ERR-04)
Tests verifying graceful error states:
- Invalid route path shows 404
- Non-existent project shows not-found state
- Non-existent thread shows not-found state
- Deleted resource via returnUrl handled gracefully (ERR-04)

### Category 4: Security Validation
Tests verifying security measures:
- External URL in returnUrl rejected
- Malformed returnUrl handled gracefully
- sessionStorage isolation (per-origin)

### Category 5: Production Deployment
Documentation and verification:
- SPA rewrite rules documented for nginx, Apache, Vercel
- Base href configuration documented
- HTTPS requirements noted

## Production Deployment Requirements

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/flutter_app/build/web;
    index index.html;

    # Critical: SPA rewrite rule for deep linking
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Optional: Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Apache Configuration
```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /

    # Don't rewrite files or directories
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d

    # Rewrite everything else to index.html
    RewriteRule ^ index.html [L]
</IfModule>
```

### Vercel Configuration (vercel.json)
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/" }
  ]
}
```

### Firebase Hosting Configuration (firebase.json)
```json
{
  "hosting": {
    "public": "build/web",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

### Base Href Configuration
```html
<!-- web/index.html -->
<!-- For root domain deployment: -->
<base href="/">

<!-- For subdirectory deployment (e.g., example.com/app/): -->
<base href="/app/">
```

## Sources

### Primary (HIGH confidence)
- Existing codebase: Phase 15-17 implementations verified via code review
- [Flutter Web Deployment Docs](https://docs.flutter.dev/deployment/web) - Official build and release guide
- [Flutter URL Strategies](https://docs.flutter.dev/ui/navigation/url-strategies) - PathUrlStrategy configuration

### Secondary (MEDIUM confidence)
- [Flutter GitHub Issue #89763](https://github.com/flutter/flutter/issues/89763) - PathUrlStrategy server behavior docs
- [Flutter GitHub Issue #90712](https://github.com/flutter/flutter/issues/90712) - F5 refresh 404 issue with path strategy
- [4Each Forum - Nginx Flutter Web](https://www.4each.com.br/threads/flutter-how-to-properly-serve-flutter-web-app-with-nginx.97415/) - Nginx configuration

### Tertiary (LOW confidence)
- WebSearch results for production deployment patterns - community configurations

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Validation phase, no new dependencies
- Architecture: HIGH - Test matrix pattern is well-established
- Pitfalls: HIGH - Identified from prior phase research and common SPA deployment issues

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (validation patterns stable)

---

## Implementation Checklist (For Planner)

Phase 18 should implement:

### Plan 1: End-to-End Validation
1. **Create comprehensive test matrix** covering all 16 requirements
2. **Execute manual tests** for each scenario
3. **Document results** in VERIFICATION.md
4. **Document edge cases** discovered during testing
5. **Verify ERR-04** specifically (returnUrl to deleted resource)

### Plan 2: Production Deployment Documentation
1. **Create PRODUCTION-DEPLOYMENT.md** with server configurations
2. **Document nginx configuration** (most common)
3. **Document Apache configuration** (.htaccess)
4. **Document Vercel configuration** (vercel.json)
5. **Document Firebase Hosting configuration** (firebase.json)
6. **Document base href requirements**
7. **Add troubleshooting section** for common issues

### Testing Environment
- Start backend: `cd backend && python run.py`
- Start frontend: `cd frontend && flutter run -d chrome`
- Use incognito windows for clean state between tests
- Test with existing resources AND deleted/non-existent resources

### Security Validation
- Test returnUrl with external URL (should reject)
- Test returnUrl with malformed path (should fall back to /home)
- Verify sessionStorage is per-origin

**No package installations needed.**
**No code changes expected** (validation phase).
**Documentation artifacts created.**
