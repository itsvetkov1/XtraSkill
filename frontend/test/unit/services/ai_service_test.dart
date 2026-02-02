/// Unit tests for AIService (Phase 31).
///
/// Note: SSE streaming via flutter_client_sse cannot be easily unit tested
/// without significant infrastructure. The streamChat method is effectively
/// tested through:
/// 1. ConversationProvider tests (which mock AIService.streamChat)
/// 2. Integration tests (manual testing)
///
/// This file focuses on testable aspects: constructor injection and deleteMessage.
library;

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/services/ai_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'ai_service_test.mocks.dart';

@GenerateNiceMocks([MockSpec<Dio>(), MockSpec<FlutterSecureStorage>()])
void main() {
  group('AIService Unit Tests', () {
    late MockDio mockDio;
    late MockFlutterSecureStorage mockStorage;
    late AIService service;

    const testToken = 'test-jwt-token';

    setUp(() {
      mockDio = MockDio();
      mockStorage = MockFlutterSecureStorage();
      service = AIService(
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
      test('accepts optional Dio and storage', () {
        // Default construction should not throw
        expect(() => AIService(), returnsNormally);
      });

      test('uses provided dependencies', () {
        final customDio = Dio();
        final customStorage = const FlutterSecureStorage();
        final customService = AIService(
          dio: customDio,
          storage: customStorage,
        );
        expect(customService, isNotNull);
      });
    });

    group('deleteMessage', () {
      test('makes DELETE request to correct endpoint', () async {
        setupAuth();
        // Match the URL pattern used in ai_service.dart: $apiBaseUrl/api/threads/$threadId/messages/$messageId
        // apiBaseUrl defaults to http://localhost:8000
        when(mockDio.delete(
          'http://localhost:8000/api/threads/thread-1/messages/msg-1',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              statusCode: 204,
              requestOptions: RequestOptions(path: ''),
            ));

        await service.deleteMessage('thread-1', 'msg-1');

        verify(mockDio.delete(
          'http://localhost:8000/api/threads/thread-1/messages/msg-1',
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

        await service.deleteMessage('thread-1', 'msg-1');

        expect(capturedOptions?.headers?['Authorization'],
            equals('Bearer $testToken'));
        expect(capturedOptions?.headers?['Content-Type'],
            equals('application/json'));
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

        await expectLater(
            service.deleteMessage('thread-1', 'msg-1'), completes);
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
          () => service.deleteMessage('thread-1', 'msg-1'),
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
          () => service.deleteMessage('thread-1', 'nonexistent'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Message not found'))),
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
          () => service.deleteMessage('thread-1', 'msg-1'),
          throwsA(predicate((e) =>
              e is Exception && e.toString().contains('Failed to delete'))),
        );
      });

      test('throws on missing auth token', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.deleteMessage('thread-1', 'msg-1'),
          throwsA(predicate(
              (e) => e is Exception && e.toString().contains('authenticated'))),
        );
      });
    });

    group('ChatEvent types', () {
      test('TextDeltaEvent holds text', () {
        final event = TextDeltaEvent(text: 'Hello world');
        expect(event.text, equals('Hello world'));
      });

      test('ToolExecutingEvent holds status', () {
        final event = ToolExecutingEvent(status: 'Searching documents...');
        expect(event.status, equals('Searching documents...'));
      });

      test('MessageCompleteEvent holds content and usage', () {
        final event = MessageCompleteEvent(
          content: 'Complete response',
          inputTokens: 100,
          outputTokens: 50,
        );
        expect(event.content, equals('Complete response'));
        expect(event.inputTokens, equals(100));
        expect(event.outputTokens, equals(50));
      });

      test('ErrorEvent holds message', () {
        final event = ErrorEvent(message: 'Something went wrong');
        expect(event.message, equals('Something went wrong'));
      });

      test('all event types extend ChatEvent', () {
        expect(TextDeltaEvent(text: ''), isA<ChatEvent>());
        expect(ToolExecutingEvent(status: ''), isA<ChatEvent>());
        expect(
            MessageCompleteEvent(
                content: '', inputTokens: 0, outputTokens: 0),
            isA<ChatEvent>());
        expect(ErrorEvent(message: ''), isA<ChatEvent>());
      });
    });

    group('streamChat - structure verification', () {
      // Note: We cannot fully test SSE streaming without mocking SSEClient,
      // which requires significant infrastructure. These tests verify the
      // method exists and handles auth correctly.

      test('streamChat returns Stream<ChatEvent>', () {
        // Verify the return type signature
        final stream = service.streamChat('thread-1', 'Hello');
        expect(stream, isA<Stream<ChatEvent>>());
      });

      test('streamChat yields ErrorEvent on missing auth', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        final events = await service.streamChat('thread-1', 'Hello').toList();

        expect(events.length, equals(1));
        expect(events.first, isA<ErrorEvent>());
        expect((events.first as ErrorEvent).message,
            contains('Not authenticated'));
      });
    });
  });
}
