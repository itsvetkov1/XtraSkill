/// Widget tests for conversation screen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/message.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/providers/conversation_provider.dart';
import 'package:frontend/screens/conversation/conversation_screen.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'conversation_screen_test.mocks.dart';

@GenerateNiceMocks([MockSpec<ConversationProvider>()])
void main() {
  group('ConversationScreen Widget Tests', () {
    late MockConversationProvider mockConversationProvider;
    const testThreadId = 'test-thread-123';

    setUp(() {
      mockConversationProvider = MockConversationProvider();
      // Default mock behavior
      when(mockConversationProvider.loading).thenReturn(false);
      when(mockConversationProvider.messages).thenReturn([]);
      when(mockConversationProvider.error).thenReturn(null);
      when(mockConversationProvider.isStreaming).thenReturn(false);
      when(mockConversationProvider.streamingText).thenReturn('');
      when(mockConversationProvider.statusMessage).thenReturn(null);
      when(mockConversationProvider.thread).thenReturn(null);
      when(mockConversationProvider.loadThread(any)).thenAnswer((_) async {});
      when(mockConversationProvider.clearConversation())
          .thenAnswer((_) async {});
      when(mockConversationProvider.clearError()).thenAnswer((_) async {});
    });

    testWidgets('Message bubbles render for user and assistant roles',
        (tester) async {
      final mockMessages = [
        Message(
          id: '1',
          role: MessageRole.user,
          content: 'Hello, can you help me?',
          createdAt: DateTime.now(),
        ),
        Message(
          id: '2',
          role: MessageRole.assistant,
          content: 'Of course! How can I assist you?',
          createdAt: DateTime.now(),
        ),
      ];

      when(mockConversationProvider.messages).thenReturn(mockMessages);
      when(mockConversationProvider.loading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Hello, can you help me?'), findsOneWidget);
      expect(find.text('Of course! How can I assist you?'), findsOneWidget);
    });

    testWidgets('Chat input field present', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // ChatInput widget should be present
      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('Send button present', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.send), findsOneWidget);
    });

    testWidgets('Loading state shows during streaming', (tester) async {
      when(mockConversationProvider.isStreaming).thenReturn(true);
      when(mockConversationProvider.streamingText)
          .thenReturn('Thinking...');

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Thinking...'), findsOneWidget);
    });

    testWidgets('Empty state shows "Start conversation"', (tester) async {
      when(mockConversationProvider.messages).thenReturn([]);
      when(mockConversationProvider.loading).thenReturn(false);
      when(mockConversationProvider.isStreaming).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Start a conversation'), findsOneWidget);
      expect(find.byIcon(Icons.chat_bubble_outline), findsOneWidget);
    });

    testWidgets('Thread title displays in app bar', (tester) async {
      final mockThread = Thread(
        id: testThreadId,
        projectId: 'project-123',
        title: 'Requirements Discussion',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      when(mockConversationProvider.thread).thenReturn(mockThread);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Requirements Discussion'), findsOneWidget);
    });

    testWidgets('Shows "New Conversation" when thread has no title',
        (tester) async {
      final mockThread = Thread(
        id: testThreadId,
        projectId: 'project-123',
        title: null,
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      when(mockConversationProvider.thread).thenReturn(mockThread);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('New Conversation'), findsOneWidget);
    });

    testWidgets('Error banner shows when error present', (tester) async {
      when(mockConversationProvider.error)
          .thenReturn('Failed to send message');

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Failed to send message'), findsOneWidget);
      expect(find.text('Dismiss'), findsOneWidget);
      expect(find.byType(MaterialBanner), findsOneWidget);
    });

    testWidgets('Loading indicator shows when loading thread',
        (tester) async {
      when(mockConversationProvider.loading).thenReturn(true);
      when(mockConversationProvider.messages).thenReturn([]);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pump(); // Initial build
      await tester.pump(); // Post-frame callback

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('Multiple messages render in correct order', (tester) async {
      final mockMessages = [
        Message(
          id: '1',
          role: MessageRole.user,
          content: 'First message',
          createdAt: DateTime.now(),
        ),
        Message(
          id: '2',
          role: MessageRole.assistant,
          content: 'Second message',
          createdAt: DateTime.now(),
        ),
        Message(
          id: '3',
          role: MessageRole.user,
          content: 'Third message',
          createdAt: DateTime.now(),
        ),
      ];

      when(mockConversationProvider.messages).thenReturn(mockMessages);
      when(mockConversationProvider.loading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ConversationProvider>.value(
            value: mockConversationProvider,
            child: const ConversationScreen(threadId: testThreadId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('First message'), findsOneWidget);
      expect(find.text('Second message'), findsOneWidget);
      expect(find.text('Third message'), findsOneWidget);
    });
  });
}
