/// Unit tests for AuthService (FSVC-02).
library;

import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'auth_service_test.mocks.dart';

@GenerateNiceMocks([MockSpec<Dio>(), MockSpec<FlutterSecureStorage>()])
void main() {
  group('AuthService Unit Tests', () {
    late MockDio mockDio;
    late MockFlutterSecureStorage mockStorage;
    late AuthService service;

    const testBaseUrl = 'http://test.api';

    setUp(() {
      mockDio = MockDio();
      mockStorage = MockFlutterSecureStorage();
      service = AuthService(
        dio: mockDio,
        storage: mockStorage,
        baseUrl: testBaseUrl,
      );
    });

    // Helper to create test JWT tokens
    String createTestJwt({required int expSeconds}) {
      final header = base64Url.encode(utf8.encode('{"alg":"HS256","typ":"JWT"}'));
      final payload = base64Url.encode(utf8.encode('{"exp":$expSeconds,"sub":"user123"}'));
      // Remove padding for JWT format
      final headerNoPad = header.replaceAll('=', '');
      final payloadNoPad = payload.replaceAll('=', '');
      return '$headerNoPad.$payloadNoPad.fake-signature';
    }

    group('Constructor injection', () {
      test('accepts custom Dio instance', () {
        final customDio = Dio();
        final svc = AuthService(dio: customDio);
        expect(svc, isNotNull);
      });

      test('accepts custom FlutterSecureStorage instance', () {
        final customStorage = const FlutterSecureStorage();
        final svc = AuthService(storage: customStorage);
        expect(svc, isNotNull);
      });

      test('accepts custom baseUrl', () {
        final svc = AuthService(baseUrl: 'http://custom.api');
        expect(svc, isNotNull);
      });

      test('uses defaults when no parameters provided', () {
        final svc = AuthService();
        expect(svc, isNotNull);
      });
    });

    group('storeToken', () {
      test('writes token to secure storage with correct key', () async {
        when(mockStorage.write(key: 'auth_token', value: 'test-token'))
            .thenAnswer((_) async => {});

        await service.storeToken('test-token');

        verify(mockStorage.write(key: 'auth_token', value: 'test-token'))
            .called(1);
      });

      test('stores empty string token', () async {
        when(mockStorage.write(key: 'auth_token', value: ''))
            .thenAnswer((_) async => {});

        await service.storeToken('');

        verify(mockStorage.write(key: 'auth_token', value: '')).called(1);
      });

      test('stores long token', () async {
        final longToken = 'a' * 1000;
        when(mockStorage.write(key: 'auth_token', value: longToken))
            .thenAnswer((_) async => {});

        await service.storeToken(longToken);

        verify(mockStorage.write(key: 'auth_token', value: longToken)).called(1);
      });
    });

    group('getStoredToken', () {
      test('reads and returns token from secure storage', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'stored-token');

        final result = await service.getStoredToken();

        expect(result, equals('stored-token'));
        verify(mockStorage.read(key: 'auth_token')).called(1);
      });

      test('returns null when no token stored', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        final result = await service.getStoredToken();

        expect(result, isNull);
      });
    });

    group('isTokenValid', () {
      test('returns false when no token stored', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        final result = await service.isTokenValid();

        expect(result, isFalse);
      });

      test('returns false when token has less than 3 parts', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'invalid.token');

        final result = await service.isTokenValid();

        expect(result, isFalse);
      });

      test('returns false when token has more than 3 parts', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'too.many.parts.here');

        final result = await service.isTokenValid();

        expect(result, isFalse);
      });

      test('returns false when token payload is not valid base64', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'header.!!!invalid-base64!!!.signature');

        final result = await service.isTokenValid();

        expect(result, isFalse);
      });

      test('returns false when token payload is not valid JSON', () async {
        final invalidPayload = base64Url.encode(utf8.encode('not-json'));
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'header.$invalidPayload.signature');

        final result = await service.isTokenValid();

        expect(result, isFalse);
      });

      test('returns false when token payload has no exp field', () async {
        final payloadNoExp = base64Url.encode(utf8.encode('{"sub":"user123"}'));
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'header.$payloadNoExp.signature');

        final result = await service.isTokenValid();

        expect(result, isFalse);
      });

      test('returns false when token is expired', () async {
        final expiredToken = createTestJwt(
          expSeconds:
              DateTime.now().subtract(const Duration(hours: 1)).millisecondsSinceEpoch ~/
                  1000,
        );
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => expiredToken);

        final result = await service.isTokenValid();

        expect(result, isFalse);
      });

      test('returns true when token is not expired', () async {
        final validToken = createTestJwt(
          expSeconds:
              DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch ~/
                  1000,
        );
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => validToken);

        final result = await service.isTokenValid();

        expect(result, isTrue);
      });

      test('returns true when token expires in the future (edge case - 1 second)',
          () async {
        final validToken = createTestJwt(
          expSeconds:
              DateTime.now().add(const Duration(seconds: 2)).millisecondsSinceEpoch ~/
                  1000,
        );
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => validToken);

        final result = await service.isTokenValid();

        expect(result, isTrue);
      });
    });

    group('getCurrentUser', () {
      test('throws exception when no token stored', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.getCurrentUser(),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  e.toString().contains('No authentication token found'),
            ),
          ),
        );
      });

      test('makes GET request to /auth/me with Bearer token', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/auth/me',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {'id': '123', 'email': 'test@example.com'},
              statusCode: 200,
              requestOptions: RequestOptions(path: '/auth/me'),
            ));

        await service.getCurrentUser();

        final captured = verify(mockDio.get(
          captureAny,
          options: captureAnyNamed('options'),
        )).captured;
        expect(captured[0], equals('$testBaseUrl/auth/me'));
        final options = captured[1] as Options;
        expect(options.headers!['Authorization'], equals('Bearer test-token'));
      });

      test('returns user data map on success', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/auth/me',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'id': '123',
                'email': 'test@example.com',
                'oauth_provider': 'google',
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: '/auth/me'),
            ));

        final result = await service.getCurrentUser();

        expect(result['id'], equals('123'));
        expect(result['email'], equals('test@example.com'));
        expect(result['oauth_provider'], equals('google'));
      });

      test('throws exception on Dio error', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/auth/me',
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.connectionTimeout,
          requestOptions: RequestOptions(path: '/auth/me'),
          message: 'Connection timeout',
        ));

        expect(
          () => service.getCurrentUser(),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  e.toString().contains('Failed to get user info'),
            ),
          ),
        );
      });

      test('throws exception on 401 response', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'expired-token');
        when(mockDio.get(
          '$testBaseUrl/auth/me',
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 401,
            requestOptions: RequestOptions(path: '/auth/me'),
          ),
          requestOptions: RequestOptions(path: '/auth/me'),
        ));

        expect(
          () => service.getCurrentUser(),
          throwsA(isA<Exception>()),
        );
      });
    });

    group('getUsage', () {
      test('throws exception when no token stored', () async {
        when(mockStorage.read(key: 'auth_token')).thenAnswer((_) async => null);

        expect(
          () => service.getUsage(),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  e.toString().contains('No authentication token found'),
            ),
          ),
        );
      });

      test('makes GET request to /auth/usage with Bearer token', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/auth/usage',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {'input_tokens': 1000, 'output_tokens': 500},
              statusCode: 200,
              requestOptions: RequestOptions(path: '/auth/usage'),
            ));

        await service.getUsage();

        final captured = verify(mockDio.get(
          captureAny,
          options: captureAnyNamed('options'),
        )).captured;
        expect(captured[0], equals('$testBaseUrl/auth/usage'));
        final options = captured[1] as Options;
        expect(options.headers!['Authorization'], equals('Bearer test-token'));
      });

      test('returns usage data map on success', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/auth/usage',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
              data: {
                'input_tokens': 1000,
                'output_tokens': 500,
                'total_cost': 0.015,
                'month': '2026-02',
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: '/auth/usage'),
            ));

        final result = await service.getUsage();

        expect(result['input_tokens'], equals(1000));
        expect(result['output_tokens'], equals(500));
        expect(result['total_cost'], equals(0.015));
        expect(result['month'], equals('2026-02'));
      });

      test('throws exception on Dio error', () async {
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => 'test-token');
        when(mockDio.get(
          '$testBaseUrl/auth/usage',
          options: anyNamed('options'),
        )).thenThrow(DioException(
          type: DioExceptionType.connectionTimeout,
          requestOptions: RequestOptions(path: '/auth/usage'),
          message: 'Connection timeout',
        ));

        expect(
          () => service.getUsage(),
          throwsA(
            predicate(
              (e) =>
                  e is Exception &&
                  e.toString().contains('Failed to get usage info'),
            ),
          ),
        );
      });
    });

    group('logout', () {
      test('deletes token from secure storage', () async {
        when(mockStorage.delete(key: 'auth_token'))
            .thenAnswer((_) async => {});
        when(mockDio.post('$testBaseUrl/auth/logout'))
            .thenAnswer((_) async => Response(
                  data: {},
                  statusCode: 200,
                  requestOptions: RequestOptions(path: '/auth/logout'),
                ));

        await service.logout();

        verify(mockStorage.delete(key: 'auth_token')).called(1);
      });

      test('makes POST request to /auth/logout', () async {
        when(mockStorage.delete(key: 'auth_token'))
            .thenAnswer((_) async => {});
        when(mockDio.post('$testBaseUrl/auth/logout'))
            .thenAnswer((_) async => Response(
                  data: {},
                  statusCode: 200,
                  requestOptions: RequestOptions(path: '/auth/logout'),
                ));

        await service.logout();

        verify(mockDio.post('$testBaseUrl/auth/logout')).called(1);
      });

      test('ignores backend errors during logout', () async {
        when(mockStorage.delete(key: 'auth_token'))
            .thenAnswer((_) async => {});
        when(mockDio.post('$testBaseUrl/auth/logout')).thenThrow(DioException(
          type: DioExceptionType.connectionError,
          requestOptions: RequestOptions(path: '/auth/logout'),
        ));

        // Should not throw
        await service.logout();

        // Storage delete should still have been called
        verify(mockStorage.delete(key: 'auth_token')).called(1);
      });

      test('completes even when backend returns 500', () async {
        when(mockStorage.delete(key: 'auth_token'))
            .thenAnswer((_) async => {});
        when(mockDio.post('$testBaseUrl/auth/logout')).thenThrow(DioException(
          type: DioExceptionType.badResponse,
          response: Response(
            statusCode: 500,
            requestOptions: RequestOptions(path: '/auth/logout'),
          ),
          requestOptions: RequestOptions(path: '/auth/logout'),
        ));

        // Should not throw
        await service.logout();

        verify(mockStorage.delete(key: 'auth_token')).called(1);
      });
    });

    group('loginWithGoogle', () {
      test('makes POST request to /auth/google/initiate', () async {
        when(mockDio.post('$testBaseUrl/auth/google/initiate'))
            .thenAnswer((_) async => Response(
                  data: {'auth_url': 'https://accounts.google.com/oauth'},
                  statusCode: 200,
                  requestOptions:
                      RequestOptions(path: '/auth/google/initiate'),
                ));

        // Note: launchUrl cannot be tested in unit tests, so we expect the
        // exception from launchUrl not being available in test environment
        try {
          await service.loginWithGoogle();
        } catch (e) {
          // Expected - launchUrl doesn't work in test environment
        }

        verify(mockDio.post('$testBaseUrl/auth/google/initiate')).called(1);
      });

      test('throws exception on Dio error', () async {
        when(mockDio.post('$testBaseUrl/auth/google/initiate'))
            .thenThrow(DioException(
          type: DioExceptionType.connectionError,
          requestOptions: RequestOptions(path: '/auth/google/initiate'),
        ));

        expect(
          () => service.loginWithGoogle(),
          throwsA(
            predicate(
              (e) =>
                  e is Exception && e.toString().contains('OAuth login failed'),
            ),
          ),
        );
      });
    });

    group('loginWithMicrosoft', () {
      test('makes POST request to /auth/microsoft/initiate', () async {
        when(mockDio.post('$testBaseUrl/auth/microsoft/initiate'))
            .thenAnswer((_) async => Response(
                  data: {
                    'auth_url': 'https://login.microsoftonline.com/oauth'
                  },
                  statusCode: 200,
                  requestOptions:
                      RequestOptions(path: '/auth/microsoft/initiate'),
                ));

        // Note: launchUrl cannot be tested in unit tests
        try {
          await service.loginWithMicrosoft();
        } catch (e) {
          // Expected - launchUrl doesn't work in test environment
        }

        verify(mockDio.post('$testBaseUrl/auth/microsoft/initiate')).called(1);
      });

      test('throws exception on Dio error', () async {
        when(mockDio.post('$testBaseUrl/auth/microsoft/initiate'))
            .thenThrow(DioException(
          type: DioExceptionType.connectionError,
          requestOptions: RequestOptions(path: '/auth/microsoft/initiate'),
        ));

        expect(
          () => service.loginWithMicrosoft(),
          throwsA(
            predicate(
              (e) =>
                  e is Exception && e.toString().contains('OAuth login failed'),
            ),
          ),
        );
      });
    });
  });
}
