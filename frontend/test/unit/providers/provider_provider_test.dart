/// Unit tests for ProviderProvider (Phase 31, Plan 04).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/providers/provider_provider.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'provider_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<SharedPreferences>()])
void main() {
  group('ProviderProvider Unit Tests', () {
    late MockSharedPreferences mockPrefs;

    setUp(() {
      mockPrefs = MockSharedPreferences();
    });

    group('ProviderProvider.load() factory', () {
      test('loads saved provider preference (anthropic)', () async {
        when(mockPrefs.getString('defaultLlmProvider')).thenReturn('anthropic');

        final provider = await ProviderProvider.load(mockPrefs);

        expect(provider.selectedProvider, equals('anthropic'));
        verify(mockPrefs.getString('defaultLlmProvider')).called(1);
      });

      test('loads saved provider preference (google)', () async {
        when(mockPrefs.getString('defaultLlmProvider')).thenReturn('google');

        final provider = await ProviderProvider.load(mockPrefs);

        expect(provider.selectedProvider, equals('google'));
      });

      test('loads saved provider preference (deepseek)', () async {
        when(mockPrefs.getString('defaultLlmProvider')).thenReturn('deepseek');

        final provider = await ProviderProvider.load(mockPrefs);

        expect(provider.selectedProvider, equals('deepseek'));
      });

      test('defaults to anthropic when no preference saved', () async {
        when(mockPrefs.getString('defaultLlmProvider')).thenReturn(null);

        final provider = await ProviderProvider.load(mockPrefs);

        expect(provider.selectedProvider, equals('anthropic'));
      });

      test('defaults to anthropic when saved value is invalid', () async {
        when(mockPrefs.getString('defaultLlmProvider')).thenReturn('invalid-provider');

        final provider = await ProviderProvider.load(mockPrefs);

        expect(provider.selectedProvider, equals('anthropic'));
      });

      test('defaults to anthropic when read fails', () async {
        when(mockPrefs.getString('defaultLlmProvider')).thenThrow(Exception('Storage corrupted'));

        final provider = await ProviderProvider.load(mockPrefs);

        expect(provider.selectedProvider, equals('anthropic'));
      });
    });

    group('Initial State', () {
      test('selectedProvider matches constructor parameter', () {
        final provider = ProviderProvider(mockPrefs, initialProvider: 'google');

        expect(provider.selectedProvider, equals('google'));
      });

      test('selectedProvider defaults to anthropic when not specified', () {
        final provider = ProviderProvider(mockPrefs);

        expect(provider.selectedProvider, equals('anthropic'));
      });

      test('providers getter returns unmodifiable list', () {
        final provider = ProviderProvider(mockPrefs);

        expect(provider.providers, equals(['anthropic', 'google', 'deepseek']));
      });

      test('providers list cannot be modified', () {
        final provider = ProviderProvider(mockPrefs);

        expect(() => provider.providers.add('openai'), throwsUnsupportedError);
      });
    });

    group('setProvider()', () {
      test('sets selectedProvider to anthropic', () async {
        when(mockPrefs.setString('defaultLlmProvider', 'anthropic')).thenAnswer((_) async => true);

        final provider = ProviderProvider(mockPrefs, initialProvider: 'google');

        await provider.setProvider('anthropic');

        expect(provider.selectedProvider, equals('anthropic'));
      });

      test('sets selectedProvider to google', () async {
        when(mockPrefs.setString('defaultLlmProvider', 'google')).thenAnswer((_) async => true);

        final provider = ProviderProvider(mockPrefs, initialProvider: 'anthropic');

        await provider.setProvider('google');

        expect(provider.selectedProvider, equals('google'));
      });

      test('sets selectedProvider to deepseek', () async {
        when(mockPrefs.setString('defaultLlmProvider', 'deepseek')).thenAnswer((_) async => true);

        final provider = ProviderProvider(mockPrefs, initialProvider: 'anthropic');

        await provider.setProvider('deepseek');

        expect(provider.selectedProvider, equals('deepseek'));
      });

      test('throws ArgumentError for invalid provider', () async {
        final provider = ProviderProvider(mockPrefs);

        expect(
          () => provider.setProvider('invalid'),
          throwsA(isA<ArgumentError>()),
        );
      });

      test('throws ArgumentError with descriptive message', () async {
        final provider = ProviderProvider(mockPrefs);

        expect(
          () => provider.setProvider('openai'),
          throwsA(
            predicate<ArgumentError>((e) => e.message.toString().contains('openai')),
          ),
        );
      });

      test('persists via setString with key defaultLlmProvider', () async {
        when(mockPrefs.setString('defaultLlmProvider', 'google')).thenAnswer((_) async => true);

        final provider = ProviderProvider(mockPrefs, initialProvider: 'anthropic');

        await provider.setProvider('google');

        verify(mockPrefs.setString('defaultLlmProvider', 'google')).called(1);
      });

      test('notifies listeners', () async {
        when(mockPrefs.setString('defaultLlmProvider', 'google')).thenAnswer((_) async => true);

        final provider = ProviderProvider(mockPrefs, initialProvider: 'anthropic');
        var notified = false;
        provider.addListener(() => notified = true);

        await provider.setProvider('google');

        expect(notified, isTrue);
      });

      test('still works if persistence fails (graceful degradation)', () async {
        when(mockPrefs.setString('defaultLlmProvider', 'google')).thenThrow(Exception('Disk full'));

        final provider = ProviderProvider(mockPrefs, initialProvider: 'anthropic');
        var notified = false;
        provider.addListener(() => notified = true);

        await provider.setProvider('google');

        // UI still updates despite persistence failure
        expect(provider.selectedProvider, equals('google'));
        expect(notified, isTrue);
      });

      test('does not persist or notify for invalid provider', () async {
        final provider = ProviderProvider(mockPrefs, initialProvider: 'anthropic');
        var notified = false;
        provider.addListener(() => notified = true);

        try {
          await provider.setProvider('invalid');
        } catch (_) {}

        // Should not have changed state or notified
        expect(provider.selectedProvider, equals('anthropic'));
        expect(notified, isFalse);
        verifyNever(mockPrefs.setString(any, any));
      });
    });
  });
}
