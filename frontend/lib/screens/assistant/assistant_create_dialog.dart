/// Dialog for creating a new Assistant conversation thread.
library;

import 'package:flutter/material.dart';

import '../../models/thread.dart';
import '../../services/thread_service.dart';

/// Dialog for creating a new Assistant thread (simplified, project-less)
class AssistantCreateDialog extends StatefulWidget {
  const AssistantCreateDialog({super.key});

  /// Static show method for consistency with other dialogs
  static Future<Thread?> show(BuildContext context) {
    return showDialog<Thread>(
      context: context,
      builder: (context) => const AssistantCreateDialog(),
    );
  }

  @override
  State<AssistantCreateDialog> createState() => _AssistantCreateDialogState();
}

class _AssistantCreateDialogState extends State<AssistantCreateDialog> {
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isCreating = false;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _createThread() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isCreating = true);

    try {
      final threadService = ThreadService();
      final thread = await threadService.createAssistantThread(
        title: _titleController.text.trim(),
        description: _descriptionController.text.trim().isEmpty
            ? null
            : _descriptionController.text.trim(),
      );

      if (mounted) {
        Navigator.of(context).pop(thread); // Return thread to caller
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isCreating = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to create conversation: ${e.toString()}'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('New Conversation'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Title',
                hintText: 'e.g., Debug CSS Layout',
                border: OutlineInputBorder(),
              ),
              maxLength: 255,
              autofocus: true,
              enabled: !_isCreating,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Title is required';
                }
                if (value.length > 255) {
                  return 'Title must be 255 characters or less';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _descriptionController,
              decoration: const InputDecoration(
                labelText: 'Description (optional)',
                hintText: 'Optional details about this conversation',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
              enabled: !_isCreating,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isCreating ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isCreating ? null : _createThread,
          child: _isCreating
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Create'),
        ),
      ],
    );
  }
}
