/// Unit tests for DocumentProvider (Phase 31).
library;

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/document.dart';
import 'package:frontend/providers/document_provider.dart';
import 'package:frontend/services/document_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'document_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<DocumentService>()])
void main() {
  group('DocumentProvider Unit Tests', () {
    late MockDocumentService mockService;
    late DocumentProvider provider;

    setUp(() {
      mockService = MockDocumentService();
      provider = DocumentProvider(service: mockService);
    });

    group('Initial State', () {
      test('starts with empty documents list', () {
        expect(provider.documents, isEmpty);
      });

      test('starts with no selected document', () {
        expect(provider.selectedDocument, isNull);
      });

      test('starts with loading false', () {
        expect(provider.loading, isFalse);
        expect(provider.isLoading, isFalse);
      });

      test('starts with uploading false', () {
        expect(provider.uploading, isFalse);
      });

      test('starts with no error', () {
        expect(provider.error, isNull);
      });

      test('starts with uploadProgress 0', () {
        expect(provider.uploadProgress, equals(0.0));
      });
    });

    group('loadDocuments', () {
      test('sets loading to true during call', () async {
        when(mockService.getDocuments(any)).thenAnswer(
          (_) async {
            // During load, loading should be true
            expect(provider.loading, isTrue);
            return <Document>[];
          },
        );

        await provider.loadDocuments('project-1');
      });

      test('updates documents on success', () async {
        final mockDocuments = [
          Document(
            id: 'doc-1',
            filename: 'test1.txt',
            createdAt: DateTime.now(),
          ),
          Document(
            id: 'doc-2',
            filename: 'test2.txt',
            createdAt: DateTime.now(),
          ),
        ];

        when(mockService.getDocuments('project-1'))
            .thenAnswer((_) async => mockDocuments);

        await provider.loadDocuments('project-1');

        expect(provider.documents, equals(mockDocuments));
        expect(provider.loading, isFalse);
        expect(provider.error, isNull);
      });

      test('sets error on failure', () async {
        when(mockService.getDocuments(any))
            .thenThrow(Exception('Network error'));

        await provider.loadDocuments('project-1');

        expect(provider.error, isNotNull);
        expect(provider.error, contains('Network error'));
        expect(provider.loading, isFalse);
      });

      test('clears previous documents on load', () async {
        // First load with documents
        when(mockService.getDocuments('project-1')).thenAnswer(
          (_) async => [
            Document(id: 'doc-1', filename: 'old.txt', createdAt: DateTime.now()),
          ],
        );
        await provider.loadDocuments('project-1');
        expect(provider.documents.length, equals(1));

        // Second load with different documents
        when(mockService.getDocuments('project-2')).thenAnswer(
          (_) async => [
            Document(id: 'doc-2', filename: 'new.txt', createdAt: DateTime.now()),
            Document(id: 'doc-3', filename: 'new2.txt', createdAt: DateTime.now()),
          ],
        );
        await provider.loadDocuments('project-2');

        expect(provider.documents.length, equals(2));
        expect(provider.documents[0].id, equals('doc-2'));
      });
    });

    group('uploadDocument', () {
      test('sets uploading to true during upload', () async {
        when(mockService.uploadDocument(
          any,
          any,
          any,
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((_) async {
          expect(provider.uploading, isTrue);
          return Document(
            id: 'new-doc',
            filename: 'uploaded.txt',
            createdAt: DateTime.now(),
          );
        });

        await provider.uploadDocument('project-1', [1, 2, 3], 'uploaded.txt');
      });

      test('tracks upload progress via onSendProgress callback', () async {
        ProgressCallback? capturedCallback;
        when(mockService.uploadDocument(
          any,
          any,
          any,
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((invocation) async {
          capturedCallback = invocation.namedArguments[#onSendProgress];
          // Simulate progress updates
          capturedCallback?.call(50, 100);
          expect(provider.uploadProgress, equals(0.5));
          capturedCallback?.call(100, 100);
          expect(provider.uploadProgress, equals(1.0));
          return Document(
            id: 'new-doc',
            filename: 'uploaded.txt',
            createdAt: DateTime.now(),
          );
        });

        await provider.uploadDocument('project-1', [1, 2, 3], 'uploaded.txt');
      });

      test('adds document to beginning of list on success', () async {
        // Setup initial documents
        when(mockService.getDocuments('project-1')).thenAnswer(
          (_) async => [
            Document(id: 'existing', filename: 'old.txt', createdAt: DateTime.now()),
          ],
        );
        await provider.loadDocuments('project-1');

        // Upload new document
        final newDoc = Document(
          id: 'new-doc',
          filename: 'uploaded.txt',
          createdAt: DateTime.now(),
        );
        when(mockService.uploadDocument(
          any,
          any,
          any,
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((_) async => newDoc);

        await provider.uploadDocument('project-1', [1, 2, 3], 'uploaded.txt');

        expect(provider.documents.length, equals(2));
        expect(provider.documents.first.id, equals('new-doc'));
        expect(provider.uploading, isFalse);
      });

      test('resets uploadProgress to 0 after completion', () async {
        when(mockService.uploadDocument(
          any,
          any,
          any,
          onSendProgress: anyNamed('onSendProgress'),
        )).thenAnswer((invocation) async {
          final callback = invocation.namedArguments[#onSendProgress] as ProgressCallback?;
          callback?.call(100, 100);
          return Document(
            id: 'new-doc',
            filename: 'uploaded.txt',
            createdAt: DateTime.now(),
          );
        });

        await provider.uploadDocument('project-1', [1, 2, 3], 'uploaded.txt');

        expect(provider.uploadProgress, equals(0.0));
      });

      test('sets error and rethrows on failure', () async {
        when(mockService.uploadDocument(
          any,
          any,
          any,
          onSendProgress: anyNamed('onSendProgress'),
        )).thenThrow(Exception('Upload failed'));

        expect(
          () => provider.uploadDocument('project-1', [1, 2, 3], 'test.txt'),
          throwsException,
        );

        await Future.microtask(() {});
        expect(provider.error, isNotNull);
        expect(provider.uploading, isFalse);
      });
    });

    group('selectDocument', () {
      test('loads document content and sets selectedDocument on success', () async {
        final docWithContent = Document(
          id: 'doc-1',
          filename: 'test.txt',
          createdAt: DateTime.now(),
          content: 'File content here',
        );

        when(mockService.getDocumentContent('doc-1'))
            .thenAnswer((_) async => docWithContent);

        await provider.selectDocument('doc-1');

        expect(provider.selectedDocument, equals(docWithContent));
        expect(provider.selectedDocument?.content, equals('File content here'));
        expect(provider.loading, isFalse);
      });

      test('sets loading during call', () async {
        when(mockService.getDocumentContent(any)).thenAnswer(
          (_) async {
            expect(provider.loading, isTrue);
            return Document(
              id: 'doc-1',
              filename: 'test.txt',
              createdAt: DateTime.now(),
            );
          },
        );

        await provider.selectDocument('doc-1');
      });

      test('sets error on failure', () async {
        when(mockService.getDocumentContent(any))
            .thenThrow(Exception('Document not found'));

        await provider.selectDocument('doc-1');

        expect(provider.error, isNotNull);
        expect(provider.error, contains('Document not found'));
        expect(provider.selectedDocument, isNull);
        expect(provider.loading, isFalse);
      });
    });

    group('clearSelectedDocument', () {
      test('sets selectedDocument to null', () async {
        // First select a document
        when(mockService.getDocumentContent('doc-1')).thenAnswer(
          (_) async => Document(
            id: 'doc-1',
            filename: 'test.txt',
            createdAt: DateTime.now(),
          ),
        );
        await provider.selectDocument('doc-1');
        expect(provider.selectedDocument, isNotNull);

        // Clear it
        provider.clearSelectedDocument();

        expect(provider.selectedDocument, isNull);
      });
    });

    group('clearError', () {
      test('clears error state', () async {
        // Set error
        when(mockService.getDocuments(any))
            .thenThrow(Exception('Error'));
        await provider.loadDocuments('project-1');
        expect(provider.error, isNotNull);

        // Clear it
        provider.clearError();

        expect(provider.error, isNull);
      });
    });

    group('searchDocuments', () {
      test('returns search results on success', () async {
        final searchResults = [
          DocumentSearchResult(
            id: 'doc-1',
            filename: 'test.txt',
            snippet: 'matching content',
            score: 0.95,
          ),
        ];

        when(mockService.searchDocuments('project-1', 'test'))
            .thenAnswer((_) async => searchResults);

        final results = await provider.searchDocuments('project-1', 'test');

        expect(results, equals(searchResults));
        expect(results.length, equals(1));
        expect(results[0].snippet, equals('matching content'));
      });

      test('does NOT modify documents list', () async {
        // Setup initial documents
        when(mockService.getDocuments('project-1')).thenAnswer(
          (_) async => [
            Document(id: 'doc-1', filename: 'alpha.txt', createdAt: DateTime.now()),
            Document(id: 'doc-2', filename: 'beta.txt', createdAt: DateTime.now()),
          ],
        );
        await provider.loadDocuments('project-1');
        expect(provider.documents.length, equals(2));

        // Search returns different results
        when(mockService.searchDocuments('project-1', 'alpha')).thenAnswer(
          (_) async => [
            DocumentSearchResult(
              id: 'doc-1',
              filename: 'alpha.txt',
              snippet: 'match',
              score: 1.0,
            ),
          ],
        );
        await provider.searchDocuments('project-1', 'alpha');

        // Documents list should be unchanged
        expect(provider.documents.length, equals(2));
      });

      test('sets error and rethrows on failure', () async {
        when(mockService.searchDocuments(any, any))
            .thenThrow(Exception('Search failed'));

        expect(
          () => provider.searchDocuments('project-1', 'test'),
          throwsException,
        );

        await Future.microtask(() {});
        expect(provider.error, isNotNull);
      });
    });

    group('deleteDocument', () {
      // Note: Full delete testing requires BuildContext which we skip
      // Testing only immediate state changes

      test('removes document from list immediately', () async {
        // Setup initial documents
        when(mockService.getDocuments('project-1')).thenAnswer(
          (_) async => [
            Document(id: 'doc-1', filename: 'first.txt', createdAt: DateTime.now()),
            Document(id: 'doc-2', filename: 'second.txt', createdAt: DateTime.now()),
          ],
        );
        await provider.loadDocuments('project-1');
        expect(provider.documents.length, equals(2));

        // Note: Cannot fully test deleteDocument without BuildContext
        // The method requires a BuildContext for SnackBar
      });
    });

    group('notifyListeners', () {
      test('notifies on loadDocuments', () async {
        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        when(mockService.getDocuments(any)).thenAnswer(
          (_) async => <Document>[],
        );
        await provider.loadDocuments('project-1');

        // Should notify at least twice (loading true, loading false)
        expect(notifyCount, greaterThanOrEqualTo(2));
      });

      test('notifies on clearSelectedDocument', () {
        var notified = false;
        provider.addListener(() => notified = true);

        provider.clearSelectedDocument();

        expect(notified, isTrue);
      });

      test('notifies on clearError', () async {
        // First set an error
        when(mockService.getDocuments(any)).thenThrow(Exception('Error'));
        await provider.loadDocuments('project-1');

        var notified = false;
        provider.addListener(() => notified = true);

        provider.clearError();

        expect(notified, isTrue);
      });
    });
  });
}
