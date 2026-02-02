# Phase 32: Frontend Widget & Model Tests - Research

**Researched:** 2026-02-02
**Domain:** Flutter widget testing, Model JSON serialization, Component testing
**Confidence:** HIGH

## Summary

Phase 32 requires widget tests for key UI components (ChatInput, MessageBubble, ThreadList, DocumentList, screens) and JSON serialization round-trip tests for all models. The codebase already has an established widget testing pattern using Mockito with `@GenerateNiceMocks` for provider mocking. Phase 31 established 490 tests across providers and services.

The research reveals:
1. **Existing widget tests** for ChatInput (14 tests), ConversationScreen (12 tests), DocumentListScreen (7 tests), ChatsScreen (18 tests), ThreadListScreen (8 tests) - these need review/expansion
2. **No dedicated MessageBubble tests** - widget exists but lacks isolated tests
3. **No model serialization tests** - 6 models exist with fromJson/toJson methods
4. **Screen coverage gaps** - HomeScreen, SettingsScreen, SplashScreen, CallbackScreen, NotFoundScreen lack tests

**Primary recommendation:** Expand existing widget tests for complete coverage, add isolated MessageBubble tests, create model round-trip tests for all 6 models.

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
| provider | ^6.1.5+1 | State management | Already in project, for mocking providers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Mockito | Mocktail | No codegen needed, but project already uses Mockito |
| Individual widget tests | Golden tests | Visual regression but higher maintenance |

**Installation:**
Already installed - no new dependencies required.

## Architecture Patterns

### Recommended Test Structure
```
frontend/test/
├── unit/
│   ├── models/                    # NEW: Model serialization tests
│   │   ├── message_test.dart
│   │   ├── project_test.dart
│   │   ├── document_test.dart
│   │   ├── thread_test.dart
│   │   ├── token_usage_test.dart
│   │   └── thread_sort_test.dart
│   ├── providers/ (existing)
│   └── services/ (existing)
├── widget/
│   ├── chat_input_test.dart (existing - complete)
│   ├── message_bubble_test.dart        # NEW
│   ├── conversation_screen_test.dart (existing - expand)
│   ├── document_list_screen_test.dart (existing - complete)
│   ├── thread_list_screen_test.dart (existing - complete)
│   ├── chats_screen_test.dart (existing - complete)
│   ├── project_list_screen_test.dart (existing - has failures)
│   ├── login_screen_test.dart (existing - complete)
│   ├── home_screen_test.dart           # NEW
│   ├── settings_screen_test.dart       # NEW
│   └── splash_screen_test.dart         # NEW (optional)
└── integration/ (existing)
```

### Pattern 1: Widget Unit Test Structure
**What:** Test isolated widget behavior with mocked dependencies
**When to use:** Testing reusable widgets like MessageBubble, ChatInput
**Example:**
```dart
// Source: Established pattern in chat_input_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/screens/conversation/widgets/message_bubble.dart';
import 'package:frontend/models/message.dart';

void main() {
  group('MessageBubble Widget Tests', () {
    testWidgets('user message aligned right', (tester) async {
      final message = Message(
        id: '1',
        role: MessageRole.user,
        content: 'Hello',
        createdAt: DateTime.now(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MessageBubble(message: message),
          ),
        ),
      );

      final align = tester.widget<Align>(find.byType(Align));
      expect(align.alignment, Alignment.centerRight);
    });

    testWidgets('assistant message has copy button', (tester) async {
      final message = Message(
        id: '1',
        role: MessageRole.assistant,
        content: 'Response',
        createdAt: DateTime.now(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MessageBubble(message: message),
          ),
        ),
      );

      expect(find.byIcon(Icons.copy), findsOneWidget);
    });
  });
}
```

