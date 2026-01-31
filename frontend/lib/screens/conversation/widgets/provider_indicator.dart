/// Provider indicator widget showing current model.
library;

import 'package:flutter/material.dart';

import '../../../core/constants.dart';

/// Displays the provider for a conversation with colored icon.
///
/// Shows provider name and icon above the chat input.
/// Per CONTEXT.md: icon gets color tint, text stays neutral.
class ProviderIndicator extends StatelessWidget {
  /// Provider ID (anthropic, google, deepseek)
  final String? provider;

  const ProviderIndicator({
    super.key,
    required this.provider,
  });

  @override
  Widget build(BuildContext context) {
    final config = ProviderConfigs.getConfig(provider);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            config.icon,
            size: 16,
            color: config.color,
          ),
          const SizedBox(width: 8),
          Text(
            config.displayName,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}
