/// Skill browser bottom sheet for selecting skills.
library;

import 'package:flutter/material.dart';
import 'package:skeletonizer/skeletonizer.dart';

import '../../../models/skill.dart';
import '../../../services/skill_service.dart';
import '../../../widgets/responsive_layout.dart';
import 'skill_card.dart';

/// A bottom sheet that displays all available skills in a responsive grid.
///
/// Opens as a draggable modal bottom sheet (50%-90% height) with:
/// - Loading state: Skeleton cards
/// - Error state: Friendly message + retry button
/// - Empty state: "No skills available"
/// - Success state: Responsive grid of skill cards (3/2/1 columns)
class SkillBrowserSheet extends StatefulWidget {
  const SkillBrowserSheet({super.key});

  /// Show the skill browser as a modal bottom sheet
  ///
  /// Returns the selected [Skill] or null if dismissed without selection.
  static Future<Skill?> show(BuildContext context) {
    return showModalBottomSheet<Skill>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (sheetContext) => const SkillBrowserSheet(),
    );
  }

  @override
  State<SkillBrowserSheet> createState() => _SkillBrowserSheetState();
}

class _SkillBrowserSheetState extends State<SkillBrowserSheet> {
  final SkillService _skillService = SkillService();

  List<Skill>? _skills;
  bool _isLoading = true;
  String? _error;
  int? _selectedIndex;

  @override
  void initState() {
    super.initState();
    _loadSkills();
  }

  /// Load skills from the API
  Future<void> _loadSkills() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final skills = await _skillService.getSkills();
      if (mounted) {
        setState(() {
          _skills = skills;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Couldn\'t load skills';
          _isLoading = false;
        });
      }
    }
  }

  /// Handle skill selection with highlight animation
  Future<void> _handleSelection(Skill skill, int index) async {
    // Guard against double-tap
    if (_selectedIndex != null) return;

    setState(() => _selectedIndex = index);

    // Brief highlight before closing
    await Future.delayed(const Duration(milliseconds: 300));

    if (mounted) {
      Navigator.pop(context, skill);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.5,
      minChildSize: 0.3,
      maxChildSize: 0.9,
      expand: false,
      builder: (context, scrollController) {
        return Column(
          children: [
            _buildHeader(context),
            Expanded(child: _buildBody(context, scrollController)),
          ],
        );
      },
    );
  }

  /// Build sheet header with drag handle and title
  Widget _buildHeader(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Drag handle
        const SizedBox(height: 8),
        Container(
          width: 40,
          height: 4,
          decoration: BoxDecoration(
            color: theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.4),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(height: 12),

        // Title
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Text(
                'Choose a Skill',
                style: theme.textTheme.titleLarge,
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // Divider
        const Divider(height: 1),
      ],
    );
  }

  /// Build sheet body based on current state
  Widget _buildBody(BuildContext context, ScrollController scrollController) {
    if (_isLoading) {
      return _buildLoadingState(scrollController);
    }

    if (_error != null) {
      return _buildErrorState(context);
    }

    if (_skills == null || _skills!.isEmpty) {
      return _buildEmptyState(context);
    }

    return _buildGrid(_skills!, scrollController);
  }

  /// Build loading state with skeleton cards
  Widget _buildLoadingState(ScrollController scrollController) {
    final dummySkill = Skill(
      name: 'Loading Skill',
      description: 'Loading description text for the skill card',
      features: [
        'Feature one',
        'Feature two',
        'Feature three',
      ],
      skillPath: '',
    );

    return Skeletonizer(
      enabled: true,
      child: _buildGrid(
        List.generate(6, (_) => dummySkill),
        scrollController,
      ),
    );
  }

  /// Build error state with retry button
  Widget _buildErrorState(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline,
              size: 48,
              color: theme.colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              _error!,
              style: theme.textTheme.bodyLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: _loadSkills,
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  /// Build empty state
  Widget _buildEmptyState(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.inbox_outlined,
              size: 48,
              color: theme.colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'No skills available',
              style: theme.textTheme.bodyLarge,
            ),
          ],
        ),
      ),
    );
  }

  /// Build responsive grid of skill cards
  Widget _buildGrid(List<Skill> skills, ScrollController scrollController) {
    return GridView.builder(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: _getColumnCount(context),
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: _getAspectRatio(context),
      ),
      itemCount: skills.length,
      itemBuilder: (context, index) {
        return SkillCard(
          skill: skills[index],
          isSelected: _selectedIndex == index,
          onTap: () => _handleSelection(skills[index], index),
        );
      },
    );
  }

  /// Get column count based on screen size
  int _getColumnCount(BuildContext context) {
    if (context.isDesktop) return 3;
    if (context.isTablet) return 2;
    return 1;
  }

  /// Get aspect ratio based on screen size
  ///
  /// Mobile (1 col): wider cards (~2.5)
  /// Tablet (2 cols): medium cards (~1.4)
  /// Desktop (3 cols): compact cards (~1.3)
  double _getAspectRatio(BuildContext context) {
    if (context.isDesktop) return 1.3;
    if (context.isTablet) return 1.4;
    return 2.5;
  }
}
