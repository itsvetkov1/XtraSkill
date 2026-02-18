/// Skill selector widget for choosing Claude Code skills.
library;

import 'package:flutter/material.dart';

import '../../../models/skill.dart';
import 'skill_browser_sheet.dart';

/// Icon button that opens the skill browser bottom sheet
///
/// Replaces the previous PopupMenuButton approach with a richer browsing experience.
class SkillSelector extends StatelessWidget {
  /// Callback when skill is selected from the browser
  final void Function(Skill) onSkillSelected;

  const SkillSelector({
    super.key,
    required this.onSkillSelected,
  });

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.add_box_outlined),
      tooltip: 'Choose a skill',
      onPressed: () async {
        final skill = await SkillBrowserSheet.show(context);
        if (skill != null) {
          onSkillSelected(skill);
        }
      },
    );
  }
}