### Pattern 2: Screen Widget Test with Provider Mocking
**What:** Test screens with mocked providers using ChangeNotifierProvider.value
**When to use:** All screen tests (HomeScreen, SettingsScreen, etc.)
**Example:**
```dart
// Source: Established pattern in chats_screen_test.dart
@GenerateNiceMocks([
  MockSpec<ProjectProvider>(),
  MockSpec<ChatsProvider>(),
  MockSpec<AuthProvider>(),
])
void main() {
  group('HomeScreen Widget Tests', () {
    late MockProjectProvider mockProjectProvider;
    late MockChatsProvider mockChatsProvider;
    late MockAuthProvider mockAuthProvider;

    setUp(() {
      mockProjectProvider = MockProjectProvider();
      mockChatsProvider = MockChatsProvider();
      mockAuthProvider = MockAuthProvider();

      // Default mock behavior
      when(mockProjectProvider.projects).thenReturn([]);
      when(mockProjectProvider.isLoading).thenReturn(false);
      when(mockAuthProvider.displayName).thenReturn('John');
      when(mockAuthProvider.email).thenReturn('john@example.com');
    });

    Widget buildTestWidget() {
      return MaterialApp(
        home: MultiProvider(
          providers: [
            ChangeNotifierProvider<ProjectProvider>.value(
              value: mockProjectProvider,
            ),
            ChangeNotifierProvider<ChatsProvider>.value(
              value: mockChatsProvider,
            ),
            ChangeNotifierProvider<AuthProvider>.value(
              value: mockAuthProvider,
            ),
          ],
          child: const HomeScreen(),
        ),
      );
    }

    testWidgets('shows personalized greeting', (tester) async {
      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('Welcome back, John'), findsOneWidget);
    });
  });
}
```

### Pattern 3: Model JSON Round-Trip Test
**What:** Test fromJson/toJson methods produce valid round-trip serialization
**When to use:** All models with serialization methods
**Example:**
```dart
// Source: Flutter testing best practices
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/message.dart';

void main() {
  group('Message Model Tests', () {
    group('JSON Serialization', () {
      test('fromJson creates valid instance', () {
        final json = {
          'id': '123',
          'role': 'user',
          'content': 'Hello world',
          'created_at': '2026-02-02T10:00:00.000Z',
        };

        final message = Message.fromJson(json);

        expect(message.id, '123');
        expect(message.role, MessageRole.user);
        expect(message.content, 'Hello world');
        expect(message.createdAt.year, 2026);
      });

      test('toJson produces valid map', () {
        final message = Message(
          id: '123',
          role: MessageRole.assistant,
          content: 'Response',
          createdAt: DateTime.utc(2026, 2, 2, 10, 0),
        );

        final json = message.toJson();

        expect(json['id'], '123');
        expect(json['role'], 'assistant');
        expect(json['content'], 'Response');
        expect(json['created_at'], '2026-02-02T10:00:00.000Z');
      });

      test('round-trip serialization preserves data', () {
        final original = Message(
          id: 'test-id',
          role: MessageRole.user,
          content: 'Test message',
          createdAt: DateTime.utc(2026, 1, 15, 14, 30),
        );

        final json = original.toJson();
        final restored = Message.fromJson(json);

        expect(restored.id, original.id);
        expect(restored.role, original.role);
        expect(restored.content, original.content);
        expect(restored.createdAt, original.createdAt);
      });
    });

    group('MessageRole Enum', () {
      test('fromJson handles valid roles', () {
        expect(MessageRole.fromJson('user'), MessageRole.user);
        expect(MessageRole.fromJson('assistant'), MessageRole.assistant);
      });

      test('fromJson defaults to user for unknown role', () {
        expect(MessageRole.fromJson('unknown'), MessageRole.user);
      });

      test('toJson returns correct string', () {
        expect(MessageRole.user.toJson(), 'user');
        expect(MessageRole.assistant.toJson(), 'assistant');
      });
    });
  });
}
```

### Anti-Patterns to Avoid
- **Testing Flutter framework:** Don't test that pumpWidget works, test YOUR widget logic
- **Over-mocking:** Don't mock simple model objects, only mock services/providers
- **Incomplete pump:** Use pumpAndSettle() after actions that trigger animations/rebuilds
- **Missing MaterialApp:** Widget tests need MaterialApp wrapper for theme/localization
- **Testing private methods:** Test public behavior through public API

## Widget Inventory

### Widgets Requiring Tests

