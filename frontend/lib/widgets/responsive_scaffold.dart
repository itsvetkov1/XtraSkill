/// Responsive scaffold widget for authenticated routes.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/config.dart';
import '../providers/auth_provider.dart';
import '../providers/navigation_provider.dart';

/// Responsive scaffold shell widget that wraps all authenticated routes
///
/// Provides persistent navigation across all screens with responsive behavior:
/// - Desktop (>=900px): NavigationRail always visible, extended/collapsed based on user preference
/// - Tablet (600-899px): NavigationRail collapsed (icons only)
/// - Mobile (<600px): AppBar with hamburger menu opening Drawer
///
/// Usage in StatefulShellRoute:
/// ```dart
/// StatefulShellRoute.indexedStack(
///   builder: (context, state, navigationShell) => ResponsiveScaffold(
///     child: navigationShell,
///     currentIndex: navigationShell.currentIndex,
///     onDestinationSelected: (index) => navigationShell.goBranch(index),
///   ),
///   branches: [...]
/// )
/// ```
class ResponsiveScaffold extends StatelessWidget {
  const ResponsiveScaffold({
    super.key,
    required this.child,
    required this.currentIndex,
    required this.onDestinationSelected,
  });

  /// The current route's content (typically StatefulNavigationShell)
  final Widget child;

  /// Currently selected navigation destination index
  final int currentIndex;

  /// Callback when user selects a navigation destination
  final Function(int) onDestinationSelected;

  /// Navigation destinations shared between NavigationRail and Drawer
  static const List<_NavigationDestination> _destinations = [
    _NavigationDestination(
      icon: Icons.home_outlined,
      selectedIcon: Icons.home,
      label: 'Home',
    ),
    _NavigationDestination(
      icon: Icons.folder_outlined,
      selectedIcon: Icons.folder,
      label: 'Projects',
    ),
    _NavigationDestination(
      icon: Icons.settings_outlined,
      selectedIcon: Icons.settings,
      label: 'Settings',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Desktop: NavigationRail extended or collapsed based on user preference
        if (constraints.maxWidth >= Breakpoints.tablet) {
          return _DesktopLayout(
            currentIndex: currentIndex,
            onDestinationSelected: onDestinationSelected,
            destinations: _destinations,
            child: child,
          );
        }

        // Tablet: NavigationRail collapsed (icons only)
        if (constraints.maxWidth >= Breakpoints.mobile) {
          return _TabletLayout(
            currentIndex: currentIndex,
            onDestinationSelected: onDestinationSelected,
            destinations: _destinations,
            child: child,
          );
        }

        // Mobile: AppBar with hamburger menu opening Drawer
        return _MobileLayout(
          currentIndex: currentIndex,
          onDestinationSelected: onDestinationSelected,
          destinations: _destinations,
          child: child,
        );
      },
    );
  }
}

/// Internal class for navigation destination data
class _NavigationDestination {
  const _NavigationDestination({
    required this.icon,
    required this.selectedIcon,
    required this.label,
  });

  final IconData icon;
  final IconData selectedIcon;
  final String label;
}

/// Desktop layout with NavigationRail (extended/collapsed based on preference)
class _DesktopLayout extends StatelessWidget {
  const _DesktopLayout({
    required this.child,
    required this.currentIndex,
    required this.onDestinationSelected,
    required this.destinations,
  });

  final Widget child;
  final int currentIndex;
  final Function(int) onDestinationSelected;
  final List<_NavigationDestination> destinations;

  @override
  Widget build(BuildContext context) {
    return Consumer<NavigationProvider>(
      builder: (context, navProvider, _) {
        final isExtended = navProvider.isSidebarExpanded;

        return Scaffold(
          body: Row(
            children: [
              // NavigationRail
              NavigationRail(
                extended: isExtended,
                minExtendedWidth: 250,
                backgroundColor:
                    Theme.of(context).colorScheme.surfaceContainerLow,
                selectedIndex: currentIndex,
                onDestinationSelected: (index) => onDestinationSelected(index),
                // Must be none when extended to prevent assertion error
                labelType: NavigationRailLabelType.none,
                // Leading: App branding
                leading: _NavigationRailHeader(isExtended: isExtended),
                // Trailing: Expand/collapse toggle (desktop only)
                trailing: Expanded(
                  child: Align(
                    alignment: Alignment.bottomCenter,
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 16.0),
                      child: IconButton(
                        icon: Icon(
                          isExtended
                              ? Icons.chevron_left
                              : Icons.chevron_right,
                        ),
                        tooltip:
                            isExtended ? 'Collapse sidebar' : 'Expand sidebar',
                        onPressed: () => navProvider.toggleSidebar(),
                      ),
                    ),
                  ),
                ),
                destinations: destinations
                    .map(
                      (d) => NavigationRailDestination(
                        icon: Icon(d.icon),
                        selectedIcon: Icon(d.selectedIcon),
                        label: Text(d.label),
                      ),
                    )
                    .toList(),
              ),
              // Vertical divider
              const VerticalDivider(thickness: 1, width: 1),
              // Main content
              Expanded(child: child),
            ],
          ),
        );
      },
    );
  }
}

