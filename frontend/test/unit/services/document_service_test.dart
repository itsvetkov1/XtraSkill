/// Unit tests for DocumentService (Phase 31).
library;

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/document.dart';
import 'package:frontend/services/document_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'document_service_test.mocks.dart';

@GenerateNiceMocks([MockSpec<Dio>(), MockSpec<FlutterSecureStorage>()])
void main() {
  group('DocumentService Unit Tests', () {
    late MockDio mockDio;
    late MockFlutterSecureStorage mockStorage;
    late DocumentService service;

    const testToken = 'test-jwt-token';

    setUp(() {
      mockDio = MockDio();
      mockStorage = MockFlutterSecureStorage();
      service = DocumentService(
        dio: mockDio,
        storage: mockStorage,
      );
    });

    // Helper to setup standard auth mock
    void setupAuth() {
      when(mockStorage.read(key: 'auth_token'))
          .thenAnswer((_) async => testToken);
    }

    group('Constructor', () {
      test('accepts optional Dio, storage, and baseUrl', () {
        // Default construction should not throw
        expect(() => DocumentService(), returnsNormally);
      });

      test('uses provided dependencies', () {
        final customDio = Dio();
        final customStorage = const FlutterSecureStorage();
        final customService = DocumentService(
          dio: customDio,
          storage: customStorage,
        );
        expect(customService, isNotNull);
      });
    });

    group('getDocuments', () {
      test('makes GET request to /projects/{projectId}/documents', () async {
        setupAuth();
        when(mockDio.get(
          '/api/projects/proj-1/documents',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.getDocuments('proj-1');

        verify(mockDio.get(
          '/api/projects/proj-1/documents',
          options: anyNamed('options'),
        )).called(1);
      });

      test('returns list of Document objects', () async {
        setupAuth();
        when(mockDio.get(
          '/api/projects/proj-1/documents',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [
                {
                  'id': 'doc-1',
                  'filename': 'test1.txt',
                  'created_at': '2024-01-01T00:00:00Z',
                },
                {
                  'id': 'doc-2',
                  'filename': 'test2.txt',
                  'created_at': '2024-01-02T00:00:00Z',
                },
              ],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final documents = await service.getDocuments('proj-1');

        expect(documents.length, equals(2));
        expect(documents[0].id, equals('doc-1'));
        expect(documents[0].filename, equals('test1.txt'));
        expect(documents[1].id, equals('doc-2'));
      });

      test('handles empty list', () async {
        setupAuth();
        when(mockDio.get(
          '/api/projects/proj-1/documents',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final documents = await service.getDocuments('proj-1');

        expect(documents, isEmpty);
      });
    });

    group('uploadDocument', () {
      test('makes POST request with FormData', () async {
        setupAuth();
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((_) async => Response(
              data: {
                'id': 'doc-1',
                'filename': 'test.txt',
                'created_at': DateTime.now().toIso8601String(),
              },
              statusCode: 201,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.uploadDocument('proj-1', [1, 2, 3], 'test.txt');

        verify(mockDio.post(
          '/api/projects/proj-1/documents',
          data: anyNamed('data'),
          options: anyNamed('options'),
          onSendProgress: anyNamed('onSendProgress'),
        )).called(1);
      });

      test('includes auth token in request', () async {
        setupAuth();
        Options? capturedOptions;
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((invocation) async {
          capturedOptions = invocation.namedArguments[#options] as Options?;
          return Response(
            data: {
              'id': 'doc-1',
              'filename': 'test.txt',
              'created_at': DateTime.now().toIso8601String(),
            },
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.uploadDocument('proj-1', [1, 2, 3], 'test.txt');

        expect(capturedOptions?.headers?['Authorization'],
            equals('Bearer $testToken'));
      });

      test('creates FormData with file bytes and filename', () async {
        setupAuth();
        dynamic capturedData;
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((invocation) async {
          capturedData = invocation.namedArguments[#data];
          return Response(
            data: {
              'id': 'doc-1',
              'filename': 'test.txt',
              'created_at': DateTime.now().toIso8601String(),
            },
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.uploadDocument('proj-1', [1, 2, 3], 'test.txt');

        expect(capturedData, isA<FormData>());
        final formData = capturedData as FormData;
        expect(formData.files.length, equals(1));
        expect(formData.files.first.value.filename, equals('test.txt'));
      });

      test('invokes onSendProgress callback during upload', () async {
        setupAuth();
        ProgressCallback? capturedProgress;
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((invocation) async {
          capturedProgress =
              invocation.namedArguments[#onSendProgress] as ProgressCallback?;
          // Simulate progress updates
          capturedProgress?.call(50, 100);
          capturedProgress?.call(100, 100);
          return Response(
            data: {
              'id': 'doc-1',
              'filename': 'test.txt',
              'created_at': DateTime.now().toIso8601String(),
            },
            statusCode: 201,
            requestOptions: RequestOptions(path: ''),
          );
        });

        var progressValues = <double>[];
        await service.uploadDocument(
          'proj-1',
          [1, 2, 3],
          'test.txt',
          onSendProgress: (sent, total) => progressValues.add(sent / total),
        );

        expect(progressValues, contains(0.5));
        expect(progressValues, contains(1.0));
      });

      test('returns created Document object', () async {
        setupAuth();
        final createdAt = DateTime.now();
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((_) async => Response(
              data: {
                'id': 'new-doc',
                'filename': 'uploaded.txt',
                'created_at': createdAt.toIso8601String(),
              },
              statusCode: 201,
              requestOptions: RequestOptions(path: ''),
            ));

        final document =
            await service.uploadDocument('proj-1', [1, 2, 3], 'uploaded.txt');

        expect(document.id, equals('new-doc'));
        expect(document.filename, equals('uploaded.txt'));
      });

      test('works without onSendProgress callback', () async {
        setupAuth();
        when(mockDio.post(
          any,
          data: anyNamed('data'),
          options: anyNamed('options'),
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((_) async => Response(
              data: {
                'id': 'doc-1',
                'filename': 'test.txt',
                'created_at': DateTime.now().toIso8601String(),
              },
              statusCode: 201,
              requestOptions: RequestOptions(path: ''),
            ));

        // Should not throw when no callback provided
        final document =
            await service.uploadDocument('proj-1', [1, 2, 3], 'test.txt');

        expect(document, isNotNull);
      });
    });

    group('getDocumentContent', () {
      test('makes GET request to /documents/{id}', () async {
        setupAuth();
        when(mockDio.get(
          '/api/documents/doc-1',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'id': 'doc-1',
                'filename': 'test.txt',
                'created_at': '2024-01-01T00:00:00Z',
                'content': 'File content here',
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.getDocumentContent('doc-1');

        verify(mockDio.get(
          '/api/documents/doc-1',
          options: anyNamed('options'),
        )).called(1);
      });

      test('returns Document with content field populated', () async {
        setupAuth();
        when(mockDio.get(
          '/api/documents/doc-1',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'id': 'doc-1',
                'filename': 'test.txt',
                'created_at': '2024-01-01T00:00:00Z',
                'content': 'Detailed file content',
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final document = await service.getDocumentContent('doc-1');

        expect(document.id, equals('doc-1'));
        expect(document.filename, equals('test.txt'));
        expect(document.content, equals('Detailed file content'));
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
            data: {
              'id': 'doc-1',
              'filename': 'test.txt',
              'created_at': '2024-01-01T00:00:00Z',
            },
            statusCode: 200,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.getDocumentContent('doc-1');

        expect(capturedOptions?.headers?['Authorization'],
            equals('Bearer $testToken'));
      });
    });

    group('searchDocuments', () {
      test('makes GET request to /projects/{projectId}/documents/search',
          () async {
        setupAuth();
        when(mockDio.get(
          '/api/projects/proj-1/documents/search',
          queryParameters: anyNamed('queryParameters'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.searchDocuments('proj-1', 'test query');

        verify(mockDio.get(
          '/api/projects/proj-1/documents/search',
          queryParameters: {'q': 'test query'},
          options: anyNamed('options'),
        )).called(1);
      });

      test('returns list of DocumentSearchResult objects', () async {
        setupAuth();
        when(mockDio.get(
          '/api/projects/proj-1/documents/search',
          queryParameters: anyNamed('queryParameters'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [
                {
                  'id': 'doc-1',
                  'filename': 'test1.txt',
                  'snippet': 'matching content here',
                  'score': 0.95,
                },
                {
                  'id': 'doc-2',
                  'filename': 'test2.txt',
                  'snippet': 'another match',
                  'score': 0.85,
                },
              ],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final results = await service.searchDocuments('proj-1', 'test');

        expect(results.length, equals(2));
        expect(results[0].id, equals('doc-1'));
        expect(results[0].filename, equals('test1.txt'));
        expect(results[0].snippet, equals('matching content here'));
        expect(results[0].score, equals(0.95));
      });

      test('handles empty results', () async {
        setupAuth();
        when(mockDio.get(
          '/api/projects/proj-1/documents/search',
          queryParameters: anyNamed('queryParameters'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: [],
              statusCode: 200,
              requestOptions: RequestOptions(path: ''),
            ));

        final results = await service.searchDocuments('proj-1', 'nonexistent');

        expect(results, isEmpty);
      });
    });

    group('deleteDocument', () {
      test('makes DELETE request to /documents/{id}', () async {
        setupAuth();
        when(mockDio.delete(
          '/api/documents/doc-1',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              statusCode: 204,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.deleteDocument('doc-1');

        verify(mockDio.delete(
          '/api/documents/doc-1',
          options: anyNamed('options'),
        )).called(1);
      });

      test('includes auth token in request', () async {
        setupAuth();
        Options? capturedOptions;
        when(mockDio.delete(
          any,
          options: anyNamed('options'),
        )).thenAnswer((invocation) async {
          capturedOptions = invocation.namedArguments[#options] as Options?;
          return Response(
            statusCode: 204,
            requestOptions: RequestOptions(path: ''),
          );
        });

        await service.deleteDocument('doc-1');

        expect(capturedOptions?.headers?['Authorization'],
            equals('Bearer $testToken'));
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

        // Should not throw
        await expectLater(
            service.deleteDocument('doc-1'), completes);
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
          () => service.deleteDocument('doc-1'),
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
          () => service.deleteDocument('nonexistent'),
          throwsA(predicate(
              (e) => e is Exception && e.toString().contains('not found'))),
        );
      });

      test('throws generic error on other failures', () async {
        setupAuth();
        when(mockDio.delete(
          any,
          options: anyNamed('options'),
        )).thenThrow(DioException(
          message: 'Network error',
          requestOptions: RequestOptions(path: ''),
        ));

        expect(
          () => service.deleteDocument('doc-1'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Failed to delete'))),
        );
      });
    });

    group('DocumentSearchResult', () {
      test('fromJson parses correctly', () {
        final json = {
          'id': 'doc-1',
          'filename': 'test.txt',
          'snippet': 'matching text',
          'score': 0.95,
        };

        final result = DocumentSearchResult.fromJson(json);

        expect(result.id, equals('doc-1'));
        expect(result.filename, equals('test.txt'));
        expect(result.snippet, equals('matching text'));
        expect(result.score, equals(0.95));
      });

      test('fromJson handles integer score', () {
        final json = {
          'id': 'doc-1',
          'filename': 'test.txt',
          'snippet': 'text',
          'score': 1, // Integer instead of double
        };

        final result = DocumentSearchResult.fromJson(json);

        expect(result.score, equals(1.0));
      });
    });
  });
}