| Widget | File | Current Tests | Status | Key Behaviors to Test |
|--------|------|---------------|--------|----------------------|
| ChatInput | chat_input.dart | 14 tests | Complete | Text entry, send button states, multiline, enabled/disabled |
| MessageBubble | message_bubble.dart | 0 tests | NEW | User vs assistant styling, alignment, copy button |
| StreamingMessage | streaming_message.dart | 0 tests | Optional | Streaming text display |
| ProviderIndicator | provider_indicator.dart | 0 tests | Optional | Provider icon display |
| AddToProjectButton | add_to_project_button.dart | 0 tests | Optional | Button states, dialog |

### Screens Requiring Tests

| Screen | File | Current Tests | Status | Key States to Test |
|--------|------|---------------|--------|-------------------|
| ConversationScreen | conversation_screen.dart | 12 tests | Expand | Loading, empty, populated, streaming, error |
| DocumentListScreen | document_list_screen.dart | 7 tests | Complete | Loading, empty, populated, error |
| ThreadListScreen | thread_list_screen.dart | 8 tests | Complete | Search, sort, empty, populated |
| ChatsScreen | chats_screen.dart | 18 tests | Complete | Search, sort, pagination, project/global threads |
| ProjectListScreen | project_list_screen.dart | 8 tests | Fix needed | One test failing |
| LoginScreen | login_screen.dart | 5 tests | Complete | Buttons, loading, error states |
| HomeScreen | home_screen.dart | 0 tests | NEW | Greeting, action buttons, recent projects |
| SettingsScreen | settings_screen.dart | 0 tests | NEW | Profile, theme toggle, provider selector, usage, logout |
| SplashScreen | splash_screen.dart | 0 tests | Optional | Loading indicator |
| NotFoundScreen | not_found_screen.dart | 0 tests | Optional | Error message, navigation |

## Model Inventory

### Models Requiring Serialization Tests

| Model | File | Fields | Complexity | Test Priority |
|-------|------|--------|------------|---------------|
| Message | message.dart | 4 + MessageRole enum | Low | High |
| Project | project.dart | 7 (nullable documents/threads) | Medium | High |
| Document | document.dart | 4 (nullable content) | Low | High |
| Thread | thread.dart | 10 (many nullable) | High | High |
| PaginatedThreads | thread.dart | 5 | Medium | High |
| TokenUsage | token_usage.dart | 6 + computed properties | Medium | High |
| ThreadSortOption | thread_sort.dart | enum only | Very Low | Low |

### Model Test Scenarios

Each model should test:
1. **fromJson with all fields** - Complete JSON parses correctly
2. **fromJson with minimal fields** - Optional fields default correctly
3. **fromJson with null values** - Nullable fields handled
4. **toJson produces valid map** - All fields serialized
5. **Round-trip preserves data** - fromJson(toJson(x)) == x
6. **Edge cases** - Empty strings, special characters, dates

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Provider mocking | Manual mock classes | @GenerateNiceMocks | Auto-updates with interface changes |
| DateTime assertions | String comparison | DateTime equality with UTC | Timezone-safe comparison |
| Widget finding | Manual traversal | find.* finders | Standard API, more readable |
| Animation waiting | Fixed delays | pumpAndSettle() | Reliable, no flaky timing |

**Key insight:** Follow established patterns from existing widget tests rather than inventing new approaches.

## Common Pitfalls

### Pitfall 1: Not Wrapping in MaterialApp
**What goes wrong:** Tests fail with "No MediaQuery widget ancestor found"
**Why it happens:** Widgets need MaterialApp for theme, media query, etc.
**How to avoid:** Always wrap test widgets in MaterialApp with Scaffold
**Warning signs:** MediaQuery/Localizations errors

### Pitfall 2: Forgetting pumpAndSettle After Actions
**What goes wrong:** State changes not reflected, assertions fail
**Why it happens:** Widget tree not rebuilt after state change
**How to avoid:** Call pumpAndSettle() after tap/enterText/state changes
**Warning signs:** Expected widgets not found after interactions