/// Tablet layout with collapsed NavigationRail (icons only)
class _TabletLayout extends StatelessWidget {
  const _TabletLayout({
    required this.child,
    required this.currentIndex,
    required this.onDestinationSelected,
    required this.destinations,
  });

  final Widget child;
  final int currentIndex;
  final Function(int) onDestinationSelected;
  final List<_NavigationDestination> destinations;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // Collapsed NavigationRail (icons only with labels below)
          NavigationRail(
            extended: false,
            backgroundColor: Theme.of(context).colorScheme.surfaceContainerLow,
            selectedIndex: currentIndex,
            onDestinationSelected: (index) => onDestinationSelected(index),
            // Show labels below icons when collapsed
            labelType: NavigationRailLabelType.all,
            // Leading: App icon only (no text)
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 16.0),
              child: Icon(
                Icons.analytics_outlined,
                size: 32,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            destinations: destinations
                .map(
                  (d) => NavigationRailDestination(
                    icon: Icon(d.icon),
                    selectedIcon: Icon(d.selectedIcon),
                    label: Text(d.label),
                  ),
                )
                .toList(),
          ),
          // Vertical divider
          const VerticalDivider(thickness: 1, width: 1),
          // Main content
          Expanded(child: child),
        ],
      ),
    );
  }
}

/// Mobile layout with AppBar and hamburger menu opening Drawer
class _MobileLayout extends StatelessWidget {
  const _MobileLayout({
    required this.child,
    required this.currentIndex,
    required this.onDestinationSelected,
    required this.destinations,
  });

  final Widget child;
  final int currentIndex;
  final Function(int) onDestinationSelected;
  final List<_NavigationDestination> destinations;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BA Assistant'),
      ),
      drawer: _NavigationDrawer(
        currentIndex: currentIndex,
        onDestinationSelected: onDestinationSelected,
        destinations: destinations,
      ),
      body: child,
    );
  }
}

/// NavigationRail header with app branding and user email
class _NavigationRailHeader extends StatelessWidget {
  const _NavigationRailHeader({required this.isExtended});

  final bool isExtended;

  @override
  Widget build(BuildContext context) {
    if (!isExtended) {
      // Collapsed: Just the icon
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 16.0),
        child: Icon(
          Icons.analytics_outlined,
          size: 32,
          color: Theme.of(context).colorScheme.primary,
        ),
      );
    }

    // Extended: Icon, title, and user email
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.analytics_outlined,
            size: 40,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 12),
          Text(
            'BA Assistant',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 4),
          Consumer<AuthProvider>(
            builder: (context, authProvider, child) {
              return Text(
                authProvider.email ?? 'User',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                overflow: TextOverflow.ellipsis,
              );
            },
          ),
        ],
      ),
    );
  }
}

/// Navigation drawer for mobile layout
class _NavigationDrawer extends StatelessWidget {
  const _NavigationDrawer({
    required this.currentIndex,
    required this.onDestinationSelected,
    required this.destinations,
  });

  final int currentIndex;
  final Function(int) onDestinationSelected;
  final List<_NavigationDestination> destinations;

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          // Drawer header with app branding
          DrawerHeader(
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Icon(
                  Icons.analytics_outlined,
                  size: 48,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
                const SizedBox(height: 12),
                Text(
                  'BA Assistant',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: Theme.of(context).colorScheme.onPrimaryContainer,
                      ),
                ),
                const SizedBox(height: 4),
                Consumer<AuthProvider>(
                  builder: (context, authProvider, child) {
                    return Text(
                      authProvider.email ?? 'User',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color:
                                Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                    );
                  },
                ),
              ],
            ),
          ),
          // Navigation items
          ...destinations.asMap().entries.map((entry) {
            final index = entry.key;
            final destination = entry.value;
            final isSelected = index == currentIndex;

            return ListTile(
              leading: Icon(
                isSelected ? destination.selectedIcon : destination.icon,
              ),
              title: Text(destination.label),
              selected: isSelected,
              onTap: () {
                // Close drawer first
                Navigator.pop(context);
                // Then navigate
                onDestinationSelected(index);
              },
            );
          }),
        ],
      ),
    );
  }
}
