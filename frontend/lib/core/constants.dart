/// Application constants and configuration.
library;

import 'package:flutter/material.dart';

/// Configuration for an LLM provider display.
class ProviderConfig {
  final String id;
  final String displayName;
  final Color color;
  final IconData icon;
  final bool isExperimental;
  final String? modelName;

  const ProviderConfig({
    required this.id,
    required this.displayName,
    required this.color,
    required this.icon,
    this.isExperimental = false,
    this.modelName,
  });
}

/// Provider configurations for UI display.
///
/// Colors from CONTEXT.md:
/// - Claude: Anthropic orange (#D97706)
/// - Gemini: Google blue (#4285F4)
/// - DeepSeek: Teal/cyan (#00B8D4)
class ProviderConfigs {
  static const anthropic = ProviderConfig(
    id: 'anthropic',
    displayName: 'Claude',
    color: Color(0xFFD97706),
    icon: Icons.smart_toy_outlined,
  );

  static const google = ProviderConfig(
    id: 'google',
    displayName: 'Gemini',
    color: Color(0xFF4285F4),
    icon: Icons.auto_awesome_outlined,
  );

  static const deepseek = ProviderConfig(
    id: 'deepseek',
    displayName: 'DeepSeek',
    color: Color(0xFF00B8D4),
    icon: Icons.psychology_outlined,
  );

  static const claudeCodeSdk = ProviderConfig(
    id: 'claude-code-sdk',
    displayName: 'Claude Code (SDK)',
    color: Color(0xFFD97706), // Same Anthropic orange
    icon: Icons.code_outlined,
    isExperimental: true,
    modelName: 'Claude Sonnet 4.5',
  );

  static const claudeCodeCli = ProviderConfig(
    id: 'claude-code-cli',
    displayName: 'Claude Code (CLI)',
    color: Color(0xFFD97706), // Same Anthropic orange
    icon: Icons.terminal_outlined,
    isExperimental: true,
    modelName: 'Claude Sonnet 4.5',
  );

  static const openclaw = ProviderConfig(
    id: 'openclaw',
    displayName: 'OpenClaw',
    color: Color(0xFF6366F1), // Indigo/purple
    icon: Icons.hub_outlined,
    isExperimental: true,
  );

  /// Get config by provider ID, falls back to anthropic if unknown.
  static ProviderConfig getConfig(String? providerId) {
    switch (providerId) {
      case 'google':
        return google;
      case 'deepseek':
        return deepseek;
      case 'claude-code-sdk':
        return claudeCodeSdk;
      case 'claude-code-cli':
        return claudeCodeCli;
      case 'openclaw':
        return openclaw;
      case 'anthropic':
      default:
        return anthropic;
    }
  }

  /// All available providers for dropdown.
  static const List<ProviderConfig> all = [anthropic, google, deepseek, claudeCodeSdk, claudeCodeCli, openclaw];
}
