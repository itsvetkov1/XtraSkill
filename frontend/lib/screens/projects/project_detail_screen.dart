/// Project detail screen content showing project info and tabs for documents/threads.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../providers/project_provider.dart';
import '../../providers/thread_provider.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../documents/document_upload_screen.dart';
import '../threads/thread_list_screen.dart';

/// Project detail screen content with tabs for documents and threads
///
/// This widget keeps its own Scaffold for TabController and FAB management,
/// but removes the AppBar (shell provides navigation via breadcrumbs).
///
/// Note: Nested Scaffold is acceptable here because the shell Scaffold
/// provides the outer structure and this inner Scaffold only manages
/// the TabBar and FAB without an AppBar.
class ProjectDetailScreen extends StatefulWidget {
  const ProjectDetailScreen({
    super.key,
    required this.projectId,
  });

  final String projectId;

  @override
  State<ProjectDetailScreen> createState() => _ProjectDetailScreenState();
}

class _ProjectDetailScreenState extends State<ProjectDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    // Listen to tab changes to refresh threads when switching to Threads tab
    _tabController.addListener(() {
      if (_tabController.index == 1 && !_tabController.indexIsChanging) {
        // Threads tab selected, refresh threads
        context.read<ThreadProvider>().loadThreads(widget.projectId);
      }
    });

    // Load project details
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ProjectProvider>().selectProject(widget.projectId);
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ProjectProvider>(
      builder: (context, provider, child) {
        // Show loading indicator
        if (provider.loading && provider.selectedProject == null) {
          return const Center(child: CircularProgressIndicator());
        }

        // Show error message
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
                  onPressed: () =>
                      provider.selectProject(widget.projectId),
                  child: const Text('Retry'),
                ),
              ],
            ),
          );
        }

        final project = provider.selectedProject;
        if (project == null) {
          return const Center(child: Text('Project not found'));
        }

        return Column(
          children: [
            // Project info header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          project.name,
                          style: Theme.of(context).textTheme.headlineSmall,
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
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Text(
                        'Created: ${_formatDate(project.createdAt)}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      const SizedBox(width: 16),
                      Text(
                        'Updated: ${_formatDate(project.updatedAt)}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
              ),
            ),
            // Tab bar
            Material(
              color: Theme.of(context).colorScheme.surface,
              child: TabBar(
                controller: _tabController,
                tabs: const [
                  Tab(text: 'Documents', icon: Icon(Icons.description)),
                  Tab(text: 'Threads', icon: Icon(Icons.chat)),
                ],
              ),
            ),
            // Tabs content
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // Documents tab
                  _DocumentsTab(projectId: widget.projectId),
                  // Threads tab
                  ThreadListScreen(projectId: widget.projectId),
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

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }
}

/// Documents tab showing list of documents in project
class _DocumentsTab extends StatelessWidget {
  const _DocumentsTab({required this.projectId});

  final String projectId;

  @override
  Widget build(BuildContext context) {
    return Consumer<ProjectProvider>(
      builder: (context, provider, child) {
        final project = provider.selectedProject;
        if (project == null) return const SizedBox();

        // Empty state
        if (project.documents == null || project.documents!.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.description_outlined,
                    size: 64, color: Theme.of(context).colorScheme.primary),
                const SizedBox(height: 16),
                Text(
                  'No documents yet',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                const Text('Upload documents to provide context for AI conversations'),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () {
                    // Navigate to document upload screen
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (context) => DocumentUploadScreen(projectId: projectId),
                      ),
                    );
                  },
                  icon: const Icon(Icons.upload_file),
                  label: const Text('Upload Document'),
                ),
              ],
            ),
          );
        }

        // Document list (placeholder - full implementation in Plan 03)
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: project.documents!.length,
          itemBuilder: (context, index) {
            final doc = project.documents![index];
            return ListTile(
              leading: const Icon(Icons.description),
              title: Text(doc['filename'] ?? 'Unknown'),
              subtitle: Text('Uploaded: ${doc['created_at'] ?? ''}'),
            );
          },
        );
      },
    );
  }
}
