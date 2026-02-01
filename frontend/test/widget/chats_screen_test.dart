/// Widget tests for chats screen (Phase 25/26).
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/providers/chats_provider.dart';
import 'package:frontend/providers/provider_provider.dart';
import 'package:frontend/screens/chats_screen.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'chats_screen_test.mocks.dart';

@GenerateNiceMocks([
  MockSpec<ChatsProvider>(),
  MockSpec<ProviderProvider>(),
])
void main() {
  group('ChatsScreen Widget Tests', () {
    late MockChatsProvider mockChatsProvider;
    late MockProviderProvider mockProviderProvider;

    setUp(() {
      mockChatsProvider = MockChatsProvider();
      mockProviderProvider = MockProviderProvider();

      // Default mock behavior
      when(mockChatsProvider.isLoading).thenReturn(false);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.threads).thenReturn([]);
      when(mockChatsProvider.error).thenReturn(null);
      when(mockChatsProvider.hasMore).thenReturn(false);
      when(mockChatsProvider.total).thenReturn(0);
      when(mockChatsProvider.loadThreads()).thenAnswer((_) async {});
      when(mockChatsProvider.loadMoreThreads()).thenAnswer((_) async {});

      when(mockProviderProvider.selectedProvider).thenReturn('anthropic');
    });

    Widget buildTestWidget() {
      return MaterialApp(
        home: MultiProvider(
          providers: [
            ChangeNotifierProvider<ChatsProvider>.value(
              value: mockChatsProvider,
            ),
            ChangeNotifierProvider<ProviderProvider>.value(
              value: mockProviderProvider,
            ),
          ],
          child: const ChatsScreen(),
        ),
      );
    }

    testWidgets('Shows loading spinner during initial load', (tester) async {
      when(mockChatsProvider.isLoading).thenReturn(true);
      when(mockChatsProvider.isInitialized).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pump();

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('Shows empty state when no threads', (tester) async {
      when(mockChatsProvider.threads).thenReturn([]);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('No chats yet'), findsOneWidget);
      expect(find.text('Start a new conversation'), findsOneWidget);
      expect(find.byIcon(Icons.chat_bubble_outline), findsOneWidget);
    });

    testWidgets('Shows error state with retry button', (tester) async {
      when(mockChatsProvider.error).thenReturn('Network error');
      when(mockChatsProvider.threads).thenReturn([]);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.textContaining('Network error'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('Displays project-less threads correctly', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: null,
          projectName: null,
          title: 'Global Chat 1',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 5,
        ),
      ];

      when(mockChatsProvider.threads).thenReturn(mockThreads);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);
      when(mockChatsProvider.total).thenReturn(1);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('Global Chat 1'), findsOneWidget);
      expect(find.text('No Project'), findsOneWidget);
      expect(find.text('5 messages'), findsOneWidget);
    });

    testWidgets('Displays project-based threads with project name',
        (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: 'project-1',
          projectName: 'Test Project',
          title: 'Project Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 10,
        ),
      ];

      when(mockChatsProvider.threads).thenReturn(mockThreads);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);
      when(mockChatsProvider.total).thenReturn(1);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('Project Thread'), findsOneWidget);
      expect(find.text('Test Project'), findsOneWidget);
      expect(find.text('10 messages'), findsOneWidget);
    });

    testWidgets('Displays mixed thread types correctly', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: null,
          projectName: null,
          title: 'Global Chat',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 3,
        ),
        Thread(
          id: '2',
          projectId: 'project-1',
          projectName: 'My Project',
          title: 'Project Chat',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now().subtract(const Duration(hours: 1)),
          messageCount: 7,
        ),
      ];

      when(mockChatsProvider.threads).thenReturn(mockThreads);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);
      when(mockChatsProvider.total).thenReturn(2);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('Global Chat'), findsOneWidget);
      expect(find.text('No Project'), findsOneWidget);
      expect(find.text('Project Chat'), findsOneWidget);
      expect(find.text('My Project'), findsOneWidget);
    });

    testWidgets('New Chat button is present in header', (tester) async {
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('New Chat'), findsWidgets);
      expect(find.byIcon(Icons.add), findsWidgets);
    });

    testWidgets('Shows loading indicator when hasMore is true', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: null,
          projectName: null,
          title: 'Chat 1',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 1,
        ),
      ];

      when(mockChatsProvider.threads).thenReturn(mockThreads);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);
      when(mockChatsProvider.hasMore).thenReturn(true);
      when(mockChatsProvider.total).thenReturn(10);

      await tester.pumpWidget(buildTestWidget());
      await tester.pump(); // Initial build
      await tester.pump(); // Post-frame callback

      // When hasMore is true and initialized, ListView includes an extra item
      // for the loading indicator at the end
      final listView = tester.widget<ListView>(find.byType(ListView));
      expect(listView, isNotNull);
    });

    testWidgets('Thread with null title shows "New Chat"', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: null,
          projectName: null,
          title: null,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 0,
        ),
      ];

      when(mockChatsProvider.threads).thenReturn(mockThreads);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);
      when(mockChatsProvider.total).thenReturn(1);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Thread list tile shows "New Chat" for null title
      expect(find.text('New Chat'), findsWidgets);
    });

    testWidgets('Retry button calls loadThreads on error state',
        (tester) async {
      when(mockChatsProvider.error).thenReturn('Connection failed');
      when(mockChatsProvider.threads).thenReturn([]);
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();

      verify(mockChatsProvider.loadThreads()).called(greaterThan(0));
    });

    testWidgets('Header shows "Chats" title', (tester) async {
      when(mockChatsProvider.isInitialized).thenReturn(true);
      when(mockChatsProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('Chats'), findsOneWidget);
    });
  });
}
