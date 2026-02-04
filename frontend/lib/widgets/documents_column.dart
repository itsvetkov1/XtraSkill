/// Collapsible documents column widget for project layout.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../providers/document_column_provider.dart';
import '../providers/document_provider.dart';
import '../providers/project_provider.dart';
import '../screens/documents/document_upload_screen.dart';
import '../widgets/delete_confirmation_dialog.dart';

/// Collapsible documents column widget.
///
/// Displays a thin strip when collapsed (48px) that can be expanded
/// to show the full document list (280px). Uses AnimatedSize for
/// smooth transitions between states.
class DocumentsColumn extends StatelessWidget {
  const DocumentsColumn({
    super.key,
    required this.projectId,
  });

  final String projectId;

  @override
  Widget build(BuildContext context) {
    return Consumer<DocumentColumnProvider>(
      builder: (context, columnProvider, _) {
        return AnimatedSize(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeInOut,
          alignment: Alignment.centerLeft,
          child: SizedBox(
            width: columnProvider.isExpanded ? 280 : 48,
            child: columnProvider.isExpanded
                ? _ExpandedContent(projectId: projectId)
                : const _CollapsedStrip(),
          ),
        );
      },
    );
  }
}

/// Collapsed state: thin strip with folder icon.
class _CollapsedStrip extends StatelessWidget {
  const _CollapsedStrip();

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      color: colorScheme.surfaceContainerLow,
      child: InkWell(
        onTap: () => context.read<DocumentColumnProvider>().expand(),
        child: Center(
          child: Tooltip(
            message: 'Show documents',
            child: Icon(
              Icons.folder_outlined,
              color: colorScheme.onSurfaceVariant,
            ),
          ),
        ),
      ),
    );
  }
}

/// Expanded state: header with actions and document list.
class _ExpandedContent extends StatelessWidget {
  const _ExpandedContent({required this.projectId});

  final String projectId;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Container(
      color: colorScheme.surfaceContainerLow,
      child: Column(
        children: [
          // Header row with title and actions
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Text(
                  'Documents',
                  style: textTheme.titleSmall,
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.upload_file),
                  tooltip: 'Upload document',
                  iconSize: 20,
                  visualDensity: VisualDensity.compact,
                  onPressed: () => _onUpload(context),
                ),
                IconButton(
                  icon: const Icon(Icons.chevron_left),
                  tooltip: 'Hide documents',
                  iconSize: 20,
                  visualDensity: VisualDensity.compact,
                  onPressed: () =>
                      context.read<DocumentColumnProvider>().collapse(),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          // Document list
          Expanded(
            child: _DocumentList(projectId: projectId),
          ),
        ],
      ),
    );
  }

  void _onUpload(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => DocumentUploadScreen(projectId: projectId),
      ),
    );
  }
}

/// Document list showing documents from the project.
class _DocumentList extends StatelessWidget {
  const _DocumentList({required this.projectId});

  final String projectId;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Consumer<ProjectProvider>(
      builder: (context, provider, _) {
        final project = provider.selectedProject;
        if (project == null) return const SizedBox();

        final documents = project.documents;

        // Empty state
        if (documents == null || documents.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'No documents',
                style: TextStyle(color: colorScheme.onSurfaceVariant),
              ),
            ),
          );
        }

        // Document list
        return ListView.builder(
          padding: const EdgeInsets.symmetric(vertical: 4),
          itemCount: documents.length,
          itemBuilder: (context, index) {
            final doc = documents[index];
            final filename = doc['filename'] as String? ?? 'Unknown';
            final documentId = doc['id'] as String?;

            return ListTile(
              leading: const Icon(Icons.description, size: 20),
              title: Text(
                filename,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 13),
              ),
              dense: true,
              visualDensity: VisualDensity.compact,
              trailing: PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert, size: 18),
                tooltip: 'Document options',
                padding: EdgeInsets.zero,
                iconSize: 18,
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'delete',
                    child: Row(
                      children: [
                        Icon(Icons.delete_outline, size: 18),
                        SizedBox(width: 8),
                        Text('Delete'),
                      ],
                    ),
                  ),
                ],
                onSelected: (value) {
                  if (value == 'delete' && documentId != null) {
                    _onDelete(context, documentId, filename);
                  }
                },
              ),
              onTap: () {
                if (documentId != null) {
                  _onView(context, documentId);
                }
              },
            );
          },
        );
      },
    );
  }

  void _onView(BuildContext context, String documentId) {
    // Use push to add to browser history (back button returns to project)
    context.push('/projects/$projectId/documents/$documentId');
  }

  Future<void> _onDelete(
    BuildContext context,
    String documentId,
    String filename,
  ) async {
    final confirmed = await showDeleteConfirmationDialog(
      context: context,
      itemType: 'document',
    );

    if (confirmed && context.mounted) {
      context.read<DocumentProvider>().deleteDocument(context, documentId);

      // Refresh project to update document list
      context.read<ProjectProvider>().selectProject(projectId);
    }
  }
}
