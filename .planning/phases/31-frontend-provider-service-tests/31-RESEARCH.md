# Phase 31: Frontend Provider & Service Tests - Research

**Researched:** 2026-02-02
**Domain:** Flutter unit testing, Provider pattern, Dio HTTP mocking
**Confidence:** HIGH

## Summary

Phase 31 requires unit test coverage for all frontend providers and services. The codebase already has an established testing pattern using Mockito with `@GenerateNiceMocks` annotation and the existing `ChatsProvider` test file provides an excellent template. The providers follow the standard ChangeNotifier pattern with injected service dependencies, making them easily testable.

The research reveals:
1. **10 providers** exist in `lib/providers/`, each using ChangeNotifier
2. **6 services** exist in `lib/services/`, each using Dio for HTTP calls
3. **Existing patterns** in `test/unit/chats_provider_test.dart` and widget tests demonstrate the mocking approach
4. **Dependencies** (Mockito 5.6.3, build_runner 2.10.5) are already in pubspec.yaml

**Primary recommendation:** Follow the existing `chats_provider_test.dart` pattern for all providers - mock the service dependency, verify state changes and method calls.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flutter_test | SDK | Flutter test framework | Official Flutter testing library |
| mockito | ^5.6.3 | Mock generation | Industry standard, already in project |
| build_runner | ^2.10.5 | Code generation | Required for @GenerateNiceMocks |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| http_mock_adapter | - | Dio request mocking | Alternative for service-level HTTP tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Mockito | Mocktail | No codegen needed, but project already uses Mockito |
| Manual mocks | Generated mocks | Generated mocks auto-update with interface changes |

**Installation:**
Already installed - no new dependencies required.

## Architecture Patterns

### Recommended Test Structure
```
frontend/test/
├── unit/
│   ├── providers/
│   │   ├── auth_provider_test.dart
│   │   ├── auth_provider_test.mocks.dart (generated)
│   │   ├── project_provider_test.dart
│   │   ├── project_provider_test.mocks.dart (generated)
│   │   ├── document_provider_test.dart
│   │   ├── thread_provider_test.dart
│   │   ├── conversation_provider_test.dart
│   │   ├── chats_provider_test.dart (existing - expand)
│   │   ├── theme_provider_test.dart
│   │   └── ...
│   └── services/
│       ├── api_service_test.dart (if exists)
│       ├── auth_service_test.dart
│       └── auth_service_test.mocks.dart (generated)
├── widget/ (existing)
└── integration/ (existing)
```

### Pattern 1: Provider Unit Test Structure
**What:** Test ChangeNotifier providers with mocked service dependencies
**When to use:** All provider tests
**Example:**
```dart
// Source: Existing chats_provider_test.dart pattern
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

@GenerateNiceMocks([MockSpec<SomeService>()])
void main() {
  group('SomeProvider Unit Tests', () {
    late MockSomeService mockService;
    late SomeProvider provider;

    setUp(() {
      mockService = MockSomeService();
      provider = SomeProvider(service: mockService);
    });

    group('Initial State', () {
      test('starts with expected defaults', () {
        expect(provider.loading, isFalse);
        expect(provider.error, isNull);
        expect(provider.items, isEmpty);
      });
    });

    group('loadItems', () {
      test('sets loading true during operation', () async {
        when(mockService.getItems()).thenAnswer((_) async {
          expect(provider.loading, isTrue); // Verify during call
          return [];
        });
        await provider.loadItems();
        expect(provider.loading, isFalse); // Verify after call
      });

      test('updates state on success', () async {
        final items = [Item(id: '1')];
        when(mockService.getItems()).thenAnswer((_) async => items);

        await provider.loadItems();

        expect(provider.items, equals(items));
        expect(provider.error, isNull);
      });

      test('sets error on failure', () async {
        when(mockService.getItems()).thenThrow(Exception('Network error'));

        await provider.loadItems();

        expect(provider.error, contains('Network error'));
        expect(provider.items, isEmpty);
      });
    });
  });
}
```

