/// Skill selector widget for choosing Claude Code skills.
library;

import 'package:flutter/material.dart';

import '../../../models/skill.dart';
import '../../../services/skill_service.dart';

/// Popup menu button for selecting skills
class SkillSelector extends StatelessWidget {
  /// Callback when skill is selected
  final void Function(Skill) onSkillSelected;

  /// Skill service for fetching skills
  final SkillService _skillService = SkillService();

  SkillSelector({
    super.key,
    required this.onSkillSelected,
  });

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Skill>>(
      future: _skillService.getSkills(),
      builder: (context, snapshot) {
        final skills = snapshot.data ?? [];
        final isLoading = snapshot.connectionState == ConnectionState.waiting;
        final hasError = snapshot.hasError;
        final isEmpty = skills.isEmpty && !isLoading;

        return PopupMenuButton<Skill>(
          icon: const Icon(Icons.add_box_outlined),
          tooltip: isLoading
              ? 'Loading skills...'
              : isEmpty
                  ? 'No skills available'
                  : 'Select skill',
          enabled: !isLoading && !isEmpty && !hasError,
          itemBuilder: (context) {
            if (isLoading) {
              return [
                PopupMenuItem<Skill>(
                  enabled: false,
                  child: Row(
                    children: [
                      const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Loading skills...',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ];
            }

            if (isEmpty) {
              return [
                PopupMenuItem<Skill>(
                  enabled: false,
                  child: Text(
                    'No skills available',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ),
              ];
            }

            if (hasError) {
              return [
                PopupMenuItem<Skill>(
                  enabled: false,
                  child: Text(
                    'Failed to load skills',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ),
              ];
            }

            return skills.map((skill) {
              return PopupMenuItem<Skill>(
                value: skill,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      skill.displayName,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    if (skill.description.isNotEmpty)
                      Text(
                        skill.description,
                        style: TextStyle(
                          fontSize: 12,
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                  ],
                ),
              );
            }).toList();
          },
          onSelected: onSkillSelected,
        );
      },
    );
  }
}
