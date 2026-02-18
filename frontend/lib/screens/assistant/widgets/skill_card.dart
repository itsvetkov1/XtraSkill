/// Skill card widget for displaying individual skills in the browser.
library;

import 'package:flutter/material.dart';
import '../../../models/skill.dart';
import '../../../utils/skill_emoji.dart';

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
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Row 1: Emoji + Name
                  Row(
                    children: [
                      Text(
                        getSkillEmoji(skill.name),
                        style: const TextStyle(fontSize: 28),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          skill.name,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),

                  // Row 2: Description
                  const SizedBox(height: 8),
                  Text(
                    skill.description,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),

                  // Row 3: Features (first 3 only)
                  if (skill.features.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    ...skill.features.take(3).map((feature) {
                      final featureStyle = theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                        fontSize: 11,
                      );

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 2),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('• ', style: featureStyle),
                            Expanded(
                              child: Text(
                                feature,
                                style: featureStyle,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
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
        ),
      ),
    );
  }
}