### Pattern 2: Service Unit Test Structure
**What:** Test service HTTP calls with mocked Dio
**When to use:** All service tests
**Example:**
```dart
// Service test with mocked Dio and FlutterSecureStorage
import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

@GenerateNiceMocks([MockSpec<Dio>(), MockSpec<FlutterSecureStorage>()])
void main() {
  group('AuthService Unit Tests', () {
    late MockDio mockDio;
    late MockFlutterSecureStorage mockStorage;
    late AuthService service;

    setUp(() {
      mockDio = MockDio();
      mockStorage = MockFlutterSecureStorage();
      service = AuthService(
        dio: mockDio,
        storage: mockStorage,
        baseUrl: 'http://test.api',
      );
    });

    group('getCurrentUser', () {
      test('returns user data on success', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          'http://test.api/auth/me',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: {'id': '123', 'email': 'test@example.com'},
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        ));

        final result = await service.getCurrentUser();

        expect(result['id'], equals('123'));
        expect(result['email'], equals('test@example.com'));
      });

      test('throws when no token', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => null);

        expect(() => service.getCurrentUser(), throwsException);
      });
    });
  });
}
```

### Pattern 3: Testing notifyListeners() calls
**What:** Verify listeners are notified at correct points
**When to use:** Critical state changes where UI update timing matters
**Example:**
```dart
test('notifies listeners on state change', () async {
  var notifyCount = 0;
  provider.addListener(() => notifyCount++);

  when(mockService.loadData()).thenAnswer((_) async => []);
  await provider.loadData();

  // Loading start + loading end = 2 notifications
  expect(notifyCount, equals(2));
});
```

### Anti-Patterns to Avoid
- **Testing implementation details:** Don't test private methods, test public behavior
- **Over-mocking:** Don't mock simple value objects (models), only mock services/dependencies
- **Flaky time-based tests:** Use fake timers for timeout/timer tests, not real delays
- **Testing Flutter framework:** Don't test that ChangeNotifier works, test YOUR logic

## Provider Inventory

### Providers Requiring Tests

| Provider | File | Service Dependency | Complexity | Key Methods |
|----------|------|-------------------|------------|-------------|
| AuthProvider | auth_provider.dart | AuthService | Medium | checkAuthStatus, loginWithGoogle, loginWithMicrosoft, handleCallback, logout |
| ProjectProvider | project_provider.dart | ProjectService | High | loadProjects, createProject, selectProject, updateProject, deleteProject |
| DocumentProvider | document_provider.dart | DocumentService | High | loadDocuments, uploadDocument, selectDocument, deleteDocument |
| ThreadProvider | thread_provider.dart | ThreadService | High | loadThreads, createThread, selectThread, renameThread, deleteThread |
| ConversationProvider | conversation_provider.dart | AIService, ThreadService | High | loadThread, sendMessage, deleteMessage, retryLastMessage |
| ChatsProvider | chats_provider.dart | ThreadService | Medium | loadThreads, loadMoreThreads, createNewChat (EXISTS - expand) |
| ThemeProvider | theme_provider.dart | SharedPreferences | Low | toggleTheme |
| NavigationProvider | navigation_provider.dart | SharedPreferences | Low | toggleSidebar |
| ProviderProvider | provider_provider.dart | SharedPreferences | Low | setProvider |
| DocumentColumnProvider | document_column_provider.dart | None | Very Low | toggle, expand, collapse |

### Providers NOT Requiring Tests (Out of Scope)
- **UrlStorageService** - Uses dart:html directly, cannot be unit tested in standard Flutter test environment

## Service Inventory

### Services Requiring Tests

| Service | File | HTTP Methods | Complexity | Key Methods |
|---------|------|--------------|------------|-------------|
| AuthService | auth_service.dart | Dio, FlutterSecureStorage | Medium | loginWithGoogle, loginWithMicrosoft, storeToken, getStoredToken, isTokenValid, getCurrentUser, getUsage, logout |
| ProjectService | project_service.dart | Dio, FlutterSecureStorage | Medium | getProjects, createProject, getProject, updateProject, deleteProject |
| DocumentService | document_service.dart | Dio, FlutterSecureStorage | Medium | uploadDocument, getDocuments, getDocumentContent, searchDocuments, deleteDocument |
| ThreadService | thread_service.dart | Dio, FlutterSecureStorage | Medium | getThreads, createThread, getThread, deleteThread, renameThread, getGlobalThreads, createGlobalThread, associateWithProject |
| AIService | ai_service.dart | Dio, FlutterSecureStorage, SSE | High | streamChat, deleteMessage |

### Services NOT Requiring Tests
- **UrlStorageService** - Browser-only service (uses dart:html)

