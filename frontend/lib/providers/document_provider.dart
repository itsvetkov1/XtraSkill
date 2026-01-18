import 'package:flutter/foundation.dart';
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

  DocumentProvider({DocumentService? service})
      : _service = service ?? DocumentService();

  // Getters
  List<Document> get documents => _documents;
  Document? get selectedDocument => _selectedDocument;
  bool get loading => _loading;
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
    String filePath,
    String filename,
  ) async {
    _uploading = true;
    _uploadProgress = 0.0;
    _error = null;
    notifyListeners();

    try {
      final document = await _service.uploadDocument(
        projectId,
        filePath,
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
}
