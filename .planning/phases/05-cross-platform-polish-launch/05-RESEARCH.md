# Phase 5: Cross-Platform Polish & Launch - Research

**Researched:** 2026-01-28
**Domain:** Flutter cross-platform quality assurance, production deployment, UI polish
**Confidence:** HIGH

## Summary

Phase 5 transforms a functionally complete MVP into a production-ready application across web, Android, and iOS. Research reveals Flutter has entered its "Production Era" in 2026 with mature tooling, stable rendering (Impeller), and enterprise-grade reliability. The standard approach involves: (1) comprehensive cross-platform testing using unit/widget/integration test pyramid, (2) systematic UI polish with skeleton loaders and Material 3 error patterns, (3) production deployment with PaaS platforms (Railway/Render) using environment-specific OAuth configurations, (4) platform-specific validation across browsers and mobile devices, and (5) quality gates around performance metrics, code signing, and behavioral verification.

Key findings: Flutter 3.x with Impeller eliminates shader jank on iOS/Android, Material 3 is now default with proven adaptive patterns, skeletonizer package provides zero-effort skeleton loaders, separate OAuth app registrations are required for dev/prod environments, and GitHub Actions provides mature CI/CD pipelines for automated testing and deployment. Browser compatibility remains challenging (Safari lacks WasmGC), but testing in Chrome → Firefox → Edge → Safari order catches issues early.

**Primary recommendation:** Implement test pyramid (many unit/widget, selective integration), add skeletonizer for loading states, configure separate OAuth credentials per environment, deploy backend to Railway/Render with Gunicorn+Uvicorn workers, validate on real devices before store submission, and establish CI/CD pipeline with automated quality gates.

## Standard Stack

### Core Testing & Quality

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flutter_test | SDK | Widget and unit testing | Built-in Flutter testing framework, zero-config |
| integration_test | SDK | End-to-end testing | Official integration testing package, runs on real devices |
| mockito | 5.6.3+ | Mocking dependencies | De facto standard for Dart/Flutter mocking |
| flutter_lints | 5.0.0+ | Static analysis | Official Flutter lint rules, enforces best practices |

### UI Polish

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| skeletonizer | 2.1.2+ | Skeleton loaders | Auto-converts widgets to skeletons, zero duplication, Material 3 compatible |
| Material 3 | SDK (default) | Design system | Default since Flutter 3.16, adaptive components, proven patterns |

### Production Deployment

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Railway | Current | Backend PaaS hosting | Git-based deployment, managed HTTPS, environment variables, PostgreSQL/SQLite support |
| Render | Current | Alternative PaaS | Infrastructure-as-code (render.yaml), auto HTTPS, managed databases |
| Gunicorn + Uvicorn | Latest | Production ASGI server | FastAPI official recommendation for multi-core utilization |
| GitHub Actions | Current | CI/CD pipeline | Native GitHub integration, flutter-action available, free for public repos |

### Mobile Deployment

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Fastlane | Latest | iOS/Android automation | Industry standard for mobile CI/CD, automates signing and store uploads |
| Codemagic CLI | Latest | Code signing automation | Handles iOS signing without Mac, integrates with CI/CD |

### Installation

**Backend production server:**
```bash
pip install gunicorn uvicorn[standard]
```

**Frontend testing:**
```bash
flutter pub add --dev mockito build_runner
flutter pub add skeletonizer
```

**CI/CD (GitHub Actions - no local install):**
```yaml
# See Architecture Patterns section for workflow configuration
```

## Architecture Patterns

### Recommended Testing Structure

```
test/
├── unit/                    # Business logic tests
│   ├── services/           # AI service, auth, etc.
│   └── models/             # Data models
├── widget/                  # UI component tests
│   ├── screens/            # Screen-level widgets
│   └── widgets/            # Reusable widgets
└── integration/             # End-to-end tests
    ├── auth_flow_test.dart
    ├── project_crud_test.dart
    └── conversation_test.dart
```

### Pattern 1: Test Pyramid

