import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/thread.dart';
import 'package:frontend/models/message.dart';

void main() {
  group('Thread', () {
    group('fromJson', () {
      test('creates instance from complete JSON', () {
        final json = {
          'id': 'thread-123',
          'project_id': 'project-456',
          'project_name': 'Test Project',
          'title': 'Test Thread',
          'created_at': '2026-02-01T10:00:00.000Z',
          'updated_at': '2026-02-01T11:00:00.000Z',
          'last_activity_at': '2026-02-01T12:00:00.000Z',
          'message_count': 5,
          'model_provider': 'anthropic',
        };

        final thread = Thread.fromJson(json);

        expect(thread.id, 'thread-123');
        expect(thread.projectId, 'project-456');
        expect(thread.projectName, 'Test Project');
        expect(thread.title, 'Test Thread');
        expect(thread.createdAt, DateTime.parse('2026-02-01T10:00:00.000Z'));
        expect(thread.updatedAt, DateTime.parse('2026-02-01T11:00:00.000Z'));
        expect(thread.lastActivityAt, DateTime.parse('2026-02-01T12:00:00.000Z'));
        expect(thread.messageCount, 5);
        expect(thread.modelProvider, 'anthropic');
        expect(thread.messages, isNull);
      });

      test('handles minimal required fields', () {
        final json = {
          'id': 'thread-minimal',
          'created_at': '2026-02-01T10:00:00.000Z',
          'updated_at': '2026-02-01T11:00:00.000Z',
        };

        final thread = Thread.fromJson(json);

        expect(thread.id, 'thread-minimal');
        expect(thread.projectId, isNull);
        expect(thread.projectName, isNull);
        expect(thread.title, isNull);
        expect(thread.createdAt, DateTime.parse('2026-02-01T10:00:00.000Z'));
        expect(thread.updatedAt, DateTime.parse('2026-02-01T11:00:00.000Z'));
        expect(thread.lastActivityAt, isNull);
        expect(thread.messageCount, isNull);
        expect(thread.modelProvider, isNull);
        expect(thread.messages, isNull);
      });

      test('handles null projectId', () {
        final json = {
          'id': 'thread-no-project',
          'project_id': null,
          'project_name': null,
          'created_at': '2026-02-01T10:00:00.000Z',
          'updated_at': '2026-02-01T11:00:00.000Z',
        };

        final thread = Thread.fromJson(json);

        expect(thread.projectId, isNull);
        expect(thread.projectName, isNull);
        expect(thread.hasProject, isFalse);
      });

      test('handles null lastActivityAt', () {
        final json = {
          'id': 'thread-no-activity',
          'created_at': '2026-02-01T10:00:00.000Z',
          'updated_at': '2026-02-01T11:00:00.000Z',
          'last_activity_at': null,
        };

        final thread = Thread.fromJson(json);

        expect(thread.lastActivityAt, isNull);
      });

      test('handles null messageCount and modelProvider', () {
        final json = {
          'id': 'thread-null-fields',
          'created_at': '2026-02-01T10:00:00.000Z',
          'updated_at': '2026-02-01T11:00:00.000Z',
          'message_count': null,
          'model_provider': null,
        };

        final thread = Thread.fromJson(json);

        expect(thread.messageCount, isNull);
        expect(thread.modelProvider, isNull);
      });

      test('parses nested messages array', () {
        final json = {
          'id': 'thread-with-messages',
          'created_at': '2026-02-01T10:00:00.000Z',
          'updated_at': '2026-02-01T11:00:00.000Z',
          'messages': [
            {
              'id': 'msg-1',
              'role': 'user',
              'content': 'Hello',
              'created_at': '2026-02-01T10:01:00.000Z',
            },
            {
              'id': 'msg-2',
              'role': 'assistant',
              'content': 'Hi there!',
              'created_at': '2026-02-01T10:02:00.000Z',
            },
          ],
        };

        final thread = Thread.fromJson(json);

        expect(thread.messages, isNotNull);
        expect(thread.messages!.length, 2);
        expect(thread.messages![0].id, 'msg-1');
        expect(thread.messages![0].role, MessageRole.user);
        expect(thread.messages![0].content, 'Hello');
        expect(thread.messages![1].id, 'msg-2');
        expect(thread.messages![1].role, MessageRole.assistant);
        expect(thread.messages![1].content, 'Hi there!');
      });

      test('handles empty messages array', () {
        final json = {
          'id': 'thread-empty-messages',
          'created_at': '2026-02-01T10:00:00.000Z',
          'updated_at': '2026-02-01T11:00:00.000Z',
          'messages': [],
        };

        final thread = Thread.fromJson(json);

        expect(thread.messages, isNotNull);
        expect(thread.messages, isEmpty);
      });
    });

    group('toJson', () {
      test('produces valid map with all fields', () {
        final thread = Thread(
          id: 'thread-123',
          projectId: 'project-456',
          projectName: 'Test Project',
          title: 'Test Thread',
          createdAt: DateTime.parse('2026-02-01T10:00:00.000Z'),
          updatedAt: DateTime.parse('2026-02-01T11:00:00.000Z'),
          lastActivityAt: DateTime.parse('2026-02-01T12:00:00.000Z'),
          messageCount: 5,
          modelProvider: 'anthropic',
        );

        final json = thread.toJson();

        expect(json['id'], 'thread-123');
        expect(json['project_id'], 'project-456');
        expect(json['project_name'], 'Test Project');
        expect(json['title'], 'Test Thread');
        expect(json['created_at'], '2026-02-01T10:00:00.000Z');
        expect(json['updated_at'], '2026-02-01T11:00:00.000Z');
        expect(json['last_activity_at'], '2026-02-01T12:00:00.000Z');
        expect(json['message_count'], 5);
        expect(json['model_provider'], 'anthropic');
      });

      test('excludes null optional fields', () {
        final thread = Thread(
          id: 'thread-minimal',
          createdAt: DateTime.parse('2026-02-01T10:00:00.000Z'),
          updatedAt: DateTime.parse('2026-02-01T11:00:00.000Z'),
        );

        final json = thread.toJson();

        expect(json['id'], 'thread-minimal');
        expect(json.containsKey('project_id'), isFalse);
        expect(json.containsKey('project_name'), isFalse);
        expect(json.containsKey('last_activity_at'), isFalse);
        expect(json.containsKey('message_count'), isFalse);
        expect(json.containsKey('model_provider'), isFalse);
        expect(json.containsKey('messages'), isFalse);
      });

      test('serializes nested messages', () {
        final thread = Thread(
          id: 'thread-with-messages',
          createdAt: DateTime.parse('2026-02-01T10:00:00.000Z'),
          updatedAt: DateTime.parse('2026-02-01T11:00:00.000Z'),
          messages: [
            Message(
              id: 'msg-1',
              role: MessageRole.user,
              content: 'Hello',
              createdAt: DateTime.parse('2026-02-01T10:01:00.000Z'),
            ),
            Message(
              id: 'msg-2',
              role: MessageRole.assistant,
              content: 'Hi there!',
              createdAt: DateTime.parse('2026-02-01T10:02:00.000Z'),
            ),
          ],
        );

        final json = thread.toJson();

        expect(json['messages'], isNotNull);
        expect(json['messages'], isA<List>());
        expect(json['messages'].length, 2);
        expect(json['messages'][0]['id'], 'msg-1');
        expect(json['messages'][0]['role'], 'user');
        expect(json['messages'][1]['id'], 'msg-2');
        expect(json['messages'][1]['role'], 'assistant');
      });
    });

    group('hasProject', () {
      test('returns true for non-null non-empty projectId', () {
        final thread = Thread(
          id: 'thread-1',
          projectId: 'project-123',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        expect(thread.hasProject, isTrue);
      });

      test('returns false for null projectId', () {
        final thread = Thread(
          id: 'thread-1',
          projectId: null,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        expect(thread.hasProject, isFalse);
      });

      test('returns false for empty projectId', () {
        final thread = Thread(
          id: 'thread-1',
          projectId: '',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        expect(thread.hasProject, isFalse);
      });
    });

    group('round-trip', () {
      test('preserves all fields', () {
        final original = Thread(
          id: 'thread-round-trip',
          projectId: 'project-456',
          projectName: 'Round Trip Project',
          title: 'Round Trip Thread',
          createdAt: DateTime.parse('2026-02-01T10:00:00.000Z'),
          updatedAt: DateTime.parse('2026-02-01T11:00:00.000Z'),
          lastActivityAt: DateTime.parse('2026-02-01T12:00:00.000Z'),
          messageCount: 10,
          modelProvider: 'openai',
        );

        final json = original.toJson();
        final restored = Thread.fromJson(json);

        expect(restored.id, original.id);
        expect(restored.projectId, original.projectId);
        expect(restored.projectName, original.projectName);
        expect(restored.title, original.title);
        expect(restored.createdAt, original.createdAt);
        expect(restored.updatedAt, original.updatedAt);
        expect(restored.lastActivityAt, original.lastActivityAt);
        expect(restored.messageCount, original.messageCount);
        expect(restored.modelProvider, original.modelProvider);
      });

      test('preserves nested messages', () {
        final original = Thread(
          id: 'thread-with-messages',
          createdAt: DateTime.parse('2026-02-01T10:00:00.000Z'),
          updatedAt: DateTime.parse('2026-02-01T11:00:00.000Z'),
          messages: [
            Message(
              id: 'msg-1',
              role: MessageRole.user,
              content: 'Test message content',
              createdAt: DateTime.parse('2026-02-01T10:05:00.000Z'),
            ),
          ],
        );

        final json = original.toJson();
        final restored = Thread.fromJson(json);

        expect(restored.messages, isNotNull);
        expect(restored.messages!.length, 1);
        expect(restored.messages![0].id, original.messages![0].id);
        expect(restored.messages![0].role, original.messages![0].role);
        expect(restored.messages![0].content, original.messages![0].content);
        expect(restored.messages![0].createdAt, original.messages![0].createdAt);
      });
    });
  });

  group('PaginatedThreads', () {
    group('fromJson', () {
      test('parses threads array', () {
        final json = {
          'threads': [
            {
              'id': 'thread-1',
              'created_at': '2026-02-01T10:00:00.000Z',
              'updated_at': '2026-02-01T11:00:00.000Z',
              'title': 'First Thread',
            },
            {
              'id': 'thread-2',
              'created_at': '2026-02-01T12:00:00.000Z',
              'updated_at': '2026-02-01T13:00:00.000Z',
              'title': 'Second Thread',
            },
          ],
          'total': 50,
          'page': 1,
          'page_size': 10,
          'has_more': true,
        };

        final paginated = PaginatedThreads.fromJson(json);

        expect(paginated.threads.length, 2);
        expect(paginated.threads[0].id, 'thread-1');
        expect(paginated.threads[0].title, 'First Thread');
        expect(paginated.threads[1].id, 'thread-2');
        expect(paginated.threads[1].title, 'Second Thread');
      });

      test('parses pagination fields', () {
        final json = {
          'threads': [
            {
              'id': 'thread-1',
              'created_at': '2026-02-01T10:00:00.000Z',
              'updated_at': '2026-02-01T11:00:00.000Z',
            },
          ],
          'total': 100,
          'page': 3,
          'page_size': 20,
          'has_more': true,
        };

        final paginated = PaginatedThreads.fromJson(json);

        expect(paginated.total, 100);
        expect(paginated.page, 3);
        expect(paginated.pageSize, 20);
        expect(paginated.hasMore, isTrue);
      });

      test('handles empty threads array', () {
        final json = {
          'threads': [],
          'total': 0,
          'page': 1,
          'page_size': 10,
          'has_more': false,
        };

        final paginated = PaginatedThreads.fromJson(json);

        expect(paginated.threads, isEmpty);
        expect(paginated.total, 0);
        expect(paginated.hasMore, isFalse);
      });

      test('parses threads with nested messages', () {
        final json = {
          'threads': [
            {
              'id': 'thread-with-msgs',
              'created_at': '2026-02-01T10:00:00.000Z',
              'updated_at': '2026-02-01T11:00:00.000Z',
              'messages': [
                {
                  'id': 'msg-1',
                  'role': 'user',
                  'content': 'Hello',
                  'created_at': '2026-02-01T10:01:00.000Z',
                },
              ],
            },
          ],
          'total': 1,
          'page': 1,
          'page_size': 10,
          'has_more': false,
        };

        final paginated = PaginatedThreads.fromJson(json);

        expect(paginated.threads[0].messages, isNotNull);
        expect(paginated.threads[0].messages!.length, 1);
        expect(paginated.threads[0].messages![0].content, 'Hello');
      });

      test('hasMore false at end of results', () {
        final json = {
          'threads': [
            {
              'id': 'last-thread',
              'created_at': '2026-02-01T10:00:00.000Z',
              'updated_at': '2026-02-01T11:00:00.000Z',
            },
          ],
          'total': 5,
          'page': 5,
          'page_size': 1,
          'has_more': false,
        };

        final paginated = PaginatedThreads.fromJson(json);

        expect(paginated.hasMore, isFalse);
        expect(paginated.page, 5);
        expect(paginated.total, 5);
      });
    });
  });
}
