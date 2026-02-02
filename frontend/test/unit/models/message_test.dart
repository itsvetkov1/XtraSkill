import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/models/message.dart';

void main() {
  group('MessageRole', () {
    group('fromJson', () {
      test('parses user role', () {
        final role = MessageRole.fromJson('user');
        expect(role, MessageRole.user);
      });

      test('parses assistant role', () {
        final role = MessageRole.fromJson('assistant');
        expect(role, MessageRole.assistant);
      });

      test('defaults to user for unknown role', () {
        final role = MessageRole.fromJson('unknown');
        expect(role, MessageRole.user);
      });

      test('defaults to user for empty string', () {
        final role = MessageRole.fromJson('');
        expect(role, MessageRole.user);
      });
    });

    group('toJson', () {
      test('returns "user" for user role', () {
        expect(MessageRole.user.toJson(), 'user');
      });

      test('returns "assistant" for assistant role', () {
        expect(MessageRole.assistant.toJson(), 'assistant');
      });
    });
  });

  group('Message', () {
    final testDateTime = DateTime.utc(2026, 2, 1, 12, 30, 45);
    final testJson = {
      'id': 'msg-123',
      'role': 'assistant',
      'content': 'Hello, how can I help?',
      'created_at': '2026-02-01T12:30:45.000Z',
    };

    group('fromJson', () {
      test('creates valid instance from complete JSON', () {
        final message = Message.fromJson(testJson);

        expect(message.id, 'msg-123');
        expect(message.role, MessageRole.assistant);
        expect(message.content, 'Hello, how can I help?');
        expect(message.createdAt, testDateTime);
      });

      test('parses user role correctly', () {
        final json = {...testJson, 'role': 'user'};
        final message = Message.fromJson(json);

        expect(message.role, MessageRole.user);
      });

      test('parses ISO 8601 datetime with timezone', () {
        final json = {...testJson, 'created_at': '2026-02-01T12:30:45Z'};
        final message = Message.fromJson(json);

        expect(message.createdAt, testDateTime);
      });

      test('parses ISO 8601 datetime without timezone', () {
        final json = {...testJson, 'created_at': '2026-02-01T12:30:45'};
        final message = Message.fromJson(json);

        expect(message.createdAt.year, 2026);
        expect(message.createdAt.month, 2);
        expect(message.createdAt.day, 1);
        expect(message.createdAt.hour, 12);
        expect(message.createdAt.minute, 30);
        expect(message.createdAt.second, 45);
      });
    });

    group('toJson', () {
      test('produces valid map with all fields', () {
        final message = Message(
          id: 'msg-456',
          role: MessageRole.user,
          content: 'Test content',
          createdAt: testDateTime,
        );

        final json = message.toJson();

        expect(json['id'], 'msg-456');
        expect(json['role'], 'user');
        expect(json['content'], 'Test content');
        expect(json['created_at'], '2026-02-01T12:30:45.000Z');
      });

      test('serializes assistant role correctly', () {
        final message = Message(
          id: 'msg-789',
          role: MessageRole.assistant,
          content: 'Response',
          createdAt: testDateTime,
        );

        final json = message.toJson();

        expect(json['role'], 'assistant');
      });
    });

    group('round-trip', () {
      test('preserves all fields through fromJson(toJson(x))', () {
        final original = Message(
          id: 'msg-roundtrip',
          role: MessageRole.assistant,
          content: 'Test round-trip content with special chars: <>&"\'',
          createdAt: testDateTime,
        );

        final json = original.toJson();
        final restored = Message.fromJson(json);

        expect(restored.id, original.id);
        expect(restored.role, original.role);
        expect(restored.content, original.content);
        expect(restored.createdAt, original.createdAt);
      });

      test('preserves user role through round-trip', () {
        final original = Message(
          id: 'msg-user',
          role: MessageRole.user,
          content: 'User message',
          createdAt: testDateTime,
        );

        final json = original.toJson();
        final restored = Message.fromJson(json);

        expect(restored.role, MessageRole.user);
      });

      test('preserves empty content through round-trip', () {
        final original = Message(
          id: 'msg-empty',
          role: MessageRole.assistant,
          content: '',
          createdAt: testDateTime,
        );

        final json = original.toJson();
        final restored = Message.fromJson(json);

        expect(restored.content, '');
      });
    });
  });
}
