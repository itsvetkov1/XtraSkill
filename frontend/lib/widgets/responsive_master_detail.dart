/// Responsive master-detail layout widget.
library;

import 'package:flutter/material.dart';

import '../core/config.dart';

/// Responsive master-detail layout that adapts between mobile and desktop
///
/// Mobile (<600px): Shows master list, taps navigate to detail screen
/// Desktop (>=600px): Shows split view with master on left, detail on right
///
/// Example:
/// ```dart
/// ResponsiveMasterDetail(
///   masterBuilder: (context, onSelect) => ProjectListView(onSelect: onSelect),
///   detailBuilder: (context) => ProjectDetailView(),
///   selectedId: currentProjectId,
/// )
/// ```
class ResponsiveMasterDetail extends StatelessWidget {
  const ResponsiveMasterDetail({
    super.key,
    required this.masterBuilder,
    required this.detailBuilder,
    this.selectedId,
    this.masterWidth = 300.0,
  });

  /// Builder for master list (left side on desktop)
  /// Receives onSelect callback to notify of item selection
  final Widget Function(BuildContext context, Function(String) onSelect)
      masterBuilder;

  /// Builder for detail view (right side on desktop, separate screen on mobile)
  final Widget Function(BuildContext context) detailBuilder;

  /// Currently selected item ID
  final String? selectedId;

  /// Width of master panel on desktop (default 300px)
  final double masterWidth;

  @override
  Widget build(BuildContext context) {
    final isDesktop =
        MediaQuery.of(context).size.width >= Breakpoints.tablet;

    if (isDesktop) {
      // Desktop: Split view
      return Row(
        children: [
          // Master panel (fixed width)
          SizedBox(
            width: masterWidth,
            child: masterBuilder(context, (id) {
              // On desktop, selection updates state but doesn't navigate
              // Parent widget handles state update
            }),
          ),
          // Divider
          const VerticalDivider(width: 1),
          // Detail panel (flexible width)
          Expanded(
            child: selectedId != null
                ? detailBuilder(context)
                : const Center(
                    child: Text('Select an item to view details'),
                  ),
          ),
        ],
      );
    } else {
      // Mobile: Master only (detail shown via navigation)
      return masterBuilder(context, (id) {
        // On mobile, selection navigates to detail screen
        // Parent widget handles navigation
      });
    }
  }
}