### Pitfall 3: DateTime Comparison Issues
**What goes wrong:** Round-trip tests fail on datetime comparison
**Why it happens:** Local vs UTC, millisecond precision differences
**How to avoid:** Use UTC datetimes, compare toIso8601String() outputs
**Warning signs:** Tests pass locally but fail in CI

### Pitfall 4: Mock Not Returning Values
**What goes wrong:** Null errors during widget rendering
**Why it happens:** MockSpec doesn't stub all accessed properties
**How to avoid:** Set up all accessed properties in setUp()
**Warning signs:** Null check operator used on null value

### Pitfall 5: Testing Clipboard Operations
**What goes wrong:** Clipboard tests fail in test environment
**Why it happens:** Clipboard requires platform channel not available in tests
**How to avoid:** Test that callback fires, mock clipboard if needed
**Warning signs:** MissingPluginException for clipboard

## Code Examples

### Example 1: Complete Widget Unit Test (ChatInput)
See `frontend/test/widget/chat_input_test.dart` - 14 comprehensive tests covering all interaction scenarios.

### Example 2: Screen Test with Multiple Providers
See `frontend/test/widget/chats_screen_test.dart` - demonstrates MultiProvider mocking pattern.

### Example 3: Model Test with Optional Fields
```dart
group('Thread Model Tests', () {
  test('fromJson handles minimal required fields', () {
    final json = {
      'id': 'thread-1',
      'created_at': '2026-02-02T10:00:00.000Z',
      'updated_at': '2026-02-02T10:00:00.000Z',
    };

    final thread = Thread.fromJson(json);

    expect(thread.id, 'thread-1');
    expect(thread.projectId, isNull);
    expect(thread.title, isNull);
    expect(thread.messageCount, isNull);
    expect(thread.messages, isNull);
  });

  test('fromJson parses nested messages', () {
    final json = {
      'id': 'thread-1',
      'created_at': '2026-02-02T10:00:00.000Z',
      'updated_at': '2026-02-02T10:00:00.000Z',
      'messages': [
        {
          'id': 'msg-1',
          'role': 'user',
          'content': 'Hello',
          'created_at': '2026-02-02T10:00:00.000Z',
        }
      ],
    };

    final thread = Thread.fromJson(json);

    expect(thread.messages, isNotNull);
    expect(thread.messages!.length, 1);
    expect(thread.messages![0].content, 'Hello');
  });

  test('toJson excludes null optional fields', () {
    final thread = Thread(
      id: 'thread-1',
      createdAt: DateTime.utc(2026, 2, 2),
      updatedAt: DateTime.utc(2026, 2, 2),
    );

    final json = thread.toJson();

    expect(json.containsKey('project_id'), isFalse);
    expect(json.containsKey('title'), isFalse);
    expect(json.containsKey('message_count'), isFalse);
  });
});
```

