/// Unit tests for ThemeProvider (Phase 31, Plan 04).
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/providers/theme_provider.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'theme_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<SharedPreferences>()])
void main() {
  group('ThemeProvider Unit Tests', () {
    late MockSharedPreferences mockPrefs;

    setUp(() {
      mockPrefs = MockSharedPreferences();
    });

    group('ThemeProvider.load() factory', () {
      test('loads saved dark mode preference (true)', () async {
        when(mockPrefs.getBool('isDarkMode')).thenReturn(true);

        final provider = await ThemeProvider.load(mockPrefs);

        expect(provider.isDarkMode, isTrue);
        expect(provider.themeMode, equals(ThemeMode.dark));
        verify(mockPrefs.getBool('isDarkMode')).called(1);
      });

      test('loads saved light mode preference (false)', () async {
        when(mockPrefs.getBool('isDarkMode')).thenReturn(false);

        final provider = await ThemeProvider.load(mockPrefs);

        expect(provider.isDarkMode, isFalse);
        expect(provider.themeMode, equals(ThemeMode.light));
      });

      test('defaults to light mode when no preference saved (null)', () async {
        when(mockPrefs.getBool('isDarkMode')).thenReturn(null);

        final provider = await ThemeProvider.load(mockPrefs);

        expect(provider.isDarkMode, isFalse);
        expect(provider.themeMode, equals(ThemeMode.light));
      });

      test('defaults to light mode when SharedPreferences read fails', () async {
        when(mockPrefs.getBool('isDarkMode')).thenThrow(Exception('Storage corrupted'));

        final provider = await ThemeProvider.load(mockPrefs);

        expect(provider.isDarkMode, isFalse);
        expect(provider.themeMode, equals(ThemeMode.light));
      });
    });

    group('Initial State (via constructor)', () {
      test('isDarkMode matches constructor parameter (true)', () {
        final provider = ThemeProvider(mockPrefs, initialDarkMode: true);

        expect(provider.isDarkMode, isTrue);
      });

      test('isDarkMode matches constructor parameter (false)', () {
        final provider = ThemeProvider(mockPrefs, initialDarkMode: false);

        expect(provider.isDarkMode, isFalse);
      });

      test('isDarkMode defaults to false when not specified', () {
        final provider = ThemeProvider(mockPrefs);

        expect(provider.isDarkMode, isFalse);
      });

      test('themeMode returns ThemeMode.dark when isDarkMode is true', () {
        final provider = ThemeProvider(mockPrefs, initialDarkMode: true);

        expect(provider.themeMode, equals(ThemeMode.dark));
      });

      test('themeMode returns ThemeMode.light when isDarkMode is false', () {
        final provider = ThemeProvider(mockPrefs, initialDarkMode: false);

        expect(provider.themeMode, equals(ThemeMode.light));
      });
    });

    group('toggleTheme()', () {
      test('toggles isDarkMode from false to true', () async {
        when(mockPrefs.setBool('isDarkMode', true)).thenAnswer((_) async => true);

        final provider = ThemeProvider(mockPrefs, initialDarkMode: false);

        await provider.toggleTheme();

        expect(provider.isDarkMode, isTrue);
        expect(provider.themeMode, equals(ThemeMode.dark));
      });

      test('toggles isDarkMode from true to false', () async {
        when(mockPrefs.setBool('isDarkMode', false)).thenAnswer((_) async => true);

        final provider = ThemeProvider(mockPrefs, initialDarkMode: true);

        await provider.toggleTheme();

        expect(provider.isDarkMode, isFalse);
        expect(provider.themeMode, equals(ThemeMode.light));
      });

      test('persists immediately to SharedPreferences via setBool', () async {
        when(mockPrefs.setBool('isDarkMode', true)).thenAnswer((_) async => true);

        final provider = ThemeProvider(mockPrefs, initialDarkMode: false);

        await provider.toggleTheme();

        verify(mockPrefs.setBool('isDarkMode', true)).called(1);
      });

      test('notifies listeners after toggle', () async {
        when(mockPrefs.setBool('isDarkMode', true)).thenAnswer((_) async => true);

        final provider = ThemeProvider(mockPrefs, initialDarkMode: false);
        var notified = false;
        provider.addListener(() => notified = true);

        await provider.toggleTheme();

        expect(notified, isTrue);
      });

      test('still toggles UI even if setBool fails (graceful degradation)', () async {
        when(mockPrefs.setBool('isDarkMode', true)).thenThrow(Exception('Disk full'));

        final provider = ThemeProvider(mockPrefs, initialDarkMode: false);
        var notified = false;
        provider.addListener(() => notified = true);

        await provider.toggleTheme();

        // UI still updates despite persistence failure
        expect(provider.isDarkMode, isTrue);
        expect(provider.themeMode, equals(ThemeMode.dark));
        expect(notified, isTrue);
      });

      test('toggles multiple times correctly', () async {
        when(mockPrefs.setBool('isDarkMode', any)).thenAnswer((_) async => true);

        final provider = ThemeProvider(mockPrefs, initialDarkMode: false);

        await provider.toggleTheme();
        expect(provider.isDarkMode, isTrue);

        await provider.toggleTheme();
        expect(provider.isDarkMode, isFalse);

        await provider.toggleTheme();
        expect(provider.isDarkMode, isTrue);
      });
    });
  });
}
