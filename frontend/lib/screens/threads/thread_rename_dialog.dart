/// Dialog for renaming a conversation thread.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/thread_provider.dart';

/// Dialog for renaming an existing thread
class ThreadRenameDialog extends StatefulWidget {
  const ThreadRenameDialog({
    super.key,
    required this.threadId,
    required this.currentTitle,
  });

  final String threadId;
  final String? currentTitle;

  @override
  State<ThreadRenameDialog> createState() => _ThreadRenameDialogState();
}

class _ThreadRenameDialogState extends State<ThreadRenameDialog> {
  late final TextEditingController _titleController;
  final _formKey = GlobalKey<FormState>();
  bool _isRenaming = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.currentTitle ?? '');
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _renameThread() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isRenaming = true);

    try {
      final provider = context.read<ThreadProvider>();
      final title = _titleController.text.trim();

      final result = await provider.renameThread(
        widget.threadId,
        title.isEmpty ? null : title,
      );

      if (mounted) {
        if (result != null) {
          Navigator.of(context).pop(true); // Return success
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Conversation renamed')),
          );
        } else {
          setState(() => _isRenaming = false);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(provider.error ?? 'Failed to rename conversation'),
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRenaming = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to rename: ${e.toString()}'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Rename Conversation'),
      content: Form(
        key: _formKey,
        child: TextFormField(
          controller: _titleController,
          decoration: const InputDecoration(
            labelText: 'Title',
            hintText: 'e.g., Login Flow Discussion',
            border: OutlineInputBorder(),
          ),
          maxLength: 255,
          autofocus: true,
          enabled: !_isRenaming,
          validator: (value) {
            if (value != null && value.length > 255) {
              return 'Title must be 255 characters or less';
            }
            return null;
          },
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isRenaming ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isRenaming ? null : _renameThread,
          child: _isRenaming
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Rename'),
        ),
      ],
    );
  }
}
