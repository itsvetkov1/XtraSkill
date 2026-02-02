import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/document.dart';

void main() {
  group('Document', () {
    final testCreatedAt = DateTime.utc(2026, 1, 20, 9, 15, 30);

    final completeJson = {
      'id': 'doc-123',
      'filename': 'requirements.pdf',
      'content': 'This is the document content with full text.',
      'created_at': '2026-01-20T09:15:30.000Z',
    };

    final minimalJson = {
      'id': 'doc-456',
      'filename': 'notes.txt',
      'created_at': '2026-01-20T09:15:30.000Z',
    };

    group('fromJson', () {
      test('creates instance from complete JSON with all fields', () {
        final document = Document.fromJson(completeJson);

        expect(document.id, 'doc-123');
        expect(document.filename, 'requirements.pdf');
        expect(document.content, 'This is the document content with full text.');
        expect(document.createdAt, testCreatedAt);
      });

      test('creates instance from minimal JSON without content', () {
        final document = Document.fromJson(minimalJson);

        expect(document.id, 'doc-456');
        expect(document.filename, 'notes.txt');
        expect(document.content, isNull);
        expect(document.createdAt, testCreatedAt);
      });

      test('handles null content explicitly', () {
        final json = {...minimalJson, 'content': null};
        final document = Document.fromJson(json);

        expect(document.content, isNull);
      });

      test('handles empty content string', () {
        final json = {...minimalJson, 'content': ''};
        final document = Document.fromJson(json);

        expect(document.content, '');
      });

      test('parses ISO 8601 datetime correctly', () {
        final document = Document.fromJson(completeJson);

        expect(document.createdAt.year, 2026);
        expect(document.createdAt.month, 1);
        expect(document.createdAt.day, 20);
        expect(document.createdAt.hour, 9);
        expect(document.createdAt.minute, 15);
        expect(document.createdAt.second, 30);
      });

      test('handles various filename extensions', () {
        final extensions = ['pdf', 'txt', 'docx', 'md', 'json'];

        for (final ext in extensions) {
          final json = {...minimalJson, 'filename': 'file.$ext'};
          final document = Document.fromJson(json);
          expect(document.filename, 'file.$ext');
        }
      });
    });

    group('toJson', () {
      test('produces valid map with all required fields', () {
        final document = Document(
          id: 'doc-789',
          filename: 'output.txt',
          createdAt: testCreatedAt,
        );

        final json = document.toJson();

        expect(json['id'], 'doc-789');
        expect(json['filename'], 'output.txt');
        expect(json['created_at'], '2026-01-20T09:15:30.000Z');
      });

      test('excludes content when null', () {
        final document = Document(
          id: 'doc-789',
          filename: 'output.txt',
          createdAt: testCreatedAt,
        );

        final json = document.toJson();

        expect(json.containsKey('content'), false);
      });

      test('includes content when present', () {
        final document = Document(
          id: 'doc-789',
          filename: 'output.txt',
          createdAt: testCreatedAt,
          content: 'Document content here',
        );

        final json = document.toJson();

        expect(json.containsKey('content'), true);
        expect(json['content'], 'Document content here');
      });

      test('includes empty content string when set', () {
        final document = Document(
          id: 'doc-789',
          filename: 'output.txt',
          createdAt: testCreatedAt,
          content: '',
        );

        final json = document.toJson();

        expect(json.containsKey('content'), true);
        expect(json['content'], '');
      });

      test('serializes datetime in ISO 8601 format', () {
        final document = Document(
          id: 'doc-dt',
          filename: 'test.txt',
          createdAt: DateTime.utc(2026, 12, 31, 23, 59, 59),
        );

        final json = document.toJson();

        expect(json['created_at'], '2026-12-31T23:59:59.000Z');
      });
    });

    group('round-trip', () {
      test('preserves all fields through fromJson(toJson(x))', () {
        final original = Document(
          id: 'doc-roundtrip',
          filename: 'roundtrip.pdf',
          createdAt: testCreatedAt,
          content: 'Full content with special chars: <>&"\' and unicode: ',
        );

        final json = original.toJson();
        final restored = Document.fromJson(json);

        expect(restored.id, original.id);
        expect(restored.filename, original.filename);
        expect(restored.createdAt, original.createdAt);
        expect(restored.content, original.content);
      });

      test('preserves null content through round-trip', () {
        final original = Document(
          id: 'doc-null',
          filename: 'nocontent.txt',
          createdAt: testCreatedAt,
        );

        final json = original.toJson();
        final restored = Document.fromJson(json);

        expect(restored.id, original.id);
        expect(restored.filename, original.filename);
        expect(restored.createdAt, original.createdAt);
        expect(restored.content, isNull);
      });

      test('preserves empty content through round-trip', () {
        final original = Document(
          id: 'doc-empty',
          filename: 'empty.txt',
          createdAt: testCreatedAt,
          content: '',
        );

        final json = original.toJson();
        final restored = Document.fromJson(json);

        expect(restored.content, '');
      });

      test('preserves multiline content through round-trip', () {
        final multilineContent = '''Line 1
Line 2
Line 3 with tabs:\t\ttext
Line 4 with special: <html>&amp;</html>''';

        final original = Document(
          id: 'doc-multiline',
          filename: 'multiline.txt',
          createdAt: testCreatedAt,
          content: multilineContent,
        );

        final json = original.toJson();
        final restored = Document.fromJson(json);

        expect(restored.content, multilineContent);
      });
    });
  });
}