**What:** Many fast unit tests, moderate widget tests, few comprehensive integration tests
**When to use:** All production applications requiring confidence with fast feedback
**Example:**
```dart
// Source: https://docs.flutter.dev/testing/overview

// Unit test (fast, many of these)
test('AI service generates valid summary', () {
  final service = AIService(mockClient);
  final summary = service.generateSummary('conversation text');
  expect(summary, isNotEmpty);
  expect(summary.length, lessThan(100));
});

// Widget test (moderate number)
testWidgets('Login screen displays OAuth buttons', (tester) async {
  await tester.pumpWidget(const MaterialApp(home: LoginScreen()));
  expect(find.text('Sign in with Google'), findsOneWidget);
  expect(find.text('Sign in with Microsoft'), findsOneWidget);
});

// Integration test (few, critical flows only)
testWidgets('Complete project creation and document upload flow',
  (tester) async {
  // Full end-to-end workflow on real device
});
```

**Ratio guidance:** Aim for 70% unit, 20% widget, 10% integration by test count.

### Pattern 2: Skeleton Loader States

**What:** Toggle between skeleton UI and real content with single boolean flag
**When to use:** Any data-loading scenario (API calls, document fetch, project list)
**Example:**
```dart
// Source: https://pub.dev/packages/skeletonizer

class ProjectListScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<ProjectProvider>(
      builder: (context, provider, _) {
        return Skeletonizer(
          enabled: provider.isLoading,
          child: ListView.builder(
            itemCount: provider.isLoading ? 5 : provider.projects.length,
            itemBuilder: (context, index) {
              final project = provider.isLoading
                ? Project.placeholder() // Fake data for skeleton
                : provider.projects[index];
              return ListTile(
                title: Text(project.name),
                subtitle: Text(project.description),
              );
            },
          ),
        );
      },
    );
  }
}
```

### Pattern 3: Environment-Specific OAuth Configuration

**What:** Separate OAuth app registrations per environment with environment variable management
**When to use:** Production deployment requiring secure authentication across dev/staging/prod
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/entra/identity-platform/reply-url

# backend/app/config.py
class Settings(BaseSettings):
    # Development OAuth (localhost)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Production uses separate app registration with https:// redirect URIs
    environment: str = "development"

    @property
    def oauth_redirect_uri(self) -> str:
        if self.environment == "production":
            return "https://app.example.com/auth/callback"
        return "http://localhost:8080/auth/callback"

# Deployment:
# Development: GOOGLE_CLIENT_ID=dev-app-client-id
# Production:  GOOGLE_CLIENT_ID=prod-app-client-id (separate registration)
```

### Pattern 4: Production Error Handling

**What:** Global error handlers with user-friendly UI and logging service integration
**When to use:** All production Flutter apps to prevent crashes and provide recovery
**Example:**
```dart
// Source: https://docs.flutter.dev/testing/errors

Future<void> main() async {
  await initializeLogging(); // Sentry, Firebase Crashlytics, etc.

  // Handle Flutter framework errors (build/layout/paint)
  FlutterError.onError = (details) {
    FlutterError.presentError(details); // Preserves console logging
    if (kReleaseMode) {
      logErrorToService(details); // Send to monitoring service
    }
  };

  // Handle async/platform errors (plugins, method channels)
  PlatformDispatcher.instance.onError = (error, stack) {
    logErrorToService(error, stack);
    return true; // Prevents crash
  };

  // Custom error widgets (replace red debug screens)
  ErrorWidget.builder = (errorDetails) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48),
            const SizedBox(height: 16),
            const Text('Something went wrong'),
            ElevatedButton(
              onPressed: () => SystemNavigator.pop(), // Close and restart
              child: const Text('Restart App'),
            ),
          ],
        ),
      ),
    );
  };

  runApp(const MyApp());
}
```

### Pattern 5: Material 3 Error Feedback

**What:** Use SnackBars for peripheral errors, AlertDialogs for blocking errors, with recovery actions
**When to use:** Network failures, API timeouts, validation errors
**Example:**
```dart
// Source: https://m1.material.io/patterns/errors.html

// Peripheral error (non-blocking)
void showNetworkError(BuildContext context) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: const Text('Network error. Check your connection.'),
      action: SnackBarAction(
        label: 'Retry',
        onPressed: () => retryLastAction(),
      ),
      duration: const Duration(seconds: 5),
    ),
  );
}

