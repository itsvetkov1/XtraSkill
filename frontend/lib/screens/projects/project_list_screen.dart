/// Project list screen content with create/update functionality.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:skeletonizer/skeletonizer.dart';

import '../../models/project.dart';
import '../../providers/project_provider.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/responsive_layout.dart';

/// Project list screen content showing all user's projects
///
/// This widget provides the content only - the ResponsiveScaffold shell
/// handles all navigation (sidebar, drawer, AppBar, breadcrumbs).
class ProjectListScreen extends StatefulWidget {
  const ProjectListScreen({super.key});

  @override
  State<ProjectListScreen> createState() => _ProjectListScreenState();
}

class _ProjectListScreenState extends State<ProjectListScreen> {
  @override
  void initState() {
    super.initState();
    // Load projects on screen initialization
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ProjectProvider>().loadProjects();
    });
  }

  /// Create placeholder project for skeleton loader
  Project _createPlaceholderProject() {
    return Project(
      id: 'placeholder',
      name: 'Loading project name',
      description: 'Loading project description text here',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Use Scaffold for FAB positioning only (no AppBar)
      body: Consumer<ProjectProvider>(
        builder: (context, provider, child) {
          // Show error as SnackBar
          if (provider.error != null) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Failed to load projects. ${provider.error}'),
                    action: SnackBarAction(
                      label: 'Retry',
                      onPressed: () => provider.loadProjects(),
                    ),
                    duration: const Duration(seconds: 5),
                  ),
                );
                provider.clearError();
              }
            });
          }

          // Show empty state when not loading and no projects
          if (!provider.isLoading && provider.projects.isEmpty) {
            return EmptyState(
              icon: Icons.folder_outlined,
              title: 'No projects yet',
              message: 'Create your first project to get started!',
              buttonLabel: 'Create Project',
              onPressed: () => _showCreateProjectDialog(context),
            );
          }

          // Show project list with skeleton loader
          return RefreshIndicator(
            onRefresh: () => provider.loadProjects(),
            child: Skeletonizer(
              enabled: provider.isLoading,
              child: ListView.builder(
                padding: ResponsiveHelper.getResponsivePadding(context),
                itemCount: provider.isLoading ? 5 : provider.projects.length,
                itemBuilder: (context, index) {
                  final project = provider.isLoading
                      ? _createPlaceholderProject()
                      : provider.projects[index];
                  return _ProjectCard(
                    project: project,
                    onTap: () {
                      if (!provider.isLoading) {
                        // Navigate to detail screen on all platforms
                        context.push('/projects/${project.id}');
                      }
                    },
                  );
                },
              ),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateProjectDialog(context),
        tooltip: 'Create Project',
        child: const Icon(Icons.add),
      ),
    );
  }

  /// Show create project dialog
  void _showCreateProjectDialog(BuildContext context) {
    final nameController = TextEditingController();
    final descriptionController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create Project'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: nameController,
                decoration: const InputDecoration(
                  labelText: 'Name',
                  hintText: 'Enter project name',
                  border: OutlineInputBorder(),
                ),
                autofocus: true,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Name is required';
                  }
                  if (value.length > 255) {
                    return 'Name must be 255 characters or less';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Description (optional)',
                  hintText: 'Enter project description',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (formKey.currentState!.validate()) {
                final provider = context.read<ProjectProvider>();
                final project = await provider.createProject(
                  nameController.text,
                  descriptionController.text.isEmpty
                      ? null
                      : descriptionController.text,
                );
                if (context.mounted) {
                  Navigator.of(context).pop();
                  if (project != null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Project created')),
                    );
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(provider.error ?? 'Failed to create project'),
                        backgroundColor: Theme.of(context).colorScheme.error,
                      ),
                    );
                  }
                }
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }
}

/// Project card widget
class _ProjectCard extends StatelessWidget {
  const _ProjectCard({
    required this.project,
    required this.onTap,
  });

  final Project project;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.folder,
                      color: Theme.of(context).colorScheme.primary),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      project.name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ),
                  Icon(Icons.chevron_right,
                      color: Theme.of(context).colorScheme.onSurfaceVariant),
                ],
              ),
              if (project.description != null &&
                  project.description!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  project.description!,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
              ],
              const SizedBox(height: 8),
              Text(
                'Updated ${DateFormatter.format(project.updatedAt)}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
