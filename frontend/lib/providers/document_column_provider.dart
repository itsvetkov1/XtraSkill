/// Document column state management provider.
library;

import 'package:flutter/material.dart';

/// Provider for document column expanded/collapsed state.
///
/// Manages session-scoped state for the collapsible documents column.
/// Unlike NavigationProvider, this does NOT persist across app restarts
/// (requirement: "within session" state only).
///
/// Default state: collapsed (LAYOUT-03 requirement)
class DocumentColumnProvider extends ChangeNotifier {
  /// Current expanded state (true = expanded, false = collapsed)
  bool _isExpanded = false;

  /// Whether the document column is currently expanded
  bool get isExpanded => _isExpanded;

  /// Toggle between expanded and collapsed states
  void toggle() {
    _isExpanded = !_isExpanded;
    notifyListeners();
  }

  /// Expand the column if currently collapsed
  ///
  /// Only notifies listeners if state actually changes.
  void expand() {
    if (!_isExpanded) {
      _isExpanded = true;
      notifyListeners();
    }
  }

  /// Collapse the column if currently expanded
  ///
  /// Only notifies listeners if state actually changes.
  void collapse() {
    if (_isExpanded) {
      _isExpanded = false;
      notifyListeners();
    }
  }
}