// Blocking error (requires user action)
void showCriticalError(BuildContext context, String message) {
  showDialog(
    context: context,
    barrierDismissible: false,
    builder: (context) => AlertDialog(
      icon: const Icon(Icons.error_outline),
      title: const Text('Action Required'),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('OK'),
        ),
        TextButton(
          onPressed: () {
            Navigator.of(context).pop();
            performRecoveryAction();
          },
          child: const Text('Retry'),
        ),
      ],
    ),
  );
}
```

### Pattern 6: CI/CD Pipeline with GitHub Actions

**What:** Automated testing, building, and deployment on push/PR
**When to use:** All production projects to maintain quality and accelerate releases
**Example:**
```yaml
# Source: https://medium.com/@sharmapraveen91/automate-flutter-ci-cd-with-github-actions

# .github/workflows/flutter-ci.yml
name: Flutter CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.x'
          channel: 'stable'
          cache: true

      - name: Install dependencies
        run: flutter pub get
        working-directory: ./frontend

      - name: Run tests
        run: flutter test
        working-directory: ./frontend

      - name: Analyze code
        run: flutter analyze
        working-directory: ./frontend

  build-web:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.x'
          channel: 'stable'

      - name: Build web
        run: flutter build web --release
        working-directory: ./frontend

      - name: Deploy to Firebase Hosting
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          channelId: live
```

### Anti-Patterns to Avoid

- **Locking orientation to portrait only:** Breaks Android large-screen guidelines, prevents foldable support, creates accessibility issues
- **Checking Platform.isPhone/isTablet:** App window size != device type; use MediaQuery.sizeOf() with breakpoints instead
- **Using Opacity widget in animations:** Expensive rendering; use AnimatedOpacity or FadeInImage instead
- **Building large concrete Lists with off-screen children:** High build cost; use ListView.builder or GridView.builder with lazy loading
- **Hardcoding OAuth redirect URIs:** Security risk and environment inflexibility; use environment variables and separate registrations
- **Testing only on desktop during development:** Mobile performance differs significantly; test frequently on real devices

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Skeleton loaders | Custom animated placeholders for each screen | skeletonizer package | Auto-converts existing widgets to skeletons, zero UI duplication, maintains design consistency, handles animations automatically |
| Error logging/crash reporting | Custom error collection and aggregation | Firebase Crashlytics or Sentry | Production-grade dashboards, user impact tracking, symbolication, release tracking, alerting |
| OAuth redirect URI validation | String comparison with wildcards | Exact string matching per OAuth 2.1 spec | Security requirement; wildcards enable phishing attacks; separate app registrations are standard practice |
| Mobile app signing automation | Shell scripts for keystore management | Fastlane or Codemagic CLI | Handles certificates, provisioning profiles, store uploads, TestFlight distribution; battle-tested across thousands of apps |
| CI/CD build matrix | Custom scripts for test execution | GitHub Actions with flutter-action | Caching, parallel jobs, artifact management, secrets handling, deployment integrations |
| iOS code signing | Manual certificate management | Xcode automatic signing or Codemagic | Certificate expiration, provisioning profiles, team management, CI/CD integration |

**Key insight:** Cross-platform polish requires handling platform-specific edge cases (Safari compatibility, Android permissions, iOS notarization) that established tools have already solved. Custom solutions miss critical details and create maintenance burden.

## Common Pitfalls

### Pitfall 1: Testing Only in Debug Mode

**What goes wrong:** Performance issues and rendering bugs don't appear until production release; users experience jank and crashes that never occurred during development.

**Why it happens:** Flutter debug mode disables optimizations (tree shaking, minification, Impeller), adds debugging overhead, and exhibits different memory/CPU characteristics than release builds.

**How to avoid:**
- Always test integration tests in `--profile` or `--release` mode
- Run performance profiling on real devices (not simulators/emulators)
- Test on low-end Android devices and older iPads before launch
- Use `flutter build web --release` for production-equivalent web testing

**Warning signs:**
- Frame render times < 16ms in debug but > 16ms in release
- Animations smooth on desktop but janky on mobile
- Memory leaks only visible after extended use

### Pitfall 2: Single OAuth App Registration for All Environments

**What goes wrong:** Development redirect URIs (localhost) exposed in production configuration; production secrets leaked in development; Google/Microsoft flag security violations and disable OAuth.

**Why it happens:** Developers share OAuth credentials across environments to avoid configuration complexity; belief that redirect URI validation is flexible.

**How to avoid:**
- Create separate OAuth app registrations in Google Cloud Console / Azure AD for each environment
- Development: `http://localhost:8080/auth/callback`
- Staging: `https://staging.example.com/auth/callback`
- Production: `https://app.example.com/auth/callback`
- Use environment variables to switch client IDs/secrets
- Never commit OAuth secrets to git (use .env files with .gitignore)