### Note on ApiService
The requirements mention `FSVC-01: ApiService has unit test coverage`. However, there is no `api_service.dart` file in the codebase. The HTTP functionality is distributed across individual services (AuthService, ProjectService, etc.). This requirement may need clarification or may refer to testing the common HTTP patterns within these services.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mock generation | Manual mock classes | @GenerateNiceMocks | Auto-updates with interface changes |
| HTTP response simulation | Custom response builders | Response() from Dio | Handles all response metadata |
| Timer testing | Thread.sleep() delays | FakeAsync / fake_async | Deterministic, fast tests |
| Listener verification | Complex callback tracking | addListener + counter | Simple pattern already established |

**Key insight:** The project already has working test patterns in chats_provider_test.dart - replicate this pattern rather than inventing new approaches.

## Common Pitfalls

### Pitfall 1: Forgetting to Run build_runner
**What goes wrong:** Tests fail with "class not found" for mock classes
**Why it happens:** Mockito generates mocks via build_runner, must regenerate after changes
**How to avoid:** Run `flutter pub run build_runner build --delete-conflicting-outputs` after adding @GenerateNiceMocks
**Warning signs:** Import errors for `.mocks.dart` files

### Pitfall 2: Testing Async State Changes Incorrectly
**What goes wrong:** Tests pass but miss intermediate state changes
**Why it happens:** Only checking final state, not state during async operation
**How to avoid:** Use callback verification within when().thenAnswer() to check loading states
**Warning signs:** isLoading never tested as true

### Pitfall 3: Not Testing Error Paths
**What goes wrong:** Code coverage looks good but errors cause crashes in production
**Why it happens:** Only testing happy paths
**How to avoid:** For every service call, test both success and failure scenarios
**Warning signs:** No tests using `thenThrow()`

### Pitfall 4: Mocking Concrete Classes Instead of Injected Dependencies
**What goes wrong:** Tests are brittle and break with implementation changes
**Why it happens:** Service creates its own Dio instance
**How to avoid:** All services already support constructor injection - use it
**Warning signs:** Tests require modifying production code

### Pitfall 5: Testing Timer-Based Delete Operations
**What goes wrong:** Tests take 10+ seconds or are flaky
**Why it happens:** deleteProject/deleteDocument/deleteThread use 10-second timers
**How to avoid:** Either test the optimistic removal immediately, or use fake timers
**Warning signs:** Tests with `await Future.delayed(Duration(seconds: 10))`

## Code Examples

### Example 1: Complete Provider Test (from existing chats_provider_test.dart)
See `frontend/test/unit/chats_provider_test.dart` for the established pattern - 440 lines of comprehensive tests.

### Example 2: Service Test with DioException Handling
```dart
test('throws appropriate error on 401', () async {
  when(mockStorage.read(key: 'auth_token'))
      .thenAnswer((_) async => 'expired-token');
  when(mockDio.get(any, options: anyNamed('options')))
      .thenThrow(DioException(
        type: DioExceptionType.badResponse,
        response: Response(
          statusCode: 401,
          requestOptions: RequestOptions(path: ''),
        ),
        requestOptions: RequestOptions(path: ''),
      ));

  expect(
    () => service.getProjects(),
    throwsA(predicate((e) => e.toString().contains('Unauthorized'))),
  );
});
```

