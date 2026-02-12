import 'dart:convert';
import 'dart:typed_data';

import 'package:file_saver/file_saver.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:skeletonizer/skeletonizer.dart';

import '../../models/document.dart';
import '../../providers/document_provider.dart';
import '../../services/document_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../../widgets/empty_state.dart';
import 'document_upload_screen.dart';

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

  /// Get format-specific icon for document
  IconData _getDocumentIcon(Document doc) {
    final ct = doc.contentType ?? 'text/plain';
    if (ct.contains('spreadsheet') || ct == 'text/csv') return Icons.table_chart;
    if (ct == 'application/pdf') return Icons.picture_as_pdf;
    if (ct.contains('wordprocessing')) return Icons.article;
    return Icons.description;
  }

  /// Get format-specific subtitle hint
  String _getDocumentSubtitle(Document doc) {
    final dateStr = 'Uploaded ${DateFormatter.format(doc.createdAt)}';
    final metadata = doc.metadata;

    if (metadata != null) {
      if (doc.isTableFormat) {
        final rowCount = metadata['total_rows'] ?? metadata['row_count'];
        if (rowCount != null) {
          return '$dateStr • $rowCount rows';
        }
      } else if (doc.contentType == 'application/pdf') {
        final pageCount = metadata['page_count'];
        if (pageCount != null) {
          return '$dateStr • $pageCount pages';
        }
      }
    }

    return dateStr;
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
                    leading: Icon(_getDocumentIcon(doc), size: 40),
                    title: Text(doc.filename),
                    subtitle: Text(
                      _getDocumentSubtitle(doc),
                      style: const TextStyle(fontSize: 12),
                    ),
                    trailing: provider.isLoading
                        ? const Icon(Icons.chevron_right)
                        : PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'view') {
                                context.push('/projects/${widget.projectId}/documents/${doc.id}');
                              } else if (value == 'download') {
                                _downloadDocument(context, doc);
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
                                value: 'download',
                                child: Row(
                                  children: [
                                    Icon(Icons.download),
                                    SizedBox(width: 8),
                                    Text('Download'),
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
                            context.push('/projects/${widget.projectId}/documents/${doc.id}');
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

  /// Download document - fetches content first if needed
  Future<void> _downloadDocument(BuildContext context, Document doc) async {
    try {
      // Show loading indicator
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              SizedBox(width: 16),
              Text('Preparing download...'),
            ],
          ),
          duration: Duration(seconds: 30), // Will be dismissed on completion
        ),
      );

      final extension = doc.filename.contains('.')
          ? doc.filename.split('.').last
          : 'txt';
      final nameWithoutExt = doc.filename.replaceAll(RegExp(r'\.[^.]+$'), '');

      Uint8List bytes;
      MimeType mimeType;

      if (doc.isRichFormat) {
        // Rich format: download original binary via download endpoint
        final service = DocumentService();
        final downloadedBytes = await service.downloadDocument(doc.id);
        bytes = Uint8List.fromList(downloadedBytes);

        // Determine MIME type based on extension
        if (extension == 'xlsx') {
          mimeType = MimeType.microsoftExcel;
        } else if (extension == 'csv') {
          mimeType = MimeType.csv;
        } else if (extension == 'pdf') {
          mimeType = MimeType.pdf;
        } else if (extension == 'docx') {
          mimeType = MimeType.microsoftWord;
        } else {
          mimeType = MimeType.other;
        }
      } else {
        // Text format: fetch content first
        final provider = context.read<DocumentProvider>();
        await provider.selectDocument(doc.id);

        if (!mounted) return;

        final loadedDoc = provider.selectedDocument;
        if (loadedDoc == null || loadedDoc.content == null) {
          ScaffoldMessenger.of(context).clearSnackBars();
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to load document content')),
          );
          return;
        }

        bytes = Uint8List.fromList(utf8.encode(loadedDoc.content!));
        mimeType = MimeType.text;

        // Clear the selected document (we just needed it for download)
        provider.clearSelectedDocument();
      }

      await FileSaver.instance.saveFile(
        name: nameWithoutExt,
        bytes: bytes,
        ext: extension,
        mimeType: mimeType,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).clearSnackBars();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Downloaded ${doc.filename}'),
            action: SnackBarAction(label: 'OK', onPressed: () {}),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).clearSnackBars();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Download failed: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
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
