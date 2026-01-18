/// Project state management provider.
library;

import 'package:flutter/foundation.dart';

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

  ProjectProvider({ProjectService? projectService})
      : _projectService = projectService ?? ProjectService();

  /// Get list of projects
  List<Project> get projects => _projects;

  /// Get selected project
  Project? get selectedProject => _selectedProject;

  /// Get loading state
  bool get loading => _loading;

  /// Get error message
  String? get error => _error;

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
  Future<void> selectProject(String id) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _selectedProject = await _projectService.getProject(id);
      _error = null;
    } catch (e) {
      _error = e.toString();
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

  /// Clear error message
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