**Warning signs:**
- OAuth consent screen shows "unverified app" warning in production
- Redirect URI mismatch errors (`AADSTS50011` from Microsoft)
- Backend logs show localhost redirect URIs in production traffic

### Pitfall 3: Ignoring Browser Compatibility Testing

**What goes wrong:** App works perfectly in Chrome (development browser) but breaks in Safari with missing features, layout bugs, or performance degradation; significant user segment (iOS Safari ~30% mobile traffic) cannot use app.

**Why it happens:** Chrome DevTools is primary development environment; Safari lacks WasmGC and parts of WebGL 2; Flutter Web has known Safari limitations.

**How to avoid:**
- Test in order: Chrome → Firefox → Edge → Safari (increasing complexity)
- Use BrowserStack or LambdaTest for automated cross-browser testing
- Test on real iOS devices (Safari behavior differs from desktop)
- Verify file uploads, auth flows, and streaming features in all browsers
- Consider providing browser compatibility warning for unsupported browsers

**Warning signs:**
- Users report "white screen" on iOS devices
- File picker doesn't work on Safari
- OAuth callback fails on mobile Safari
- SSE streaming doesn't reconnect on Safari

### Pitfall 4: No Loading States (Blank Screen Problem)

**What goes wrong:** User sees blank white screen for 2-5 seconds while data loads from API; perceives app as broken or frozen; abandons before content appears.

**Why it happens:** Developers focus on happy path (data loaded) and forget to handle loading state; assume network calls are instant; test on fast local networks.

**How to avoid:**
- Add loading states to every screen that fetches data
- Use skeletonizer package for zero-effort skeleton loaders
- Display skeleton immediately, toggle `enabled: false` when data arrives
- Test on throttled network (Chrome DevTools → Network → Slow 3G)
- Never show blank screens or "Loading..." text; show structured placeholders

**Warning signs:**
- Flash of empty content before data appears
- User taps button multiple times because no feedback
- Analytics show high bounce rate on screens with API calls

### Pitfall 5: Platform-Specific Features Leak Across Platforms

**What goes wrong:** iOS-style navigation appears on Android; Android back button doesn't work on iOS; web app shows mobile drawer navigation on desktop; inconsistent UX confuses users.

**Why it happens:** Flutter's "single codebase" promise misinterpreted as "single UI for all platforms"; developers don't use Material adaptive widgets; responsive breakpoints not implemented.

**How to avoid:**
- Use `ResponsiveLayout` widget with mobile/tablet/desktop variants
- Implement platform-adaptive navigation (Drawer vs NavigationRail vs Tabs)
- Test on each platform before claiming "cross-platform support"
- Use Material 3 adaptive components (NavigationBar, NavigationRail)
- Check `MediaQuery.sizeOf(context).width` not `Platform.isAndroid`

**Warning signs:**
- Desktop users see hamburger menu on 1920px screens
- Android back button exits app instead of closing drawer
- iOS users expect swipe-back but it doesn't work

### Pitfall 6: Production Deployment Without Environment Variable Validation

**What goes wrong:** Backend starts with default `SECRET_KEY="dev-secret-key"` in production; OAuth fails because `GOOGLE_CLIENT_ID` is empty; AI features silently fail because `ANTHROPIC_API_KEY` is missing; security vulnerabilities exposed.

**Why it happens:** Environment variables configured incorrectly on PaaS platform; developers forget to set required variables; no validation at startup.

