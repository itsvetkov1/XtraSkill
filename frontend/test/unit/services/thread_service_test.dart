/// Unit tests for ThreadService (Phase 31).
library;

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/services/thread_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'thread_service_test.mocks.dart';

@GenerateNiceMocks([MockSpec<Dio>(), MockSpec<FlutterSecureStorage>()])
void main() {
  group('ThreadService Unit Tests', () {
    late MockDio mockDio;
    late MockFlutterSecureStorage mockStorage;
    late ThreadService service;

    const testBaseUrl = 'http://test.api';
    const testToken = 'test-jwt-token';

    setUp(() {
      mockDio = MockDio();
      mockStorage = MockFlutterSecureStorage();
      service = ThreadService(
        baseUrl: testBaseUrl,
        dio: mockDio,
        storage: mockStorage,
      );
    });

    // Helper to setup standard auth mock
    void setupAuth() {
      when(mockStorage.read(key: 'auth_token'))
          .thenAnswer((_) async => testToken);
    }

    // Helper to create standard thread JSON
    Map<String, dynamic> createThreadJson({
      String id = 'thread-1',
      String? projectId,
      String? projectName,
      String? title,
      String createdAt = '2024-01-01T00:00:00Z',
      String updatedAt = '2024-01-01T00:00:00Z',
      int? messageCount,
      String? modelProvider,
    }) {
      return {
        'id': id,
        if (projectId != null) 'project_id': projectId,
        if (projectName != null) 'project_name': projectName,
        'title': title,
        'created_at': createdAt,
        'updated_at': updatedAt,
        if (messageCount != null) 'message_count': messageCount,
        if (modelProvider != null) 'model_provider': modelProvider,
      };
    }

    group('Constructor', () {
      test('accepts optional Dio, storage, and baseUrl', () {
        // Default construction should not throw
        expect(() => ThreadService(), returnsNormally);
      });

      test('uses provided dependencies', () {
        final customDio = Dio();
        final customStorage = const FlutterSecureStorage();
        final customService = ThreadService(
          dio: customDio,
          storage: customStorage,
          baseUrl: 'http://custom.api',
        );
        expect(customService, isNotNull);
      });
    });

    group('getThreads', () {
      test('makes GET request to /projects/{projectId}/threads', () async {
        setupAuth();
        when(mockDio.get(
          '$testBaseUrl/api/projects/proj-1/threads',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.getThreads('proj-1');

        verify(mockDio.get(
          '$testBaseUrl/api/projects/proj-1/threads',
          options: anyNamed('options'),
        )).called(1);
      });

      test('returns list of Thread objects', () async {
        setupAuth();
        when(mockDio.get(
          '$testBaseUrl/api/projects/proj-1/threads',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [
                createThreadJson(id: 't1', title: 'Thread 1'),
                createThreadJson(id: 't2', title: 'Thread 2'),
              ],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final threads = await service.getThreads('proj-1');

        expect(threads.length, equals(2));
        expect(threads[0].id, equals('t1'));
        expect(threads[0].title, equals('Thread 1'));
        expect(threads[1].id, equals('t2'));
      });

      test('includes auth token in request', () async {
        setupAuth();
        Options? capturedOptions;
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenAnswer((invocation) async {
          capturedOptions = invocation.namedArguments[#options] as Options?;
          return Response(
            data: [],
            statusCode: 200,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.getThreads('proj-1');

        expect(capturedOptions?.headers?['Authorization'],
            equals('Bearer $testToken'));
      });

      test('throws on missing auth token', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.getThreads('proj-1'),
          throwsA(predicate((e) => e is Exception)),
        );
      });

      test('throws on 401 Unauthorized', () async {
        setupAuth();
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 401,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.getThreads('proj-1'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Authentication'))),
        );
      });

      test('throws on 404 Project not found', () async {
        setupAuth();
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 404,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.getThreads('nonexistent'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Project not found'))),
        );
      });
    });

    group('createThread', () {
      test('makes POST request to /projects/{projectId}/threads', () async {
        setupAuth();
        when(mockDio.post(
          '$testBaseUrl/api/projects/proj-1/threads',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(id: 'new-thread'),
              statusCode: 201,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.createThread('proj-1', 'New Thread');

        verify(mockDio.post(
          '$testBaseUrl/api/projects/proj-1/threads',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).called(1);
      });

      test('sends title in body when provided', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'new-thread'),
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.createThread('proj-1', 'My Thread Title');

        expect(capturedData?['title'], equals('My Thread Title'));
      });

      test('does not send title when null', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'new-thread'),
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.createThread('proj-1', null);

        expect(capturedData?.containsKey('title'), isFalse);
      });

      test('does not send title when empty', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'new-thread'),
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.createThread('proj-1', '');

        expect(capturedData?.containsKey('title'), isFalse);
      });

      test('sends model_provider when provided', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'new-thread', modelProvider: 'openai'),
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.createThread('proj-1', 'Thread', provider: 'openai');

        expect(capturedData?['model_provider'], equals('openai'));
      });

      test('returns created Thread object', () async {
        setupAuth();
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(
                id: 'created-thread',
                title: 'Created Thread',
                projectId: 'proj-1',
              ),
              statusCode: 201,
              requestOptions: RequestOptions(path: ''),
            ));

        final thread = await service.createThread('proj-1', 'Created Thread');

        expect(thread.id, equals('created-thread'));
        expect(thread.title, equals('Created Thread'));
      });

      test('throws on 400 invalid data', () async {
        setupAuth();
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 400,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.createThread('proj-1', 'Thread'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Invalid thread data'))),
        );
      });
    });

    group('getThread', () {
      test('makes GET request to /threads/{threadId}', () async {
        setupAuth();
        when(mockDio.get(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(id: 'thread-1'),
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.getThread('thread-1');

        verify(mockDio.get(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
        )).called(1);
      });

      test('returns Thread object with messages array', () async {
        setupAuth();
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'id': 'thread-1',
                'title': 'Test Thread',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z',
                'messages': [
                  {
                    'id': 'msg-1',
                    'role': 'user',
                    'content': 'Hello',
                    'created_at': '2024-01-01T00:00:00Z',
                  },
                  {
                    'id': 'msg-2',
                    'role': 'assistant',
                    'content': 'Hi there!',
                    'created_at': '2024-01-01T00:00:01Z',
                  },
                ],
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final thread = await service.getThread('thread-1');

        expect(thread.id, equals('thread-1'));
        expect(thread.title, equals('Test Thread'));
        expect(thread.messages, isNotNull);
        expect(thread.messages!.length, equals(2));
        expect(thread.messages![0].content, equals('Hello'));
      });

      test('throws on 404 Thread not found', () async {
        setupAuth();
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 404,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.getThread('nonexistent'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Thread not found'))),
        );
      });
    });

    group('deleteThread', () {
      test('makes DELETE request to /threads/{id}', () async {
        setupAuth();
        when(mockDio.delete(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              statusCode: 204,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.deleteThread('thread-1');

        verify(mockDio.delete(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
        )).called(1);
      });

      test('completes successfully on 204 response', () async {
        setupAuth();
        when(mockDio.delete(
          any,
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              statusCode: 204,
              requestOptions: RequestOptions(path: ''),
            ));

        await expectLater(service.deleteThread('thread-1'), completes);
      });

      test('throws on 401 Unauthorized', () async {
        setupAuth();
        when(mockDio.delete(
          any,
          options: anyNamed('options'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 401,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.deleteThread('thread-1'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Unauthorized'))),
        );
      });

      test('throws on 404 Not Found', () async {
        setupAuth();
        when(mockDio.delete(
          any,
          options: anyNamed('options'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 404,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.deleteThread('nonexistent'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Thread not found'))),
        );
      });
    });

    group('renameThread', () {
      test('makes PATCH request to /threads/{threadId}', () async {
        setupAuth();
        when(mockDio.patch(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(id: 'thread-1', title: 'New Title'),
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.renameThread('thread-1', 'New Title');

        verify(mockDio.patch(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).called(1);
      });

      test('sends title in body', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.patch(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'thread-1', title: 'Renamed'),
            statusCode: 200,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.renameThread('thread-1', 'Renamed Thread');

        expect(capturedData?['title'], equals('Renamed Thread'));
      });

      test('can clear title with null', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.patch(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'thread-1'),
            statusCode: 200,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.renameThread('thread-1', null);

        expect(capturedData?['title'], isNull);
      });

      test('returns updated Thread object', () async {
        setupAuth();
        when(mockDio.patch(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(
                id: 'thread-1',
                title: 'Updated Title',
              ),
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final thread = await service.renameThread('thread-1', 'Updated Title');

        expect(thread.id, equals('thread-1'));
        expect(thread.title, equals('Updated Title'));
      });
    });

    group('getGlobalThreads', () {
      test('makes GET request to /threads with pagination', () async {
        setupAuth();
        when(mockDio.get(
          '$testBaseUrl/api/threads?page=1&page_size=25',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'threads': [],
                'total': 0,
                'page': 1,
                'page_size': 25,
                'has_more': false,
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.getGlobalThreads();

        verify(mockDio.get(
          '$testBaseUrl/api/threads?page=1&page_size=25',
          options: anyNamed('options'),
        )).called(1);
      });

      test('uses provided page and pageSize parameters', () async {
        setupAuth();
        when(mockDio.get(
          '$testBaseUrl/api/threads?page=3&page_size=50',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'threads': [],
                'total': 100,
                'page': 3,
                'page_size': 50,
                'has_more': true,
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.getGlobalThreads(page: 3, pageSize: 50);

        verify(mockDio.get(
          '$testBaseUrl/api/threads?page=3&page_size=50',
          options: anyNamed('options'),
        )).called(1);
      });

      test('returns PaginatedThreads object', () async {
        setupAuth();
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'threads': [
                  createThreadJson(id: 't1', title: 'Thread 1'),
                  createThreadJson(id: 't2', title: 'Thread 2'),
                ],
                'total': 25,
                'page': 1,
                'page_size': 25,
                'has_more': false,
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final result = await service.getGlobalThreads(page: 1);

        expect(result.threads.length, equals(2));
        expect(result.total, equals(25));
        expect(result.page, equals(1));
        expect(result.pageSize, equals(25));
        expect(result.hasMore, isFalse);
      });

      test('parses threads with project information', () async {
        setupAuth();
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'threads': [
                  createThreadJson(
                    id: 't1',
                    title: 'Project Thread',
                    projectId: 'proj-1',
                    projectName: 'My Project',
                  ),
                  createThreadJson(
                    id: 't2',
                    title: 'Standalone Thread',
                  ),
                ],
                'total': 2,
                'page': 1,
                'page_size': 25,
                'has_more': false,
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final result = await service.getGlobalThreads();

        expect(result.threads[0].projectId, equals('proj-1'));
        expect(result.threads[0].projectName, equals('My Project'));
        expect(result.threads[0].hasProject, isTrue);
        expect(result.threads[1].projectId, isNull);
        expect(result.threads[1].hasProject, isFalse);
      });

      test('hasMore indicates more pages available', () async {
        setupAuth();
        when(mockDio.get(
          any,
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'threads': List.generate(
                  25,
                  (i) => createThreadJson(id: 't$i'),
                ),
                'total': 100,
                'page': 1,
                'page_size': 25,
                'has_more': true,
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final result = await service.getGlobalThreads();

        expect(result.hasMore, isTrue);
        expect(result.total, equals(100));
      });
    });

    group('createGlobalThread', () {
      test('makes POST request to /threads', () async {
        setupAuth();
        when(mockDio.post(
          '$testBaseUrl/api/threads',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(id: 'new-thread'),
              statusCode: 201,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.createGlobalThread();

        verify(mockDio.post(
          '$testBaseUrl/api/threads',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).called(1);
      });

      test('sends optional parameters when provided', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'new-thread'),
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.createGlobalThread(
          title: 'New Thread',
          projectId: 'proj-1',
          modelProvider: 'anthropic',
        );

        expect(capturedData?['title'], equals('New Thread'));
        expect(capturedData?['project_id'], equals('proj-1'));
        expect(capturedData?['model_provider'], equals('anthropic'));
      });

      test('creates thread without project (projectId null)', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'standalone'),
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.createGlobalThread(title: 'Standalone');

        expect(capturedData?.containsKey('project_id'), isFalse);
        expect(capturedData?['title'], equals('Standalone'));
      });

      test('returns created Thread object', () async {
        setupAuth();
        when(mockDio.post(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(
                id: 'created',
                title: 'Created Thread',
                modelProvider: 'anthropic',
              ),
              statusCode: 201,
              requestOptions: RequestOptions(path: ''),
            ));

        final thread = await service.createGlobalThread(title: 'Created Thread');

        expect(thread.id, equals('created'));
        expect(thread.title, equals('Created Thread'));
      });
    });

    group('associateWithProject', () {
      test('makes PATCH request to /threads/{threadId}', () async {
        setupAuth();
        when(mockDio.patch(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(id: 'thread-1', projectId: 'proj-1'),
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.associateWithProject('thread-1', 'proj-1');

        verify(mockDio.patch(
          '$testBaseUrl/api/threads/thread-1',
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).called(1);
      });

      test('sends project_id in body', () async {
        setupAuth();
        Map<String, dynamic>? capturedData;
        when(mockDio.patch(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((invocation) async {
          capturedData =
              invocation.namedArguments[#data] as Map<String, dynamic>?;
          return Response(
            data: createThreadJson(id: 'thread-1', projectId: 'proj-1'),
            statusCode: 200,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.associateWithProject('thread-1', 'proj-1');

        expect(capturedData?['project_id'], equals('proj-1'));
      });

      test('returns updated Thread with project', () async {
        setupAuth();
        when(mockDio.patch(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
              data: createThreadJson(
                id: 'thread-1',
                projectId: 'proj-1',
                projectName: 'My Project',
              ),
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final thread =
            await service.associateWithProject('thread-1', 'proj-1');

        expect(thread.id, equals('thread-1'));
        expect(thread.projectId, equals('proj-1'));
        expect(thread.hasProject, isTrue);
      });

      test('throws on 400 when thread already associated', () async {
        setupAuth();
        when(mockDio.patch(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 400,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.associateWithProject('thread-1', 'proj-1'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('already associated'))),
        );
      });

      test('throws on 404 when thread or project not found', () async {
        setupAuth();
        when(mockDio.patch(
          any,
          options: anyNamed('options'),
          data: anyNamed('data'),
        )).thenThrow(DioException(
          response: Response(
            statusCode: 404,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.associateWithProject('thread-1', 'nonexistent'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('not found'))),
        );
      });
    });

    group('PaginatedThreads', () {
      test('fromJson parses all fields', () {
        final json = {
          'threads': [
            createThreadJson(id: 't1'),
            createThreadJson(id: 't2'),
          ],
          'total': 100,
          'page': 2,
          'page_size': 25,
          'has_more': true,
        };

        final result = PaginatedThreads.fromJson(json);

        expect(result.threads.length, equals(2));
        expect(result.total, equals(100));
        expect(result.page, equals(2));
        expect(result.pageSize, equals(25));
        expect(result.hasMore, isTrue);
      });

      test('fromJson handles empty threads list', () {
        final json = {
          'threads': [],
          'total': 0,
          'page': 1,
          'page_size': 25,
          'has_more': false,
        };

        final result = PaginatedThreads.fromJson(json);

        expect(result.threads, isEmpty);
        expect(result.total, equals(0));
        expect(result.hasMore, isFalse);
      });
    });
  });
}
