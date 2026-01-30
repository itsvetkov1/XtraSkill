import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:skeletonizer/skeletonizer.dart';

import '../../models/document.dart';
import '../../providers/document_provider.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../../widgets/empty_state.dart';
import 'document_upload_screen.dart';
import 'document_viewer_screen.dart';

/// Screen displaying list of documents in a project.
///
/// Shows document cards with filename and creation date.
/// Provides upload button via floating action button.
class DocumentListScreen extends StatefulWidget {
  final String projectId;

  const DocumentListScreen({super.key, required this.projectId});

  @override
  State<DocumentListScreen> createState() => _DocumentListScreenState();
}

class _DocumentListScreenState extends State<DocumentListScreen> {
  @override
  void initState() {
    super.initState();
    // Load documents when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DocumentProvider>().loadDocuments(widget.projectId);
    });
  }

  /// Create placeholder document for skeleton loader
  Document _createPlaceholderDocument() {
    return Document(
      id: 'placeholder',
      filename: 'Loading document name.txt',
      createdAt: DateTime.now(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Documents'),
      ),
      body: Consumer<DocumentProvider>(
        builder: (context, provider, child) {
          // Show error as SnackBar
          if (provider.error != null) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Failed to load documents. ${provider.error}'),
                    action: SnackBarAction(
                      label: 'Retry',
                      onPressed: () => provider.loadDocuments(widget.projectId),
                    ),
                    duration: const Duration(seconds: 5),
                  ),
                );
                provider.clearError();
              }
            });
          }

          // Show empty state when not loading and no documents
          if (!provider.isLoading && provider.documents.isEmpty) {
            return EmptyState(
              icon: Icons.description_outlined,
              title: 'No documents yet',
              message: 'Upload documents to provide context for AI conversations.',
              buttonLabel: 'Upload Document',
              buttonIcon: Icons.upload_file,
              onPressed: () async {
                await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (ctx) => DocumentUploadScreen(projectId: widget.projectId),
                  ),
                );
                if (context.mounted) {
                  context.read<DocumentProvider>().loadDocuments(widget.projectId);
                }
              },
            );
          }

          // Show document list with skeleton loader
          return Skeletonizer(
            enabled: provider.isLoading,
            child: ListView.builder(
              itemCount: provider.isLoading ? 3 : provider.documents.length,
              itemBuilder: (context, index) {
                final doc = provider.isLoading
                    ? _createPlaceholderDocument()
                    : provider.documents[index];
                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: ListTile(
                    leading: const Icon(Icons.description, size: 40),
                    title: Text(doc.filename),
                    subtitle: Text(
                      'Uploaded ${DateFormatter.format(doc.createdAt)}',
                      style: const TextStyle(fontSize: 12),
                    ),
                    trailing: provider.isLoading
                        ? const Icon(Icons.chevron_right)
                        : PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'view') {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) =>
                                        DocumentViewerScreen(documentId: doc.id),
                                  ),
                                );
                              } else if (value == 'delete') {
                                _deleteDocument(context, doc.id);
                              }
                            },
                            itemBuilder: (context) => [
                              const PopupMenuItem(
                                value: 'view',
                                child: Row(
                                  children: [
                                    Icon(Icons.visibility),
                                    SizedBox(width: 8),
                                    Text('View'),
                                  ],
                                ),
                              ),
                              const PopupMenuItem(
                                value: 'delete',
                                child: Row(
                                  children: [
                                    Icon(Icons.delete_outline),
                                    SizedBox(width: 8),
                                    Text('Delete'),
                                  ],
                                ),
                              ),
                            ],
                          ),
                    onTap: provider.isLoading
                        ? null
                        : () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) =>
                                    DocumentViewerScreen(documentId: doc.id),
                              ),
                            );
                          },
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (ctx) =>
                  DocumentUploadScreen(projectId: widget.projectId),
            ),
          );
          // Refresh list after upload
          if (context.mounted) {
            context.read<DocumentProvider>().loadDocuments(widget.projectId);
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  /// Delete document with confirmation
  Future<void> _deleteDocument(BuildContext context, String documentId) async {
    final confirmed = await showDeleteConfirmationDialog(
      context: context,
      itemType: 'document',
      // No cascade message - documents don't have children
    );

    if (confirmed && context.mounted) {
      context.read<DocumentProvider>().deleteDocument(context, documentId);
    }
  }

}
