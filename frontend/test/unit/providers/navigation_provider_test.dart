/// Unit tests for NavigationProvider (Phase 31, Plan 04).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/providers/navigation_provider.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'navigation_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<SharedPreferences>()])
void main() {
  group('NavigationProvider Unit Tests', () {
    late MockSharedPreferences mockPrefs;

    setUp(() {
      mockPrefs = MockSharedPreferences();
    });

    group('NavigationProvider.load() factory', () {
      test('loads saved expanded preference (true)', () async {
        when(mockPrefs.getBool('sidebarExpanded')).thenReturn(true);

        final provider = await NavigationProvider.load(mockPrefs);

        expect(provider.isSidebarExpanded, isTrue);
        verify(mockPrefs.getBool('sidebarExpanded')).called(1);
      });

      test('loads saved collapsed preference (false)', () async {
        when(mockPrefs.getBool('sidebarExpanded')).thenReturn(false);

        final provider = await NavigationProvider.load(mockPrefs);

        expect(provider.isSidebarExpanded, isFalse);
      });

      test('defaults to expanded when no preference saved', () async {
        when(mockPrefs.getBool('sidebarExpanded')).thenReturn(null);

        final provider = await NavigationProvider.load(mockPrefs);

        expect(provider.isSidebarExpanded, isTrue);
      });

      test('defaults to expanded when read fails', () async {
        when(mockPrefs.getBool('sidebarExpanded')).thenThrow(Exception('Storage corrupted'));

        final provider = await NavigationProvider.load(mockPrefs);

        expect(provider.isSidebarExpanded, isTrue);
      });
    });

    group('Initial State', () {
      test('isSidebarExpanded matches constructor parameter (true)', () {
        final provider = NavigationProvider(mockPrefs, initialExpanded: true);

        expect(provider.isSidebarExpanded, isTrue);
      });

      test('isSidebarExpanded matches constructor parameter (false)', () {
        final provider = NavigationProvider(mockPrefs, initialExpanded: false);

        expect(provider.isSidebarExpanded, isFalse);
      });

      test('isSidebarExpanded defaults to true when not specified', () {
        final provider = NavigationProvider(mockPrefs);

        expect(provider.isSidebarExpanded, isTrue);
      });
    });

    group('toggleSidebar()', () {
      test('toggles isSidebarExpanded from true to false', () async {
        when(mockPrefs.setBool('sidebarExpanded', false)).thenAnswer((_) async => true);

        final provider = NavigationProvider(mockPrefs, initialExpanded: true);

        await provider.toggleSidebar();

        expect(provider.isSidebarExpanded, isFalse);
      });

      test('toggles isSidebarExpanded from false to true', () async {
        when(mockPrefs.setBool('sidebarExpanded', true)).thenAnswer((_) async => true);

        final provider = NavigationProvider(mockPrefs, initialExpanded: false);

        await provider.toggleSidebar();

        expect(provider.isSidebarExpanded, isTrue);
      });

      test('persists via setBool with key sidebarExpanded', () async {
        when(mockPrefs.setBool('sidebarExpanded', false)).thenAnswer((_) async => true);

        final provider = NavigationProvider(mockPrefs, initialExpanded: true);

        await provider.toggleSidebar();

        verify(mockPrefs.setBool('sidebarExpanded', false)).called(1);
      });

      test('notifies listeners', () async {
        when(mockPrefs.setBool('sidebarExpanded', false)).thenAnswer((_) async => true);

        final provider = NavigationProvider(mockPrefs, initialExpanded: true);
        var notified = false;
        provider.addListener(() => notified = true);

        await provider.toggleSidebar();

        expect(notified, isTrue);
      });

      test('still works if persistence fails (graceful degradation)', () async {
        when(mockPrefs.setBool('sidebarExpanded', false)).thenThrow(Exception('Disk full'));

        final provider = NavigationProvider(mockPrefs, initialExpanded: true);
        var notified = false;
        provider.addListener(() => notified = true);

        await provider.toggleSidebar();

        // UI still updates despite persistence failure
        expect(provider.isSidebarExpanded, isFalse);
        expect(notified, isTrue);
      });

      test('toggles multiple times correctly', () async {
        when(mockPrefs.setBool('sidebarExpanded', any)).thenAnswer((_) async => true);

        final provider = NavigationProvider(mockPrefs, initialExpanded: true);

        await provider.toggleSidebar();
        expect(provider.isSidebarExpanded, isFalse);

        await provider.toggleSidebar();
        expect(provider.isSidebarExpanded, isTrue);

        await provider.toggleSidebar();
        expect(provider.isSidebarExpanded, isFalse);
      });
    });
  });
}
