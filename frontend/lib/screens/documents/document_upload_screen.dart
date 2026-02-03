import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../../providers/document_provider.dart';

/// Screen for uploading documents to a project.
///
/// Uses file_picker for cross-platform file selection.
/// Shows upload progress during file upload.
class DocumentUploadScreen extends StatefulWidget {
  final String projectId;

  const DocumentUploadScreen({super.key, required this.projectId});

  @override
  State<DocumentUploadScreen> createState() => _DocumentUploadScreenState();
}

class _DocumentUploadScreenState extends State<DocumentUploadScreen> {
  bool _uploading = false;

  /// Maximum file size in bytes (1MB)
  static const int _maxFileSizeBytes = 1024 * 1024;

  /// Formats file size in human-readable format
  String _formatFileSize(int bytes) {
    if (bytes < 1024) {
      return '$bytes B';
    } else if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    } else {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
  }

  /// Shows file size error dialog with actual size and limit
  void _showFileSizeError(int actualSize) {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        icon: const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 48),
        title: const Text('File too large'),
        content: Text(
          'The selected file is ${_formatFileSize(actualSize)}.\n\n'
          'Maximum file size is 1MB.\n\n'
          'Please select a smaller file.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(dialogContext);
              _pickAndUploadFile();  // Let user immediately select another file
            },
            child: const Text('Select Different File'),
          ),
        ],
      ),
    );
  }

  Future<void> _pickAndUploadFile() async {
    // Get provider reference BEFORE async gap
    final provider = context.read<DocumentProvider>();

    // Pick file with type filter (only .txt and .md)
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['txt', 'md'],
    );

    if (result == null) return;

    final file = result.files.single;
    if (file.bytes == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('File data not available')),
        );
      }
      return;
    }

    // VALIDATE FILE SIZE IMMEDIATELY (PITFALL-09: before any upload UI)
    final fileSize = file.bytes!.length;
    if (fileSize > _maxFileSizeBytes) {
      if (mounted) {
        _showFileSizeError(fileSize);
      }
      return;  // Stop here - user can select another file
    }

    // Only proceed to upload if validation passes
    setState(() {
      _uploading = true;
    });

    try {
      await provider.uploadDocument(
        widget.projectId,
        file.bytes!,
        file.name,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Document uploaded successfully'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Upload failed: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _uploading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Document'),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.cloud_upload,
                size: 100,
                color: Colors.blue,
              ),
              const SizedBox(height: 32),
              const Text(
                'Upload a text document',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              Column(
                children: [
                  const Text(
                    'Only .txt and .md files are supported',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.info_outline,
                          size: 16,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Maximum file size: 1MB',
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              Consumer<DocumentProvider>(
                builder: (context, provider, child) {
                  if (provider.uploading) {
                    return Column(
                      children: [
                        LinearProgressIndicator(
                          value: provider.uploadProgress,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          '${(provider.uploadProgress * 100).toInt()}% uploaded',
                          style: const TextStyle(fontSize: 16),
                        ),
                      ],
                    );
                  }

                  return ElevatedButton.icon(
                    onPressed: _uploading ? null : _pickAndUploadFile,
                    icon: const Icon(Icons.file_upload),
                    label: const Text('Select File'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 32,
                        vertical: 16,
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}
