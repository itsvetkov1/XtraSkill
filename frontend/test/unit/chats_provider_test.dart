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
  });
}
