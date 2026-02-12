import 'dart:convert';
import 'dart:typed_data';

import 'package:file_saver/file_saver.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/document.dart';
import '../../providers/document_provider.dart';
import '../../services/document_service.dart';
import 'widgets/excel_table_viewer.dart';
import 'widgets/pdf_text_viewer.dart';
import 'widgets/word_text_viewer.dart';

/// Screen for viewing document content.
///
/// Loads and displays decrypted document content.
/// Uses monospace font for better readability of code/markdown.
class DocumentViewerScreen extends StatefulWidget {
  final String documentId;

  const DocumentViewerScreen({super.key, required this.documentId});

  @override
  State<DocumentViewerScreen> createState() => _DocumentViewerScreenState();
}

class _DocumentViewerScreenState extends State<DocumentViewerScreen> {
  @override
  void initState() {
    super.initState();
    // Load document content when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DocumentProvider>().selectDocument(widget.documentId);
    });
  }

  @override
  void dispose() {
    // Clear selected document when leaving screen
    context.read<DocumentProvider>().clearSelectedDocument();
    super.dispose();
  }

  /// Download the document to user's device
  Future<void> _downloadDocument(Document doc) async {
    try {
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
        // Text format: encode content to bytes
        if (doc.content == null) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Document content not loaded')),
          );
          return;
        }
        bytes = Uint8List.fromList(utf8.encode(doc.content!));
        mimeType = MimeType.text;
      }

      await FileSaver.instance.saveFile(
        name: nameWithoutExt,
        bytes: bytes,
        ext: extension,
        mimeType: mimeType,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Downloaded ${doc.filename}'),
            action: SnackBarAction(label: 'OK', onPressed: () {}),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Download failed: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<DocumentProvider>(
      builder: (context, provider, child) {
        return Scaffold(
          appBar: AppBar(
            title: Text(provider.selectedDocument?.filename ?? 'Loading...'),
            actions: [
              if (provider.selectedDocument != null &&
                  provider.selectedDocument!.content != null)
                IconButton(
                  icon: const Icon(Icons.download),
                  tooltip: 'Download',
                  onPressed: () => _downloadDocument(provider.selectedDocument!),
                ),
            ],
          ),
          body: _buildBody(context, provider),
        );
      },
    );
  }

  Widget _buildBody(BuildContext context, DocumentProvider provider) {
    if (provider.loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (provider.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text('Error: ${provider.error}'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => provider.selectDocument(widget.documentId),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (provider.selectedDocument == null) {
      return const Center(child: Text('No document selected'));
    }

    return _buildDocumentContent(provider.selectedDocument!);
  }

  Widget _buildDocumentContent(Document doc) {
    final contentType = doc.contentType ?? 'text/plain';
    final content = doc.content ?? '';
    final metadata = doc.metadata ?? {};

    // Excel/CSV: table viewer with PlutoGrid
    if (contentType.contains('spreadsheet') || contentType == 'text/csv') {
      return ExcelTableViewer(
        content: content,
        metadata: metadata,
      );
    }

    // PDF: text viewer with page markers
    if (contentType == 'application/pdf') {
      return PdfTextViewer(
        content: content,
        metadata: metadata,
      );
    }

    // Word: structured paragraph viewer
    if (contentType.contains('wordprocessing')) {
      return WordTextViewer(
        content: content,
        metadata: metadata,
      );
    }

    // Default: plain text (existing behavior for .txt, .md)
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: SelectableText(
        content,
        style: const TextStyle(
          fontFamily: 'monospace',
          fontSize: 14,
          height: 1.5,
        ),
      ),
    );
  }
}
