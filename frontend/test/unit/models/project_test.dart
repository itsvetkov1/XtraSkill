import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/project.dart';

void main() {
  group('Project', () {
    final testCreatedAt = DateTime.utc(2026, 1, 15, 10, 0, 0);
    final testUpdatedAt = DateTime.utc(2026, 2, 1, 14, 30, 0);

    final completeJson = {
      'id': 'proj-123',
      'name': 'Test Project',
      'description': 'A test project description',
      'created_at': '2026-01-15T10:00:00.000Z',
      'updated_at': '2026-02-01T14:30:00.000Z',
      'documents': [
        {'id': 'doc-1', 'filename': 'file1.txt'},
        {'id': 'doc-2', 'filename': 'file2.pdf'},
      ],
      'threads': [
        {'id': 'thread-1', 'title': 'Thread 1'},
        {'id': 'thread-2', 'title': 'Thread 2'},
      ],
    };

    final minimalJson = {
      'id': 'proj-456',
      'name': 'Minimal Project',
      'created_at': '2026-01-15T10:00:00.000Z',
      'updated_at': '2026-02-01T14:30:00.000Z',
    };

    group('fromJson', () {
      test('creates instance from complete JSON', () {
        final project = Project.fromJson(completeJson);

        expect(project.id, 'proj-123');
        expect(project.name, 'Test Project');
        expect(project.description, 'A test project description');
        expect(project.createdAt, testCreatedAt);
        expect(project.updatedAt, testUpdatedAt);
        expect(project.documents, isNotNull);
        expect(project.documents!.length, 2);
        expect(project.threads, isNotNull);
        expect(project.threads!.length, 2);
      });

      test('creates instance from minimal JSON without optional fields', () {
        final project = Project.fromJson(minimalJson);

        expect(project.id, 'proj-456');
        expect(project.name, 'Minimal Project');
        expect(project.description, isNull);
        expect(project.documents, isNull);
        expect(project.threads, isNull);
      });

      test('handles null description', () {
        final json = {...minimalJson, 'description': null};
        final project = Project.fromJson(json);

        expect(project.description, isNull);
      });

      test('handles null documents', () {
        final json = {...minimalJson, 'documents': null};
        final project = Project.fromJson(json);

        expect(project.documents, isNull);
      });

      test('handles null threads', () {
        final json = {...minimalJson, 'threads': null};
        final project = Project.fromJson(json);

        expect(project.threads, isNull);
      });

      test('handles empty documents array', () {
        final json = {...minimalJson, 'documents': <Map<String, dynamic>>[]};
        final project = Project.fromJson(json);

        expect(project.documents, isNotNull);
        expect(project.documents, isEmpty);
      });

      test('handles empty threads array', () {
        final json = {...minimalJson, 'threads': <Map<String, dynamic>>[]};
        final project = Project.fromJson(json);

        expect(project.threads, isNotNull);
        expect(project.threads, isEmpty);
      });

      test('parses nested documents array correctly', () {
        final project = Project.fromJson(completeJson);

        expect(project.documents![0]['id'], 'doc-1');
        expect(project.documents![0]['filename'], 'file1.txt');
        expect(project.documents![1]['id'], 'doc-2');
        expect(project.documents![1]['filename'], 'file2.pdf');
      });

      test('parses nested threads array correctly', () {
        final project = Project.fromJson(completeJson);

        expect(project.threads![0]['id'], 'thread-1');
        expect(project.threads![0]['title'], 'Thread 1');
        expect(project.threads![1]['id'], 'thread-2');
        expect(project.threads![1]['title'], 'Thread 2');
      });
    });

    group('toJson', () {
      test('produces valid map with all required fields', () {
        final project = Project(
          id: 'proj-789',
          name: 'Output Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
        );

        final json = project.toJson();

        expect(json['id'], 'proj-789');
        expect(json['name'], 'Output Project');
        expect(json['created_at'], '2026-01-15T10:00:00.000Z');
        expect(json['updated_at'], '2026-02-01T14:30:00.000Z');
      });

      test('includes description when present', () {
        final project = Project(
          id: 'proj-789',
          name: 'Output Project',
          description: 'Project with description',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
        );

        final json = project.toJson();

        expect(json['description'], 'Project with description');
      });

      test('includes null description in output', () {
        final project = Project(
          id: 'proj-789',
          name: 'Output Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
        );

        final json = project.toJson();

        // description key is present but null
        expect(json.containsKey('description'), true);
        expect(json['description'], isNull);
      });

      test('excludes documents when null', () {
        final project = Project(
          id: 'proj-789',
          name: 'Output Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
        );

        final json = project.toJson();

        expect(json.containsKey('documents'), false);
      });

      test('excludes threads when null', () {
        final project = Project(
          id: 'proj-789',
          name: 'Output Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
        );

        final json = project.toJson();

        expect(json.containsKey('threads'), false);
      });

      test('includes documents when present', () {
        final project = Project(
          id: 'proj-789',
          name: 'Output Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
          documents: [
            {'id': 'doc-1', 'filename': 'test.txt'},
          ],
        );

        final json = project.toJson();

        expect(json.containsKey('documents'), true);
        expect(json['documents']!.length, 1);
        expect(json['documents']![0]['filename'], 'test.txt');
      });

      test('includes threads when present', () {
        final project = Project(
          id: 'proj-789',
          name: 'Output Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
          threads: [
            {'id': 'thread-1', 'title': 'Test Thread'},
          ],
        );

        final json = project.toJson();

        expect(json.containsKey('threads'), true);
        expect(json['threads']!.length, 1);
        expect(json['threads']![0]['title'], 'Test Thread');
      });
    });

    group('round-trip', () {
      test('preserves all fields through fromJson(toJson(x))', () {
        final original = Project(
          id: 'proj-roundtrip',
          name: 'Round-trip Project',
          description: 'Test description with special chars: <>&"\' ',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
          documents: [
            {'id': 'doc-rt', 'filename': 'roundtrip.txt'},
          ],
          threads: [
            {'id': 'thread-rt', 'title': 'Round-trip Thread'},
          ],
        );

        final json = original.toJson();
        final restored = Project.fromJson(json);

        expect(restored.id, original.id);
        expect(restored.name, original.name);
        expect(restored.description, original.description);
        expect(restored.createdAt, original.createdAt);
        expect(restored.updatedAt, original.updatedAt);
        expect(restored.documents!.length, original.documents!.length);
        expect(restored.documents![0]['id'], original.documents![0]['id']);
        expect(restored.threads!.length, original.threads!.length);
        expect(restored.threads![0]['id'], original.threads![0]['id']);
      });

      test('preserves null optional fields through round-trip', () {
        final original = Project(
          id: 'proj-nulls',
          name: 'Nullable Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
        );

        final json = original.toJson();
        final restored = Project.fromJson(json);

        expect(restored.id, original.id);
        expect(restored.name, original.name);
        expect(restored.description, isNull);
        expect(restored.documents, isNull);
        expect(restored.threads, isNull);
      });

      test('preserves empty arrays through round-trip', () {
        final original = Project(
          id: 'proj-empty',
          name: 'Empty Arrays Project',
          createdAt: testCreatedAt,
          updatedAt: testUpdatedAt,
          documents: [],
          threads: [],
        );

        final json = original.toJson();
        final restored = Project.fromJson(json);

        expect(restored.documents, isNotNull);
        expect(restored.documents, isEmpty);
        expect(restored.threads, isNotNull);
        expect(restored.threads, isEmpty);
      });
    });
  });
}
