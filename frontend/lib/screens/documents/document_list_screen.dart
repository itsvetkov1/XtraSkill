import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:skeletonizer/skeletonizer.dart';

import '../../models/document.dart';
import '../../providers/document_provider.dart';
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
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.folder_open, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text(
                    'No documents uploaded',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Tap the + button to upload a document',
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
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
                      'Uploaded: ${_formatDate(doc.createdAt)}',
                      style: const TextStyle(fontSize: 12),
                    ),
                    trailing: const Icon(Icons.chevron_right),
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
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) =>
                  DocumentUploadScreen(projectId: widget.projectId),
            ),
          ).then((_) {
            // Refresh list after upload
            context.read<DocumentProvider>().loadDocuments(widget.projectId);
          });
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }
}
