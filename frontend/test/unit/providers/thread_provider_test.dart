/// Unit tests for ThreadProvider (Phase 31).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/models/thread_sort.dart';
import 'package:frontend/providers/thread_provider.dart';
import 'package:frontend/services/thread_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'thread_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<ThreadService>()])
void main() {
  group('ThreadProvider Unit Tests', () {
    late MockThreadService mockService;
    late ThreadProvider provider;

    setUp(() {
      mockService = MockThreadService();
      provider = ThreadProvider(threadService: mockService);
    });

    group('Initial State', () {
      test('starts with empty threads list', () {
        expect(provider.threads, isEmpty);
      });

      test('starts with no selected thread', () {
        expect(provider.selectedThread, isNull);
      });

      test('starts with loading false', () {
        expect(provider.loading, isFalse);
        expect(provider.isLoading, isFalse);
      });

      test('starts with no error', () {
        expect(provider.error, isNull);
      });

      test('starts with empty searchQuery', () {
        expect(provider.searchQuery, isEmpty);
      });

      test('starts with sortOption = newest', () {
        expect(provider.sortOption, equals(ThreadSortOption.newest));
      });

      test('starts with empty filteredThreads', () {
        expect(provider.filteredThreads, isEmpty);
      });
    });

    group('loadThreads', () {
      test('sets loading to true during call', () async {
        when(mockService.getThreads(any)).thenAnswer(
          (_) async {
            expect(provider.loading, isTrue);
            return <Thread>[];
          },
        );

        await provider.loadThreads('project-1');
      });

      test('updates threads on success', () async {
        final mockThreads = [
          Thread(
            id: '1',
            projectId: 'project-1',
            title: 'Thread 1',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
          Thread(
            id: '2',
            projectId: 'project-1',
            title: 'Thread 2',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
        ];

        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => mockThreads);

        await provider.loadThreads('project-1');

        expect(provider.threads, equals(mockThreads));
        expect(provider.loading, isFalse);
        expect(provider.error, isNull);
      });

      test('rethrows error on failure', () async {
        when(mockService.getThreads(any))
            .thenThrow(Exception('Network error'));

        expect(
          () => provider.loadThreads('project-1'),
          throwsException,
        );
      });

      test('sets error message on failure', () async {
        when(mockService.getThreads(any))
            .thenThrow(Exception('Network error'));

        try {
          await provider.loadThreads('project-1');
        } catch (_) {}

        expect(provider.error, isNotNull);
        expect(provider.error, contains('Network error'));
        expect(provider.loading, isFalse);
      });
    });

    group('createThread', () {
      test('adds thread to beginning of list on success', () async {
        // Setup initial threads
        when(mockService.getThreads('project-1')).thenAnswer(
          (_) async => [
            Thread(
              id: 'existing',
              projectId: 'project-1',
              title: 'Existing',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            ),
          ],
        );
        await provider.loadThreads('project-1');

        // Create new thread
        final newThread = Thread(
          id: 'new-1',
          projectId: 'project-1',
          title: 'New Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        when(mockService.createThread('project-1', 'New Thread', provider: null))
            .thenAnswer((_) async => newThread);

        final result = await provider.createThread('project-1', 'New Thread');

        expect(result, equals(newThread));
        expect(provider.threads.length, equals(2));
        expect(provider.threads.first.id, equals('new-1'));
      });

      test('returns thread on success', () async {
        final newThread = Thread(
          id: 'new-1',
          projectId: 'project-1',
          title: 'Test',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        when(mockService.createThread('project-1', 'Test', provider: null))
            .thenAnswer((_) async => newThread);

        final result = await provider.createThread('project-1', 'Test');

        expect(result.id, equals('new-1'));
        expect(result.title, equals('Test'));
      });

      test('passes optional provider parameter', () async {
        final newThread = Thread(
          id: 'new-1',
          projectId: 'project-1',
          title: 'Test',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          modelProvider: 'google',
        );
        when(mockService.createThread('project-1', 'Test', provider: 'google'))
            .thenAnswer((_) async => newThread);

        await provider.createThread('project-1', 'Test', provider: 'google');

        verify(mockService.createThread('project-1', 'Test', provider: 'google'))
            .called(1);
      });

      test('rethrows error on failure', () async {
        when(mockService.createThread(any, any, provider: anyNamed('provider')))
            .thenThrow(Exception('Creation failed'));

        expect(
          () => provider.createThread('project-1', 'Test'),
          throwsException,
        );
      });

      test('sets error message on failure', () async {
        when(mockService.createThread(any, any, provider: anyNamed('provider')))
            .thenThrow(Exception('Creation failed'));

        try {
          await provider.createThread('project-1', 'Test');
        } catch (_) {}

        expect(provider.error, isNotNull);
        expect(provider.loading, isFalse);
      });
    });

    group('selectThread', () {
      test('loads thread with messages and sets selectedThread on success', () async {
        final threadWithMessages = Thread(
          id: 'thread-1',
          projectId: 'project-1',
          title: 'Selected Thread',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          messages: [], // Would include messages in real response
        );

        when(mockService.getThread('thread-1'))
            .thenAnswer((_) async => threadWithMessages);

        await provider.selectThread('thread-1');

        expect(provider.selectedThread, equals(threadWithMessages));
        expect(provider.loading, isFalse);
      });

      test('sets loading during call', () async {
        when(mockService.getThread(any)).thenAnswer(
          (_) async {
            expect(provider.loading, isTrue);
            return Thread(
              id: 'thread-1',
              title: 'Test',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            );
          },
        );

        await provider.selectThread('thread-1');
      });

      test('rethrows error on failure', () async {
        when(mockService.getThread(any))
            .thenThrow(Exception('Thread not found'));

        expect(
          () => provider.selectThread('thread-1'),
          throwsException,
        );
      });

      test('sets error message on failure', () async {
        when(mockService.getThread(any))
            .thenThrow(Exception('Thread not found'));

        try {
          await provider.selectThread('thread-1');
        } catch (_) {}

        expect(provider.error, isNotNull);
        expect(provider.error, contains('Thread not found'));
        expect(provider.loading, isFalse);
      });
    });

    group('renameThread', () {
      test('updates thread in list on success', () async {
        // Setup initial threads
        when(mockService.getThreads('project-1')).thenAnswer(
          (_) async => [
            Thread(
              id: 'thread-1',
              projectId: 'project-1',
              title: 'Old Title',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            ),
          ],
        );
        await provider.loadThreads('project-1');

        // Rename thread
        final renamedThread = Thread(
          id: 'thread-1',
          projectId: 'project-1',
          title: 'New Title',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        when(mockService.renameThread('thread-1', 'New Title'))
            .thenAnswer((_) async => renamedThread);

        final result = await provider.renameThread('thread-1', 'New Title');

        expect(result?.title, equals('New Title'));
        expect(provider.threads.first.title, equals('New Title'));
      });

      test('updates selectedThread if same thread is renamed', () async {
        // Select a thread first
        final thread = Thread(
          id: 'thread-1',
          projectId: 'project-1',
          title: 'Old Title',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        when(mockService.getThread('thread-1'))
            .thenAnswer((_) async => thread);
        await provider.selectThread('thread-1');

        // Also load it into threads list
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => [thread]);
        await provider.loadThreads('project-1');

        // Rename it
        final renamedThread = Thread(
          id: 'thread-1',
          projectId: 'project-1',
          title: 'New Title',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        when(mockService.renameThread('thread-1', 'New Title'))
            .thenAnswer((_) async => renamedThread);

        await provider.renameThread('thread-1', 'New Title');

        expect(provider.selectedThread?.title, equals('New Title'));
      });

      test('returns thread on success', () async {
        when(mockService.getThreads('project-1')).thenAnswer(
          (_) async => [
            Thread(
              id: 'thread-1',
              title: 'Old',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            ),
          ],
        );
        await provider.loadThreads('project-1');

        final renamedThread = Thread(
          id: 'thread-1',
          title: 'New',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        when(mockService.renameThread('thread-1', 'New'))
            .thenAnswer((_) async => renamedThread);

        final result = await provider.renameThread('thread-1', 'New');

        expect(result, isNotNull);
        expect(result?.title, equals('New'));
      });

      test('sets error and returns null on failure (does NOT rethrow)', () async {
        when(mockService.getThreads('project-1')).thenAnswer(
          (_) async => [
            Thread(
              id: 'thread-1',
              title: 'Test',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            ),
          ],
        );
        await provider.loadThreads('project-1');

        when(mockService.renameThread(any, any))
            .thenThrow(Exception('Rename failed'));

        // Should NOT throw
        final result = await provider.renameThread('thread-1', 'New');

        expect(result, isNull);
        expect(provider.error, isNotNull);
        expect(provider.loading, isFalse);
      });
    });

    group('clearThreads', () {
      test('resets all state including search/sort', () async {
        // Setup initial state
        when(mockService.getThreads('project-1')).thenAnswer(
          (_) async => [
            Thread(
              id: 'thread-1',
              title: 'Test',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            ),
          ],
        );
        await provider.loadThreads('project-1');
        provider.setSearchQuery('test');
        provider.setSortOption(ThreadSortOption.alphabetical);
        expect(provider.threads.isNotEmpty, isTrue);
        expect(provider.searchQuery, isNotEmpty);
        expect(provider.sortOption, equals(ThreadSortOption.alphabetical));

        // Clear
        provider.clearThreads();

        expect(provider.threads, isEmpty);
        expect(provider.selectedThread, isNull);
        expect(provider.error, isNull);
        expect(provider.loading, isFalse);
        expect(provider.searchQuery, isEmpty);
        expect(provider.sortOption, equals(ThreadSortOption.newest));
      });
    });

    group('clearError', () {
      test('clears error state', () async {
        // Set error
        when(mockService.getThreads(any))
            .thenThrow(Exception('Error'));
        try {
          await provider.loadThreads('project-1');
        } catch (_) {}
        expect(provider.error, isNotNull);

        // Clear it
        provider.clearError();

        expect(provider.error, isNull);
      });
    });

    group('setSearchQuery/clearSearch', () {
      test('setSearchQuery updates searchQuery', () {
        provider.setSearchQuery('test query');

        expect(provider.searchQuery, equals('test query'));
      });

      test('setSearchQuery notifies listeners', () {
        var notified = false;
        provider.addListener(() => notified = true);

        provider.setSearchQuery('test');

        expect(notified, isTrue);
      });

      test('clearSearch resets searchQuery to empty', () {
        provider.setSearchQuery('test query');
        expect(provider.searchQuery, isNotEmpty);

        provider.clearSearch();

        expect(provider.searchQuery, isEmpty);
      });

      test('clearSearch notifies listeners', () {
        provider.setSearchQuery('test');

        var notified = false;
        provider.addListener(() => notified = true);

        provider.clearSearch();

        expect(notified, isTrue);
      });
    });

    group('setSortOption', () {
      test('updates sortOption', () {
        provider.setSortOption(ThreadSortOption.oldest);

        expect(provider.sortOption, equals(ThreadSortOption.oldest));
      });

      test('notifies listeners', () {
        var notified = false;
        provider.addListener(() => notified = true);

        provider.setSortOption(ThreadSortOption.alphabetical);

        expect(notified, isTrue);
      });
    });

    group('filteredThreads', () {
      final threads = [
        Thread(
          id: '1',
          title: 'Alpha',
          createdAt: DateTime(2024, 1, 1),
          updatedAt: DateTime(2024, 1, 1),
        ),
        Thread(
          id: '2',
          title: 'Beta',
          createdAt: DateTime(2024, 1, 3),
          updatedAt: DateTime(2024, 1, 3),
        ),
        Thread(
          id: '3',
          title: 'Charlie',
          createdAt: DateTime(2024, 1, 2),
          updatedAt: DateTime(2024, 1, 2),
        ),
      ];

      test('filters by search query case-insensitively', () async {
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threads);
        await provider.loadThreads('project-1');

        provider.setSearchQuery('alpha');

        final filtered = provider.filteredThreads;
        expect(filtered.length, equals(1));
        expect(filtered[0].title, equals('Alpha'));
      });

      test('filters with uppercase query', () async {
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threads);
        await provider.loadThreads('project-1');

        provider.setSearchQuery('BETA');

        final filtered = provider.filteredThreads;
        expect(filtered.length, equals(1));
        expect(filtered[0].title, equals('Beta'));
      });

      test('returns all threads when search query is empty', () async {
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threads);
        await provider.loadThreads('project-1');

        expect(provider.searchQuery, isEmpty);
        expect(provider.filteredThreads.length, equals(3));
      });

      test('sorts by newest (default) - updatedAt descending', () async {
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threads);
        await provider.loadThreads('project-1');

        expect(provider.sortOption, equals(ThreadSortOption.newest));
        final sorted = provider.filteredThreads;

        // Beta (Jan 3), Charlie (Jan 2), Alpha (Jan 1)
        expect(sorted[0].title, equals('Beta'));
        expect(sorted[1].title, equals('Charlie'));
        expect(sorted[2].title, equals('Alpha'));
      });

      test('sorts by oldest - updatedAt ascending', () async {
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threads);
        await provider.loadThreads('project-1');

        provider.setSortOption(ThreadSortOption.oldest);
        final sorted = provider.filteredThreads;

        // Alpha (Jan 1), Charlie (Jan 2), Beta (Jan 3)
        expect(sorted[0].title, equals('Alpha'));
        expect(sorted[1].title, equals('Charlie'));
        expect(sorted[2].title, equals('Beta'));
      });

      test('sorts alphabetically - title ascending', () async {
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threads);
        await provider.loadThreads('project-1');

        provider.setSortOption(ThreadSortOption.alphabetical);
        final sorted = provider.filteredThreads;

        // Alpha, Beta, Charlie
        expect(sorted[0].title, equals('Alpha'));
        expect(sorted[1].title, equals('Beta'));
        expect(sorted[2].title, equals('Charlie'));
      });

      test('combines filter and sort correctly', () async {
        final moreThreads = [
          Thread(
            id: '1',
            title: 'Test Alpha',
            createdAt: DateTime(2024, 1, 1),
            updatedAt: DateTime(2024, 1, 1),
          ),
          Thread(
            id: '2',
            title: 'Test Beta',
            createdAt: DateTime(2024, 1, 3),
            updatedAt: DateTime(2024, 1, 3),
          ),
          Thread(
            id: '3',
            title: 'Other',
            createdAt: DateTime(2024, 1, 2),
            updatedAt: DateTime(2024, 1, 2),
          ),
        ];
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => moreThreads);
        await provider.loadThreads('project-1');

        // Filter by 'Test' and sort alphabetically
        provider.setSearchQuery('Test');
        provider.setSortOption(ThreadSortOption.alphabetical);

        final result = provider.filteredThreads;
        expect(result.length, equals(2));
        expect(result[0].title, equals('Test Alpha'));
        expect(result[1].title, equals('Test Beta'));
      });

      test('uses lastActivityAt when available for sorting', () async {
        final threadsWithActivity = [
          Thread(
            id: '1',
            title: 'Old Thread',
            createdAt: DateTime(2024, 1, 1),
            updatedAt: DateTime(2024, 1, 1),
            lastActivityAt: DateTime(2024, 1, 5), // Most recent activity
          ),
          Thread(
            id: '2',
            title: 'New Thread',
            createdAt: DateTime(2024, 1, 3),
            updatedAt: DateTime(2024, 1, 3),
            // No lastActivityAt, uses updatedAt
          ),
        ];
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threadsWithActivity);
        await provider.loadThreads('project-1');

        final sorted = provider.filteredThreads;
        // Old Thread has lastActivityAt of Jan 5, New Thread uses updatedAt Jan 3
        expect(sorted[0].title, equals('Old Thread'));
        expect(sorted[1].title, equals('New Thread'));
      });

      test('handles null titles in alphabetical sort', () async {
        final threadsWithNulls = [
          Thread(
            id: '1',
            title: null, // Untitled
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
          Thread(
            id: '2',
            title: 'Zebra',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
        ];
        when(mockService.getThreads('project-1'))
            .thenAnswer((_) async => threadsWithNulls);
        await provider.loadThreads('project-1');

        provider.setSortOption(ThreadSortOption.alphabetical);
        final sorted = provider.filteredThreads;

        // null title becomes '' which sorts before 'Zebra'
        expect(sorted[0].title, isNull);
        expect(sorted[1].title, equals('Zebra'));
      });
    });

    group('deleteThread', () {
      // Note: Full delete testing requires BuildContext which we skip
      // Testing only immediate state changes

      test('would remove thread from list immediately', () async {
        // Setup initial threads
        when(mockService.getThreads('project-1')).thenAnswer(
          (_) async => [
            Thread(
              id: 'thread-1',
              title: 'First',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            ),
            Thread(
              id: 'thread-2',
              title: 'Second',
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            ),
          ],
        );
        await provider.loadThreads('project-1');
        expect(provider.threads.length, equals(2));

        // Note: Cannot fully test deleteThread without BuildContext
        // The method requires a BuildContext for SnackBar
      });
    });

    group('notifyListeners', () {
      test('notifies on loadThreads', () async {
        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        when(mockService.getThreads(any)).thenAnswer(
          (_) async => <Thread>[],
        );
        await provider.loadThreads('project-1');

        // Should notify at least twice (loading true, loading false)
        expect(notifyCount, greaterThanOrEqualTo(2));
      });

      test('notifies on clearThreads', () {
        var notified = false;
        provider.addListener(() => notified = true);

        provider.clearThreads();

        expect(notified, isTrue);
      });

      test('notifies on clearError', () async {
        when(mockService.getThreads(any)).thenThrow(Exception('Error'));
        try {
          await provider.loadThreads('project-1');
        } catch (_) {}

        var notified = false;
        provider.addListener(() => notified = true);

        provider.clearError();

        expect(notified, isTrue);
      });
    });
  });
}
