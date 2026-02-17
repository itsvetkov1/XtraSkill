# Feature Landscape: Assistant Integration

**Domain:** Dual-mode chat application (BA vs General Assistant)
**Researched:** 2026-02-17

## Table Stakes

Features users expect from a general assistant chat. Missing these would make the Assistant section feel incomplete compared to the BA section.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Thread creation** | Core chat functionality | Low | Clone existing thread creation dialog |
| **Message sending** | Basic chat interaction | Low | Reuse existing conversation screen |
| **SSE streaming** | Real-time responses (matches BA UX) | Low | Already implemented in conversation route |
| **Thread listing** | See past conversations | Low | Clone ChatsScreen with thread_type filter |
| **Thread deletion** | Manage conversation history | Low | Already implemented in thread routes |
| **Thread renaming** | Organize conversations | Low | Already implemented in thread routes |
| **Markdown rendering** | Code blocks, formatting | Low | Already implemented in message widgets |
| **Model provider selection** | User chooses LLM (Anthropic/Gemini/DeepSeek) | Medium | Already implemented, just expose in UI |
| **Token usage tracking** | Cost transparency | Low | Already implemented, reuse existing tracking |
| **Deep linking** | Shareable conversation URLs | Low | Already implemented for BA threads |

## Differentiators

Features that set the Assistant section apart from the BA section. Not expected, but valuable for user adoption.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **No system prompt overhead** | Faster responses (no 600-line BA prompt) | Low | Natural consequence of thread_type |
| **General knowledge access** | Not limited to BA domain | Low | Natural consequence of no specialized prompt |
| **Project-agnostic** | Works without creating projects first | Low | Thread.project_id = null |
| **Simpler UX** | No mode selection (Meeting/Refinement) | Low | Remove conversation_mode from UI |
| **Faster onboarding** | New users can chat immediately | Low | No document upload prerequisite |
| **Cross-project knowledge** | Assistant can discuss multiple projects | Medium | Future: allow referencing project docs |

## Anti-Features

Features to explicitly NOT build for MVP. These would complicate the Assistant without proportional value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Document search tool** | No project context, unclear scope | Defer to Phase 2 if needed |
| **Artifact generation** | No BRD/user story use case in Assistant | Omit save_artifact tool entirely |
| **Conversation mode** | "Meeting" vs "Document Refinement" is BA-specific | Remove mode selector for Assistant threads |
| **Project association** | Breaks clean separation | Keep Assistant threads project-less |
| **BA-specific prompting** | Defeats purpose of general assistant | Use minimal system prompt |
| **MCP tools** | Search/artifact tools are BA domain | Conditionally disable MCP servers |

## Feature Dependencies

```
Thread Type Field (Thread model)
    ↓
Thread Creation API (with type parameter)
    ↓
AI Service Conditional Logic (prompt + tool selection)
    ↓
    ├─→ Assistant Screen (UI for listing/creating)
    └─→ Conversation Screen (already exists, no changes)
```

**Critical path:** Thread type must exist in database before Assistant screen can filter by it.

## Feature Parity Matrix

Comparison of BA threads vs Assistant threads:

| Feature | BA Threads | Assistant Threads | Implementation Status |
|---------|-----------|-------------------|----------------------|
| Thread creation | ✅ Project-scoped | ✅ User-scoped | Existing route, add type param |
| Message sending | ✅ Via conversation route | ✅ Via conversation route | No changes needed |
| Streaming responses | ✅ SSE | ✅ SSE | No changes needed |
| System prompt | ✅ 600-line BA prompt | ✅ 5-line generic prompt | New constant needed |
| Document search | ✅ MCP tool | ❌ Omitted | Conditional MCP config |
| Artifact generation | ✅ MCP tool | ❌ Omitted | Conditional MCP config |
| Conversation mode | ✅ Meeting/Refinement | ❌ N/A | Remove mode selector |
| Project association | ✅ Required | ❌ Forbidden | Validation in route |
| Provider selection | ✅ At creation | ✅ At creation | Reuse existing UI |
| Thread listing | ✅ ChatsScreen | ✅ AssistantScreen | Clone ChatsScreen |
| Deep linking | ✅ `/chats/:id` | ✅ `/assistant/:id` | Add route |

