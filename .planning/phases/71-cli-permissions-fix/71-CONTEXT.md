# Phase 71: CLI Permissions Fix - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `--dangerously-skip-permissions` to all three Claude CLI subprocess spawn paths so the assistant runs non-interactively without blocking on any permission prompt. This is a backend-only infrastructure change in `claude_cli_adapter.py`.

</domain>

<decisions>
## Implementation Decisions

### Permission scope
- Flag applies to ALL thread types (BA analysis + Assistant) — both run non-interactively
- Flag applies uniformly to ALL three spawn paths (warm pool, cold spawn, direct fallback)
- No tool restrictions — CLI can use all tools freely in the controlled backend environment
- Security hardening is a future concern (v2.0 backlog), not this phase

### Configuration
- Flag is hardcoded — always on, no env var toggle, no config option
- Add the flag to ALL code locations: the `cmd` list in `stream_chat()` AND both `_spawn_warm_process()` and `_cold_spawn()` subprocess calls
- No CLI version validation at startup — let it fail loudly at first use if the flag isn't supported
- If the CLI rejects the flag, surface the error to the user as a setup issue (don't silently retry without it)

### Claude's Discretion
- Exact placement of the flag in argument lists
- Whether to extract the flag as a constant or inline it
- Test structure and assertions

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The change is mechanical: add one flag to three `create_subprocess_exec` calls and the `cmd` list.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 71-cli-permissions-fix*
*Context gathered: 2026-02-23*
