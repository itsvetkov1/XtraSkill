/// Tool configuration state management.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Available OpenClaw tools
class ToolInfo {
  final String id;
  final String name;
  final String description;
  final bool requiresExternalConfig;

  const ToolInfo({
    required this.id,
    required this.name,
    required this.description,
    this.requiresExternalConfig = false,
  });
}

/// Provider managing OpenClaw tool configuration
class ToolConfigProvider extends ChangeNotifier {
  final SharedPreferences _prefs;
  
  /// Storage key prefix
  static const String _prefix = 'tool_enabled_';
  
  /// All available tools
  static const List<ToolInfo> availableTools = [
    ToolInfo(
      id: 'search_documents',
      name: 'Search Documents',
      description: 'Search across project documents',
    ),
    ToolInfo(
      id: 'save_artifact',
      name: 'Save Artifact',
      description: 'Save generated content to project',
    ),
    ToolInfo(
      id: 'send_email',
      name: 'Send Email',
      description: 'Send emails via configured account',
      requiresExternalConfig: true,
    ),
    ToolInfo(
      id: 'check_calendar',
      name: 'Check Calendar',
      description: 'View Google Calendar events',
      requiresExternalConfig: true,
    ),
    ToolInfo(
      id: 'post_twitter',
      name: 'Post Twitter',
      description: 'Post to Twitter/X',
      requiresExternalConfig: true,
    ),
    ToolInfo(
      id: 'spawn_subagent',
      name: 'Spawn Sub-Agent',
      description: 'Delegate to specialized sub-agents',
    ),
    ToolInfo(
      id: 'web_search',
      name: 'Web Search',
      description: 'Search the web for current information',
    ),
  ];

  /// Enabled tools cache
  Map<String, bool> _enabledTools = {};

  ToolConfigProvider(this._prefs) {
    _loadSettings();
  }

  void _loadSettings() {
    for (final tool in availableTools) {
      _enabledTools[tool.id] = _prefs.getBool('$_prefix${tool.id}') ?? true;
    }
  }

  /// Check if a tool is enabled
  bool isEnabled(String toolId) {
    return _enabledTools[toolId] ?? true;
  }

  /// Toggle a tool on/off
  Future<void> toggleTool(String toolId) async {
    final current = _enabledTools[toolId] ?? true;
    _enabledTools[toolId] = !current;
    await _prefs.setBool('$_prefix$toolId', !current);
    notifyListeners();
  }

  /// Set a tool's enabled state
  Future<void> setEnabled(String toolId, bool enabled) async {
    _enabledTools[toolId] = enabled;
    await _prefs.setBool('$_prefix$toolId', enabled);
    notifyListeners();
  }

  /// Get list of enabled tool IDs
  List<String> get enabledToolIds {
    return _enabledTools.entries
        .where((e) => e.value)
        .map((e) => e.key)
        .toList();
  }
}
