/// Widget tests for thread list screen (Phase 27).
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/models/thread_sort.dart';
import 'package:frontend/providers/thread_provider.dart';
import 'package:frontend/screens/threads/thread_list_screen.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'thread_list_screen_test.mocks.dart';

@GenerateNiceMocks([MockSpec<ThreadProvider>()])
void main() {
  group('ThreadListScreen Search/Sort Tests', () {
    late MockThreadProvider mockThreadProvider;
    const testProjectId = 'test-project-123';

    setUp(() {
      mockThreadProvider = MockThreadProvider();

      // Default mock behavior
      when(mockThreadProvider.isLoading).thenReturn(false);
      when(mockThreadProvider.loading).thenReturn(false);
      when(mockThreadProvider.threads).thenReturn([]);
      when(mockThreadProvider.filteredThreads).thenReturn([]);
      when(mockThreadProvider.error).thenReturn(null);
      when(mockThreadProvider.searchQuery).thenReturn('');
      when(mockThreadProvider.sortOption).thenReturn(ThreadSortOption.newest);
      when(mockThreadProvider.loadThreads(any)).thenAnswer((_) async {});
      when(mockThreadProvider.clearSearch()).thenReturn(null);
      when(mockThreadProvider.clearError()).thenReturn(null);
    });

    Widget buildTestWidget() {
      return MaterialApp(
        home: ChangeNotifierProvider<ThreadProvider>.value(
          value: mockThreadProvider,
          child: const ThreadListScreen(projectId: testProjectId),
        ),
      );
    }

    testWidgets('Search bar filters project threads by title', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: testProjectId,
          title: 'Requirements Discussion',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 5,
        ),
        Thread(
          id: '2',
          projectId: testProjectId,
          title: 'Bug Fixing Session',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now().subtract(const Duration(hours: 1)),
          messageCount: 3,
        ),
      ];

      when(mockThreadProvider.threads).thenReturn(mockThreads);
      when(mockThreadProvider.filteredThreads).thenReturn(mockThreads);
      when(mockThreadProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Verify search bar is present
      expect(find.byType(SearchBar), findsOneWidget);

      // Enter search text
      await tester.enterText(find.byType(SearchBar), 'Requirements');
      await tester.pumpAndSettle();

      // Verify setSearchQuery was called with the search text
      verify(mockThreadProvider.setSearchQuery('Requirements')).called(1);
    });

    testWidgets('Sort options change project thread order', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: testProjectId,
          title: 'Alpha Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 5,
        ),
        Thread(
          id: '2',
          projectId: testProjectId,
          title: 'Beta Thread',
          createdAt: DateTime.now().subtract(const Duration(days: 1)),
          updatedAt: DateTime.now().subtract(const Duration(days: 1)),
          lastActivityAt: DateTime.now().subtract(const Duration(days: 1)),
          messageCount: 3,
        ),
      ];

      when(mockThreadProvider.threads).thenReturn(mockThreads);
      when(mockThreadProvider.filteredThreads).thenReturn(mockThreads);
      when(mockThreadProvider.isLoading).thenReturn(false);
      when(mockThreadProvider.sortOption).thenReturn(ThreadSortOption.newest);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Verify SegmentedButton is present with sort options
      expect(find.byType(SegmentedButton<ThreadSortOption>), findsOneWidget);
      expect(find.text('Newest'), findsOneWidget);
      expect(find.text('Oldest'), findsOneWidget);
      expect(find.text('A-Z'), findsOneWidget);

      // Tap on Oldest option
      await tester.tap(find.text('Oldest'));
      await tester.pumpAndSettle();

      // Verify setSortOption was called
      verify(mockThreadProvider.setSortOption(ThreadSortOption.oldest)).called(1);
    });

    testWidgets('Empty search results show appropriate message', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: testProjectId,
          title: 'Existing Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 5,
        ),
      ];

      // Setup: threads exist but filter returns empty
      when(mockThreadProvider.threads).thenReturn(mockThreads);
      when(mockThreadProvider.filteredThreads).thenReturn([]);
      when(mockThreadProvider.searchQuery).thenReturn('nonexistent');
      when(mockThreadProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Verify "No conversations matching" message
      expect(find.textContaining("No conversations matching 'nonexistent'"), findsOneWidget);
      expect(find.text('Clear search'), findsOneWidget);
      expect(find.byIcon(Icons.search_off), findsOneWidget);
    });

    testWidgets('Clear button clears search and shows all threads', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: testProjectId,
          title: 'Test Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 5,
        ),
      ];

      // Setup: threads exist but filter returns empty (active search)
      when(mockThreadProvider.threads).thenReturn(mockThreads);
      when(mockThreadProvider.filteredThreads).thenReturn([]);
      when(mockThreadProvider.searchQuery).thenReturn('search term');
      when(mockThreadProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Find and tap clear search button
      await tester.tap(find.text('Clear search'));
      await tester.pumpAndSettle();

      // Verify clearSearch was called
      verify(mockThreadProvider.clearSearch()).called(1);
    });

    testWidgets('Threads display correctly with filter applied', (tester) async {
      final filteredThreads = [
        Thread(
          id: '1',
          projectId: testProjectId,
          title: 'Matching Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 10,
        ),
      ];

      when(mockThreadProvider.threads).thenReturn(filteredThreads);
      when(mockThreadProvider.filteredThreads).thenReturn(filteredThreads);
      when(mockThreadProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Verify thread is displayed
      expect(find.text('Matching Thread'), findsOneWidget);
      expect(find.text('10'), findsOneWidget); // message count
    });

    testWidgets('Empty state shows when no threads exist', (tester) async {
      when(mockThreadProvider.threads).thenReturn([]);
      when(mockThreadProvider.filteredThreads).thenReturn([]);
      when(mockThreadProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Verify empty state message (not search empty state)
      expect(find.text('No conversations yet'), findsOneWidget);
      expect(find.text('Start Conversation'), findsOneWidget);
    });

    testWidgets('Alphabetical sort option selectable', (tester) async {
      final mockThreads = [
        Thread(
          id: '1',
          projectId: testProjectId,
          title: 'Zebra Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastActivityAt: DateTime.now(),
          messageCount: 1,
        ),
      ];

      when(mockThreadProvider.threads).thenReturn(mockThreads);
      when(mockThreadProvider.filteredThreads).thenReturn(mockThreads);
      when(mockThreadProvider.isLoading).thenReturn(false);
      when(mockThreadProvider.sortOption).thenReturn(ThreadSortOption.newest);

      await tester.pumpWidget(buildTestWidget());
      await tester.pumpAndSettle();

      // Tap A-Z sort option
      await tester.tap(find.text('A-Z'));
      await tester.pumpAndSettle();

      verify(mockThreadProvider.setSortOption(ThreadSortOption.alphabetical)).called(1);
    });
  });
}
