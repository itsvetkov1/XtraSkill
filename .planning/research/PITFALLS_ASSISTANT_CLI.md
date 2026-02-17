# Pitfalls Research: Separating BA Assistant from Claude Code CLI

**Domain:** Refactoring single-purpose AI chat app to dual-mode architecture (BA Assistant + Claude Code CLI)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Executive Summary

Adding a separate "Assistant" mode (standalone Claude Code CLI) to an existing single-purpose chat app (BA Assistant) introduces **five critical failure modes**: (1) system prompt leakage between BA and Assistant flows, (2) document ownership isolation failures causing cross-project contamination, (3) CLI subprocess lifecycle mismanagement blocking the event loop, (4) navigation context conflicts with existing GoRouter, and (5) shared service state bleeding BA-specific behavior into Assistant threads. All five require architectural prevention in foundation phases—remediation after implementation is expensive or impossible.

The most dangerous pitfall is **implicit system prompt injection** (OWASP LLM01:2025). BA Assistant has a 15KB system prompt hardcoded in `ai_service.py`. When building the Assistant flow, developers commonly refactor this into a "configurable" parameter but fail to enforce context isolation, allowing project documents with embedded instructions to manipulate the BA prompt or vice versa. Prevention requires **context firewalls** at the service layer, not UI-level filtering.

Second highest risk: **CLI subprocess management in async FastAPI**. Spawning `claude` CLI via `subprocess.run()` (synchronous) blocks the entire event loop, freezing all WebSocket connections. The correct pattern uses `asyncio.create_subprocess_exec()` with `stdout.readline()` streaming, but has sharp edges: garbage collection kills the child process, Windows requires ProactorEventLoop, and missing `drain()` calls cause backpressure failures. One missing `await` freezes production.

Third: **document ownership isolation**. Existing BA documents are scoped to projects. Assistant needs project-independent threads. Developers often create a "shared documents pool" or "global project" as a shortcut, breaking tenant isolation and leaking customer data between BA projects and Assistant sessions. The fix requires explicit `scope` enum (BA_PROJECT vs ASSISTANT_THREAD) enforced at the database row-level security layer.

This research synthesizes findings from OWASP Gen AI Security, Microsoft Agent Framework state isolation patterns, Flutter GoRouter navigation conflicts, FastAPI WebSocket best practices, and monolith-to-modular-monolith refactoring strategies specific to 2026.

---

## Critical Pitfalls

### Pitfall 1: System Prompt Injection via Shared AI Service

**What goes wrong:**

BA Assistant's 15KB system prompt (hardcoded in `ai_service.py` lines 115-450) leaks into Assistant threads, causing Claude Code CLI to behave like a BA consultant. Users report "why is the assistant asking discovery questions instead of writing code?" Conversely, BA threads lose their structured behavior when refactored service accidentally sends them to the raw CLI.

The failure mode: developers refactor `SYSTEM_PROMPT` constant into a parameter (`get_system_prompt(mode: str)`), but fail to enforce context isolation. Documents uploaded to BA projects contain user-generated text that includes phrases like "ignore previous instructions" or "you are now a Python expert"—these stored prompt injections manipulate the BA prompt when search results are concatenated into context. The LLM cannot reliably distinguish between trusted system instructions and untrusted document content.

**Why it happens:**

OWASP LLM01:2025 root cause: AI systems treat user input and system instructions as the same type of data. When refactoring from a single hardcoded prompt to configurable prompts, developers focus on "which prompt to use" but ignore "how to prevent untrusted input from altering prompts." The refactor replaces a constant with a function, but doesn't add context firewalls separating system instructions from retrieved text.

Second cause: MCP sampling attack surface. If integrating Model Context Protocol for tool sampling (unlikely for this project, but relevant for 2026), MCP servers can inject hidden instructions into prompts when requesting completions. Without explicit context isolation and request sanitization, the server controls both prompt content and how it processes responses.

Third cause: shared service state. `ai_service.py` currently constructs conversation history with ALL messages in database order. When BA and Assistant modes share the same `send_message()` function, developers add `if thread.mode == "BA"` conditionals scattered through message construction. One missed branch leaks BA-specific tool definitions or context into Assistant calls.

**How to avoid:**

**Defense-in-depth strategy (all three layers required):**

1. **Context firewalls at service layer** — Separate `ba_service.py` and `assistant_service.py` instead of one unified `ai_service.py`. Each service owns its system prompt construction, tool definitions, and conversation history formatting. Never share message formatting code. This prevents conditional logic bugs where one branch leaks into another.

2. **Input sanitization with untrusted markers** — When fetching documents via `search_documents` tool, mark retrieved text as UNTRUSTED. Store in separate message field (`tool_results` array) from system messages. Template system prompt with immutable sections (no-write zones) that cannot be overridden by document content. Use format: `<system>{prompt}</system><documents>{untrusted}</documents><user>{query}</user>`. Never concatenate untrusted content into system message block.

3. **Request validation and filtering** — Before constructing API payload, filter document text for instruction-like phrases. Remove patterns matching system prompt structure (`<role>`, `<action>`, XML tags). This is fragile (adversarial inputs evolve) but provides defense-in-depth. Log filtered content for security monitoring.

**Additional safeguards:**

