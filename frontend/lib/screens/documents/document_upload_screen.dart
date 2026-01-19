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

  Future<void> _pickAndUploadFile() async {
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

    setState(() {
      _uploading = true;
    });

    try {
      final provider = context.read<DocumentProvider>();
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
              const Text(
                'Only .txt and .md files are supported\nMaximum file size: 1MB',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey),
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