**How to avoid:**
```python
# backend/app/config.py
def validate_required(self) -> None:
    if self.environment == "production":
        if self.secret_key == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set in production")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set for AI features")
        if not self.google_client_id or not self.microsoft_client_id:
            raise ValueError("OAuth credentials required for production")

# backend/main.py
settings.validate_required()  # Call on startup
```

**Warning signs:**
- Backend starts but auth doesn't work
- No error messages, features silently fail
- Production uses development database URL
- CORS errors from unexpected origins

## Code Examples

### Cross-Browser Testing Script

```dart
// Source: https://docs.flutter.dev/platform-integration/web/faq

// frontend/test_driver/cross_browser_test.dart
import 'package:flutter_driver/flutter_driver.dart';
import 'package:test/test.dart';

void main() {
  group('Cross-browser compatibility', () {
    FlutterDriver? driver;

    setUpAll(() async {
      driver = await FlutterDriver.connect();
    });

    tearDownAll(() async {
      await driver?.close();
    });

    test('OAuth flow works across browsers', () async {
      // Navigate to login
      await driver!.tap(find.byValueKey('google_login_button'));

      // Wait for callback
      await driver!.waitFor(find.byValueKey('home_screen'));

      // Verify authenticated state
      expect(await driver!.getText(find.byValueKey('user_email')),
             isNotEmpty);
    });

    test('File upload works across browsers', () async {
      // Test file picker functionality
      await driver!.tap(find.byValueKey('upload_button'));

      // Note: Actual file selection requires platform channels
      // This tests UI responsiveness
      await driver!.waitFor(find.byValueKey('file_picker_dialog'));
    });
  });
}

// Run with: flutter drive --target=test_driver/app.dart --driver=test_driver/cross_browser_test.dart
// Test browsers: Chrome, Firefox, Edge, Safari
```

### Production Backend Startup with Validation

```python
# Source: https://render.com/articles/fastapi-production-deployment-best-practices

# backend/main.py
from fastapi import FastAPI
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    # Validate configuration before starting
    try:
        settings.validate_required()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    app = FastAPI(
        title="Business Analyst Assistant API",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

app = create_app()

# Production deployment:
# gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Responsive Navigation Pattern

```dart
// Source: https://docs.flutter.dev/ui/adaptive-responsive/best-practices

