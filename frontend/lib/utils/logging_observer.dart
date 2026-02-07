/// Navigation observer for go_router route tracking.
///
/// Logs all navigation events (push, pop, replace) to LoggingService
/// for comprehensive user journey tracking.
library;

import 'package:flutter/material.dart';

import '../services/logging_service.dart';

/// Custom NavigatorObserver that logs route changes to LoggingService
class LoggingNavigatorObserver extends NavigatorObserver {
  /// LoggingService instance for logging navigation events
  final LoggingService _loggingService = LoggingService();

  @override
  void didPush(Route route, Route? previousRoute) {
    super.didPush(route, previousRoute);
    if (route.settings.name != null) {
      _loggingService.logNavigation('Navigated to ${route.settings.name}');
    }
  }

  @override
  void didPop(Route route, Route? previousRoute) {
    super.didPop(route, previousRoute);
    if (previousRoute?.settings.name != null) {
      _loggingService
          .logNavigation('Returned to ${previousRoute!.settings.name}');
    }
  }

  @override
  void didReplace({Route? newRoute, Route? oldRoute}) {
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
    if (newRoute?.settings.name != null) {
      _loggingService
          .logNavigation('Replaced with ${newRoute!.settings.name}');
    }
  }
}
