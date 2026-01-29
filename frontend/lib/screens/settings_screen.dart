/// Settings screen content for user preferences.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/theme_provider.dart';

/// Settings screen content displaying theme toggle and user preferences
///
/// This widget provides the content only - the ResponsiveScaffold shell
/// handles all navigation (sidebar, drawer, AppBar, breadcrumbs).
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        // Theme Section
        _buildSectionHeader(context, 'Appearance'),
        Consumer<ThemeProvider>(
          builder: (context, themeProvider, _) {
            return SwitchListTile(
              title: const Text('Dark Mode'),
              value: themeProvider.isDarkMode,
              onChanged: (_) => themeProvider.toggleTheme(),
            );
          },
        ),
        const Divider(),

        // Placeholder for future settings sections (SET-01, SET-02, SET-05 in Phase 8)
        _buildSectionHeader(context, 'Account'),
        const ListTile(
          title: Text('Profile'),
          subtitle: Text('Coming soon'),
          enabled: false,
        ),
      ],
    );
  }

  Widget _buildSectionHeader(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w600,
            ),
      ),
    );
  }
}
