/// Project detail screen with threads-first layout and collapsible documents column.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../providers/project_provider.dart';
import '../../providers/thread_provider.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../../widgets/documents_column.dart';
import '../../widgets/resource_not_found_state.dart';
import '../threads/thread_list_screen.dart';

/// Project detail screen with threads-first layout.
///
/// Displays project info header at top, with a Row below containing:
/// - DocumentsColumn: Collapsible side column for documents (48px collapsed, 280px expanded)
/// - ThreadListScreen: Primary content area showing conversation threads
///
/// This replaces the previous tab-based navigation (Documents/Threads tabs)
/// to provide immediate access to threads while keeping documents accessible
/// via the collapsible column.
class ProjectDetailScreen extends StatefulWidget {
  const ProjectDetailScreen({
    super.key,
    required this.projectId,
  });

  final String projectId;

  @override
  State<ProjectDetailScreen> createState() => _ProjectDetailScreenState();
}

class _ProjectDetailScreenState extends State<ProjectDetailScreen> {
  @override
  void initState() {
    super.initState();

    // Load project details and threads immediately (threads is primary view now)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ProjectProvider>().selectProject(widget.projectId);
      context.read<ThreadProvider>().loadThreads(widget.projectId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ProjectProvider>(
      builder: (context, provider, child) {
        // Show loading indicator
        if (provider.loading && provider.selectedProject == null) {
          return const Center(child: CircularProgressIndicator());
        }

        // Show not-found state (ERR-02) - check BEFORE generic error
        if (provider.isNotFound) {
          return ResourceNotFoundState(
            icon: Icons.folder_off_outlined,
            title: 'Project not found',
            message:
                'This project may have been deleted or you may not have access to it.',
            buttonLabel: 'Back to Projects',
            onPressed: () => context.go('/projects'),
          );
        }

        // Show error message (network/server errors)
        if (provider.error != null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline,
                    size: 48, color: Theme.of(context).colorScheme.error),
                const SizedBox(height: 16),
                Text(
                  'Error loading project',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                SelectableText(provider.error!),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => provider.selectProject(widget.projectId),
                  child: const Text('Retry'),
                ),
              ],
            ),
          );
        }

        final project = provider.selectedProject;
        if (project == null) {
          // Shouldn't reach here - either loading, error, or isNotFound
          return const Center(child: CircularProgressIndicator());
        }

        return Column(
          children: [
            // Project info header - consolidated for reduced vertical space
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              project.name,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Updated ${DateFormatter.format(project.updatedAt)}',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Theme.of(context).colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.edit),
                        tooltip: 'Edit Project',
                        onPressed: () => _showEditProjectDialog(context),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete_outline),
                        tooltip: 'Delete Project',
                        onPressed: () => _deleteProject(context),
                      ),
                    ],
                  ),
                  if (project.description != null &&
                      project.description!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      project.description!,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ],
              ),
            ),
            // Main content area: Documents column + Threads list
            Expanded(
              child: Row(
                children: [
                  // Collapsible documents column (LAYOUT-02, 03, 04, 05, 06)
                  DocumentsColumn(projectId: widget.projectId),

                  // Vertical divider between column and threads
                  const VerticalDivider(width: 1, thickness: 1),

                  // Threads list - always visible, primary content (LAYOUT-01)
                  Expanded(
                    child: ThreadListScreen(projectId: widget.projectId),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  /// Show edit project dialog
  void _showEditProjectDialog(BuildContext context) {
    final provider = context.read<ProjectProvider>();
    final project = provider.selectedProject;
    if (project == null) return;

    final nameController = TextEditingController(text: project.name);
    final descriptionController =
        TextEditingController(text: project.description ?? '');
    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Project'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: nameController,
                decoration: const InputDecoration(
                  labelText: 'Name',
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
                final updatedProject = await provider.updateProject(
                  project.id,
                  nameController.text,
                  descriptionController.text.isEmpty
                      ? null
                      : descriptionController.text,
                );
                if (context.mounted) {
                  Navigator.of(context).pop();
                  if (updatedProject != null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Project updated')),
                    );
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(provider.error ?? 'Failed to update project'),
                        backgroundColor: Theme.of(context).colorScheme.error,
                      ),
                    );
                  }
                }
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  /// Delete project with confirmation
  Future<void> _deleteProject(BuildContext context) async {
    final confirmed = await showDeleteConfirmationDialog(
      context: context,
      itemType: 'project',
      cascadeMessage: 'This will delete all threads and documents in this project.',
    );

    if (confirmed && context.mounted) {
      context.read<ProjectProvider>().deleteProject(context, widget.projectId);

      // Navigate back to projects list
      context.go('/projects');
    }
  }
}
