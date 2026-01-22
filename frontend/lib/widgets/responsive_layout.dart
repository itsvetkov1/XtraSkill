/// Responsive layout utilities for cross-platform UI adaptation.
library;

import 'package:flutter/material.dart';

import '../core/config.dart';

/// Responsive layout widget that adapts UI based on screen width.
///
/// Supports three breakpoints:
/// - Mobile: width < 600 (phones)
/// - Tablet: 600 <= width < 900
/// - Desktop: width >= 900
///
/// Example:
/// ```dart
/// ResponsiveLayout(
///   mobile: MobileView(),
///   tablet: TabletView(), // Optional - falls back to mobile
///   desktop: DesktopView(),
/// )
/// ```
class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    required this.desktop,
  });

  /// Widget to display on mobile screens (< 600px)
  final Widget mobile;

  /// Widget to display on tablet screens (600-900px)
  /// If null, falls back to mobile widget
  final Widget? tablet;

  /// Widget to display on desktop screens (>= 900px)
  final Widget desktop;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= Breakpoints.tablet) {
          return desktop;
        }
        if (constraints.maxWidth >= Breakpoints.mobile) {
          return tablet ?? mobile;
        }
        return mobile;
      },
    );
  }
}

/// Utility functions for responsive design checks
extension ResponsiveContext on BuildContext {
  /// Check if current screen is mobile sized (< 600px)
  bool get isMobile {
    return MediaQuery.of(this).size.width < Breakpoints.mobile;
  }

  /// Check if current screen is tablet sized (600-900px)
  bool get isTablet {
    final width = MediaQuery.of(this).size.width;
    return width >= Breakpoints.mobile && width < Breakpoints.tablet;
  }

  /// Check if current screen is desktop sized (>= 900px)
  bool get isDesktop {
    return MediaQuery.of(this).size.width >= Breakpoints.tablet;
  }
}

/// Helper functions for responsive design (static methods)
class ResponsiveHelper {
  /// Check if screen width is mobile sized (< 600px)
  static bool isMobile(BuildContext context) {
    return MediaQuery.of(context).size.width < Breakpoints.mobile;
  }

  /// Check if screen width is tablet sized (600-900px)
  static bool isTablet(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    return width >= Breakpoints.mobile && width < Breakpoints.tablet;
  }

  /// Check if screen width is desktop sized (>= 900px)
  static bool isDesktop(BuildContext context) {
    return MediaQuery.of(context).size.width >= Breakpoints.tablet;
  }

  /// Get responsive padding based on screen size
  static EdgeInsets getResponsivePadding(BuildContext context) {
    if (isDesktop(context)) {
      return const EdgeInsets.all(32.0);
    } else if (isTablet(context)) {
      return const EdgeInsets.all(24.0);
    } else {
      return const EdgeInsets.all(16.0);
    }
  }

  /// Get responsive max width for content
  static double getMaxContentWidth(BuildContext context) {
    if (isDesktop(context)) {
      return 1200.0;
    } else if (isTablet(context)) {
      return 800.0;
    } else {
      return double.infinity;
    }
  }
}
