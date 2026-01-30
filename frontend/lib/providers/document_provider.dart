import 'dart:async';
import 'package:flutter/material.dart';
import '../models/document.dart';
import '../services/document_service.dart';

/// Provider for document state management.
///
/// Manages documents list, selected document content, and upload progress.
class DocumentProvider extends ChangeNotifier {
  final DocumentService _service;

  List<Document> _documents = [];
  Document? _selectedDocument;
  bool _loading = false;
  String? _error;
  double _uploadProgress = 0.0;
  bool _uploading = false;

  /// Item pending deletion (during undo window)
  Document? _pendingDelete;

  /// Index where item was before removal (for restoration)
  int _pendingDeleteIndex = 0;

  /// Timer for deferred deletion
  Timer? _deleteTimer;

  DocumentProvider({DocumentService? service})
      : _service = service ?? DocumentService();

  // Getters
  List<Document> get documents => _documents;
  Document? get selectedDocument => _selectedDocument;
  bool get loading => _loading;
  bool get isLoading => _loading; // Alias for skeleton loader compatibility
  String? get error => _error;
  double get uploadProgress => _uploadProgress;
  bool get uploading => _uploading;

  /// Load documents for a project.
  Future<void> loadDocuments(String projectId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _documents = await _service.getDocuments(projectId);
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Upload a document to a project.
  ///
  /// Shows upload progress and adds document to list on success.
  Future<void> uploadDocument(
    String projectId,
    List<int> fileBytes,
    String filename,
  ) async {
    _uploading = true;
    _uploadProgress = 0.0;
    _error = null;
    notifyListeners();

    try {
      final document = await _service.uploadDocument(
        projectId,
        fileBytes,
        filename,
        onSendProgress: (sent, total) {
          _uploadProgress = sent / total;
          notifyListeners();
        },
      );

      // Add to documents list
      _documents.insert(0, document);
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _uploading = false;
      _uploadProgress = 0.0;
      notifyListeners();
    }
  }

  /// Load document content by ID.
  ///
  /// Sets [selectedDocument] with decrypted content.
  Future<void> selectDocument(String documentId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _selectedDocument = await _service.getDocumentContent(documentId);
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Clear selected document content.
  void clearSelectedDocument() {
    _selectedDocument = null;
    notifyListeners();
  }

  /// Clear error message.
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Search documents within a project.
  ///
  /// Returns search results without modifying documents list.
  Future<List<DocumentSearchResult>> searchDocuments(
    String projectId,
    String query,
  ) async {
    try {
      return await _service.searchDocuments(projectId, query);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// Delete document with optimistic UI and undo support
  ///
  /// Immediately removes from list, shows SnackBar with undo.
  /// Actual deletion happens after 10 seconds unless undone.
  Future<void> deleteDocument(BuildContext context, String documentId) async {
    // Find document in list
    final index = _documents.indexWhere((d) => d.id == documentId);
    if (index == -1) return;

    // Cancel any previous pending delete (commit it immediately)
    if (_pendingDelete != null) {
      await _commitPendingDelete();
    }

    // Remove optimistically
    _pendingDelete = _documents[index];
    _pendingDeleteIndex = index;
    _documents.removeAt(index);

    // Clear selected if it was the deleted document
    if (_selectedDocument?.id == documentId) {
      _selectedDocument = null;
    }

    notifyListeners();

    // Show undo SnackBar
    if (context.mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Document deleted'),
          duration: const Duration(seconds: 10),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: () => _undoDelete(),
          ),
        ),
      );
    }

    // Start deletion timer
    _deleteTimer?.cancel();
    _deleteTimer = Timer(const Duration(seconds: 10), () {
      _commitPendingDelete();
    });
  }

  void _undoDelete() {
    _deleteTimer?.cancel();
    if (_pendingDelete != null) {
      // Restore at original position (or start if index invalid)
      final insertIndex = _pendingDeleteIndex.clamp(0, _documents.length);
      _documents.insert(insertIndex, _pendingDelete!);
      _pendingDelete = null;
      notifyListeners();
    }
  }

  Future<void> _commitPendingDelete() async {
    if (_pendingDelete == null) return;

    final documentToDelete = _pendingDelete!;
    final originalIndex = _pendingDeleteIndex;
    _pendingDelete = null;

    try {
      await _service.deleteDocument(documentToDelete.id);
    } catch (e) {
      // Rollback: restore to list
      final insertIndex = originalIndex.clamp(0, _documents.length);
      _documents.insert(insertIndex, documentToDelete);
      _error = 'Failed to delete document: $e';
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _deleteTimer?.cancel();
    super.dispose();
  }
}
