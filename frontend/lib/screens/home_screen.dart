/// Home screen content for authenticated users.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/project.dart';
import '../providers/auth_provider.dart';
import '../providers/chats_provider.dart';
import '../providers/project_provider.dart';
import '../widgets/responsive_layout.dart';

/// Home screen content shown in the navigation shell after authentication
///
/// This widget provides the content only - the ResponsiveScaffold shell
/// handles all navigation (sidebar, drawer, AppBar, breadcrumbs).
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    // Load projects after frame is built
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ProjectProvider>().loadProjects();
    });
  }

  /// Get user's display name for greeting
  String _getUserName(AuthProvider auth) {
    if (auth.displayName != null && auth.displayName!.isNotEmpty) {
      return auth.displayName!;
    }
    if (auth.email != null && auth.email!.isNotEmpty) {
      return auth.email!.split('@').first;
    }
    return 'there';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 600),
        child: SingleChildScrollView(
          padding: ResponsiveHelper.getResponsivePadding(context),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 24),
              // App icon
              Icon(
                Icons.analytics_outlined,
                size: 64,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(height: 24),
              // Personalized greeting
              Consumer<AuthProvider>(
                builder: (context, auth, child) {
                  final userName = _getUserName(auth);
                  return Text(
                    'Welcome back, $userName',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
                  );
                },
              ),
              const SizedBox(height: 48),
              // Action buttons
              _buildActionButtons(context, theme),
              const SizedBox(height: 48),
              // Recent projects section
              _buildRecentProjects(context, theme),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, ThemeData theme) {
    return Column(
      children: [
        // Primary action: New Chat (project-less)
        FilledButton.icon(
          onPressed: () async {
            final chatsProvider = context.read<ChatsProvider>();
            final thread = await chatsProvider.createNewChat();
            if (thread != null && context.mounted) {
              context.go('/chats/${thread.id}');
            }
          },
          icon: const Icon(Icons.chat_bubble),
          label: const Text('New Chat'),
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            textStyle: theme.textTheme.titleMedium,
          ),
        ),
        const SizedBox(height: 16),
        // Secondary action: Browse Projects
        OutlinedButton.icon(
          onPressed: () => context.go('/projects'),
          icon: const Icon(Icons.folder_outlined),
          label: const Text('Browse Projects'),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
        ),
      ],
    );
  }

  Widget _buildRecentProjects(BuildContext context, ThemeData theme) {
    return Consumer<ProjectProvider>(
      builder: (context, provider, child) {
        // Show loading state
        if (provider.isLoading && provider.projects.isEmpty) {
          return const SizedBox.shrink();
        }

        // Show empty hint if no projects
        if (provider.projects.isEmpty) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Text(
              'No projects yet - create your first one!',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
          );
        }

        // Get up to 3 most recent projects
        final recentProjects = provider.projects.take(3).toList();

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Section header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Recent Projects',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                TextButton(
                  onPressed: () => context.go('/projects'),
                  child: const Text('See all'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Project cards
            ...recentProjects.map(
              (project) => _buildProjectCard(context, theme, project),
            ),
          ],
        );
      },
    );
  }

  Widget _buildProjectCard(
    BuildContext context,
    ThemeData theme,
    Project project,
  ) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () => context.go('/projects/${project.id}'),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                project.name,
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              if (project.description != null &&
                  project.description!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  project.description!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
