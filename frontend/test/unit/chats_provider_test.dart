/// Unit tests for ChatsProvider (Phase 25/26).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/providers/chats_provider.dart';
import 'package:frontend/services/thread_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'chats_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<ThreadService>()])
void main() {
  group('ChatsProvider Unit Tests', () {
    late MockThreadService mockThreadService;
    late ChatsProvider provider;

    setUp(() {
      mockThreadService = MockThreadService();
      provider = ChatsProvider(threadService: mockThreadService);
    });

    group('Initial State', () {
      test('starts with empty threads list', () {
        expect(provider.threads, isEmpty);
      });

      test('starts with isLoading false', () {
        expect(provider.isLoading, isFalse);
      });

      test('starts with isInitialized false', () {
        expect(provider.isInitialized, isFalse);
      });

      test('starts with hasMore false', () {
        expect(provider.hasMore, isFalse);
      });

      test('starts with no error', () {
        expect(provider.error, isNull);
      });

      test('starts with total 0', () {
        expect(provider.total, equals(0));
      });
    });

    group('loadThreads', () {
      test('sets isLoading to true during load', () async {
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async {
            // During load, isLoading should be true
            expect(provider.isLoading, isTrue);
            return PaginatedThreads(
              threads: [],
              total: 0,
              page: 1,
              pageSize: 25,
              hasMore: false,
            );
          },
        );

        await provider.loadThreads();
      });

      test('sets isInitialized to true after successful load', () async {
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [],
            total: 0,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );

        await provider.loadThreads();

        expect(provider.isInitialized, isTrue);
      });

      test('updates threads on successful load', () async {
        final mockThreads = [
          Thread(
            id: '1',
            projectId: null,
            title: 'Thread 1',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
          Thread(
            id: '2',
            projectId: 'project-1',
            projectName: 'Project',
            title: 'Thread 2',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
        ];

        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: mockThreads,
            total: 2,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );

        await provider.loadThreads();

        expect(provider.threads, equals(mockThreads));
        expect(provider.total, equals(2));
      });

      test('updates hasMore correctly', () async {
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [],
            total: 30,
            page: 1,
            pageSize: 25,
            hasMore: true,
          ),
        );

        await provider.loadThreads();

        expect(provider.hasMore, isTrue);
      });

      test('sets error on failure', () async {
        when(mockThreadService.getGlobalThreads(page: 1))
            .thenThrow(Exception('Network error'));

        await provider.loadThreads();

        expect(provider.error, isNotNull);
        expect(provider.error, contains('Network error'));
        expect(provider.hasMore, isFalse);
      });

      test('clears error on successful load', () async {
        // First load fails
        when(mockThreadService.getGlobalThreads(page: 1))
            .thenThrow(Exception('Network error'));
        await provider.loadThreads();
        expect(provider.error, isNotNull);

        // Second load succeeds
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [],
            total: 0,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );
        await provider.loadThreads();

        expect(provider.error, isNull);
      });

      test('prevents duplicate loads', () async {
        var callCount = 0;
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async {
            callCount++;
            await Future.delayed(const Duration(milliseconds: 100));
            return PaginatedThreads(
              threads: [],
              total: 0,
              page: 1,
              pageSize: 25,
              hasMore: false,
            );
          },
        );

        // Start two loads simultaneously
        provider.loadThreads();
        provider.loadThreads();

        await Future.delayed(const Duration(milliseconds: 200));

        expect(callCount, equals(1));
      });
    });

    group('loadMoreThreads', () {
      test('does not load if not initialized', () async {
        expect(provider.isInitialized, isFalse);

        await provider.loadMoreThreads();

        verifyNever(mockThreadService.getGlobalThreads(page: anyNamed('page')));
      });

      test('does not load if hasMore is false', () async {
        // Initialize first
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [],
            total: 0,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );
        await provider.loadThreads();

        await provider.loadMoreThreads();

        verify(mockThreadService.getGlobalThreads(page: 1)).called(1);
        verifyNever(mockThreadService.getGlobalThreads(page: 2));
      });

      test('loads next page when hasMore is true', () async {
        // Initialize with hasMore = true
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '1',
                title: 'Thread 1',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 30,
            page: 1,
            pageSize: 25,
            hasMore: true,
          ),
        );
        await provider.loadThreads();

        when(mockThreadService.getGlobalThreads(page: 2)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '2',
                title: 'Thread 2',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 30,
            page: 2,
            pageSize: 25,
            hasMore: false,
          ),
        );

        await provider.loadMoreThreads();

        verify(mockThreadService.getGlobalThreads(page: 2)).called(1);
        expect(provider.threads.length, equals(2));
        expect(provider.hasMore, isFalse);
      });

      test('appends threads to existing list', () async {
        // Initialize
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '1',
                title: 'Thread 1',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 2,
            page: 1,
            pageSize: 1,
            hasMore: true,
          ),
        );
        await provider.loadThreads();
        expect(provider.threads.length, equals(1));

        // Load more
        when(mockThreadService.getGlobalThreads(page: 2)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '2',
                title: 'Thread 2',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 2,
            page: 2,
            pageSize: 1,
            hasMore: false,
          ),
        );
        await provider.loadMoreThreads();

        expect(provider.threads.length, equals(2));
        expect(provider.threads[0].id, equals('1'));
        expect(provider.threads[1].id, equals('2'));
      });

      test('sets error on failure without clearing threads', () async {
        // Initialize successfully
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '1',
                title: 'Thread 1',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 30,
            page: 1,
            pageSize: 25,
            hasMore: true,
          ),
        );
        await provider.loadThreads();

        // Load more fails
        when(mockThreadService.getGlobalThreads(page: 2))
            .thenThrow(Exception('Network error'));
        await provider.loadMoreThreads();

        expect(provider.error, isNotNull);
        expect(provider.threads.length, equals(1)); // Threads preserved
        expect(provider.hasMore, isFalse); // Stop trying to load more
      });
    });

    group('createNewChat', () {
      test('creates thread and adds to beginning of list', () async {
        final newThread = Thread(
          id: 'new-1',
          projectId: null,
          title: null,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          modelProvider: 'anthropic',
        );

        when(mockThreadService.createGlobalThread(
          title: null,
          projectId: null,
          modelProvider: 'anthropic',
        )).thenAnswer((_) async => newThread);

        // Initialize first
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: 'existing-1',
                title: 'Existing',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 1,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );
        await provider.loadThreads();

        final result = await provider.createNewChat(modelProvider: 'anthropic');

        expect(result, equals(newThread));
        expect(provider.threads.first.id, equals('new-1'));
        expect(provider.total, equals(2));
      });

      test('passes model provider to service', () async {
        final newThread = Thread(
          id: 'new-1',
          projectId: null,
          title: null,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          modelProvider: 'google',
        );

        when(mockThreadService.createGlobalThread(
          title: null,
          projectId: null,
          modelProvider: 'google',
        )).thenAnswer((_) async => newThread);

        await provider.createNewChat(modelProvider: 'google');

        verify(mockThreadService.createGlobalThread(
          title: null,
          projectId: null,
          modelProvider: 'google',
        )).called(1);
      });

      test('returns null and sets error on failure', () async {
        when(mockThreadService.createGlobalThread(
          title: anyNamed('title'),
          projectId: anyNamed('projectId'),
          modelProvider: anyNamed('modelProvider'),
        )).thenThrow(Exception('Creation failed'));

        final result = await provider.createNewChat();

        expect(result, isNull);
        expect(provider.error, isNotNull);
      });
    });

    group('clearError', () {
      test('clears error state', () async {
        // Set error
        when(mockThreadService.getGlobalThreads(page: 1))
            .thenThrow(Exception('Error'));
        await provider.loadThreads();
        expect(provider.error, isNotNull);

        provider.clearError();

        expect(provider.error, isNull);
      });
    });

    // ==================== FPROV-06 Additional Tests ====================

    group('loadThreads edge cases (FPROV-06)', () {
      test('isLoading is false after successful load', () async {
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [],
            total: 0,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );

        await provider.loadThreads();

        expect(provider.isLoading, isFalse);
      });

      test('isLoading is false after failed load', () async {
        when(mockThreadService.getGlobalThreads(page: 1))
            .thenThrow(Exception('Network error'));

        await provider.loadThreads();

        expect(provider.isLoading, isFalse);
      });

      test('threads list is replaced (not appended) on reload', () async {
        // First load
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '1',
                title: 'Thread 1',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 1,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );
        await provider.loadThreads();
        expect(provider.threads.length, equals(1));
        expect(provider.threads.first.id, equals('1'));

        // Reload with different data
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '2',
                title: 'Thread 2',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
              Thread(
                id: '3',
                title: 'Thread 3',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 2,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );
        await provider.loadThreads();

        // Should be replaced, not appended (total 2, not 3)
        expect(provider.threads.length, equals(2));
        expect(provider.threads.first.id, equals('2'));
      });
    });

    group('loadMoreThreads edge cases (FPROV-06)', () {
      test('does not load while already loading', () async {
        var callCount = 0;

        // Initialize first
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '1',
                title: 'Thread 1',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 50,
            page: 1,
            pageSize: 25,
            hasMore: true,
          ),
        );
        await provider.loadThreads();

        // Slow loadMore
        when(mockThreadService.getGlobalThreads(page: 2)).thenAnswer(
          (_) async {
            callCount++;
            await Future.delayed(const Duration(milliseconds: 100));
            return PaginatedThreads(
              threads: [
                Thread(
                  id: '2',
                  title: 'Thread 2',
                  createdAt: DateTime.now(),
                  updatedAt: DateTime.now(),
                ),
              ],
              total: 50,
              page: 2,
              pageSize: 25,
              hasMore: true,
            );
          },
        );

        // Start two loadMore simultaneously
        provider.loadMoreThreads();
        provider.loadMoreThreads();

        await Future.delayed(const Duration(milliseconds: 200));

        expect(callCount, equals(1));
      });

      test('page number increments correctly on successive loads', () async {
        // Initialize
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '1',
                title: 'Thread 1',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 100,
            page: 1,
            pageSize: 25,
            hasMore: true,
          ),
        );
        await provider.loadThreads();

        // Page 2
        when(mockThreadService.getGlobalThreads(page: 2)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '2',
                title: 'Thread 2',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 100,
            page: 2,
            pageSize: 25,
            hasMore: true,
          ),
        );
        await provider.loadMoreThreads();

        // Page 3
        when(mockThreadService.getGlobalThreads(page: 3)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '3',
                title: 'Thread 3',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 100,
            page: 3,
            pageSize: 25,
            hasMore: false,
          ),
        );
        await provider.loadMoreThreads();

        verify(mockThreadService.getGlobalThreads(page: 1)).called(1);
        verify(mockThreadService.getGlobalThreads(page: 2)).called(1);
        verify(mockThreadService.getGlobalThreads(page: 3)).called(1);
        expect(provider.threads.length, equals(3));
      });
    });

    group('createNewChat edge cases (FPROV-06)', () {
      test('works even when not initialized (no threads loaded yet)', () async {
        expect(provider.isInitialized, isFalse);

        final newThread = Thread(
          id: 'new-1',
          title: 'New Chat',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        when(mockThreadService.createGlobalThread(
          title: anyNamed('title'),
          projectId: anyNamed('projectId'),
          modelProvider: anyNamed('modelProvider'),
        )).thenAnswer((_) async => newThread);

        final result = await provider.createNewChat();

        expect(result, equals(newThread));
        expect(provider.threads.length, equals(1));
        expect(provider.threads.first.id, equals('new-1'));
      });

      test('increments total even before first load', () async {
        expect(provider.total, equals(0));

        final newThread = Thread(
          id: 'new-1',
          title: 'New Chat',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        when(mockThreadService.createGlobalThread(
          title: anyNamed('title'),
          projectId: anyNamed('projectId'),
          modelProvider: anyNamed('modelProvider'),
        )).thenAnswer((_) async => newThread);

        await provider.createNewChat();

        expect(provider.total, equals(1));
      });
    });

    group('Listener notifications (FPROV-06)', () {
      test('notifies listeners on loadThreads start and complete', () async {
        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [],
            total: 0,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );

        await provider.loadThreads();

        // Should notify at least twice: loading start, loading complete
        expect(notifyCount, greaterThanOrEqualTo(2));
      });

      test('notifies listeners on loadMoreThreads', () async {
        // Initialize first
        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '1',
                title: 'Thread 1',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 50,
            page: 1,
            pageSize: 25,
            hasMore: true,
          ),
        );
        await provider.loadThreads();

        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        when(mockThreadService.getGlobalThreads(page: 2)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: [
              Thread(
                id: '2',
                title: 'Thread 2',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            total: 50,
            page: 2,
            pageSize: 25,
            hasMore: false,
          ),
        );

        await provider.loadMoreThreads();

        // Should notify at least twice: loading start, loading complete
        expect(notifyCount, greaterThanOrEqualTo(2));
      });

      test('notifies listeners on createNewChat success', () async {
        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        final newThread = Thread(
          id: 'new-1',
          title: 'New Chat',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        when(mockThreadService.createGlobalThread(
          title: anyNamed('title'),
          projectId: anyNamed('projectId'),
          modelProvider: anyNamed('modelProvider'),
        )).thenAnswer((_) async => newThread);

        await provider.createNewChat();

        // Should notify on success
        expect(notifyCount, greaterThanOrEqualTo(1));
      });

      test('notifies listeners on createNewChat failure', () async {
        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        when(mockThreadService.createGlobalThread(
          title: anyNamed('title'),
          projectId: anyNamed('projectId'),
          modelProvider: anyNamed('modelProvider'),
        )).thenThrow(Exception('Creation failed'));

        await provider.createNewChat();

        // Should notify on error
        expect(notifyCount, greaterThanOrEqualTo(1));
      });

      test('notifies listeners on clearError', () async {
        // Set error first
        when(mockThreadService.getGlobalThreads(page: 1))
            .thenThrow(Exception('Error'));
        await provider.loadThreads();

        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        provider.clearError();

        expect(notifyCount, equals(1));
      });
    });

    group('Thread with project association (FPROV-06)', () {
      test('handles threads with projectId and projectName correctly',
          () async {
        final threadsWithProjects = [
          Thread(
            id: '1',
            projectId: null,
            projectName: null,
            title: 'Standalone Chat',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
          Thread(
            id: '2',
            projectId: 'project-1',
            projectName: 'My Project',
            title: 'Project Chat',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
          Thread(
            id: '3',
            projectId: 'project-2',
            projectName: 'Another Project',
            title: 'Another Chat',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
          ),
        ];

        when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
          (_) async => PaginatedThreads(
            threads: threadsWithProjects,
            total: 3,
            page: 1,
            pageSize: 25,
            hasMore: false,
          ),
        );

        await provider.loadThreads();

        expect(provider.threads.length, equals(3));

        // Standalone thread
        expect(provider.threads[0].projectId, isNull);
        expect(provider.threads[0].projectName, isNull);

        // Project-associated threads
        expect(provider.threads[1].projectId, equals('project-1'));
        expect(provider.threads[1].projectName, equals('My Project'));
        expect(provider.threads[2].projectId, equals('project-2'));
        expect(provider.threads[2].projectName, equals('Another Project'));
      });
    });
  });
}