### Example 3: Testing SharedPreferences-based Provider
```dart
// For ThemeProvider, NavigationProvider, ProviderProvider
@GenerateNiceMocks([MockSpec<SharedPreferences>()])
void main() {
  group('ThemeProvider', () {
    late MockSharedPreferences mockPrefs;

    setUp(() {
      mockPrefs = MockSharedPreferences();
    });

    test('loads saved dark mode preference', () async {
      when(mockPrefs.getBool('isDarkMode')).thenReturn(true);

      final provider = await ThemeProvider.load(mockPrefs);

      expect(provider.isDarkMode, isTrue);
      expect(provider.themeMode, equals(ThemeMode.dark));
    });

    test('defaults to light mode when no preference saved', () async {
      when(mockPrefs.getBool('isDarkMode')).thenReturn(null);

      final provider = await ThemeProvider.load(mockPrefs);

      expect(provider.isDarkMode, isFalse);
    });

    test('toggleTheme persists immediately', () async {
      when(mockPrefs.getBool('isDarkMode')).thenReturn(false);
      when(mockPrefs.setBool('isDarkMode', true)).thenAnswer((_) async => true);

      final provider = await ThemeProvider.load(mockPrefs);
      await provider.toggleTheme();

      verify(mockPrefs.setBool('isDarkMode', true)).called(1);
      expect(provider.isDarkMode, isTrue);
    });
  });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| @GenerateMocks | @GenerateNiceMocks | Mockito 5.1 | Cleaner stubs with sensible defaults |
| Manual when() for each method | NiceMocks auto-stub | Mockito 5.1 | Less boilerplate |

**Current versions in use:**
- mockito: ^5.6.3 (latest stable)
- build_runner: ^2.10.5 (latest stable)

## Open Questions

Things that couldn't be fully resolved:

1. **ApiService Requirement**
   - What we know: FSVC-01 requires ApiService tests, but no api_service.dart exists
   - What's unclear: Whether this refers to a missing service or the common HTTP patterns
   - Recommendation: Treat as N/A or clarify with user, test individual services instead

2. **SSE Stream Testing (AIService.streamChat)**
   - What we know: streamChat uses flutter_client_sse for Server-Sent Events
   - What's unclear: Best approach to mock SSEClient.subscribeToSSE
   - Recommendation: May need to abstract SSE client or test with integration tests

3. **BuildContext in Delete Methods**
   - What we know: deleteProject/deleteDocument/deleteThread require BuildContext for SnackBar
   - What's unclear: How to unit test methods requiring BuildContext
   - Recommendation: Test the state management logic separately, skip SnackBar verification in unit tests

## File Creation Summary

### Test Files to Create
| File | Tests For | Priority |
|------|-----------|----------|
| `test/unit/providers/auth_provider_test.dart` | AuthProvider | High |
| `test/unit/providers/project_provider_test.dart` | ProjectProvider | High |
| `test/unit/providers/document_provider_test.dart` | DocumentProvider | High |
| `test/unit/providers/thread_provider_test.dart` | ThreadProvider | High |
| `test/unit/providers/conversation_provider_test.dart` | ConversationProvider | High |
| `test/unit/providers/theme_provider_test.dart` | ThemeProvider | Medium |
| `test/unit/providers/navigation_provider_test.dart` | NavigationProvider | Low |
| `test/unit/providers/provider_provider_test.dart` | ProviderProvider | Low |
| `test/unit/providers/document_column_provider_test.dart` | DocumentColumnProvider | Low |
| `test/unit/services/auth_service_test.dart` | AuthService | High |
| `test/unit/services/project_service_test.dart` | ProjectService | Medium |
| `test/unit/services/document_service_test.dart` | DocumentService | Medium |
| `test/unit/services/thread_service_test.dart` | ThreadService | Medium |
| `test/unit/services/ai_service_test.dart` | AIService | Medium |

### Existing File to Expand
| File | Current State | Action |
|------|--------------|--------|
| `test/unit/chats_provider_test.dart` | Partial coverage | Add search/sort tests per FPROV-06 |

## Sources

### Primary (HIGH confidence)
- Existing codebase: `frontend/test/unit/chats_provider_test.dart` - established testing pattern
- Existing codebase: `frontend/test/widget/project_list_screen_test.dart` - Mockito usage
- Existing codebase: `frontend/pubspec.yaml` - current dependencies

### Secondary (MEDIUM confidence)
- [Flutter Documentation: Mock dependencies using Mockito](https://docs.flutter.dev/cookbook/testing/unit/mocking)
- [Flutter Documentation: Simple app state management](https://docs.flutter.dev/data-and-backend/state-mgmt/simple)
- [Mock Dio Requests for Flutter Unit Testing](https://tillitsdone.com/blogs/mock-dio-requests-in-flutter-tests/)

### Tertiary (LOW confidence)
- [Medium: Unit Test the Change Notifier in Flutter](https://medium.com/@shreebhagwat94/unit-test-the-change-notifier-in-flutter-74fb75e8fe58)
- [DEV Community: http-mock-adapter](https://dev.to/lomsa/simulating-http-request-response-workflow-for-effective-testing-in-dart-flutter-via-http-mock-adapter-5eii)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - using existing project patterns
- Architecture: HIGH - established in chats_provider_test.dart
- Pitfalls: HIGH - derived from actual codebase analysis

**Research date:** 2026-02-02
**Valid until:** 60 days (stable testing patterns, low churn)
