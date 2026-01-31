/// Dialog for creating a new conversation thread.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/provider_provider.dart';
import '../../providers/thread_provider.dart';

/// Dialog for creating a new thread in a project
class ThreadCreateDialog extends StatefulWidget {
  const ThreadCreateDialog({
    super.key,
    required this.projectId,
  });

  final String projectId;

  @override
  State<ThreadCreateDialog> createState() => _ThreadCreateDialogState();
}

class _ThreadCreateDialogState extends State<ThreadCreateDialog> {
  final _titleController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isCreating = false;

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _createThread() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isCreating = true);

    try {
      final threadProvider = context.read<ThreadProvider>();
      final providerProvider = context.read<ProviderProvider>();
      final title = _titleController.text.trim();

      // Create thread with title and current default LLM provider
      await threadProvider.createThread(
        widget.projectId,
        title.isEmpty ? null : title,
        provider: providerProvider.selectedProvider,
      );

      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Conversation created')),
        );
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
                labelText: 'Title (optional)',
                hintText: 'e.g., Login Flow Discussion',
                border: OutlineInputBorder(),
              ),
              maxLength: 255,
              autofocus: true,
              enabled: !_isCreating,
              validator: (value) {
                if (value != null && value.length > 255) {
                  return 'Title must be 255 characters or less';
                }
                return null;
              },
            ),
            const SizedBox(height: 8),
            Text(
              'Leave title empty for untitled conversations',
              style: Theme.of(context).textTheme.bodySmall,
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