### Example 4: Testing Computed Properties
```dart
group('TokenUsage computed properties', () {
  test('totalTokens returns sum of input and output', () {
    final usage = TokenUsage(
      totalCost: 10.0,
      totalRequests: 100,
      totalInputTokens: 5000,
      totalOutputTokens: 3000,
      monthStart: '2026-02-01',
      budget: 100.0,
    );

    expect(usage.totalTokens, 8000);
  });

  test('costPercentage clamped between 0 and 1', () {
    final overBudget = TokenUsage(
      totalCost: 150.0,
      totalRequests: 100,
      totalInputTokens: 5000,
      totalOutputTokens: 3000,
      monthStart: '2026-02-01',
      budget: 100.0,
    );

    expect(overBudget.costPercentage, 1.0);
  });

  test('costPercentageDisplay formats correctly', () {
    final usage = TokenUsage(
      totalCost: 12.5,
      totalRequests: 100,
      totalInputTokens: 5000,
      totalOutputTokens: 3000,
      monthStart: '2026-02-01',
      budget: 100.0,
    );

    expect(usage.costPercentageDisplay, '12.5%');
  });
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pump() multiple times | pumpAndSettle() | Established | More reliable animation handling |
| Manual widget tree traversal | find.* API | Established | Cleaner, more readable tests |
| @GenerateMocks | @GenerateNiceMocks | Mockito 5.1 | Cleaner stubs with sensible defaults |

**Current test count:** 490 tests (6 failures in project_list_screen_test.dart)

## File Creation Summary

### Test Files to Create

| File | Tests For | Priority | Est. Tests |
|------|-----------|----------|------------|
| `test/unit/models/message_test.dart` | Message, MessageRole | High | 8-10 |
| `test/unit/models/project_test.dart` | Project | High | 8-10 |
| `test/unit/models/document_test.dart` | Document | High | 6-8 |
| `test/unit/models/thread_test.dart` | Thread, PaginatedThreads | High | 15-20 |
| `test/unit/models/token_usage_test.dart` | TokenUsage | High | 8-10 |
| `test/widget/message_bubble_test.dart` | MessageBubble | High | 8-10 |
| `test/widget/home_screen_test.dart` | HomeScreen | Medium | 10-12 |
| `test/widget/settings_screen_test.dart` | SettingsScreen | Medium | 12-15 |

### Existing Files to Fix/Expand

| File | Current State | Action | Est. New Tests |
|------|--------------|--------|----------------|
| `test/widget/project_list_screen_test.dart` | 1 failing test | Fix test | 0 |
| `test/widget/conversation_screen_test.dart` | Partial | Add copy/retry tests | 3-5 |

### Optional/Low Priority

| File | Tests For | Priority |
|------|-----------|----------|
| `test/unit/models/thread_sort_test.dart` | ThreadSortOption enum | Very Low |
| `test/widget/splash_screen_test.dart` | SplashScreen | Low |
| `test/widget/not_found_screen_test.dart` | NotFoundScreen | Low |
| `test/widget/streaming_message_test.dart` | StreamingMessage | Low |

## Open Questions

Things that couldn't be fully resolved:

1. **Clipboard Testing**
   - What we know: MessageBubble has copy functionality using Clipboard.setData
   - What's unclear: Test environment may not support clipboard operations
   - Recommendation: Test that copy button exists and tap triggers callback; skip actual clipboard verification

2. **AuthService in SettingsScreen**
   - What we know: SettingsScreen creates AuthService directly for usage fetch
   - What's unclear: How to mock AuthService that's instantiated inside widget
   - Recommendation: Either refactor to inject service, or mock at HTTP level, or skip usage tests

3. **Navigation Testing in HomeScreen**
   - What we know: HomeScreen uses GoRouter for navigation (context.go)
   - What's unclear: How to verify navigation without full router setup
   - Recommendation: Verify buttons exist and are tappable; skip navigation verification in unit tests

## Sources

### Primary (HIGH confidence)
- Existing codebase: `frontend/test/widget/chat_input_test.dart` - established widget testing pattern
- Existing codebase: `frontend/test/widget/chats_screen_test.dart` - provider mocking pattern
- Existing codebase: `frontend/lib/models/*.dart` - model structure analysis
- [Flutter Widget Testing Introduction](https://docs.flutter.dev/cookbook/testing/widget/introduction) - official Flutter docs

### Secondary (MEDIUM confidence)
- [WidgetTester API](https://api.flutter.dev/flutter/flutter_test/WidgetTester-class.html) - API reference
- [pumpAndSettle documentation](https://api.flutter.dev/flutter/flutter_test/WidgetTester/pumpAndSettle.html) - frame handling
- [Flutter JSON Serialization](https://docs.flutter.dev/data-and-backend/serialization/json) - serialization patterns

### Tertiary (LOW confidence)
- [DCM Testing Guide](https://dcm.dev/blog/2025/07/30/navigating-hard-parts-testing-flutter-developers) - advanced patterns
- [Medium: Widget and Integration Test](https://medium.com/@shreebhagwat94/widget-and-integration-test-bd019c8777bc) - examples

## Metadata

**Confidence breakdown:**
- Widget testing patterns: HIGH - established in existing tests
- Model serialization: HIGH - standard Dart patterns, simple models
- Screen coverage gaps: HIGH - direct file analysis

**Research date:** 2026-02-02
**Valid until:** 60 days (stable testing patterns, low churn)
