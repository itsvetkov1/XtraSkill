/// Settings screen content for user preferences.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/constants.dart';
import '../models/token_usage.dart';
import '../providers/auth_provider.dart';
import '../providers/provider_provider.dart';
import '../providers/theme_provider.dart';
import '../providers/logging_provider.dart';
import '../services/auth_service.dart';

/// Settings screen content displaying user profile, theme toggle, usage, and logout
///
/// This widget provides the content only - the ResponsiveScaffold shell
/// handles all navigation (sidebar, drawer, AppBar, breadcrumbs).
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _isLoadingUsage = true;
  TokenUsage? _usage;
  String? _usageError;

  @override
  void initState() {
    super.initState();
    // Fetch usage data after the first frame to ensure context is ready
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _fetchUsage();
    });
  }

  Future<void> _fetchUsage() async {
    if (!mounted) return;

    setState(() {
      _isLoadingUsage = true;
      _usageError = null;
    });

    try {
      final authService = AuthService();
      final usageData = await authService.getUsage();

      if (!mounted) return;

      setState(() {
        _usage = TokenUsage.fromJson(usageData);
        _isLoadingUsage = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _usageError = 'Unable to load usage data';
        _isLoadingUsage = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        // Account Section
        _buildSectionHeader(context, 'Account'),
        Consumer<AuthProvider>(
          builder: (context, authProvider, _) {
            return _buildProfileTile(context, authProvider);
          },
        ),
        const Divider(),

        // Appearance Section
        _buildSectionHeader(context, 'Appearance'),
        Consumer<ThemeProvider>(
          builder: (context, themeProvider, _) {
            return SwitchListTile(
              title: const Text('Dark Mode'),
              subtitle: const Text('Use dark theme'),
              value: themeProvider.isDarkMode,
              onChanged: (_) => themeProvider.toggleTheme(),
            );
          },
        ),
        const Divider(),

        // Preferences Section
        _buildSectionHeader(context, 'Preferences'),
        Consumer<ProviderProvider>(
          builder: (builderContext, providerProvider, _) {
            return ListTile(
              title: const Text('Default AI Provider'),
              subtitle: const Text('Provider for new conversations'),
              trailing: DropdownButton<String>(
                value: providerProvider.selectedProvider,
                underline: const SizedBox.shrink(),
                items: ProviderConfigs.all.map((config) {
                  return DropdownMenuItem<String>(
                    value: config.id,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(config.icon, color: config.color, size: 20),
                        const SizedBox(width: 8),
                        Text(config.displayName),
                        // Experimental badge for Claude Code providers
                        if (config.isExperimental) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: Theme.of(builderContext).colorScheme.secondaryContainer,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              'EXPERIMENTAL',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: Theme.of(builderContext).colorScheme.onSecondaryContainer,
                              ),
                            ),
                          ),
                        ],
                        // Model name for providers with modelName set
                        if (config.modelName != null) ...[
                          const SizedBox(width: 8),
                          Text(
                            '\u2014 ${config.modelName}',
                            style: Theme.of(builderContext).textTheme.bodySmall?.copyWith(
                              color: Theme.of(builderContext).colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    providerProvider.setProvider(value);
                  }
                },
              ),
            );
          },
        ),
        Consumer<LoggingProvider>(
          builder: (context, loggingProvider, _) {
            return SwitchListTile(
              title: const Text('Detailed Logging'),
              subtitle: const Text('Capture diagnostic logs for troubleshooting'),
              value: loggingProvider.isLoggingEnabled,
              onChanged: (_) => loggingProvider.toggleLogging(),
            );
          },
        ),
        const Divider(),

        // Usage Section
        _buildSectionHeader(context, 'Usage'),
        _buildUsageTile(context),
        const Divider(),

        // Actions Section
        _buildSectionHeader(context, 'Actions'),
        _buildLogoutTile(context),
        const SizedBox(height: 32),
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

  Widget _buildProfileTile(BuildContext context, AuthProvider authProvider) {
    final email = authProvider.email ?? 'Unknown';
    final displayName = authProvider.displayName;
    final provider = authProvider.authProvider;
    final initials = _getInitials(displayName ?? email);

    // Determine if we need three lines:
    // Line 1: displayName (or email if no displayName)
    // Line 2: email (only if displayName exists)
    // Line 3: "Signed in with X" (if provider exists)
    final hasDisplayName = displayName != null;
    final hasProvider = provider != null;
    final isThreeLine = hasDisplayName && hasProvider;

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        child: Text(
          initials,
          style: TextStyle(
            color: Theme.of(context).colorScheme.onPrimaryContainer,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      title: Text(displayName ?? email),
      subtitle: _buildProfileSubtitle(context, email, displayName, provider),
      isThreeLine: isThreeLine,
    );
  }

  Widget? _buildProfileSubtitle(
    BuildContext context,
    String email,
    String? displayName,
    String? provider,
  ) {
    final lines = <Widget>[];

    // Show email if we have a display name (email becomes secondary)
    if (displayName != null) {
      lines.add(Text(email));
    }

    // Show provider if available
    if (provider != null) {
      lines.add(
        Text(
          'Signed in with ${_formatProviderName(provider)}',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
        ),
      );
    }

    if (lines.isEmpty) return null;
    if (lines.length == 1) return lines.first;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: lines,
    );
  }

  String _formatProviderName(String provider) {
    switch (provider.toLowerCase()) {
      case 'google':
        return 'Google';
      case 'microsoft':
        return 'Microsoft';
      default:
        return provider;
    }
  }

  String _getInitials(String name) {
    final parts =
        name.split(RegExp(r'[\s@]+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts[0][0].toUpperCase();
    return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
  }

  Widget _buildUsageTile(BuildContext context) {
    if (_isLoadingUsage) {
      return const ListTile(
        title: Text('Monthly Token Budget'),
        subtitle: Padding(
          padding: EdgeInsets.only(top: 8),
          child: LinearProgressIndicator(),
        ),
      );
    }

    if (_usageError != null || _usage == null) {
      return ListTile(
        title: const Text('Monthly Token Budget'),
        subtitle: Text(
          _usageError ?? 'Unable to load usage data',
          style: TextStyle(color: Theme.of(context).colorScheme.error),
        ),
        trailing: IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: _fetchUsage,
          tooltip: 'Retry',
        ),
      );
    }

    final percentText = _usage!.costPercentageDisplay;
    final percentage = _usage!.costPercentage;

    return ListTile(
      title: const Text('Monthly Token Budget'),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: percentage,
            backgroundColor:
                Theme.of(context).colorScheme.surfaceContainerHighest,
            color: percentage > 0.8
                ? Colors.orange
                : Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 4),
          Text(
            '\$${_usage!.totalCost.toStringAsFixed(2)} / \$${_usage!.budget.toStringAsFixed(2)} used ($percentText)',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  Widget _buildLogoutTile(BuildContext context) {
    return ListTile(
      leading: Icon(Icons.logout, color: Theme.of(context).colorScheme.error),
      title: Text(
        'Log Out',
        style: TextStyle(color: Theme.of(context).colorScheme.error),
      ),
      onTap: () => _showLogoutConfirmation(context),
    );
  }

  Future<void> _showLogoutConfirmation(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: const Text('Log Out'),
          content: const Text('Are you sure you want to log out?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              style: TextButton.styleFrom(
                foregroundColor: Theme.of(dialogContext).colorScheme.error,
              ),
              child: const Text('Log Out'),
            ),
          ],
        );
      },
    );

    // CRITICAL: Check context.mounted before using context after await
    if (confirmed == true && context.mounted) {
      await context.read<AuthProvider>().logout();
      // GoRouter redirect handles navigation to login automatically
    }
  }
}
