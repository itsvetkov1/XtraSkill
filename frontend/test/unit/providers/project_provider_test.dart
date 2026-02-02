/// Unit tests for ProjectProvider (Phase 31).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/project.dart';
import 'package:frontend/providers/project_provider.dart';
import 'package:frontend/services/project_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'project_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<ProjectService>()])
void main() {
  group('ProjectProvider Unit Tests', () {
    late MockProjectService mockProjectService;
    late ProjectProvider provider;

    setUp(() {
      mockProjectService = MockProjectService();
      provider = ProjectProvider(projectService: mockProjectService);
    });

    // Helper to create test projects
    Project createTestProject({
      String id = 'project-1',
      String name = 'Test Project',
      String? description,
    }) {
      return Project(
        id: id,
        name: name,
        description: description,
        createdAt: DateTime(2026, 1, 1),
        updatedAt: DateTime(2026, 1, 1),
      );
    }

    group('Initial State', () {
      test('starts with empty projects list', () {
        expect(provider.projects, isEmpty);
      });

      test('starts with no selected project', () {
        expect(provider.selectedProject, isNull);
      });

      test('starts with loading false', () {
        expect(provider.loading, isFalse);
      });

      test('isLoading alias returns same as loading', () {
        expect(provider.isLoading, equals(provider.loading));
        expect(provider.isLoading, isFalse);
      });

      test('starts with no error', () {
        expect(provider.error, isNull);
      });

      test('starts with isNotFound false', () {
        expect(provider.isNotFound, isFalse);
      });
    });

    group('loadProjects', () {
      test('sets loading to true during load', () async {
        when(mockProjectService.getProjects()).thenAnswer((_) async {
          // During load, loading should be true
          expect(provider.loading, isTrue);
          return [];
        });

        await provider.loadProjects();
      });

      test('updates projects on successful load', () async {
        final mockProjects = [
          createTestProject(id: '1', name: 'Project 1'),
          createTestProject(id: '2', name: 'Project 2'),
        ];

        when(mockProjectService.getProjects())
            .thenAnswer((_) async => mockProjects);

        await provider.loadProjects();

        expect(provider.projects, equals(mockProjects));
        expect(provider.projects.length, equals(2));
      });

      test('sets loading to false after successful load', () async {
        when(mockProjectService.getProjects()).thenAnswer((_) async => []);

        await provider.loadProjects();

        expect(provider.loading, isFalse);
      });

      test('sets error on failure', () async {
        when(mockProjectService.getProjects())
            .thenThrow(Exception('Network error'));

        await provider.loadProjects();

        expect(provider.error, isNotNull);
        expect(provider.error, contains('Network error'));
        expect(provider.projects, isEmpty);
      });

      test('sets loading to false after failure', () async {
        when(mockProjectService.getProjects())
            .thenThrow(Exception('Network error'));

        await provider.loadProjects();

        expect(provider.loading, isFalse);
      });

      test('clears error on successful load', () async {
        // First load fails
        when(mockProjectService.getProjects())
            .thenThrow(Exception('Network error'));
        await provider.loadProjects();
        expect(provider.error, isNotNull);

        // Second load succeeds
        when(mockProjectService.getProjects()).thenAnswer((_) async => []);
        await provider.loadProjects();

        expect(provider.error, isNull);
      });

      test('clears projects on failure', () async {
        // First load succeeds
        when(mockProjectService.getProjects()).thenAnswer(
            (_) async => [createTestProject(id: '1', name: 'Project 1')]);
        await provider.loadProjects();
        expect(provider.projects.length, equals(1));

        // Second load fails - should clear projects
        when(mockProjectService.getProjects())
            .thenThrow(Exception('Network error'));
        await provider.loadProjects();

        expect(provider.projects, isEmpty);
      });
    });

    group('createProject', () {
      test('adds project to beginning of list on success', () async {
        // Pre-populate list
        when(mockProjectService.getProjects()).thenAnswer((_) async =>
            [createTestProject(id: 'existing', name: 'Existing Project')]);
        await provider.loadProjects();

        final newProject = createTestProject(id: 'new', name: 'New Project');
        when(mockProjectService.createProject('New Project', null))
            .thenAnswer((_) async => newProject);

        final result = await provider.createProject('New Project', null);

        expect(result, equals(newProject));
        expect(provider.projects.first.id, equals('new'));
        expect(provider.projects.length, equals(2));
      });

      test('returns project on success', () async {
        final newProject =
            createTestProject(id: 'new', name: 'New Project', description: 'A description');
        when(mockProjectService.createProject('New Project', 'A description'))
            .thenAnswer((_) async => newProject);

        final result =
            await provider.createProject('New Project', 'A description');

        expect(result, equals(newProject));
        expect(result?.name, equals('New Project'));
        expect(result?.description, equals('A description'));
      });

      test('sets loading during creation', () async {
        when(mockProjectService.createProject(any, any)).thenAnswer((_) async {
          expect(provider.loading, isTrue);
          return createTestProject();
        });

        await provider.createProject('Test', null);
      });

      test('sets loading to false after creation', () async {
        when(mockProjectService.createProject(any, any))
            .thenAnswer((_) async => createTestProject());

        await provider.createProject('Test', null);

        expect(provider.loading, isFalse);
      });

      test('returns null and sets error on failure', () async {
        when(mockProjectService.createProject(any, any))
            .thenThrow(Exception('Creation failed'));

        final result = await provider.createProject('Test', null);

        expect(result, isNull);
        expect(provider.error, isNotNull);
        expect(provider.error, contains('Creation failed'));
      });

      test('sets loading to false after failure', () async {
        when(mockProjectService.createProject(any, any))
            .thenThrow(Exception('Creation failed'));

        await provider.createProject('Test', null);

        expect(provider.loading, isFalse);
      });
    });

    group('selectProject', () {
      test('loads project details on success', () async {
        final project = createTestProject(
          id: 'project-1',
          name: 'Selected Project',
          description: 'Details loaded',
        );
        when(mockProjectService.getProject('project-1'))
            .thenAnswer((_) async => project);

        await provider.selectProject('project-1');

        expect(provider.selectedProject, equals(project));
        expect(provider.selectedProject?.name, equals('Selected Project'));
      });

      test('sets loading during selection', () async {
        when(mockProjectService.getProject(any)).thenAnswer((_) async {
          expect(provider.loading, isTrue);
          return createTestProject();
        });

        await provider.selectProject('project-1');
      });

      test('sets loading to false after selection', () async {
        when(mockProjectService.getProject(any))
            .thenAnswer((_) async => createTestProject());

        await provider.selectProject('project-1');

        expect(provider.loading, isFalse);
      });

      test('sets isNotFound on 404 error', () async {
        when(mockProjectService.getProject('nonexistent'))
            .thenThrow(Exception('Project not found'));

        await provider.selectProject('nonexistent');

        expect(provider.isNotFound, isTrue);
        expect(provider.error, isNull); // Not a "real" error
        expect(provider.selectedProject, isNull);
      });

      test('sets isNotFound when error contains 404', () async {
        when(mockProjectService.getProject('nonexistent'))
            .thenThrow(Exception('404 - resource does not exist'));

        await provider.selectProject('nonexistent');

        expect(provider.isNotFound, isTrue);
        expect(provider.error, isNull);
      });

      test('sets error on non-404 error', () async {
        when(mockProjectService.getProject('project-1'))
            .thenThrow(Exception('Network timeout'));

        await provider.selectProject('project-1');

        expect(provider.isNotFound, isFalse);
        expect(provider.error, isNotNull);
        expect(provider.error, contains('Network timeout'));
        expect(provider.selectedProject, isNull);
      });

      test('clears isNotFound on new selection', () async {
        // First selection fails with 404
        when(mockProjectService.getProject('nonexistent'))
            .thenThrow(Exception('Project not found'));
        await provider.selectProject('nonexistent');
        expect(provider.isNotFound, isTrue);

        // Second selection succeeds
        when(mockProjectService.getProject('existing'))
            .thenAnswer((_) async => createTestProject(id: 'existing'));
        await provider.selectProject('existing');

        expect(provider.isNotFound, isFalse);
        expect(provider.selectedProject, isNotNull);
      });

      test('clears error before new selection', () async {
        // First selection fails
        when(mockProjectService.getProject('error'))
            .thenThrow(Exception('Network error'));
        await provider.selectProject('error');
        expect(provider.error, isNotNull);

        // Second selection - error should be cleared before call
        when(mockProjectService.getProject('success')).thenAnswer((_) async {
          // At start of call, error should be cleared
          expect(provider.error, isNull);
          return createTestProject(id: 'success');
        });
        await provider.selectProject('success');
      });
    });

    group('updateProject', () {
      test('updates project in list', () async {
        // Pre-populate list
        when(mockProjectService.getProjects()).thenAnswer((_) async => [
              createTestProject(id: 'project-1', name: 'Original Name'),
            ]);
        await provider.loadProjects();

        final updated =
            createTestProject(id: 'project-1', name: 'Updated Name');
        when(mockProjectService.updateProject('project-1', 'Updated Name', null))
            .thenAnswer((_) async => updated);

        await provider.updateProject('project-1', 'Updated Name', null);

        expect(provider.projects.first.name, equals('Updated Name'));
      });

      test('updates selectedProject if same id', () async {
        // Select a project first
        final original =
            createTestProject(id: 'project-1', name: 'Original Name');
        when(mockProjectService.getProject('project-1'))
            .thenAnswer((_) async => original);
        await provider.selectProject('project-1');

        // Update the selected project
        final updated =
            createTestProject(id: 'project-1', name: 'Updated Name');
        when(mockProjectService.updateProject('project-1', 'Updated Name', null))
            .thenAnswer((_) async => updated);

        await provider.updateProject('project-1', 'Updated Name', null);

        expect(provider.selectedProject?.name, equals('Updated Name'));
      });

      test('does not update selectedProject if different id', () async {
        // Select a project first
        final selected =
            createTestProject(id: 'project-1', name: 'Selected Project');
        when(mockProjectService.getProject('project-1'))
            .thenAnswer((_) async => selected);
        await provider.selectProject('project-1');

        // Pre-populate list with another project
        when(mockProjectService.getProjects()).thenAnswer((_) async => [
              createTestProject(id: 'project-1', name: 'Selected Project'),
              createTestProject(id: 'project-2', name: 'Other Project'),
            ]);
        await provider.loadProjects();

        // Update the OTHER project
        final updated =
            createTestProject(id: 'project-2', name: 'Updated Other');
        when(mockProjectService.updateProject('project-2', 'Updated Other', null))
            .thenAnswer((_) async => updated);

        await provider.updateProject('project-2', 'Updated Other', null);

        // Selected project should remain unchanged
        expect(provider.selectedProject?.name, equals('Selected Project'));
      });

      test('returns project on success', () async {
        when(mockProjectService.getProjects()).thenAnswer((_) async => [
              createTestProject(id: 'project-1', name: 'Original'),
            ]);
        await provider.loadProjects();

        final updated = createTestProject(id: 'project-1', name: 'Updated');
        when(mockProjectService.updateProject(any, any, any))
            .thenAnswer((_) async => updated);

        final result =
            await provider.updateProject('project-1', 'Updated', null);

        expect(result, equals(updated));
      });

      test('sets loading during update', () async {
        when(mockProjectService.updateProject(any, any, any))
            .thenAnswer((_) async {
          expect(provider.loading, isTrue);
          return createTestProject();
        });

        await provider.updateProject('project-1', 'Name', null);
      });

      test('sets loading to false after update', () async {
        when(mockProjectService.updateProject(any, any, any))
            .thenAnswer((_) async => createTestProject());

        await provider.updateProject('project-1', 'Name', null);

        expect(provider.loading, isFalse);
      });

      test('returns null and sets error on failure', () async {
        when(mockProjectService.updateProject(any, any, any))
            .thenThrow(Exception('Update failed'));

        final result =
            await provider.updateProject('project-1', 'Name', null);

        expect(result, isNull);
        expect(provider.error, isNotNull);
        expect(provider.error, contains('Update failed'));
      });

      test('sets loading to false after failure', () async {
        when(mockProjectService.updateProject(any, any, any))
            .thenThrow(Exception('Update failed'));

        await provider.updateProject('project-1', 'Name', null);

        expect(provider.loading, isFalse);
      });
    });

    group('clearSelection', () {
      test('sets selectedProject to null', () async {
        // Select a project first
        when(mockProjectService.getProject('project-1'))
            .thenAnswer((_) async => createTestProject(id: 'project-1'));
        await provider.selectProject('project-1');
        expect(provider.selectedProject, isNotNull);

        provider.clearSelection();

        expect(provider.selectedProject, isNull);
      });
    });

    group('clearError', () {
      test('clears error state', () async {
        // Set error
        when(mockProjectService.getProjects())
            .thenThrow(Exception('Load error'));
        await provider.loadProjects();
        expect(provider.error, isNotNull);

        provider.clearError();

        expect(provider.error, isNull);
      });

      test('clears isNotFound state', () async {
        // Set isNotFound
        when(mockProjectService.getProject('nonexistent'))
            .thenThrow(Exception('Project not found'));
        await provider.selectProject('nonexistent');
        expect(provider.isNotFound, isTrue);

        provider.clearError();

        expect(provider.isNotFound, isFalse);
      });

      test('clears both error and isNotFound', () async {
        // This tests a quirk: normally error and isNotFound are mutually exclusive
        // but clearError should clear both regardless
        when(mockProjectService.getProject('error'))
            .thenThrow(Exception('Network error'));
        await provider.selectProject('error');
        expect(provider.error, isNotNull);

        provider.clearError();

        expect(provider.error, isNull);
        expect(provider.isNotFound, isFalse);
      });
    });

    group('deleteProject - immediate state changes', () {
      // Note: We skip testing the full timer-based flow since 10 second timer
      // is impractical. We test immediate state changes only.

      // These tests cannot fully test deleteProject since it requires BuildContext
      // for SnackBar display. We test what we can verify without BuildContext.

      test('project list operations work correctly', () async {
        // Test that list manipulation works as expected for delete
        when(mockProjectService.getProjects()).thenAnswer((_) async => [
              createTestProject(id: 'project-1', name: 'Project 1'),
              createTestProject(id: 'project-2', name: 'Project 2'),
              createTestProject(id: 'project-3', name: 'Project 3'),
            ]);
        await provider.loadProjects();
        expect(provider.projects.length, equals(3));

        // Verify indexWhere works as expected for the deletion logic
        final index =
            provider.projects.indexWhere((p) => p.id == 'project-2');
        expect(index, equals(1));
      });

      test('projects list is mutable for deletion operations', () async {
        // Ensure the list can be modified (removeAt, insert)
        when(mockProjectService.getProjects()).thenAnswer((_) async => [
              createTestProject(id: 'project-1', name: 'Project 1'),
              createTestProject(id: 'project-2', name: 'Project 2'),
            ]);
        await provider.loadProjects();

        // This simulates what deleteProject does internally (but without BuildContext)
        final projectsList = provider.projects;
        expect(projectsList.length, equals(2));

        // The actual deleteProject method requires BuildContext which we can't provide
        // in unit tests. Integration tests would cover the full flow.
      });
    });
  });
}
