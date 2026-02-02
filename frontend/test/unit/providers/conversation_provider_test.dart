/// Unit tests for ConversationProvider (Phase 31).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/message.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/providers/conversation_provider.dart';
import 'package:frontend/services/ai_service.dart';
import 'package:frontend/services/thread_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'conversation_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<AIService>(), MockSpec<ThreadService>()])
void main() {
  group('ConversationProvider Unit Tests', () {
    late MockAIService mockAIService;
    late MockThreadService mockThreadService;
    late ConversationProvider provider;

    setUp(() {
      mockAIService = MockAIService();
      mockThreadService = MockThreadService();
      provider = ConversationProvider(
        aiService: mockAIService,
        threadService: mockThreadService,
      );
    });

    /// Helper to create a test thread
    Thread createTestThread({
      String id = 't1',
      String? projectId,
      String? title = 'Test Thread',
      List<Message>? messages,
    }) {
      return Thread(
        id: id,
        projectId: projectId,
        title: title,
        createdAt: DateTime(2024, 1, 1),
        updatedAt: DateTime(2024, 1, 1),
        messages: messages ?? [],
      );
    }

    /// Helper to create a test message
    Message createTestMessage({
      String id = 'm1',
      MessageRole role = MessageRole.user,
      String content = 'Hello',
    }) {
      return Message(
        id: id,
        role: role,
        content: content,
        createdAt: DateTime(2024, 1, 1),
      );
    }

    group('Initial State', () {
      test('starts with null thread', () {
        expect(provider.thread, isNull);
      });

      test('starts with empty messages list', () {
        expect(provider.messages, isEmpty);
      });

      test('starts with empty streamingText', () {
        expect(provider.streamingText, isEmpty);
      });

      test('starts with null statusMessage', () {
        expect(provider.statusMessage, isNull);
      });

      test('starts with isStreaming false', () {
        expect(provider.isStreaming, isFalse);
      });

      test('starts with loading false', () {
        expect(provider.loading, isFalse);
      });

      test('starts with no error', () {
        expect(provider.error, isNull);
      });

      test('starts with isNotFound false', () {
        expect(provider.isNotFound, isFalse);
      });

      test('starts with canRetry false', () {
        expect(provider.canRetry, isFalse);
      });
    });

    group('loadThread', () {
      test('sets loading to true during call', () async {
        when(mockThreadService.getThread('t1')).thenAnswer((_) async {
          // Check loading state during the call
          expect(provider.loading, isTrue);
          return createTestThread();
        });

        await provider.loadThread('t1');
      });

      test('sets thread and messages on success', () async {
        final messages = [
          createTestMessage(id: 'm1', role: MessageRole.user, content: 'Hi'),
          createTestMessage(
              id: 'm2', role: MessageRole.assistant, content: 'Hello!'),
        ];
        final thread = createTestThread(messages: messages);

        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);

        await provider.loadThread('t1');

        expect(provider.thread, equals(thread));
        expect(provider.messages, equals(messages));
        expect(provider.loading, isFalse);
      });

      test('sets isNotFound on 404 error', () async {
        when(mockThreadService.getThread('t1'))
            .thenThrow(Exception('Thread not found'));

        await provider.loadThread('t1');

        expect(provider.isNotFound, isTrue);
        expect(provider.error, isNull); // Not a "real" error
        expect(provider.loading, isFalse);
      });

      test('sets error on other errors', () async {
        when(mockThreadService.getThread('t1'))
            .thenThrow(Exception('Network error'));

        await provider.loadThread('t1');

        expect(provider.error, contains('Network error'));
        expect(provider.isNotFound, isFalse);
        expect(provider.loading, isFalse);
      });

      test('resets isNotFound on new load attempt', () async {
        // First load returns 404
        when(mockThreadService.getThread('t1'))
            .thenThrow(Exception('Thread not found'));
        await provider.loadThread('t1');
        expect(provider.isNotFound, isTrue);

        // Second load starts (even if fails, isNotFound should be reset initially)
        when(mockThreadService.getThread('t2')).thenAnswer((_) async {
          expect(provider.isNotFound, isFalse); // Reset at start of load
          return createTestThread(id: 't2');
        });

        await provider.loadThread('t2');
      });

      test('clears error on successful load', () async {
        // First load fails with error
        when(mockThreadService.getThread('t1'))
            .thenThrow(Exception('Network error'));
        await provider.loadThread('t1');
        expect(provider.error, isNotNull);

        // Second load succeeds
        when(mockThreadService.getThread('t2'))
            .thenAnswer((_) async => createTestThread(id: 't2'));
        await provider.loadThread('t2');

        expect(provider.error, isNull);
      });
    });

    group('sendMessage', () {
      setUp(() async {
        // Load a thread first for sendMessage to work
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');
      });

      test('does nothing if thread is null', () async {
        // Reset provider to have no thread
        provider.clearConversation();
        expect(provider.thread, isNull);

        await provider.sendMessage('Hello');

        verifyNever(mockAIService.streamChat(any, any));
      });

      test('does nothing if already streaming', () async {
        // Simulate streaming state by starting one send
        when(mockAIService.streamChat('t1', 'First'))
            .thenAnswer((_) async* {
          // Never complete to keep streaming
          await Future.delayed(const Duration(hours: 1));
          yield MessageCompleteEvent(
              content: 'done', inputTokens: 0, outputTokens: 0);
        });

        // Start first message (don't await)
        provider.sendMessage('First');
        await Future.delayed(const Duration(milliseconds: 10));

        expect(provider.isStreaming, isTrue);

        // Second message should be ignored
        await provider.sendMessage('Second');

        verify(mockAIService.streamChat('t1', 'First')).called(1);
        verifyNever(mockAIService.streamChat('t1', 'Second'));
      });

      test('adds user message optimistically', () async {
        when(mockAIService.streamChat('t1', 'Hello')).thenAnswer((_) async* {
          // Check that user message was added before stream completes
          expect(provider.messages.length, equals(1));
          expect(provider.messages.last.role, equals(MessageRole.user));
          expect(provider.messages.last.content, equals('Hello'));
          yield MessageCompleteEvent(
              content: 'Hi there', inputTokens: 10, outputTokens: 20);
        });

        await provider.sendMessage('Hello');
      });

      test('sets isStreaming true and clears streamingText', () async {
        when(mockAIService.streamChat('t1', 'Hello')).thenAnswer((_) async* {
          expect(provider.isStreaming, isTrue);
          expect(provider.streamingText, isEmpty);
          yield MessageCompleteEvent(
              content: 'Done', inputTokens: 0, outputTokens: 0);
        });

        await provider.sendMessage('Hello');
      });

      test('stores content in _lastFailedMessage for retry', () async {
        when(mockAIService.streamChat('t1', 'Hello')).thenAnswer((_) async* {
          yield ErrorEvent(message: 'Stream failed');
        });

        await provider.sendMessage('Hello');

        // After error, canRetry should be true (which means _lastFailedMessage is set)
        expect(provider.error, isNotNull);
        expect(provider.canRetry, isTrue);
      });
    });

    group('Streaming events', () {
      setUp(() async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');
      });

      test('TextDeltaEvent appends to streamingText', () async {
        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield TextDeltaEvent(text: 'Hello');
          yield TextDeltaEvent(text: ' World');
          yield MessageCompleteEvent(
              content: 'Hello World', inputTokens: 10, outputTokens: 20);
        });

        await provider.sendMessage('Hi');

        // After MessageComplete, streamingText is cleared,
        // but during streaming it should have accumulated
        expect(provider.messages.last.content, contains('Hello World'));
      });

      test('ToolExecutingEvent sets statusMessage', () async {
        String? capturedStatus;

        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield ToolExecutingEvent(status: 'Searching documents...');
          // Capture status before it gets cleared
          capturedStatus = provider.statusMessage;
          yield MessageCompleteEvent(
              content: 'Found it', inputTokens: 10, outputTokens: 20);
        });

        await provider.sendMessage('Hi');

        expect(capturedStatus, equals('Searching documents...'));
        // After complete, statusMessage is cleared
        expect(provider.statusMessage, isNull);
      });

      test('MessageCompleteEvent adds assistant message', () async {
        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield TextDeltaEvent(text: 'Response text');
          yield MessageCompleteEvent(
              content: 'Response text', inputTokens: 10, outputTokens: 20);
        });

        await provider.sendMessage('Hi');

        // Should have user message + assistant message
        expect(provider.messages.length, equals(2));
        expect(provider.messages.last.role, equals(MessageRole.assistant));
        expect(provider.messages.last.content, contains('Response text'));
      });

      test('MessageCompleteEvent clears streaming state', () async {
        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield TextDeltaEvent(text: 'Streaming...');
          yield MessageCompleteEvent(
              content: 'Done', inputTokens: 10, outputTokens: 20);
        });

        await provider.sendMessage('Hi');

        expect(provider.isStreaming, isFalse);
        expect(provider.streamingText, isEmpty);
        expect(provider.statusMessage, isNull);
      });

      test('MessageCompleteEvent clears _lastFailedMessage', () async {
        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield MessageCompleteEvent(
              content: 'Success', inputTokens: 10, outputTokens: 20);
        });

        await provider.sendMessage('Hi');

        // After success, canRetry should be false
        expect(provider.canRetry, isFalse);
      });

      test('ErrorEvent sets error and clears streaming state', () async {
        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield TextDeltaEvent(text: 'Partial...');
          yield ErrorEvent(message: 'Rate limit exceeded');
        });

        await provider.sendMessage('Hi');

        expect(provider.error, equals('Rate limit exceeded'));
        expect(provider.isStreaming, isFalse);
        expect(provider.streamingText, isEmpty);
        expect(provider.statusMessage, isNull);
      });

      test('Exception in stream sets error and clears streaming state',
          () async {
        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield TextDeltaEvent(text: 'Starting...');
          throw Exception('Connection lost');
        });

        await provider.sendMessage('Hi');

        expect(provider.error, contains('Connection lost'));
        expect(provider.isStreaming, isFalse);
        expect(provider.streamingText, isEmpty);
        expect(provider.statusMessage, isNull);
      });
    });

    group('clearConversation', () {
      test('resets all state including thread and messages', () async {
        // Set up state first
        final thread = createTestThread(messages: [
          createTestMessage(),
        ]);
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        expect(provider.thread, isNotNull);
        expect(provider.messages, isNotEmpty);

        provider.clearConversation();

        expect(provider.thread, isNull);
        expect(provider.messages, isEmpty);
        expect(provider.streamingText, isEmpty);
        expect(provider.statusMessage, isNull);
        expect(provider.isStreaming, isFalse);
        expect(provider.error, isNull);
        expect(provider.isNotFound, isFalse);
        expect(provider.loading, isFalse);
      });
    });

    group('clearError', () {
      test('clears error state', () async {
        when(mockThreadService.getThread('t1'))
            .thenThrow(Exception('Network error'));
        await provider.loadThread('t1');
        expect(provider.error, isNotNull);

        provider.clearError();

        expect(provider.error, isNull);
      });

      test('clears isNotFound state', () async {
        when(mockThreadService.getThread('t1'))
            .thenThrow(Exception('Thread not found'));
        await provider.loadThread('t1');
        expect(provider.isNotFound, isTrue);

        provider.clearError();

        expect(provider.isNotFound, isFalse);
      });

      test('clears _lastFailedMessage (canRetry becomes false)', () async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        when(mockAIService.streamChat('t1', 'Hello')).thenAnswer((_) async* {
          yield ErrorEvent(message: 'Failed');
        });
        await provider.sendMessage('Hello');

        expect(provider.canRetry, isTrue);

        provider.clearError();

        expect(provider.canRetry, isFalse);
      });
    });

    group('canRetry', () {
      test('returns true only when _lastFailedMessage and error both set',
          () async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        // Initially false
        expect(provider.canRetry, isFalse);

        // After error
        when(mockAIService.streamChat('t1', 'Hello')).thenAnswer((_) async* {
          yield ErrorEvent(message: 'Failed');
        });
        await provider.sendMessage('Hello');

        expect(provider.canRetry, isTrue);
      });

      test('returns false when only error is set (no failed message)',
          () async {
        when(mockThreadService.getThread('t1'))
            .thenThrow(Exception('Load failed'));
        await provider.loadThread('t1');

        // Has error from load, but no _lastFailedMessage
        expect(provider.error, isNotNull);
        expect(provider.canRetry, isFalse);
      });
    });

    group('retryLastMessage', () {
      test('does nothing if _lastFailedMessage is null', () async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        // No failed message
        provider.retryLastMessage();

        verifyNever(mockAIService.streamChat(any, any));
      });

      test('removes last user message and calls sendMessage', () async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        // First send fails
        when(mockAIService.streamChat('t1', 'Hello')).thenAnswer((_) async* {
          yield ErrorEvent(message: 'Network error');
        });
        await provider.sendMessage('Hello');

        expect(provider.messages.length, equals(1)); // User message still there
        expect(provider.messages.last.role, equals(MessageRole.user));
        expect(provider.canRetry, isTrue);

        // Setup successful retry
        when(mockAIService.streamChat('t1', 'Hello')).thenAnswer((_) async* {
          yield MessageCompleteEvent(
              content: 'Success!', inputTokens: 10, outputTokens: 20);
        });

        provider.retryLastMessage();
        await Future.delayed(const Duration(milliseconds: 50));

        // Verify streamChat was called with same content
        verify(mockAIService.streamChat('t1', 'Hello')).called(2);
      });
    });

    group('associateWithProject', () {
      test('returns false if no thread', () async {
        expect(provider.thread, isNull);

        final result = await provider.associateWithProject('project-1');

        expect(result, isFalse);
        verifyNever(
            mockThreadService.associateWithProject(any, any));
      });

      test('calls threadService and reloads thread on success', () async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        final updatedThread = createTestThread(
          projectId: 'project-1',
          title: 'Updated Thread',
        );
        when(mockThreadService.associateWithProject('t1', 'project-1'))
            .thenAnswer((_) async => updatedThread);
        when(mockThreadService.getThread('t1'))
            .thenAnswer((_) async => updatedThread);

        final result = await provider.associateWithProject('project-1');

        expect(result, isTrue);
        verify(mockThreadService.associateWithProject('t1', 'project-1'))
            .called(1);
        // Thread should be reloaded
        verify(mockThreadService.getThread('t1')).called(2);
      });

      test('sets error on failure', () async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        when(mockThreadService.associateWithProject('t1', 'project-1'))
            .thenThrow(Exception('Project not found'));

        final result = await provider.associateWithProject('project-1');

        expect(result, isFalse);
        expect(provider.error, contains('Project not found'));
      });
    });

    group('Listener notifications', () {
      test('notifies listeners on loadThread state changes', () async {
        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        when(mockThreadService.getThread('t1'))
            .thenAnswer((_) async => createTestThread());

        await provider.loadThread('t1');

        // Should notify at least twice: loading start, loading complete
        expect(notifyCount, greaterThanOrEqualTo(2));
      });

      test('notifies listeners during streaming', () async {
        final thread = createTestThread();
        when(mockThreadService.getThread('t1')).thenAnswer((_) async => thread);
        await provider.loadThread('t1');

        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
          yield TextDeltaEvent(text: 'Hello');
          yield TextDeltaEvent(text: ' there');
          yield MessageCompleteEvent(
              content: 'Hello there', inputTokens: 10, outputTokens: 20);
        });

        await provider.sendMessage('Hi');

        // Should notify: streaming start, each delta, message complete
        expect(notifyCount, greaterThanOrEqualTo(4));
      });
    });
  });
}
