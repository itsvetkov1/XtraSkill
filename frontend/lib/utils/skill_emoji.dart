/// Emoji mapping utility for skills.
library;

/// Maps skill names to their corresponding emoji icons
const Map<String, String> _emojiMap = {
  'Business Analyst': '📊',
  'QA BFF': '🧪',
  'Software Architect': '🏗️',
  'Prompt Enhancer': '✨',
  'Judge': '⚖️',
  'Instructions Creator': '📝',
  'Evaluator Ba Docs': '📋',
  'Skill Transformer': '🔄',
  'Task Delegation': '🎯',
  'TL Assistant': '👔',
};

/// Returns the emoji icon for a given skill name.
///
/// Returns '🔧' as fallback for unknown skill names.
String getSkillEmoji(String skillName) => _emojiMap[skillName] ?? '🔧';