// frontend/lib/screens/home_screen.dart
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ResponsiveLayout(
      mobile: _buildMobileLayout(context),
      desktop: _buildDesktopLayout(context),
    );
  }

  Widget _buildMobileLayout(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Business Analyst Assistant'),
      ),
      drawer: _buildNavigationDrawer(context),
      body: _buildContent(context),
    );
  }

  Widget _buildDesktopLayout(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _selectedIndex,
            onDestinationSelected: _onDestinationSelected,
            labelType: NavigationRailLabelType.all,
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.folder_outlined),
                selectedIcon: Icon(Icons.folder),
                label: Text('Projects'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.chat_outlined),
                selectedIcon: Icon(Icons.chat),
                label: Text('Threads'),
              ),
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(child: _buildContent(context)),
        ],
      ),
    );
  }

  Widget _buildNavigationDrawer(BuildContext context) {
    return NavigationDrawer(
      selectedIndex: _selectedIndex,
      onDestinationSelected: _onDestinationSelected,
      children: const [
        NavigationDrawerDestination(
          icon: Icon(Icons.folder_outlined),
          label: Text('Projects'),
        ),
        NavigationDrawerDestination(
          icon: Icon(Icons.chat_outlined),
          label: Text('Threads'),
        ),
      ],
    );
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Skia rendering engine | Impeller rendering engine | Flutter 3.10+ (2023), stable 2026 | Eliminates shader compilation jank, consistent 60/120 FPS, predictable performance |
| WebGL rendering | WebAssembly + WebGPU | Flutter 3.22+ (2024) | Faster startup, smaller JS bridges, native-like graphics performance |
| Manual error handling per screen | Global error handlers (FlutterError.onError, PlatformDispatcher.instance.onError) | Flutter 2.0+ (2021) | Centralized error tracking, production crash reporting, user-friendly error UI |
| Manual skeleton UI duplication | skeletonizer package auto-conversion | 2024-2025 | Zero duplication, consistent loading states, 80% less boilerplate |
| Wildcard OAuth redirect URIs | Exact string matching (OAuth 2.1) | 2025-2026 | Enhanced security, prevents phishing, requires separate app registrations |
| Service workers (default) | --pwa-strategy=none (optional) | Flutter 3.19+ (2024) | Simpler caching, fewer deployment issues, faster iteration |
| Material 2 (opt-in) | Material 3 (default) | Flutter 3.16+ (2023) | Adaptive components, dynamic color, large-screen layouts, accessibility improvements |
| NDK r25 | NDK r28 | Flutter 3.38+ (2026) | Android 15 compliance (16KB memory pages), required for Google Play |

**Deprecated/outdated:**
- **Service Workers in Flutter Web:** Deprecated by default; opt-in with `--pwa-strategy` flag if needed for offline capabilities
- **Hash-based URLs (#/):** Use path-based URLs with `usePathUrlStrategy()` for better SEO and cleaner URLs
- **Platform.isAndroid/isIOS for layout decisions:** Use `MediaQuery.sizeOf()` with adaptive breakpoints instead (apps can run in resizable windows)
- **OrientationBuilder for top-level layout:** Use responsive breakpoints based on width, not device orientation
- **Manual certificate management for iOS:** Use Xcode automatic signing or Codemagic CLI for CI/CD
- **APK distribution:** Use AAB (Android App Bundle) format for Google Play (Play Store requires AAB as of 2021)

## Open Questions

### 1. Firebase Test Lab Integration

**What we know:** Firebase Test Lab can run automated tests across multiple physical devices; integration_test package supports it; costs apply for extensive device matrix.

**What's unclear:** Cost structure for solo developer MVP testing; whether Railway/Render CI/CD can trigger Firebase Test Lab runs; optimal device selection strategy for MVP validation.

**Recommendation:** Start with manual testing on 2-3 personal devices (iPhone, Android phone, desktop browser); add Firebase Test Lab when budget allows ($5-15/month estimated); prioritize real user feedback over comprehensive device matrix.

### 2. WebAssembly Stability for Production

**What we know:** Flutter supports WebAssembly compilation since 3.22; offers faster startup and smaller JS bridges; Safari lacks WasmGC requiring polyfills.

**What's unclear:** Production stability for BA Assistant use case (document upload, SSE streaming, OAuth callbacks); whether Safari polyfills introduce latency/bugs; performance improvement magnitude.

**Recommendation:** Ship with default CanvasKit renderer initially; monitor Web Vitals and user reports; enable WebAssembly in Phase 6 (post-MVP optimization) after user validation proves demand.

### 3. Performance Monitoring Service Selection

**What we know:** Options include Firebase Performance Monitoring (free tier, Flutter integration), Sentry (error tracking + performance), Datadog (enterprise-grade, expensive), or custom logging to Railway/Render.

**What's unclear:** Whether free tiers provide sufficient insight for MVP; integration complexity for solo developer; signal-to-noise ratio for 10-50 early users.

**Recommendation:** Start with Railway/Render native logging (free, zero setup); add Firebase Crashlytics (free, 15-minute setup) for Flutter error tracking; defer performance APM to post-launch based on user-reported issues.

### 4. iOS Simulator Testing Limitations

**What we know:** Apple M1/M2 Macs can run iOS simulators; performance differs from real devices; some platform features (camera, Face ID) unavailable in simulator.

**What's unclear:** For BA Assistant (OAuth, document upload, AI streaming), which bugs only appear on real devices; whether simulator testing is sufficient for MVP validation.

**Recommendation:** Test OAuth flows and file uploads on real iOS device before TestFlight submission; simulators acceptable for UI/layout verification; budget 2-3 hours for real device testing per iOS build.

## Sources

### Primary (HIGH confidence)

**Official Flutter Documentation:**
- [Testing Flutter apps](https://docs.flutter.dev/testing/overview) - Three test types, best practices, pyramid approach
- [Build and release a web app](https://docs.flutter.dev/deployment/web) - Web deployment, renderers, build modes
- [Performance best practices](https://docs.flutter.dev/perf/best-practices) - Const widgets, saveLayer(), opacity patterns
- [Adaptive and responsive design](https://docs.flutter.dev/ui/adaptive-responsive/best-practices) - MediaQuery usage, avoid platform checks, breakpoints
- [Web FAQ](https://docs.flutter.dev/platform-integration/web/faq) - Browser compatibility, dart:io limitations, isolate restrictions
- [Handling errors in Flutter](https://docs.flutter.dev/testing/errors) - FlutterError.onError, PlatformDispatcher, custom ErrorWidget
- [Build and release an Android app](https://docs.flutter.dev/deployment/android) - Keystore creation, signing configuration, app bundle
- [Build and release an iOS app](https://docs.flutter.dev/deployment/ios) - Code signing, TestFlight, App Store Connect

**Official Package Documentation:**
- [skeletonizer package](https://pub.dev/packages/skeletonizer) - Version 2.1.2, automatic widget conversion, features

**Official OAuth Documentation:**
- [Microsoft Entra redirect URI best practices](https://learn.microsoft.com/en-us/entra/identity-platform/reply-url) - Separate registrations, exact matching, localhost rules

**Production Deployment Guides:**
- [FastAPI production deployment best practices](https://render.com/articles/fastapi-production-deployment-best-practices) - Gunicorn+Uvicorn, environment variables, CORS
- [Deploy a FastAPI App | Railway Docs](https://docs.railway.com/guides/fastapi) - Railway deployment steps, configuration

### Secondary (MEDIUM confidence)

- [Material Design 3 Errors Pattern](https://m1.material.io/patterns/errors.html) - SnackBar vs AlertDialog usage, recovery actions
- [Flutter CI/CD with GitHub Actions](https://medium.com/@sharmapraveen91/automate-flutter-ci-cd-with-github-actions) - Workflow examples, deployment automation
- [Skeletonizer package guide](https://milad-akarie.medium.com/flutter-skeleton-loader-using-skeletonizer-13d410dc4ac7) - Implementation patterns, examples
- [Modern Flutter UI in 2026](https://medium.com/@expertappdevs/how-to-build-modern-ui-in-flutter-design-patterns-64615b5815fb) - Material 3 integration, responsive design
- [Flutter In 2026: Key Upgrades](https://digitaloneagency.com.au/flutter-in-2026-the-road-ahead-key-upgrades-and-how-to-prepare-your-app-strategy/) - Impeller status, production era, strategic pillars

### Tertiary (LOW confidence)

- [Why Flutter Isn't Ideal for Cross-Platform Development in 2026](https://kitrum.com/blog/why-flutter-isnt-ideal-for-cross-platform-development/) - Critical perspective, limitations discussion (contrarian view for balance)
- [Flutter Web Issues Common Problems](https://medium.com/@mrlimon28/flutter-web-issues-common-problems-and-how-to-fix-them-2024-guide-5733cbd61751) - Community-reported issues, workarounds

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official packages and tools verified through Flutter.dev, pub.dev, and official deployment docs
- Architecture: HIGH - Patterns from official documentation (Flutter, Material Design, Microsoft, Railway/Render)
- Pitfalls: MEDIUM-HIGH - Combination of official docs (HIGH) and community experiences (MEDIUM); cross-referenced multiple sources
- Performance: HIGH - Official Flutter performance documentation with current Impeller status
- Deployment: HIGH - Official deployment guides for Android/iOS/web verified with PaaS platform documentation

**Research date:** 2026-01-28
**Valid until:** 2026-03-28 (60 days - Flutter stable channel updates quarterly; production practices evolve slowly)

**Key validation notes:**
- Flutter documentation verified as current (last updated 2026-01-14)
- Material 3 confirmed as default since Flutter 3.16
- Impeller confirmed stable for iOS/Android in 2026
- OAuth 2.1 exact matching requirement confirmed via Microsoft official documentation
- All package versions verified via pub.dev (skeletonizer 2.1.2 published 44 days ago)
- PaaS deployment guides verified via Railway/Render official documentation
