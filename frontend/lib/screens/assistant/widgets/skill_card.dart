/// Skill card widget for displaying individual skills in the browser.
library;

import 'package:flutter/material.dart';
import '../../../models/skill.dart';
import '../../../utils/skill_emoji.dart';
import '../../../widgets/responsive_layout.dart';

/// A card widget that displays a single skill with emoji, name, description, and features.
///
/// Supports selection state with visual highlight animation.
class SkillCard extends StatelessWidget {
  /// The skill to display
  final Skill skill;

  /// Callback when the card is tapped
  final VoidCallback onTap;

  /// Whether this card is currently selected (for highlight animation)
  final bool isSelected;

  const SkillCard({
    super.key,
    required this.skill,
    required this.onTap,
    this.isSelected = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AnimatedScale(
      scale: isSelected ? 0.97 : 1.0,
      duration: const Duration(milliseconds: 150),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        decoration: BoxDecoration(
          color: isSelected
              ? theme.colorScheme.primaryContainer.withValues(alpha: 0.5)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Card(
          clipBehavior: Clip.antiAlias,
          elevation: 1,
          child: InkWell(
            onTap: onTap,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Row 1: Emoji + Name + Info Button
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        getSkillEmoji(skill.name),
                        style: const TextStyle(fontSize: 24),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          skill.name,
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 4),
                      GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: () => _showSkillInfoDialog(context, skill, theme),
                        child: Padding(
                          padding: const EdgeInsets.all(4),
                          child: Icon(
                            Icons.info_outline,
                            size: 18,
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                    ],
                  ),

                  // Row 2: Description
                  const SizedBox(height: 6),
                  Text(
                    skill.description,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Shows a dialog with full skill information including complete description and all features.
void _showSkillInfoDialog(BuildContext context, Skill skill, ThemeData theme) {
  showDialog(
    context: context,
    barrierDismissible: true,
    builder: (BuildContext dialogContext) {
      return AlertDialog(
        title: Row(
          children: [
            Text(getSkillEmoji(skill.name), style: const TextStyle(fontSize: 24)),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                skill.name,
                style: theme.textTheme.titleLarge,
              ),
            ),
          ],
        ),
        content: SizedBox(
          width: context.isDesktop ? 500 : (context.isTablet ? 450 : 400),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Full description (no line limit unlike card's 2-line truncation)
                Text(
                  skill.description,
                  style: theme.textTheme.bodyMedium,
                ),

                // ALL features (not limited to 3 like the card)
                if (skill.features.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Divider(),
                  const SizedBox(height: 12),
                  Text(
                    'Features',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...skill.features.map((feature) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('• ', style: theme.textTheme.bodyMedium),
                          Expanded(
                            child: Text(
                              feature,
                              style: theme.textTheme.bodyMedium,
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ],
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Close'),
          ),
        ],
      );
    },
  );
}