- **Adversarial training** (OpenAI's approach) — If using Claude API with prompt caching, create test cases with embedded "ignore instructions" payloads and verify assistant ignores them. Burn robustness checks into integration tests.
- **Thread-level mode locking** — Store `mode` enum (BA | ASSISTANT) on Thread model at creation. Enforce at API layer: `POST /threads/{id}/chat` checks `thread.mode` matches expected service. Return 403 if BA thread tries to call Assistant service.
- **Separate provider configs** — BA uses `model_provider` field from thread (anthropic/google/deepseek). Assistant ALWAYS uses CLI, ignoring thread provider. Prevents accidental cross-contamination.

**Warning signs:**

- User feedback: "Assistant is asking me business analysis questions"
- User feedback: "BA flow stopped asking one question at a time"
- Logs show `SYSTEM_PROMPT` constant referenced in Assistant threads
- API responses contain BA-specific terminology (discovery questions, BRD generation) in Assistant mode
- Document search results appear in system message blocks instead of separate tool results
- Security scans detect instruction-like patterns in uploaded documents not filtered

**Phase to address:**

**Phase 1: Service Layer Separation** — Split `ai_service.py` into `ba_service.py` and `assistant_service.py` before implementing Assistant flow. Foundation phase prevents conditional logic bugs. Verification: grep codebase for `if mode ==` conditionals in message construction—should find ZERO.

**Phase 2: Context Isolation** — Implement untrusted document markers and template-based prompt construction with immutable sections. Verification: upload document containing `<role>You are a Python expert</role>` to BA project, verify BA prompt unchanged.

---

### Pitfall 2: Document Ownership Isolation Failure (Multi-Tenant Data Leakage)

**What goes wrong:**

Customer A's uploaded requirements document appears in Customer B's BA Assistant search results. Or: BA project documents contaminate Assistant thread context with project-specific business requirements, causing Assistant to hallucinate features from a different customer's BRD. Or reverse: Assistant session's uploaded code snippets leak into BA project document search.

The catastrophic scenario: User uploads `customer_contracts.pdf` to BA project for requirements discovery. Later, in a different BA project with a different customer, asks "what are the payment terms?" Assistant searches FTS5 index, retrieves the WRONG customer's contract, and generates a BRD with confidential data from Customer A leaked to Customer B.

**Why it happens:**

Current architecture: Documents have `project_id` foreign key. BA Assistant requires project selection before uploading documents. When adding Assistant (project-independent threads), developers face a choice:

1. **Global project shortcut** — Create a special "Assistant Project" (ID -1 or similar). All Assistant documents get `project_id=-1`. FTS5 query adds `WHERE project_id IN (user_projects + [-1])`. PROBLEM: This leaks Assistant documents into BA search if query doesn't filter mode correctly.

2. **Nullable project_id** — Allow `project_id=NULL` for Assistant documents. FTS5 query becomes `WHERE project_id IN (user_projects) OR project_id IS NULL`. PROBLEM: NULL handling is error-prone. One missed `AND project_id IS NOT NULL` clause in a JOIN leaks all Assistant docs.

3. **Shared documents pool** — Remove project_id scoping entirely, add `owner_user_id`. All users see all their documents across projects. PROBLEM: Violates multi-tenant isolation. Customer requirements from different BA projects contaminate each other.

Root cause (2026 multi-tenant guidance): **Row-Level Security and tenant_id enforcement** not implemented at database layer. Application-layer filtering (`WHERE project_id IN (...)`) is fragile—one SQL query without the filter leaks data. Lack of explicit `scope` discriminator field means no way to distinguish BA vs Assistant documents in queries.

**How to avoid:**

**Recommended architecture (defense-in-depth):**

1. **Explicit scope discriminator** — Add `scope` enum to Document model: `BA_PROJECT | ASSISTANT_THREAD`. Add `context_id` field (polymorphic foreign key): stores `project_id` for BA docs, `thread_id` for Assistant docs. Every document has EXACTLY ONE scope and EXACTLY ONE context.

   ```python
   class Document(Base):
       scope = Column(Enum("BA_PROJECT", "ASSISTANT_THREAD"), nullable=False)
       context_id = Column(Integer, nullable=False)  # project_id or thread_id
       # Composite index for fast scoped queries
       __table_args__ = (Index("idx_scope_context", "scope", "context_id"),)
   ```

2. **Service-layer scoping enforcement** — `ba_service.py` ONLY queries `WHERE scope='BA_PROJECT' AND context_id IN (user_project_ids)`. `assistant_service.py` ONLY queries `WHERE scope='ASSISTANT_THREAD' AND context_id=thread_id`. Services never share query logic. Prevents conditional logic bugs.

3. **Database-level Row-Level Security** (if using PostgreSQL instead of SQLite) — Create RLS policies enforcing scope. Even if application SQL is buggy, database rejects cross-scope access. For SQLite, enforce in base repository class with mandatory scope parameter.

4. **Separate FTS5 virtual tables** — Create `documents_ba_fts` and `documents_assistant_fts` instead of one shared FTS index. Physically separate search indexes prevent accidental cross-contamination. Downside: duplicates FTS infrastructure. Trade-off for security.

**Additional safeguards:**

- **Audit logging** — Log every document search with `scope`, `context_id`, `user_id`. Monitor for anomalous patterns (BA query returning Assistant docs).
- **Integration tests with cross-contamination scenarios** — Create BA project with doc "Secret BA Data". Create Assistant thread with doc "Secret Assistant Data". Verify BA search never returns Assistant doc and vice versa.
- **Migration safety** — When adding `scope` field, existing docs get `scope='BA_PROJECT'`. No nullable fields—explicit is better than implicit.

**Warning signs:**

- User reports seeing documents they didn't upload
- FTS5 search returns results from different projects
- Document detail view shows wrong project/thread in breadcrumb
- Audit logs show `context_id` mismatches (BA service querying thread_id)
- Unit tests for scoped queries are missing or inadequate
- SQL queries with `OR project_id IS NULL` or magic values like `-1`

**Phase to address:**

**Phase 1: Data Model Isolation** — Add `scope` and `context_id` fields to Document model BEFORE implementing Assistant upload. Database migration first. Verification: all existing documents have `scope='BA_PROJECT'`. No NULL scopes.

**Phase 2: Service Scoping** — Enforce scope in service layer. BA service rejects Assistant docs, Assistant service rejects BA docs. Verification: integration test with cross-contamination scenario fails as expected.

---

### Pitfall 3: CLI Subprocess Blocking Event Loop (Async/Await Violations)

**What goes wrong:**

User sends message to Assistant thread. WebSocket connection hangs for 30-60 seconds. All other users' connections freeze—no heartbeats, no messages. Frontend shows infinite loading. Backend logs show CPU spike on single core. Server becomes unresponsive, requires restart.

Root cause: `subprocess.run(['claude', 'chat', message], capture_output=True)` in FastAPI endpoint. This synchronous call blocks the entire asyncio event loop. FastAPI runs on a single-threaded async runtime—one blocking operation freezes all concurrent requests.

The failure compounds: Claude CLI streams output over 30s. During this time, heartbeat tasks can't run (event loop blocked). Proxies timeout WebSocket connections after 60s of silence. By the time CLI returns, connection is dead. User never sees response.

**Why it happens:**

Asyncio subprocess pitfalls (Python 3.14 docs, WebSocket real-time patterns 2026):

1. **Synchronous subprocess.run() blocks event loop** — Developer familiar with `subprocess` module uses it in async context. No error at runtime—just hangs. Python doesn't warn about blocking calls in async functions.

2. **Missing await on asyncio.create_subprocess_exec()** — Correct pattern is `proc = await asyncio.create_subprocess_exec()`, but developer forgets `await`. Code compiles but doesn't work.

3. **Garbage collection kills child process** — If `proc` object goes out of scope while process still running, Python kills the child. Happens when streaming output—developer doesn't keep reference to process object.

4. **Windows ProactorEventLoop requirement** — On Windows, `SelectorEventLoop` has NO subprocess support. Code works on Mac/Linux dev machines, fails in production Windows. No error message—subprocess calls just hang.

5. **Missing drain() causes backpressure** — After `websocket.send()`, must call `await websocket.drain()` to flush buffer. Without drain(), messages queue in memory until buffer full, then everything blocks.

6. **Thread-unsafe transports** — asyncio transport classes (low-level WebSocket) are not thread-safe. If using `asyncio.run_coroutine_threadsafe()` to bridge sync/async, must not share transport objects across threads.

**How to avoid:**

**Correct async subprocess pattern:**

```python
async def stream_claude_cli(message: str) -> AsyncGenerator[str, None]:
    """Stream Claude CLI output via WebSocket without blocking."""

    # 1. Create async subprocess with pipes
    proc = await asyncio.create_subprocess_exec(
        'claude', 'chat', message,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=1024 * 1024  # 1MB buffer limit prevents memory exhaustion
    )

    # 2. Keep reference to proc (prevent GC from killing it)
    try:
        # 3. Stream stdout line-by-line
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            yield line.decode('utf-8')

        # 4. Wait for process to exit
        await proc.wait()

        # 5. Check exit code
        if proc.returncode != 0:
            stderr = await proc.stderr.read()
            raise RuntimeError(f"CLI failed: {stderr.decode()}")

    finally:
        # 6. Clean up: kill process if still running
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
```

**WebSocket integration with backpressure:**

```python
@router.post("/assistant/threads/{thread_id}/chat")
async def assistant_chat(thread_id: int, message: str, websocket: WebSocket):
    await websocket.accept()

    try:
        async for chunk in stream_claude_cli(message):
            await websocket.send_text(chunk)
            await websocket.drain()  # CRITICAL: flush buffer
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
```

**Platform-specific handling:**

```python
import sys
import asyncio

# Ensure Windows compatibility
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

**Additional safeguards:**

- **Timeout on subprocess** — Wrap in `asyncio.wait_for(proc.wait(), timeout=300)` to kill after 5 minutes max.
- **Supervisor loop for reconnects** — Claude CLI might disconnect. Implement reconnect with exponential backoff.
- **Process pool limits** — Limit concurrent CLI processes (e.g., max 10). Use semaphore to prevent spawning 100 processes under load.
- **Health checks** — Ping CLI on startup to verify it's installed and functional. Fast-fail with clear error if missing.

**Warning signs:**

- FastAPI logs show `blocking I/O` warnings
- All WebSocket connections hang simultaneously
- CPU usage spikes to 100% on single core during Assistant messages
- `subprocess.run()` or `subprocess.Popen()` calls in async functions
- Missing `await` keywords before subprocess calls
- No timeout handling on subprocess wait()
- Windows-specific test failures (works on Mac, fails on Windows)
- WebSocket connections timeout after 60s

**Phase to address:**

**Phase 1: Async Subprocess Infrastructure** — Implement `stream_claude_cli()` utility with all safeguards BEFORE integrating into chat endpoint. Unit test with mock subprocess. Verification: stress test with 10 concurrent Assistant threads, no blocking.

**Phase 2: WebSocket Integration** — Connect CLI streaming to WebSocket with proper backpressure. Integration test: send message, verify streaming chunks arrive in real-time. Verification: heartbeats continue during CLI processing.

---

### Pitfall 4: GoRouter Navigation Context Conflicts

**What goes wrong:**

User clicks "BA Assistant" tab. App navigates to `/ba/projects`. User selects project, navigates to `/ba/projects/123/threads`. User clicks "Assistant" tab to switch modes. App crashes with `currentConfiguration.isNotEmpty: You have popped the last page off of the stack`. Or: URL shows `/assistant/threads/456` but screen still displays BA project thread.

Second failure mode: Deep link `/assistant/threads/789` opens in BA project context. User sees project selector instead of Assistant UI. Breadcrumb shows "Project > Thread" instead of just "Thread". Assistant messages try to call BA-specific endpoints, get 403 errors.

Third failure mode: `Navigator.pop()` called twice (close modal, then close detail screen). In `StatefulShellRoute` architecture, this drops the entire navigation stack instead of just the two top screens. App shows blank screen, no back button works.

**Why it happens:**

GoRouter + StatefulShellRoute conflicts (Flutter issues #142678, #160504, #154759, #134373):

1. **Mixing Navigator and GoRouter calls** — Existing BA Assistant likely uses `Navigator.push()` for some modals. When adding GoRouter for tab switching, mixing `Navigator.pop()` with `GoRouter.go()` breaks state. GoRouter doesn't track Navigator stack—popping last Navigator route pops GoRouter stack too.

2. **`context.push → context.pop → context.push` duplicate bug** — If navigating programmatically (not user taps), second `context.push()` pushes TWO screens. GoRouter bug with `StatefulShellRoute`. No fix as of Feb 2026—workaround is prefer `context.go()`.

3. **Simultaneous navigation events** — Two tabs clicked in quick succession. Both call `context.go()`. Race condition: first navigation hasn't completed, second conflicts. GoRouter pushes both routes onto stack simultaneously.

4. **Deep linking conflicts with StatefulShellRoute** — Deep link `/assistant/threads/789` should open Assistant tab. But if user last viewed BA tab, StatefulShellRoute tries to preserve that state. Redirect logic breaks—app shows BA project selector instead of Assistant thread.

5. **Global pages vs branch-specific pages** — Some pages (Settings, Profile) should be global (above tab bar). Others (Thread detail) should be branch-specific (within BA or Assistant section). Configuring `navigatorKey` incorrectly causes pages to open in wrong context.

**How to avoid:**

**Recommended GoRouter architecture for dual-mode app:**

```dart
final router = GoRouter(
  initialLocation: '/ba/projects',
  routes: [
    StatefulShellRoute.indexedStack(
      branches: [
        // BA Assistant branch
        StatefulShellBranch(
          navigatorKey: _baNavigatorKey,
          routes: [
            GoRoute(
              path: '/ba/projects',
              builder: (context, state) => ProjectListScreen(),
              routes: [
                GoRoute(
                  path: ':projectId/threads',
                  builder: (context, state) => ThreadListScreen(
                    projectId: state.pathParameters['projectId']!,
                  ),
                  routes: [
                    GoRoute(
                      path: ':threadId',
                      builder: (context, state) => ConversationScreen(
                        threadId: state.pathParameters['threadId']!,
                        mode: 'BA',  // Explicit mode enforcement
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),

        // Assistant branch (project-independent)
        StatefulShellBranch(
          navigatorKey: _assistantNavigatorKey,
          routes: [
            GoRoute(
              path: '/assistant/threads',
              builder: (context, state) => AssistantThreadListScreen(),
              routes: [
                GoRoute(
                  path: ':threadId',
                  builder: (context, state) => ConversationScreen(
                    threadId: state.pathParameters['threadId']!,
                    mode: 'ASSISTANT',  // Explicit mode enforcement
                  ),
                ),
              ],
            ),
          ],
        ),
      ],

      builder: (context, state, navigationShell) {
        return ScaffoldWithNavBar(
          navigationShell: navigationShell,
          onTabChange: (index) {
            // Use go(), not push()
            if (index == 0) {
              context.go('/ba/projects');
            } else {
              context.go('/assistant/threads');
            }
          },
        );
      },
    ),

    // Global routes (above tab bar)
    GoRoute(
      path: '/settings',
      builder: (context, state) => SettingsScreen(),
      parentNavigatorKey: _rootNavigatorKey,  // Bypass shell
    ),
  ],
);
```

**Best practices to prevent conflicts:**

1. **Prefer `context.go()` over `context.push()`** — `go()` modifies stack correctly for deep links. `push()` always adds, causing duplicates.

2. **Never mix Navigator and GoRouter** — Remove ALL `Navigator.push()`, `Navigator.pop()` calls. Use `context.go()`, `context.push()`, `context.pop()` exclusively.

3. **Explicit mode parameter** — Pass `mode: 'BA' | 'ASSISTANT'` to shared screens (ConversationScreen). Screen validates mode matches thread.mode from API.

4. **Separate navigator keys** — Each `StatefulShellBranch` gets its own navigator key. Prevents stack pollution.

5. **Redirect for deep links** — Add redirect function to validate deep link context:
   ```dart
   redirect: (context, state) {
     if (state.path.startsWith('/assistant/') && !isAssistantEnabled) {
       return '/ba/projects';  // Fallback if Assistant not available
     }
     return null;  // Allow navigation
   }
   ```

6. **Debounce navigation events** — If users can trigger simultaneous navigations, debounce with 200ms delay:
   ```dart
   Timer? _navigationDebounce;
   void navigateToTab(int index) {
     _navigationDebounce?.cancel();
     _navigationDebounce = Timer(Duration(milliseconds: 200), () {
       context.go(index == 0 ? '/ba/projects' : '/assistant/threads');
     });
   }
   ```

**Warning signs:**

- `currentConfiguration.isNotEmpty` assertion failures
- Duplicate screens appear after navigation
- URL doesn't match displayed screen
- Deep links open in wrong tab
- Back button doesn't work after tab switch
- `Navigator.pop()` or `Navigator.push()` calls in codebase
- Multiple `context.push()` calls for same route
- No debouncing on tab change handler

**Phase to address:**

**Phase 1: Navigation Architecture** — Design GoRouter structure with StatefulShellRoute BEFORE implementing Assistant UI. Document navigator keys, route hierarchy, mode parameter passing. Verification: deep link tests for all routes, no duplicate screens.

**Phase 2: Refactor Existing Navigation** — Remove all Navigator calls from BA Assistant, replace with GoRouter. Verification: grep for `Navigator.` finds only comments, not code.

---

### Pitfall 5: Shared Service State Leakage (Monolith Refactoring Anti-Pattern)

**What goes wrong:**

User creates BA thread, asks "What questions should I ask?" Assistant responds with BA discovery questions (correct). Same user switches to Assistant mode, asks "Write a Python script." Assistant responds "Let's explore your business objective first" (WRONG—leaked BA behavior).

Or reverse: User in BA mode asks "Help me with requirements discovery." Assistant responds with code snippets instead of discovery questions (leaked Assistant behavior).

Root cause: `ai_service.py` refactored to accept `mode` parameter but retains shared state:

```python
# Anti-pattern: shared state with conditionals
class AIService:
    def __init__(self):
        self.tools = [search_documents, save_artifact]  # Shared tool list

    async def send_message(self, thread_id: int, message: str, mode: str):
        if mode == "BA":
            system_prompt = SYSTEM_PROMPT_BA
            tools = self.tools  # Both modes share tools
        else:
            system_prompt = ""  # No prompt for Assistant
            tools = []  # But tools still initialized above

        # BUG: Conditional logic scattered through function
        # One missed branch leaks BA behavior into Assistant
        ...
```

The failure mode: Developers refactor by adding `if mode ==` conditionals throughout the existing service. Logic branches become complex (50+ lines of if/else). One branch forgets to filter BA-specific tools. Tool definitions leak into Assistant context. LLM sees `save_artifact` tool, assumes it should generate BRDs even in Assistant mode.

**Why it happens:**

Monolith-to-microservices refactoring anti-patterns (2026 guidance):

1. **Shared dependencies without explicit boundaries** — Existing code has implicit coupling: `ai_service.py` imports `SYSTEM_PROMPT` constant, `search_documents` function, `Artifact` model. When refactoring, developers parameterize the system prompt but forget tools and models are also coupled.

2. **Incremental refactoring without preparatory extraction** — The "strangler fig" pattern says wrap new functionality around the old monolith. But for AI services, this means BA and Assistant share conversation history formatting, tool definition logic, token counting, etc. Shared code with conditionals is fragile.

3. **Configuration over composition** — Developers choose one service with configuration (`mode` parameter) over two separate services. Configuration scales poorly—adding a third mode (e.g., "Code Review") requires modifying all branches. Composition (separate services) scales linearly.

4. **Database models coupling services** — `Thread` model has `model_provider` field (anthropic/google/deepseek). BA uses this field. Assistant should ALWAYS use CLI, ignoring provider. But shared service reads `thread.model_provider` unconditionally. BA thread with `provider='anthropic'` accidentally uses Anthropic API instead of CLI when in Assistant mode.

**How to avoid:**

**Modular monolith pattern (not microservices—same FastAPI app, separate modules):**

```
backend/app/services/
├── ai/                          # Shared AI utilities
│   ├── __init__.py
│   ├── llm_factory.py          # Shared LLM adapter factory
│   └── token_counter.py        # Shared token utilities
├── ba_assistant/               # BA-specific service
│   ├── __init__.py
│   ├── ba_service.py           # BA conversation logic
│   ├── ba_prompts.py           # BA system prompt
│   └── ba_tools.py             # search_documents, save_artifact
└── assistant/                  # Assistant-specific service
    ├── __init__.py
    ├── assistant_service.py    # CLI conversation logic
    ├── cli_manager.py          # Subprocess management
    └── assistant_tools.py      # CLI-specific tools (if any)
```

**Dependency injection for clean separation:**

```python
# ba_assistant/ba_service.py
from app.services.ai import LLMFactory
from app.services.ba_assistant.ba_prompts import SYSTEM_PROMPT
from app.services.ba_assistant.ba_tools import get_ba_tools

class BAService:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT  # BA-specific
        self.tools = get_ba_tools()         # BA-specific

    async def send_message(self, thread: Thread, message: str):
        # ZERO conditionals—this service is ONLY for BA
        llm = LLMFactory.create(thread.model_provider)
        return await llm.chat(
            system=self.system_prompt,
            tools=self.tools,
            history=thread.messages,
            message=message
        )

# assistant/assistant_service.py
from app.services.assistant.cli_manager import CLIManager

class AssistantService:
    def __init__(self):
        self.cli = CLIManager()  # No system prompt, no tools

    async def send_message(self, thread: Thread, message: str):
        # ZERO conditionals—this service is ONLY for Assistant
        # Ignores thread.model_provider—always uses CLI
        return await self.cli.stream_chat(
            history=thread.messages,
            message=message
        )
```

**API routing enforces separation:**

```python
# routes/ba_routes.py
from app.services.ba_assistant import BAService

@router.post("/ba/threads/{thread_id}/chat")
async def ba_chat(thread_id: int, message: str):
    thread = get_thread(thread_id)
    if thread.mode != "BA":
        raise HTTPException(403, "This thread is not a BA thread")

    service = BAService()
    return await service.send_message(thread, message)

# routes/assistant_routes.py
from app.services.assistant import AssistantService

@router.post("/assistant/threads/{thread_id}/chat")
async def assistant_chat(thread_id: int, message: str):
    thread = get_thread(thread_id)
    if thread.mode != "ASSISTANT":
        raise HTTPException(403, "This thread is not an Assistant thread")

    service = AssistantService()
    return await service.send_message(thread, message)
```

**Additional safeguards:**

- **Factory pattern for service instantiation** — Don't import services directly. Use factory: `ServiceFactory.get_service(thread.mode)` returns correct service instance. Prevents import mistakes.
- **Integration tests with mode validation** — Create BA thread, call `/assistant/threads/{id}/chat`, verify 403. Create Assistant thread, call `/ba/threads/{id}/chat`, verify 403.
- **Static analysis** — Lint rule: flag any `if mode ==` conditionals in service files. Services should have ZERO mode awareness.

**Warning signs:**

- `if mode ==` or `if thread.mode ==` conditionals in service files
- Shared tool definitions between BA and Assistant
- Single `ai_service.py` file with 500+ lines
- Tool definitions imported in both BA and Assistant code paths
- Thread model `model_provider` field accessed in Assistant service
- Logs show Assistant threads calling `save_artifact` tool
- Integration tests missing for cross-mode API calls (403 validation)

**Phase to address:**

**Phase 1: Service Extraction** — Split `ai_service.py` into `ba_service.py` and `assistant_service.py` BEFORE implementing Assistant features. Extract shared utilities (LLMFactory, token counter) into `ai/` module. Verification: no `if mode` conditionals in service files.

**Phase 2: Route Separation** — Create `ba_routes.py` and `assistant_routes.py` with mode validation. Verification: call wrong endpoint for thread mode, verify 403.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single `ai_service.py` with `mode` parameter | Faster initial implementation (no file splitting) | Unmaintainable conditionals, leaked state, hard to test modes independently | Never—service separation is foundational |
| Global "Assistant Project" (project_id=-1) | Avoids schema changes, reuses existing scoping | Multi-tenant data leakage, magic values in queries, fragile filtering | Never—explicit `scope` field required |
| `subprocess.run()` in async context | Familiar API, simple code | Blocks event loop, freezes all connections, production outages | Never—use `asyncio.create_subprocess_exec()` |
| Mixed Navigator + GoRouter calls | Reuses existing modal navigation code | Stack corruption, crashes, unmaintainable navigation | Never—full GoRouter migration required |
| Shared FTS5 index for BA + Assistant | Single search implementation | Cross-contamination risk, complex query filtering | Acceptable IF `scope` field strictly enforced at DB layer |
| Nullable `project_id` for Assistant docs | Minimal schema changes | Null-handling bugs, implicit scope, JOIN edge cases | Never—use explicit `scope` enum + `context_id` |
| Hardcoded system prompt in Assistant service | Simple to implement | No flexibility, violates DRY if multiple assistants | Acceptable for MVP (single Assistant mode), refactor in Phase 3+ |
| No CLI subprocess timeout | Simpler error handling | Infinite hangs if CLI crashes, resource leaks | Never—always set timeout (5-10 min max) |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Claude CLI subprocess | Using synchronous `subprocess.run()` in async context | Use `asyncio.create_subprocess_exec()` with streaming via `stdout.readline()` |
| GoRouter deep linking | Not validating mode in redirect logic | Add `redirect: (context, state) => validateMode(state.path)` |
| FTS5 document search | Single query for both BA and Assistant | Separate queries with explicit scope: `WHERE scope='BA_PROJECT' AND context_id IN (...)` |
| WebSocket heartbeats | Missing during CLI streaming | Wrap CLI stream with `stream_with_heartbeat()` utility |
| LLM API calls | Hardcoding provider selection | Read `thread.model_provider` for BA, ignore for Assistant (always CLI) |
| System prompt construction | Concatenating document results into system message | Use separate message fields: `<system>`, `<documents>`, `<user>` with immutable sections |
| Thread creation | No mode enforcement at creation | Require `mode` enum in `POST /threads`, validate at API layer |
| Document upload | No scope validation | Reject upload if `scope='ASSISTANT_THREAD'` but `context_id` points to project |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Blocking subprocess calls | All WebSocket connections freeze during one CLI call | Use async subprocess, process pool with semaphore limiting concurrency | First production user sends Assistant message |
| No CLI process limits | Server spawns 100+ `claude` processes under load | Semaphore with max 10 concurrent CLI processes | 20+ concurrent users in Assistant mode |
| Shared FTS5 index without partitioning | Document search slows as corpus grows | Separate `documents_ba_fts` and `documents_assistant_fts` virtual tables | 10k+ documents across all users |
| Loading full conversation history | API timeout when thread has 500+ messages | Paginate history, load last 50 messages + summary of older | Thread with 200+ messages |
| No token budget enforcement | Context overflow errors, silent truncation | Track tokens per message, enforce limits: system 2k + history 50k + docs 100k | First large document upload |
| Synchronous document encryption | Upload blocks for 5-10s per file | Use `asyncio.gather()` to encrypt multiple docs in parallel | Batch upload of 5+ files |
| No WebSocket connection pooling | Frontend creates new connection per message | Reuse WebSocket connection for entire thread session | High-frequency messaging (10+ msgs/min) |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| No context isolation between BA and Assistant prompts | Prompt injection—user uploads doc with "ignore previous instructions", manipulates BA behavior | Use `<system>` immutable sections, mark documents as `<untrusted>`, filter instruction-like patterns |
| Shared document search across scopes | Multi-tenant data leakage—Customer A's BRD appears in Customer B's search | Enforce `scope` enum at DB layer, separate service queries, audit log all searches |
| No subprocess timeout on CLI calls | Denial of service—malicious input causes CLI to hang forever, resource exhaustion | Set 5-10 min timeout on `asyncio.wait_for(proc.wait())`, kill process on timeout |
| Trusting thread.mode from frontend | Mode spoofing—attacker sends BA thread ID to Assistant endpoint, bypasses scoping | Validate `thread.mode` at API layer, return 403 if mismatch |
| No input sanitization on document text | Stored XSS—malicious doc contains script tags, renders in frontend preview | Sanitize HTML in document text, use `text/plain` rendering for untrusted content |
| Mixing CLI stdout/stderr | Sensitive errors leak to user—CLI stderr contains API keys or paths | Separate stdout (user content) from stderr (logs), filter stderr before displaying |
| No rate limiting on CLI calls | Resource exhaustion—user spams Assistant, spawns 1000 processes | Per-user rate limit: 10 CLI calls/min, 100/hour |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No visual distinction between BA and Assistant modes | Users confuse modes, ask BA questions in Assistant, frustrated by wrong responses | Clear mode indicator in UI (color-coded tabs, prominent label), separate navigation paths |
| Switching modes preserves context | User in BA thread clicks "Assistant" tab, expects new context but sees BA project docs in search | Clear context on mode switch, show empty state or recent Assistant threads (not BA state) |
| No loading state during CLI streaming | 10-30s silence, user thinks app froze, refreshes page mid-response | Show "Claude is thinking..." with animated dots, heartbeat every 5s confirms connection alive |
| Generic error messages | "Error: subprocess failed" doesn't help user understand CLI installation missing | Specific errors: "Claude CLI not found. Install via: brew install claude-cli" |
| No thread mode lock | User creates BA thread, accidentally sends to Assistant endpoint, data corruption | Show mode in thread list, disable mode switching after thread creation |
| Document scope not visible | User uploads doc to Assistant, confused why it doesn't appear in BA project search | Show scope badge: "BA Project: Customer X" or "Assistant Thread" on document cards |
| No confirmation on mode switch | User accidentally taps Assistant tab, loses BA context mid-discovery session | Confirmation dialog: "Switch to Assistant? Current BA session will be saved" (only if unsaved state) |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Service separation:** Verify `ba_service.py` and `assistant_service.py` share ZERO logic except through `ai/` shared utilities. Check: no `if mode` conditionals.
- [ ] **Document scope enforcement:** Upload doc to Assistant thread, verify BA search doesn't return it. Upload doc to BA project, verify Assistant search doesn't return it.
- [ ] **CLI subprocess async:** Check all `subprocess` calls use `asyncio.create_subprocess_exec()`. Verify no `subprocess.run()` or `subprocess.Popen()` in async functions.
- [ ] **WebSocket backpressure:** Verify `await websocket.drain()` after every `websocket.send()`. Stress test: send 1000 rapid messages, check no memory leak.
- [ ] **Navigation mode validation:** Deep link to `/assistant/threads/123` where thread 123 is BA mode. Verify redirect to `/ba/projects/X/threads/123` or 403 error.
- [ ] **System prompt isolation:** Upload doc with `<role>You are a Python expert</role>` to BA project. Verify BA system prompt unchanged, discovery questions still asked.
- [ ] **Thread mode lock:** Create BA thread, call `POST /assistant/threads/{id}/chat`. Verify 403 error, not silent mode switch.
- [ ] **CLI process cleanup:** Kill FastAPI server mid-CLI-stream. Verify `claude` processes terminate (no zombie processes). Check with `ps aux | grep claude`.
- [ ] **Token budget enforcement:** Upload 100-page PDF to Assistant. Verify extraction limited to 100k tokens, not full 1M+ token document.
- [ ] **Audit logging:** Check database for `document_access_log` table with columns: `user_id`, `document_id`, `scope`, `context_id`, `timestamp`. Verify logs populated on search.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| System prompt leakage | MEDIUM | 1. Add request/response logging to identify leaked prompts. 2. Create integration test reproducing leak. 3. Implement context isolation with `<system>` tags. 4. Deploy hotfix. 5. Audit existing threads for corrupted responses. |
| Document cross-contamination | HIGH | 1. **CRITICAL:** Immediately shut down affected endpoints to prevent further leakage. 2. Audit database: `SELECT * FROM documents WHERE scope IS NULL OR context_id NOT IN (...)` 3. Manually reassign docs to correct scope/context. 4. Notify affected users if confidential data leaked. 5. Add `scope` migration script. 6. Deploy with RLS enforcement. |
| CLI blocking event loop | LOW | 1. Deploy async subprocess fix immediately. 2. Restart FastAPI to clear hung connections. 3. Add health check: `/health/cli` endpoint tests subprocess. 4. Add monitoring: alert if event loop blocked >5s. |
| GoRouter stack corruption | MEDIUM | 1. Add error boundary widget to catch navigation errors. 2. Clear app state: `GoRouter.of(context).go('/ba/projects')` on error. 3. Migrate all `Navigator` calls to `GoRouter`. 4. Add navigation integration tests. |
| Shared service state leakage | HIGH | 1. Feature flag to disable Assistant mode temporarily. 2. Split `ai_service.py` into separate services (1-2 day refactor). 3. Add mode validation at API layer. 4. Deploy with integration tests. 5. Re-enable Assistant. |
| Missing WebSocket drain() | LOW | 1. Add `drain()` after all `send()` calls. 2. Deploy immediately. 3. Verify with load test (100 concurrent connections). 4. Add linter rule flagging `send()` without subsequent `drain()`. |
| No subprocess timeout | MEDIUM | 1. Add `asyncio.wait_for(proc.wait(), timeout=600)` around all CLI calls. 2. Add process cleanup in finally block. 3. Deploy. 4. Monitor for timeout events, adjust limit if needed. |
| No document scope field | HIGH | 1. **DATA MIGRATION REQUIRED.** 2. Add `scope` and `context_id` columns. 3. Backfill: `UPDATE documents SET scope='BA_PROJECT', context_id=project_id WHERE project_id IS NOT NULL`. 4. Add NOT NULL constraints. 5. Update all queries. 6. Deploy with integration tests. 7. Monitor audit logs for a week. |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| System prompt injection | Phase 1: Service Layer Separation | Upload doc with `<role>` tag to BA project. BA prompt unchanged. |
| System prompt injection | Phase 2: Context Isolation | `search_documents` results in `<documents>` section, not `<system>`. |
| Document cross-contamination | Phase 1: Data Model Isolation | BA search query NEVER returns Assistant docs (integration test). |
| Document cross-contamination | Phase 2: Service Scoping | `ba_service.py` and `assistant_service.py` have separate query functions. |
| CLI blocking event loop | Phase 1: Async Subprocess Infrastructure | Stress test: 10 concurrent CLI calls, event loop never blocks >100ms. |
| CLI blocking event loop | Phase 2: WebSocket Integration | Send Assistant message, verify heartbeats continue during CLI processing. |
| GoRouter navigation conflicts | Phase 1: Navigation Architecture | Deep link to all routes, verify no crashes or duplicate screens. |
| GoRouter navigation conflicts | Phase 2: Refactor Existing Navigation | `grep -r "Navigator\." frontend/lib` finds zero hits (only GoRouter calls). |
| Shared service state leakage | Phase 1: Service Extraction | `ai_service.py` split into `ba_service.py`, `assistant_service.py`, `ai/` utils. |
| Shared service state leakage | Phase 2: Route Separation | Call `/assistant/threads/{ba_thread_id}/chat`, verify 403 error. |
| No subprocess timeout | Phase 1: Async Subprocess Infrastructure | CLI call with infinite loop input, verify kills after 10 min. |
| No WebSocket backpressure | Phase 2: WebSocket Integration | Send 1000 rapid messages, no memory leak, all delivered. |
| No document scope enforcement | Phase 1: Data Model Isolation | Database schema has `scope` NOT NULL with CHECK constraint. |
| Token budget explosion | Phase 3: Content Limits | Upload 100-page PDF, verify extraction stops at 100k tokens with warning. |

---

## Sources

### OWASP & Security
- [LLM Prompt Injection Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [LLM01:2025 Prompt Injection - OWASP Gen AI Security Project](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [New Prompt Injection Attack Vectors Through MCP Sampling - Palo Alto Networks](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/)
- [MCP Security Vulnerabilities: How to Prevent Prompt Injection and Tool Poisoning Attacks in 2026 - Practical DevSecOps](https://www.practical-devsecops.com/mcp-security-vulnerabilities/)
- [Multi Tenant Security - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)

### Multi-Tenant Isolation
- [Multi-Tenant Deployment: 2026 Complete Guide & Examples | Qrvey](https://qrvey.com/blog/multi-tenant-deployment/)
- [The Multi-Tenant Performance Crisis: Advanced Isolation Strategies for 2026 - AddWeb Solution](https://www.addwebsolution.com/blog/multi-tenant-performance-crisis-advanced-isolation-2026)
- [Tenant isolation in multi-tenant systems: What you need to know — WorkOS](https://workos.com/blog/tenant-isolation-in-multi-tenant-systems)
- [How to isolate each tenant's data in a multi-tenant SAAS application in Azure? - Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/1920935/how-to-isolate-each-tenants-data-in-a-multi-tenant)

### State Management & Agent Architecture
- [Microsoft Agent Framework Workflows - State Isolation | Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/state-isolation)
- [Microsoft Agent Framework Workflows - Shared States | Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/shared-states)
- [Stateful vs. stateless agents: How ZBrain helps build stateful agents](https://zbrain.ai/building-stateful-agents-with-zbrain/)

### Python Asyncio & WebSocket
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Getting Started with FastAPI WebSockets | Better Stack Community](https://betterstack.com/community/guides/scaling-python/fastapi-websockets/)
- [Python WebSocket Servers: Real-Time Communication Patterns](https://dasroot.net/posts/2026/02/python-websocket-servers-real-time-communication-patterns/)
- [Subprocesses — Python 3.14.3 documentation](https://docs.python.org/3/library/asyncio-subprocess.html)
- [Streams — Python 3.14.3 documentation](https://docs.python.org/3/library/asyncio-stream.html)
- [How to Run Two Async Functions Forever in Python (asyncio Patterns I Use in 2026) – TheLinuxCode](https://thelinuxcode.com/how-to-run-two-async-functions-forever-in-python-asyncio-patterns-i-use-in-2026/)

### Flutter GoRouter
- [GoRouter in Flutter: complete guide to advanced navigation](https://www.spaghetticoders.it/en/2026/01/26/lezione-5-navigazione-avanzata-in-flutter-con-gorouter-senza-incasinare-lapp/)
- [go_router | Flutter package](https://pub.dev/packages/go_router)
- [Flutter Navigation with GoRouter: Go vs Push](https://codewithandrea.com/articles/flutter-navigation-gorouter-go-vs-push/)
- [GitHub Issue #142678: two Navigator.pop() calls drops the whole navigation stack inside StatefulShellRoute](https://github.com/flutter/flutter/issues/142678)
- [GitHub Issue #160504: Simultaneous Button Taps Trigger Multiple Navigation Events](https://github.com/flutter/flutter/issues/160504)
- [GitHub Issue #154759: context.push --> context.pop --> context.push causes pages to be presented twice](https://github.com/flutter/flutter/issues/154759)
- [GitHub Issue #134373: Deep Linking Behavior Conflicts with StatefulShellRoute](https://github.com/flutter/flutter/issues/134373)

### Refactoring Monoliths
- [Refactoring a monolith to microservices - microservices.io](https://microservices.io/refactoring/)
- [What Is Microservices Architecture? | Google Cloud](https://cloud.google.com/architecture/microservices-architecture-refactoring-monoliths)
- [Decomposing monoliths into microservices - AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html)
- [How to break a Monolith into Microservices - Martin Fowler](https://martinfowler.com/articles/break-monolith-into-microservices.html)
- [Refactoring Towards Microservices: Preparing the Ground for Service Extraction - arXiv](https://arxiv.org/html/2510.03050)

---

*Pitfalls research for: Dual-mode AI chat app (BA Assistant + Claude Code CLI)*
*Researched: 2026-02-17*
*Confidence: HIGH (synthesized from 30+ authoritative sources, domain-specific to adding second mode to existing chat app)*
