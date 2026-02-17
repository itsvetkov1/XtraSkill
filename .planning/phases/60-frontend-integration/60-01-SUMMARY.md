---
phase: 60-frontend-integration
plan: 01
subsystem: full-stack-provider-registration
tags: [provider-registration, ui-enhancement, experimental-features]
dependency_graph:
  requires:
    - phase-58-01-sdk-adapter
    - phase-59-01-cli-adapter
  provides:
    - claude-code-providers-selectable
    - experimental-badge-ui-pattern
  affects:
    - settings-screen
    - provider-provider
    - thread-creation
tech_stack:
  added: []
  patterns:
    - experimental-feature-badging
    - provider-config-extension
key_files:
  created: []
  modified:
    - backend/app/routes/threads.py
    - frontend/lib/core/constants.dart
    - frontend/lib/providers/provider_provider.dart
    - frontend/lib/screens/settings_screen.dart
decisions:
  - title: "Experimental Badge Pattern"
    rationale: "Use Material 3 secondaryContainer color scheme for consistent experimental feature badging across app"
  - title: "Model Name Display Format"
    rationale: "Use em-dash separator (—) for clean visual separation between provider name and model version"
  - title: "Provider Icon Selection"
    rationale: "Icons.code_outlined for SDK (programming context), Icons.terminal_outlined for CLI (command-line context)"
metrics:
  duration: 184
  tasks_completed: 2
  files_modified: 4
  commits: 2
  completed_at: 2026-02-15
---

# Phase 60 Plan 01: Claude Code Provider Registration Summary

**Register Claude Code providers (SDK and CLI) across the full stack so users can select them in settings and create threads with them.**

## Objective Achieved

Claude Code providers (SDK and CLI) are now registered across the full stack. Users can select them in settings dropdown with experimental badges and model names displayed. Backend accepts these providers for thread creation.

## Tasks Completed

### Task 1: Backend and Frontend Provider Registration
**Commit:** `3ec4f4c`

**Backend Changes (threads.py):**
- Added `claude-code-sdk` and `claude-code-cli` to VALID_PROVIDERS list
- Backend now accepts these providers for thread creation via POST /threads endpoints

**Frontend Changes (constants.dart):**
- Extended ProviderConfig class with two new optional fields:
  - `isExperimental` (bool, default false) - flags experimental features
  - `modelName` (String?, nullable) - displays underlying model version
- Created two new provider configurations:
  - `claudeCodeSdk`: Claude Code (SDK) with experimental badge, model name, code icon
  - `claudeCodeCli`: Claude Code (CLI) with experimental badge, model name, terminal icon
- Added new providers to `getConfig()` switch statement
- Added new providers to `ProviderConfigs.all` list (now 5 total)

**Frontend Changes (provider_provider.dart):**
- Added `claude-code-sdk` and `claude-code-cli` to `_availableProviders` list
- Critical for validation: `setProvider()` throws ArgumentError if provider not in this list
- Ensures provider selection persistence works for Claude Code providers

**Files Modified:**
- `backend/app/routes/threads.py`
- `frontend/lib/core/constants.dart`
- `frontend/lib/providers/provider_provider.dart`

### Task 2: Settings Dropdown UI Enhancement
**Commit:** `2c87b4d`

**Changes (settings_screen.dart):**
- Enhanced dropdown items to show experimental badge for providers with `isExperimental: true`
- Badge styling:
  - Text: "EXPERIMENTAL" in 10pt, font weight 600
  - Colors: secondaryContainer background, onSecondaryContainer text
  - Material 3 color scheme for theme consistency
- Added model name display with em-dash separator (e.g., "— Claude Sonnet 4.5")
- Used spread operator (`if (condition) ...[widgets]`) for conditional rendering
- Renamed builder context parameter to `builderContext` to avoid shadowing outer context

**Visual Result:**
- Claude Code (SDK) shows: [code icon] Claude Code (SDK) [EXPERIMENTAL badge] — Claude Sonnet 4.5
- Claude Code (CLI) shows: [terminal icon] Claude Code (CLI) [EXPERIMENTAL badge] — Claude Sonnet 4.5
- Existing providers (Claude, Gemini, DeepSeek) render without badges or model names

**Files Modified:**
- `frontend/lib/screens/settings_screen.dart`

## Verification Results

