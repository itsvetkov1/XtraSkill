/// Budget state management provider for token usage tracking.
library;

import 'package:flutter/foundation.dart';

import '../models/token_usage.dart';
import '../services/auth_service.dart';

/// Budget status based on usage percentage thresholds
enum BudgetStatus {
  /// Normal operation (0-79%)
  normal,

  /// Warning threshold reached (80-94%)
  warning,

  /// Urgent threshold reached (95-99%)
  urgent,

  /// Budget exhausted (100%+)
  exhausted,
}

/// Budget provider managing token usage state and threshold detection
///
/// Uses AuthService to fetch /auth/usage API data.
/// Per PITFALL-04: Uses API-provided token counts, not local estimates.
/// Per BUD-05: Exposes percentage only, no monetary amounts.
class BudgetProvider extends ChangeNotifier {
  /// Auth service for usage API calls
  final AuthService _authService;

  BudgetStatus _status = BudgetStatus.normal;
  int _percentage = 0;
  bool _loading = true;
  String? _error;

  BudgetProvider({AuthService? authService})
      : _authService = authService ?? AuthService() {
    // Auto-refresh on construction
    refresh();
  }

  /// Current budget status based on thresholds
  BudgetStatus get status => _status;

  /// Usage percentage (0-100)
  int get percentage => _percentage;

  /// Whether usage data is being loaded
  bool get loading => _loading;

  /// Error message if fetch failed
  String? get error => _error;

  /// Refresh budget data from API
  ///
  /// Fetches /auth/usage and updates status based on thresholds:
  /// - 0-79%: normal
  /// - 80-94%: warning
  /// - 95-99%: urgent
  /// - 100%+: exhausted
  Future<void> refresh() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final usageData = await _authService.getUsage();
      final usage = TokenUsage.fromJson(usageData);

      // Calculate percentage from API-provided costPercentage (0.0-1.0)
      // Per PITFALL-04: Use API data, not estimates
      _percentage = (usage.costPercentage * 100).round();

      // Determine status based on thresholds
      if (usage.costPercentage >= 1.0) {
        _status = BudgetStatus.exhausted;
      } else if (usage.costPercentage >= 0.95) {
        _status = BudgetStatus.urgent;
      } else if (usage.costPercentage >= 0.80) {
        _status = BudgetStatus.warning;
      } else {
        _status = BudgetStatus.normal;
      }

      _loading = false;
      _error = null;
    } catch (e) {
      _loading = false;
      _error = 'Failed to load budget: $e';
      // Keep previous status on error
    }

    notifyListeners();
  }
}
