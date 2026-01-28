/// Widget tests for project list screen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/project.dart';
import 'package:frontend/providers/project_provider.dart';
import 'package:frontend/screens/projects/project_list_screen.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'project_list_screen_test.mocks.dart';

@GenerateNiceMocks([MockSpec<ProjectProvider>()])
void main() {
  group('ProjectListScreen Widget Tests', () {
    late MockProjectProvider mockProjectProvider;

    setUp(() {
      mockProjectProvider = MockProjectProvider();
      // Default mock behavior
      when(mockProjectProvider.loading).thenReturn(false);
      when(mockProjectProvider.isLoading).thenReturn(false);
      when(mockProjectProvider.projects).thenReturn([]);
      when(mockProjectProvider.error).thenReturn(null);
      when(mockProjectProvider.loadProjects()).thenAnswer((_) async {});
    });

    testWidgets('Shows empty state when no projects', (tester) async {
      when(mockProjectProvider.projects).thenReturn([]);
      when(mockProjectProvider.loading).thenReturn(false);
      when(mockProjectProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ProjectProvider>.value(
            value: mockProjectProvider,
            child: const ProjectListScreen(),
          ),
        ),
      );

      // Wait for post-frame callback
      await tester.pumpAndSettle();

      expect(find.text('No projects yet'), findsOneWidget);
      expect(find.text('Create your first project to get started'),
          findsOneWidget);
      expect(find.byIcon(Icons.folder_outlined), findsOneWidget);
    });

    testWidgets('Shows skeletonizer when loading', (tester) async {
      when(mockProjectProvider.projects).thenReturn([]);
      when(mockProjectProvider.loading).thenReturn(true);
      when(mockProjectProvider.isLoading).thenReturn(true);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ProjectProvider>.value(
            value: mockProjectProvider,
            child: const ProjectListScreen(),
          ),
        ),
      );

      await tester.pump(); // Initial build
      await tester.pump(); // Post-frame callback

      // Skeletonizer shows placeholder projects
      expect(find.text('Loading project name'), findsAtLeastNWidgets(1));
    });

    testWidgets('Project cards render with name and description',
        (tester) async {
      final mockProjects = [
        Project(
          id: '1',
          name: 'Project Alpha',
          description: 'First test project',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
        Project(
          id: '2',
          name: 'Project Beta',
          description: 'Second test project',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
      ];

      when(mockProjectProvider.projects).thenReturn(mockProjects);
      when(mockProjectProvider.loading).thenReturn(false);
      when(mockProjectProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ProjectProvider>.value(
            value: mockProjectProvider,
            child: const ProjectListScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Project Alpha'), findsOneWidget);
      expect(find.text('First test project'), findsOneWidget);
      expect(find.text('Project Beta'), findsOneWidget);
      expect(find.text('Second test project'), findsOneWidget);
      expect(find.byIcon(Icons.folder), findsNWidgets(2));
    });

    testWidgets('FloatingActionButton present for create action',
        (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ProjectProvider>.value(
            value: mockProjectProvider,
            child: const ProjectListScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.widgetWithIcon(FloatingActionButton, Icons.add),
          findsOneWidget);
    });

    testWidgets('Error state shows when provider has error', (tester) async {
      when(mockProjectProvider.error).thenReturn('Failed to load projects');
      when(mockProjectProvider.loading).thenReturn(false);
      when(mockProjectProvider.isLoading).thenReturn(false);
      when(mockProjectProvider.projects).thenReturn([]);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ProjectProvider>.value(
            value: mockProjectProvider,
            child: const ProjectListScreen(),
          ),
        ),
      );

      await tester.pump(); // Initial build
      await tester.pump(); // Post-frame callback triggers SnackBar

      // Error shown in SnackBar
      expect(find.textContaining('Failed to load projects'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('Shows project list with correct count', (tester) async {
      final mockProjects = List.generate(
        5,
        (index) => Project(
          id: '$index',
          name: 'Project $index',
          description: 'Description $index',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
      );

      when(mockProjectProvider.projects).thenReturn(mockProjects);
      when(mockProjectProvider.loading).thenReturn(false);
      when(mockProjectProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ProjectProvider>.value(
            value: mockProjectProvider,
            child: const ProjectListScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(Card), findsNWidgets(5));
      expect(find.text('Project 0'), findsOneWidget);
      expect(find.text('Project 4'), findsOneWidget);
    });

    testWidgets('Project without description renders correctly',
        (tester) async {
      final mockProjects = [
        Project(
          id: '1',
          name: 'Project No Description',
          description: null,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        ),
      ];

      when(mockProjectProvider.projects).thenReturn(mockProjects);
      when(mockProjectProvider.loading).thenReturn(false);
      when(mockProjectProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<ProjectProvider>.value(
            value: mockProjectProvider,
            child: const ProjectListScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Project No Description'), findsOneWidget);
      // Description should not be shown
      expect(find.textContaining('Updated'), findsOneWidget);
    });
  });
}
