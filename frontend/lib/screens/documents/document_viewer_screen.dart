import 'dart:convert';
import 'dart:typed_data';

import 'package:file_saver/file_saver.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/document.dart';
import '../../providers/document_provider.dart';

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
    if (doc.content == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Document content not loaded')),
      );
      return;
    }

    try {
      final bytes = Uint8List.fromList(utf8.encode(doc.content!));
      final extension = doc.filename.contains('.')
          ? doc.filename.split('.').last
          : 'txt';
      final nameWithoutExt = doc.filename.replaceAll(RegExp(r'\.[^.]+$'), '');

      await FileSaver.instance.saveFile(
        name: nameWithoutExt,
        bytes: bytes,
        ext: extension,
        mimeType: MimeType.text,
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

    final content = provider.selectedDocument!.content ?? '';

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