**Backend Verification:**
- ✅ VALID_PROVIDERS contains all 5 providers: anthropic, google, deepseek, claude-code-sdk, claude-code-cli
- ✅ 108 Claude Code adapter tests pass (from Phase 58/59)
- ✅ 265 total backend unit tests pass with zero regressions

**Frontend Verification:**
- ✅ ProviderConfig has `isExperimental` and `modelName` fields
- ✅ ProviderConfigs.all has 5 entries (3 existing + 2 new)
- ✅ ProviderConfigs.getConfig('claude-code-sdk') returns claudeCodeSdk config
- ✅ ProviderConfigs.getConfig('claude-code-cli') returns claudeCodeCli config
- ✅ ProviderProvider._availableProviders has 5 entries matching ProviderConfigs.all IDs
- ✅ `flutter analyze` passes cleanly for all modified files (constants.dart, provider_provider.dart, settings_screen.dart)

**End-to-End Streaming Coverage (UI-04):**
- ✅ Providers registered in backend VALID_PROVIDERS
- ✅ Providers registered in frontend dropdown
- ✅ Phase 58/59 adapters normalize output to ChatEvent format
- ✅ Existing MessageBubble, StreamingMessage, and thinking UI handle all ChatEvent types identically
- **Manual E2E testing deferred to TESTING-QUEUE.md per project convention**

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

**Provider Selection Flow:**
1. User opens Settings screen
2. Dropdown shows all 5 providers from ProviderConfigs.all
3. Claude Code providers display with experimental badge and model name
4. User selects provider → ProviderProvider.setProvider() validates against _availableProviders
5. Selection persists to SharedPreferences immediately
6. Selection survives app restart

**Thread Creation Flow:**
1. User creates new thread with selected provider
2. Frontend sends POST /threads with `model_provider: "claude-code-sdk"` (or cli)
3. Backend validates against VALID_PROVIDERS (now includes Claude Code providers)
4. Thread created with provider binding
5. When user sends message, AIService routes to appropriate adapter (Phase 58/59)
6. Adapter normalizes output to ChatEvent format
7. Existing streaming display renders response identically regardless of provider

**Why No New Streaming Code Needed:**
- Phase 58/59 adapters (ClaudeCodeSDKAdapter, ClaudeCLIAdapter) already normalize all provider-specific events to the standard ChatEvent format
- Existing UI components (MessageBubble, StreamingMessage, ThinkingIndicator) are provider-agnostic
- They consume ChatEvent types (TEXT, THINKING_START, THINKING_END, TOOL_USE) regardless of source
- Adding providers to registration lists enables end-to-end streaming without UI changes

## Next Steps

**Phase 60-02 (if exists):**
- Manual E2E testing of Claude Code providers
- Verify streaming display works correctly
- Verify tool execution displays work
- Verify thinking indicators render properly

**Testing Queue:**
- Add Claude Code provider selection and thread creation to `.planning/TESTING-QUEUE.md`
- Test cases:
  - TC-60-01: Select Claude Code (SDK) in settings, verify persistence across restart
  - TC-60-02: Select Claude Code (CLI) in settings, verify persistence across restart
  - TC-60-03: Create thread with Claude Code (SDK) provider, send message, verify streaming
  - TC-60-04: Create thread with Claude Code (CLI) provider, send message, verify streaming
  - TC-60-05: Verify experimental badge displays in dropdown
  - TC-60-06: Verify model name displays in dropdown

## Self-Check: PASSED

**Created Files:**
- ✅ `.planning/phases/60-frontend-integration/60-01-SUMMARY.md` (this file)

**Modified Files:**
- ✅ `backend/app/routes/threads.py` exists, contains "claude-code-sdk" and "claude-code-cli"
- ✅ `frontend/lib/core/constants.dart` exists, contains isExperimental and modelName fields
- ✅ `frontend/lib/providers/provider_provider.dart` exists, contains claude-code-sdk and claude-code-cli in _availableProviders
- ✅ `frontend/lib/screens/settings_screen.dart` exists, contains experimental badge rendering logic

**Commits:**
- ✅ `3ec4f4c` exists: feat(60-01): register Claude Code providers across stack
- ✅ `2c87b4d` exists: feat(60-01): add experimental badges and model names to settings dropdown

All claims verified. Self-check passed.
