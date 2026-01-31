/// Project state management provider.
library;

import 'dart:async';
import 'package:flutter/material.dart';

import '../models/project.dart';
import '../services/project_service.dart';

/// Project provider managing project state and API operations
class ProjectProvider extends ChangeNotifier {
  /// Project service for API calls
  final ProjectService _projectService;

  /// List of user's projects
  List<Project> _projects = [];

  /// Currently selected project with details loaded
  Project? _selectedProject;

  /// Loading state for async operations
  bool _loading = false;

  /// Error message if operation failed
  String? _error;

  /// Whether the selected project was not found (404)
  bool _isNotFound = false;

  /// Item pending deletion (during undo window)
  Project? _pendingDelete;

  /// Index where item was before removal (for restoration)
  int _pendingDeleteIndex = 0;

  /// Timer for deferred deletion
  Timer? _deleteTimer;

  ProjectProvider({ProjectService? projectService})
      : _projectService = projectService ?? ProjectService();

  /// Get list of projects
  List<Project> get projects => _projects;

  /// Get selected project
  Project? get selectedProject => _selectedProject;

  /// Get loading state
  bool get loading => _loading;

  /// Get loading state (alias for skeleton loader compatibility)
  bool get isLoading => _loading;

  /// Get error message
  String? get error => _error;

  /// Get not-found state - true when API returned 404
  bool get isNotFound => _isNotFound;

  /// Load all projects for current user
  ///
  /// Fetches projects from API and updates state.
  /// Sets loading state and handles errors.
  Future<void> loadProjects() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _projects = await _projectService.getProjects();
      _error = null;
    } catch (e) {
      _error = e.toString();
      _projects = [];
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Create a new project
  ///
  /// Args:
  ///   name: Project name (required)
  ///   description: Optional project description
  ///
  /// Adds created project to list and returns it.
  Future<Project?> createProject(String name, String? description) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final project = await _projectService.createProject(name, description);
      _projects.insert(0, project); // Add to start (most recent)
      _error = null;
      return project;
    } catch (e) {
      _error = e.toString();
      return null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Select and load project details
  ///
  /// Args:
  ///   id: Project UUID
  ///
  /// Loads project with documents and threads from API.
  /// Sets isNotFound=true if project doesn't exist (404).
  Future<void> selectProject(String id) async {
    _loading = true;
    _error = null;
    _isNotFound = false; // Reset on new selection
    notifyListeners();

    try {
      _selectedProject = await _projectService.getProject(id);
      _error = null;
    } catch (e) {
      final errorMessage = e.toString();
      // Check if it's a 404 "not found" error (from project_service.dart)
      if (errorMessage.contains('not found') ||
          errorMessage.contains('404')) {
        _isNotFound = true;
        _error = null; // Not a "real" error, just not found
      } else {
        _error = errorMessage;
        _isNotFound = false;
      }
      _selectedProject = null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Update project name and description
  ///
  /// Args:
  ///   id: Project UUID
  ///   name: Updated project name
  ///   description: Updated project description
  ///
  /// Updates project in list and selected project if applicable.
  Future<Project?> updateProject(
    String id,
    String name,
    String? description,
  ) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final updatedProject =
          await _projectService.updateProject(id, name, description);

      // Update in projects list
      final index = _projects.indexWhere((p) => p.id == id);
      if (index != -1) {
        _projects[index] = updatedProject;
      }

      // Update selected project if it's the same one
      if (_selectedProject?.id == id) {
        _selectedProject = updatedProject;
      }

      _error = null;
      return updatedProject;
    } catch (e) {
      _error = e.toString();
      return null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Clear selected project
  void clearSelection() {
    _selectedProject = null;
    notifyListeners();
  }

  /// Clear error message and not-found state
  void clearError() {
    _error = null;
    _isNotFound = false;
    notifyListeners();
  }

  /// Delete project with optimistic UI and undo support
  ///
  /// Immediately removes from list, shows SnackBar with undo.
  /// Actual deletion happens after 10 seconds unless undone.
  Future<void> deleteProject(BuildContext context, String projectId) async {
    // Find project in list
    final index = _projects.indexWhere((p) => p.id == projectId);
    if (index == -1) return;

    // Cancel any previous pending delete (commit it immediately)
    if (_pendingDelete != null) {
      await _commitPendingDelete();
    }

    // Remove optimistically
    _pendingDelete = _projects[index];
    _pendingDeleteIndex = index;
    _projects.removeAt(index);

    // Clear selected if it was the deleted project
    if (_selectedProject?.id == projectId) {
      _selectedProject = null;
    }

    notifyListeners();

    // Show undo SnackBar
    if (context.mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Project deleted'),
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
      final insertIndex = _pendingDeleteIndex.clamp(0, _projects.length);
      _projects.insert(insertIndex, _pendingDelete!);
      _pendingDelete = null;
      notifyListeners();
    }
  }

  Future<void> _commitPendingDelete() async {
    if (_pendingDelete == null) return;

    final projectToDelete = _pendingDelete!;
    final originalIndex = _pendingDeleteIndex;
    _pendingDelete = null;

    try {
      await _projectService.deleteProject(projectToDelete.id);
    } catch (e) {
      // Rollback: restore to list
      final insertIndex = originalIndex.clamp(0, _projects.length);
      _projects.insert(insertIndex, projectToDelete);
      _error = 'Failed to delete project: $e';
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _deleteTimer?.cancel();
    super.dispose();
  }
}
