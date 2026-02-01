# UX-002: Threads as Primary View with Collapsible Documents Column

**Priority:** High
**Status:** Open
**Component:** Project Layout
**Created:** 2026-01-31

---

## User Story

As a user working in a project,
I want threads to be the primary view with documents in a collapsible side column,
So that I can focus on conversations while having quick access to documents when needed.

---

## Current Behavior

- Project view has two equal tabs: "Documents" and "Threads"
- Documents tab is the default selection when opening a project
- Both tabs occupy the same screen real estate
- User must switch tabs to access documents while in a conversation

---

## Desired Behavior

### Layout Structure

```
┌─────────┬────┬─────────────────────────────────┐
│  Main   │Doc │                                 │
│  Menu   │Col │     Thread List / Conversation  │
│         │    │                                 │
│         │ ▶  │                                 │
│         │    │                                 │
└─────────┴────┴─────────────────────────────────┘
          ↑
     Collapsible
     (minimized by default)
```

### Documents Column States

**Minimized (default):**
- Thin vertical strip (~40-48px wide)
- Document icon at top
- Expand arrow/chevron indicator
- Clickable to expand

**Expanded:**
- Shows document list for the project
- Document names with file type icons
- Click document to view/preview
- Collapse button to minimize

---

## Acceptance Criteria

- [ ] Threads view is shown by default when opening a project (not Documents tab)
- [ ] Documents appear in a collapsible column between main menu and thread list
- [ ] Documents column is minimized by default
- [ ] Minimized state shows thin strip with document icon and expand indicator
- [ ] Clicking minimized column expands it to show document list
- [ ] Expanded column can be collapsed back to minimized state
- [ ] Column state persists within session (optional: across sessions)
- [ ] Documents tab is removed from project view
- [ ] All document functionality (upload, view, delete) accessible from column

---

## Technical Notes

**Files likely affected:**
- `frontend/lib/screens/projects/project_detail_screen.dart`
- `frontend/lib/screens/projects/widgets/` (new document column widget)
- May need new widget: `collapsible_documents_column.dart`

**Implementation approach:**
1. Remove TabBar/TabBarView for Documents/Threads
2. Create CollapsibleDocumentsColumn widget
3. Use Row layout: [MainMenu] [DocColumn] [ThreadsContent]
4. Implement expand/collapse animation
5. Move document list and upload functionality to column

**State management:**
- Local state for expand/collapse (StatefulWidget or Provider)
- Consider persisting preference in SharedPreferences

---

## Dependencies

None - standalone layout change

---

## Visual Reference

**Minimized state:**
```
┌────┐
│ 📄 │  ← Document icon
│    │
│ ▶  │  ← Expand indicator
│    │
└────┘
```

**Expanded state:**
```
┌──────────────┐
│ Documents  ◀ │  ← Header with collapse button
├──────────────┤
│ 📄 spec.pdf  │
│ 📄 req.docx  │
│ 📄 notes.txt │
├──────────────┤
│  [+ Upload]  │
└──────────────┘
```

---

*Created: 2026-01-31*