## MVP Recommendation

### Prioritize (Build First)

1. **Thread type field (backend)** - Database foundation
2. **AI service conditional logic (backend)** - Core behavior
3. **Thread creation with type (backend)** - API support
4. **Assistant screen (frontend)** - User-facing entry point
5. **Navigation item (frontend)** - Discoverability

### Defer (Post-MVP)

1. **Document search in Assistant** - Unclear use case, requires project association rethink
2. **Cross-project context** - Complex scoping, needs careful design
3. **Artifact generation in Assistant** - No clear non-BA use case identified
4. **Thread type migration** - Existing threads can stay as-is (default to ba_assistant)
5. **Advanced filtering** - Thread type + provider + date range filtering (nice-to-have)

## User Flows

### Flow 1: First-Time Assistant User

```
1. User logs in to BA Assistant app
   ↓
2. User sees new "Assistant" nav item
   ↓
3. User clicks "Assistant"
   ↓
4. Empty state: "No conversations yet"
   ↓
5. User clicks "New Chat" FAB
   ↓
6. Dialog: Enter title (optional), select provider
   ↓
7. Thread created (type=assistant, project_id=null)
   ↓
8. User types message
   ↓
9. Assistant responds (no BA prompt, pure Claude)
   ↓
10. User continues conversation
```

### Flow 2: BA User Exploring Assistant

```
1. User working in BA project
   ↓
2. User has question unrelated to current project
   ↓
3. User navigates to "Assistant" (global nav)
   ↓
4. User creates new Assistant chat
   ↓
5. User asks general question (e.g., "Explain OAuth 2.0")
   ↓
6. Assistant responds (no BA discovery prompts)
   ↓
7. User satisfied, returns to BA project
```

### Flow 3: Switching Between BA and Assistant

```
1. User in BA thread (project context, document search active)
   ↓
2. User navigates to "Assistant" section
   ↓
3. User selects existing Assistant thread
   ↓
4. Conversation continues (no project context, no tools)
   ↓
5. User navigates back to "Chats"
   ↓
6. User selects BA thread
   ↓
7. BA conversation resumes (project context, tools active)
```

## UI/UX Considerations

### Navigation

**Current structure:**
```
Sidebar
├── Home
├── Projects
├── Chats (All BA threads across projects)
└── Settings
```

**Proposed structure:**
```
Sidebar
├── Home
├── Projects
├── Chats (BA threads)
├── Assistant (NEW - General chat threads)
└── Settings
```

**Icon recommendation:** Different from Chats (e.g., robot icon vs chat bubble).

### Thread Creation Dialog

**BA Thread Creation:**
```
┌────────────────────────────┐
│ New BA Chat                │
├────────────────────────────┤
│ Title: [optional]          │
│ Project: [dropdown]        │
│ Provider: [dropdown]       │
│ Mode: [Meeting/Refinement] │
│                            │
│ [Cancel]  [Create]         │
└────────────────────────────┘
```

**Assistant Thread Creation:**
```
┌────────────────────────────┐
│ New Assistant Chat         │
├────────────────────────────┤
│ Title: [optional]          │
│ Provider: [dropdown]       │
│                            │
│ [Cancel]  [Create]         │
└────────────────────────────┘
```

**Differences:**
- No project selector (always null)
- No conversation mode selector (N/A for Assistant)
- Simpler, faster creation flow

### Empty States

**ChatsScreen (existing):**
```
"No BA chats yet"
"Create a project and start a discovery conversation"
```

**AssistantScreen (new):**
```
"No conversations yet"
"Start chatting with Claude Code"
```

## Sources

- [Flutter Empty State Patterns](https://docs.flutter.dev/app-architecture/design-patterns/empty-state) - UI/UX guidance
- [Existing BA Assistant Flows](file:///Users/a1testingmac/projects/XtraSkill/.planning/APP-FEATURES-AND-FLOWS.md) - Consistency reference
- Codebase Analysis: ChatsScreen, ThreadCreateDialog, ConversationScreen

---
*Feature research for: Assistant Integration*
*Researched: 2026-02-17*
*Recommendation: Start with Table Stakes only, defer Differentiators to post-MVP*
