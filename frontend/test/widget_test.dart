import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:frontend/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Verify app starts (splash screen should be shown)
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
