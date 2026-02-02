/// Unit tests for ProjectService (FSVC-01 partial).
library;

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/project.dart';
import 'package:frontend/services/project_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'project_service_test.mocks.dart';

@GenerateNiceMocks([MockSpec<Dio>(), MockSpec<FlutterSecureStorage>()])
void main() {
  group('ProjectService Unit Tests', () {
    late MockDio mockDio;
    late MockFlutterSecureStorage mockStorage;
    late ProjectService service;

    const testBaseUrl = 'http://test.api';

    setUp(() {
      mockDio = MockDio();
      mockStorage = MockFlutterSecureStorage();
      service = ProjectService(
        dio: mockDio,
        storage: mockStorage,
        baseUrl: testBaseUrl,
      );
    });

    // Helper to create project JSON
    Map<String, dynamic> createProjectJson({
      required String id,
      required String name,
      String? description,
      DateTime? createdAt,
      DateTime? updatedAt,
    }) {
      final now = DateTime.now();
      return {
        'id': id,
        'name': name,
        'description': description,
        'created_at': (createdAt ?? now).toIso8601String(),
        'updated_at': (updatedAt ?? now).toIso8601String(),
      };
    }

    group('Constructor injection', () {
      test('accepts custom Dio instance', () {
        final customDio = Dio();
        final svc = ProjectService(dio: customDio);
        expect(svc, isNotNull);
      });

      test('accepts custom FlutterSecureStorage instance', () {
        final customStorage = const FlutterSecureStorage();
        final svc = ProjectService(storage: customStorage);
        expect(svc, isNotNull);
      });

      test('accepts custom baseUrl', () {
        final svc = ProjectService(baseUrl: 'http://custom.api');
        expect(svc, isNotNull);
      });

      test('uses defaults when no parameters provided', () {
        final svc = ProjectService();
        expect(svc, isNotNull);
      });
    });

    group('getProjects', () {
      test('throws exception when not authenticated', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.getProjects(),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Not authenticated'),
            ),
          ),
        );
      });

      test('makes GET request to /api/projects with Bearer token', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [],
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects'),
            ));

        await service.getProjects();

        final captured = verify(mockDio.get(
          captureAny,
          options: captureAnyNamed('options'),
        )).captured;
        expect(captured[0], equals('$testBaseUrl/api/projects'));
        final options = captured[1] as Options;
        expect(options.headers!['Authorization'], equals('Bearer test-token'));
        expect(options.headers!['Content-Type'], equals('application/json'));
      });

      test('returns empty list when no projects', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [],
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects'),
            ));

        final result = await service.getProjects();

        expect(result, isEmpty);
      });

      test('returns list of Project objects on success', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [
                createProjectJson(id: 'p1', name: 'Project 1'),
                createProjectJson(
                    id: 'p2', name: 'Project 2', description: 'Description'),
              ],
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects'),
            ));

        final result = await service.getProjects();

        expect(result.length, equals(2));
        expect(result[0], isA<Project>());
        expect(result[0].id, equals('p1'));
        expect(result[0].name, equals('Project 1'));
        expect(result[1].id, equals('p2'));
        expect(result[1].description, equals('Description'));
      });

      test('throws appropriate error on 401', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'expired-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects',
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 401,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.getProjects(),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Unauthorized'),
            ),
          ),
        );
      });

      test('throws generic error on other failures', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects',
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.connectionError,
          requestOptions: RequestOptions(path: ''),
          message: 'Network error',
        ));

        expect(
          () => service.getProjects(),
          throwsA(
            predicate(
              (e) =>
                  e is Exception && e.toString().contains('Failed to load projects'),
            ),
          ),
        );
      });
    });

    group('createProject', () {
      test('throws exception when not authenticated', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.createProject('Test', null),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Not authenticated'),
            ),
          ),
        );
      });

      test('makes POST request to /api/projects with name and description',
          () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.post(
          '$testBaseUrl/api/projects',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createProjectJson(
                id: 'new-id',
                name: 'Test Project',
                description: 'Test Description',
              ),
              statusCode: 201,
              requestOptions: RequestOptions(path: '/api/projects'),
            ));

        await service.createProject('Test Project', 'Test Description');

        final captured = verify(mockDio.post(
          captureAny,
          data: captureAnyNamed('data'),
          options: captureAnyNamed('options'),
        )).captured;
        expect(captured[0], equals('$testBaseUrl/api/projects'));
        expect(captured[1]['name'], equals('Test Project'));
        expect(captured[1]['description'], equals('Test Description'));
      });

      test('handles null description correctly', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.post(
          '$testBaseUrl/api/projects',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createProjectJson(id: 'new-id', name: 'Test Project'),
              statusCode: 201,
              requestOptions: RequestOptions(path: '/api/projects'),
            ));

        await service.createProject('Test Project', null);

        final captured = verify(mockDio.post(
          any,
          data: captureAnyNamed('data'),
          options: anyNamed('options'),
        )).captured;
        expect(captured.first['description'], isNull);
      });

      test('returns created Project object', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.post(
          '$testBaseUrl/api/projects',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createProjectJson(
                id: 'created-123',
                name: 'New Project',
                description: 'New Description',
              ),
              statusCode: 201,
              requestOptions: RequestOptions(path: '/api/projects'),
            ));

        final result = await service.createProject('New Project', 'New Description');

        expect(result, isA<Project>());
        expect(result.id, equals('created-123'));
        expect(result.name, equals('New Project'));
        expect(result.description, equals('New Description'));
      });

      test('throws appropriate error on 401', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'expired-token');
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 401,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.createProject('Test', null),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Unauthorized'),
            ),
          ),
        );
      });

      test('throws validation error on 422', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 422,
            data: {'detail': 'Name is required'},
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.createProject('', null),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Validation error'),
            ),
          ),
        );
      });
    });

    group('getProject', () {
      test('throws exception when not authenticated', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.getProject('project-id'),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Not authenticated'),
            ),
          ),
        );
      });

      test('makes GET request to /api/projects/{id}', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects/proj-123',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createProjectJson(id: 'proj-123', name: 'Test Project'),
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects/proj-123'),
            ));

        await service.getProject('proj-123');

        verify(mockDio.get(
          '$testBaseUrl/api/projects/proj-123',
          options: anyNamed('options'),
        )).called(1);
      });

      test('returns Project object with details', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects/proj-123',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                ...createProjectJson(
                  id: 'proj-123',
                  name: 'Test Project',
                  description: 'Description',
                ),
                'documents': [
                  {'id': 'doc1', 'name': 'doc1.pdf'}
                ],
                'threads': [
                  {'id': 'thread1', 'title': 'Thread 1'}
                ],
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects/proj-123'),
            ));

        final result = await service.getProject('proj-123');

        expect(result, isA<Project>());
        expect(result.id, equals('proj-123'));
        expect(result.name, equals('Test Project'));
        expect(result.description, equals('Description'));
        expect(result.documents, isNotNull);
        expect(result.threads, isNotNull);
      });

      test('throws not found error on 404', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/api/projects/nonexistent',
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 404,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.getProject('nonexistent'),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  (e.toString().contains('not found') ||
                      e.toString().contains('404')),
            ),
          ),
        );
      });

      test('throws appropriate error on 401', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'expired-token');
        when(mockDio.get(any, options: anyNamed('options'))).thenThrow(
          DioException(
            type: DioExceptionType.badResponse,
            response: Response(
              statusCode: 401,
              requestOptions: RequestOptions(path: ''),
            ),
            requestOptions: RequestOptions(path: ''),
          ),
        );

        expect(
          () => service.getProject('project-id'),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Unauthorized'),
            ),
          ),
        );
      });
    });

    group('updateProject', () {
      test('throws exception when not authenticated', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.updateProject('id', 'name', null),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Not authenticated'),
            ),
          ),
        );
      });

      test('makes PUT request to /api/projects/{id} with name and description',
          () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.put(
          '$testBaseUrl/api/projects/proj-123',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createProjectJson(
                id: 'proj-123',
                name: 'Updated Name',
                description: 'Updated Description',
              ),
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects/proj-123'),
            ));

        await service.updateProject('proj-123', 'Updated Name', 'Updated Description');

        final captured = verify(mockDio.put(
          captureAny,
          data: captureAnyNamed('data'),
          options: captureAnyNamed('options'),
        )).captured;
        expect(captured[0], equals('$testBaseUrl/api/projects/proj-123'));
        expect(captured[1]['name'], equals('Updated Name'));
        expect(captured[1]['description'], equals('Updated Description'));
      });

      test('handles null description correctly', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.put(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createProjectJson(id: 'proj-123', name: 'Updated Name'),
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects/proj-123'),
            ));

        await service.updateProject('proj-123', 'Updated Name', null);

        final captured = verify(mockDio.put(
          any,
          data: captureAnyNamed('data'),
          options: anyNamed('options'),
        )).captured;
        expect(captured.first['description'], isNull);
      });

      test('returns updated Project object', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.put(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: createProjectJson(
                id: 'proj-123',
                name: 'New Name',
                description: 'New Description',
              ),
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects/proj-123'),
            ));

        final result =
            await service.updateProject('proj-123', 'New Name', 'New Description');

        expect(result, isA<Project>());
        expect(result.id, equals('proj-123'));
        expect(result.name, equals('New Name'));
        expect(result.description, equals('New Description'));
      });

      test('throws not found error on 404', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.put(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 404,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.updateProject('nonexistent', 'Name', null),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  (e.toString().contains('not found') ||
                      e.toString().contains('404')),
            ),
          ),
        );
      });

      test('throws validation error on 422', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.put(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 422,
            data: {'detail': 'Name too long'},
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.updateProject('proj-123', 'a' * 500, null),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Validation error'),
            ),
          ),
        );
      });
    });

    group('deleteProject', () {
      test('throws exception when not authenticated', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.deleteProject('project-id'),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Not authenticated'),
            ),
          ),
        );
      });

      test('makes DELETE request to /api/projects/{id}', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.delete(
          '$testBaseUrl/api/projects/proj-123',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: null,
              statusCode: 204,
              requestOptions: RequestOptions(path: '/api/projects/proj-123'),
            ));

        await service.deleteProject('proj-123');

        verify(mockDio.delete(
          '$testBaseUrl/api/projects/proj-123',
          options: anyNamed('options'),
        )).called(1);
      });

      test('completes successfully with 200 response', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.delete(
          '$testBaseUrl/api/projects/proj-123',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: null,
              statusCode: 200,
              requestOptions: RequestOptions(path: '/api/projects/proj-123'),
            ));

        // Should complete without throwing
        await service.deleteProject('proj-123');
      });

      test('throws not found error on 404', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.delete(
          any,
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 404,
            requestOptions: RequestOptions(path: ''),
          ),
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.deleteProject('nonexistent'),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  (e.toString().contains('not found') ||
                      e.toString().contains('404')),
            ),
          ),
        );
      });

      test('throws appropriate error on 401', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'expired-token');
        when(mockDio.delete(any, options: anyNamed('options'))).thenThrow(
          DioException(
            type: DioExceptionType.badResponse,
            response: Response(
              statusCode: 401,
              requestOptions: RequestOptions(path: ''),
            ),
            requestOptions: RequestOptions(path: ''),
          ),
        );

        expect(
          () => service.deleteProject('project-id'),
          throwsA(
            predicate(
              (e) => e is Exception && e.toString().contains('Unauthorized'),
            ),
          ),
        );
      });

      test('throws generic error on other failures', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.delete(any, options: anyNamed('options'))).thenThrow(
          DioException(
            type: DioExceptionType.connectionError,
            requestOptions: RequestOptions(path: ''),
            message: 'Network error',
          ),
        );

        expect(
          () => service.deleteProject('project-id'),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  e.toString().contains('Failed to delete project'),
            ),
          ),
        );
      });
    });
  });
}
