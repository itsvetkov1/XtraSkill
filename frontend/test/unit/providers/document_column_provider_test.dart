/// Unit tests for DocumentColumnProvider (Phase 31, Plan 04).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/providers/document_column_provider.dart';

void main() {
  group('DocumentColumnProvider Unit Tests', () {
    late DocumentColumnProvider provider;

    setUp(() {
      provider = DocumentColumnProvider();
    });

    group('Initial State', () {
      test('isExpanded starts as false (default collapsed - LAYOUT-03)', () {
        expect(provider.isExpanded, isFalse);
      });
    });

    group('toggle()', () {
      test('toggles from false to true', () {
        expect(provider.isExpanded, isFalse);

        provider.toggle();

        expect(provider.isExpanded, isTrue);
      });

      test('toggles from true to false', () {
        provider.expand();
        expect(provider.isExpanded, isTrue);

        provider.toggle();

        expect(provider.isExpanded, isFalse);
      });

      test('notifies listeners each time', () {
        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        provider.toggle();
        expect(notifyCount, equals(1));

        provider.toggle();
        expect(notifyCount, equals(2));

        provider.toggle();
        expect(notifyCount, equals(3));
      });
    });

    group('expand()', () {
      test('sets isExpanded to true if currently false', () {
        expect(provider.isExpanded, isFalse);

        provider.expand();

        expect(provider.isExpanded, isTrue);
      });

      test('returns true after expand (isExpanded is true)', () {
        provider.expand();

        expect(provider.isExpanded, isTrue);
      });

      test('notifies listeners when state changes', () {
        var notified = false;
        provider.addListener(() => notified = true);

        provider.expand();

        expect(notified, isTrue);
      });

      test('does NOT notify if already expanded (optimization)', () {
        provider.expand(); // First expand - changes state

        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        provider.expand(); // Second expand - already expanded

        expect(notifyCount, equals(0)); // Should not have notified
        expect(provider.isExpanded, isTrue);
      });
    });

    group('collapse()', () {
      test('sets isExpanded to false if currently true', () {
        provider.expand();
        expect(provider.isExpanded, isTrue);

        provider.collapse();

        expect(provider.isExpanded, isFalse);
      });

      test('returns false after collapse (isExpanded is false)', () {
        provider.expand();
        provider.collapse();

        expect(provider.isExpanded, isFalse);
      });

      test('notifies listeners when state changes', () {
        provider.expand();

        var notified = false;
        provider.addListener(() => notified = true);

        provider.collapse();

        expect(notified, isTrue);
      });

      test('does NOT notify if already collapsed (optimization)', () {
        expect(provider.isExpanded, isFalse); // Already collapsed

        var notifyCount = 0;
        provider.addListener(() => notifyCount++);

        provider.collapse(); // Already collapsed

        expect(notifyCount, equals(0)); // Should not have notified
        expect(provider.isExpanded, isFalse);
      });
    });

    group('State Combinations', () {
      test('expand then collapse returns to collapsed', () {
        provider.expand();
        provider.collapse();

        expect(provider.isExpanded, isFalse);
      });

      test('toggle, expand, collapse sequence', () {
        provider.toggle(); // false -> true
        expect(provider.isExpanded, isTrue);

        provider.expand(); // already true, no change
        expect(provider.isExpanded, isTrue);

        provider.collapse(); // true -> false
        expect(provider.isExpanded, isFalse);
      });

      test('multiple toggles return to original state', () {
        expect(provider.isExpanded, isFalse);

        provider.toggle(); // false -> true
        provider.toggle(); // true -> false

        expect(provider.isExpanded, isFalse);
      });
    });
  });
}
