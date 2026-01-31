import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:frontend/main.dart';
import 'package:frontend/providers/theme_provider.dart';
import 'package:frontend/providers/navigation_provider.dart';
import 'package:frontend/providers/provider_provider.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    // Set up mock SharedPreferences
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();

    // Create providers
    final themeProvider = await ThemeProvider.load(prefs);
    final navigationProvider = await NavigationProvider.load(prefs);
    final providerProvider = await ProviderProvider.load(prefs);

    // Build our app and trigger a frame.
    await tester.pumpWidget(MyApp(
      themeProvider: themeProvider,
      navigationProvider: navigationProvider,
      providerProvider: providerProvider,
    ));

    // Verify app starts (splash screen should be shown)
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
