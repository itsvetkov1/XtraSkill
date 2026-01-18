import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Consumer<DocumentProvider>(
          builder: (context, provider, child) {
            return Text(
              provider.selectedDocument?.filename ?? 'Loading...',
            );
          },
        ),
      ),
      body: Consumer<DocumentProvider>(
        builder: (context, provider, child) {
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
                    onPressed: () =>
                        provider.selectDocument(widget.documentId),
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
        },
      ),
    );
  }
}
