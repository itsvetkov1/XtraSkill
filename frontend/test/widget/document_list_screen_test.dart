/// Widget tests for document list screen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/document.dart';
import 'package:frontend/providers/document_provider.dart';
import 'package:frontend/screens/documents/document_list_screen.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'document_list_screen_test.mocks.dart';

@GenerateNiceMocks([MockSpec<DocumentProvider>()])
void main() {
  group('DocumentListScreen Widget Tests', () {
    late MockDocumentProvider mockDocumentProvider;
    const testProjectId = 'test-project-123';

    setUp(() {
      mockDocumentProvider = MockDocumentProvider();
      // Default mock behavior
      when(mockDocumentProvider.loading).thenReturn(false);
      when(mockDocumentProvider.documents).thenReturn([]);
      when(mockDocumentProvider.error).thenReturn(null);
      when(mockDocumentProvider.loadDocuments(any)).thenAnswer((_) async {});
    });

    testWidgets('Empty state when no documents', (tester) async {
      when(mockDocumentProvider.documents).thenReturn([]);
      when(mockDocumentProvider.loading).thenReturn(false);
      when(mockDocumentProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<DocumentProvider>.value(
            value: mockDocumentProvider,
            child: const DocumentListScreen(projectId: testProjectId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('No documents uploaded'), findsOneWidget);
      expect(find.text('Tap the + button to upload a document'), findsOneWidget);
      expect(find.byIcon(Icons.folder_open), findsOneWidget);
    });

    testWidgets('Loading state shows skeletonizer',
        (tester) async {
      when(mockDocumentProvider.documents).thenReturn([]);
      when(mockDocumentProvider.loading).thenReturn(true);
      when(mockDocumentProvider.isLoading).thenReturn(true);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<DocumentProvider>.value(
            value: mockDocumentProvider,
            child: const DocumentListScreen(projectId: testProjectId),
          ),
        ),
      );

      await tester.pump(); // Initial build
      await tester.pump(); // Post-frame callback

      // Skeletonizer shows placeholder documents
      expect(find.text('Loading document name.txt'), findsAtLeastNWidgets(1));
    });

    testWidgets('Document list renders with file names', (tester) async {
      final mockDocuments = [
        Document(
          id: '1',
          filename: 'requirements.txt',
          createdAt: DateTime.now(),
        ),
        Document(
          id: '2',
          filename: 'specifications.md',
          createdAt: DateTime.now(),
        ),
      ];

      when(mockDocumentProvider.documents).thenReturn(mockDocuments);
      when(mockDocumentProvider.loading).thenReturn(false);
      when(mockDocumentProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<DocumentProvider>.value(
            value: mockDocumentProvider,
            child: const DocumentListScreen(projectId: testProjectId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('requirements.txt'), findsOneWidget);
      expect(find.text('specifications.md'), findsOneWidget);
      expect(find.byIcon(Icons.description), findsNWidgets(2));
    });

    testWidgets('Upload button present', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<DocumentProvider>.value(
            value: mockDocumentProvider,
            child: const DocumentListScreen(projectId: testProjectId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.widgetWithIcon(FloatingActionButton, Icons.add),
          findsOneWidget);
    });

    testWidgets('Error state shows snackbar with error message',
        (tester) async {
      when(mockDocumentProvider.error)
          .thenReturn('Failed to load documents');
      when(mockDocumentProvider.loading).thenReturn(false);
      when(mockDocumentProvider.isLoading).thenReturn(false);
      when(mockDocumentProvider.documents).thenReturn([]);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<DocumentProvider>.value(
            value: mockDocumentProvider,
            child: const DocumentListScreen(projectId: testProjectId),
          ),
        ),
      );

      await tester.pump(); // Initial build
      await tester.pump(); // Post-frame callback triggers SnackBar

      // Error shown in SnackBar, not error state UI
      expect(find.textContaining('Failed to load documents'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('Document cards show creation date', (tester) async {
      final testDate = DateTime(2026, 1, 15);
      final mockDocuments = [
        Document(
          id: '1',
          filename: 'test-doc.txt',
          createdAt: testDate,
        ),
      ];

      when(mockDocumentProvider.documents).thenReturn(mockDocuments);
      when(mockDocumentProvider.loading).thenReturn(false);
      when(mockDocumentProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<DocumentProvider>.value(
            value: mockDocumentProvider,
            child: const DocumentListScreen(projectId: testProjectId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('test-doc.txt'), findsOneWidget);
      expect(find.textContaining('Uploaded:'), findsOneWidget);
      expect(find.text('Uploaded: 2026-01-15'), findsOneWidget);
    });

    testWidgets('Multiple documents render correctly', (tester) async {
      final mockDocuments = List.generate(
        3,
        (index) => Document(
          id: '$index',
          filename: 'document_$index.txt',
          createdAt: DateTime.now(),
        ),
      );

      when(mockDocumentProvider.documents).thenReturn(mockDocuments);
      when(mockDocumentProvider.loading).thenReturn(false);
      when(mockDocumentProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<DocumentProvider>.value(
            value: mockDocumentProvider,
            child: const DocumentListScreen(projectId: testProjectId),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(Card), findsNWidgets(3));
      expect(find.text('document_0.txt'), findsOneWidget);
      expect(find.text('document_1.txt'), findsOneWidget);
      expect(find.text('document_2.txt'), findsOneWidget);
    });
  });
}
