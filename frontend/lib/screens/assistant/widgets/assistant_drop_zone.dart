/// Web-only drag-and-drop zone for file uploads in Assistant chat.
library;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_dropzone/flutter_dropzone.dart';

import '../../../providers/assistant_conversation_provider.dart';

/// Web-only wrapper that adds drag-and-drop file support around its child.
///
/// On web: Wraps child with a DropzoneView for file dropping with visual feedback.
/// On mobile: Returns child directly (no drag-drop on mobile — users use file picker).
class AssistantDropZone extends StatefulWidget {
  final Widget child;
  final Function(List<AttachedFile>) onFilesDropped;

  const AssistantDropZone({
    super.key,
    required this.child,
    required this.onFilesDropped,
  });

  @override
  State<AssistantDropZone> createState() => _AssistantDropZoneState();
}

class _AssistantDropZoneState extends State<AssistantDropZone> {
  DropzoneViewController? _dropzoneController;
  bool _isDragging = false;

  @override
  Widget build(BuildContext context) {
    // Mobile: no drag-drop support, return child directly
    if (!kIsWeb) {
      return widget.child;
    }

    // Web: enable drag-and-drop
    final theme = Theme.of(context);
    final primaryColor = theme.colorScheme.primary;

    return Stack(
      children: [
        // Invisible dropzone covering entire area
        Positioned.fill(
          child: DropzoneView(
            operation: DragOperation.copy,
            cursor: CursorType.grab,
            onCreated: (ctrl) => _dropzoneController = ctrl,
            onDropFile: _handleDrop,
            onHover: () {
              setState(() => _isDragging = true);
            },
            onLeave: () {
              setState(() => _isDragging = false);
            },
          ),
        ),

        // Actual content
        widget.child,

        // Drag overlay with visual feedback
        if (_isDragging)
          Positioned.fill(
            child: Container(
              color: primaryColor.withValues(alpha: 0.1),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.cloud_upload_outlined,
                      size: 48,
                      color: primaryColor,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Drop files here',
                      style: TextStyle(
                        fontSize: 16,
                        color: primaryColor,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  Future<void> _handleDrop(dynamic event) async {
    setState(() => _isDragging = false);

    if (_dropzoneController == null) return;

    try {
      // Extract file data from the drop event
      final name = await _dropzoneController!.getFilename(event);
      final size = await _dropzoneController!.getFileSize(event);
      final bytes = await _dropzoneController!.getFileData(event);
      final mime = await _dropzoneController!.getFileMIME(event);

      // Create AttachedFile and notify parent
      final file = AttachedFile(
        name: name,
        size: size,
        bytes: bytes,
        contentType: mime,
      );

      widget.onFilesDropped([file]);
    } catch (e) {
      debugPrint('Error handling dropped file: $e');
    }
  }
}
