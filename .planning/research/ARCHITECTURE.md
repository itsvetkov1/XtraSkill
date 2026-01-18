# Architecture Patterns: AI-Powered Conversational Platform with Document Context

**Domain:** AI-powered business analyst assistant with document management
**Researched:** 2026-01-17
**Confidence:** HIGH

## Executive Summary

AI-powered conversational platforms with document context follow a **layered architecture** separating presentation (Flutter), business logic (FastAPI), AI orchestration (Claude Agent SDK), and data persistence (SQLite). The critical architectural pattern is **agentic tool orchestration** where the AI autonomously decides when to search documents, generate artifacts, or respond conversationally.

**Key Pattern:** Request → Backend → Agent SDK (with custom tools) → Stream Response

This architecture enables:
- Real-time streaming AI responses via Server-Sent Events
- Document context injection through autonomous tool calling
- Multi-threaded conversation management per project
- Artifact generation and export in multiple formats
- Cross-device synchronization through centralized backend

## Recommended Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Flutter Web  │  │Flutter Android│ │  Flutter iOS │         │
│  │              │  │               │ │              │         │
│  └──────┬───────┘  └──────┬────────┘ └──────┬───────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                   REST API + SSE Stream                         │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    API/ORCHESTRATION LAYER                      │
│                    ┌───────▼────────┐                           │
│                    │ FastAPI Server │                           │
│                    │ (Python 3.11+) │                           │
│                    └───────┬────────┘                           │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                 │
│   ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼─────┐          │
│   │   Auth    │    │   Project   │    │    AI     │          │
│   │  Service  │    │   Service   │    │  Service  │          │
│   │ (OAuth)   │    │   (CRUD)    │    │ (Agentic) │          │
│   └───────────┘    └──────┬──────┘    └─────┬─────┘          │
│                            │                  │                 │
└────────────────────────────┼──────────────────┼─────────────────┘
                             │                  │
┌────────────────────────────┼──────────────────┼─────────────────┐
│                      AI AGENT LAYER                             │
│                            │          ┌───────▼───────┐         │
│                            │          │ Claude Agent  │         │
│                            │          │     SDK       │         │
│                            │          └───────┬───────┘         │
│                            │                  │                 │
│                            │          ┌───────▼───────┐         │
│                            │          │ Custom Tools: │         │
│                            │          │ - DocSearch   │         │
│                            │          │ - ArtifactGen │         │
│                            │          │ - ThreadSum   │         │
│                            │          └───────┬───────┘         │
│                            │                  │                 │
└────────────────────────────┼──────────────────┼─────────────────┘
                             │                  │
┌────────────────────────────┼──────────────────┼─────────────────┐
│                        DATA LAYER                               │
│                    ┌───────▼──────┐    ┌──────▼──────┐         │
│                    │   SQLite     │    │  Anthropic  │         │
│                    │   Database   │    │  Claude API │         │
│                    │  (Encrypted) │    │             │         │
│                    │   + FTS5     │    │  (Sonnet)   │         │
│                    └──────────────┘    └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With | Technology |
|-----------|----------------|-------------------|------------|
| **Flutter Client** | UI rendering, user input, state management, SSE consumption | FastAPI Server (REST + SSE) | Flutter, Provider, Dio, SSE client |
| **FastAPI Server** | Request routing, authentication, business logic, response streaming | Flutter Client, SQLite, AI Service | FastAPI, SQLAlchemy, asyncio |
| **Auth Service** | OAuth flows, JWT generation, token validation | OAuth Providers (Google/MS), SQLite | authlib, python-jose |
| **Project Service** | Project/thread/document CRUD, ownership validation | SQLite, FastAPI routes | SQLAlchemy ORM |
| **AI Service** | Agent session management, tool orchestration, streaming | Claude Agent SDK, SQLite (document search) | Claude Agent SDK (Python) |
| **Claude Agent SDK** | Tool execution loop, AI reasoning, response generation | Anthropic API, Custom Tools | claude-agent-sdk |
| **Custom Tools** | DocumentSearch (FTS5 query), ArtifactGenerator (formatting), ThreadSummarizer | SQLite, AI Service context | Python async functions |
| **SQLite Database** | Data persistence, full-text search, encrypted storage | All service layers | SQLite 3.x, SQLCipher, FTS5 |
| **Anthropic API** | LLM inference, streaming responses, tool calling protocol | Claude Agent SDK | Claude Sonnet 4.5 API |

**Critical Boundary: Agent SDK as Orchestration Layer**

The Claude Agent SDK sits between business logic and AI API, handling:
- Tool invocation decisions (AI decides when to search docs)
- Multi-turn conversation management
- Streaming response assembly
- Error recovery and retries

This boundary means **your backend doesn't implement tool loops**—Agent SDK handles that complexity.

### Data Flow Patterns

#### Pattern 1: User Message → AI Response with Document Search

```
1. User types message in Flutter thread screen
   └─> Flutter: POST /threads/{id}/messages {"content": "..."}

2. FastAPI receives message, validates JWT, checks thread ownership
   └─> Save user message to SQLite (messages table)

3. FastAPI invokes AI Service with message + conversation history
   └─> AI Service initializes Agent SDK session with:
       - Conversation history (last 20 messages)
       - Project context (project_id, available documents list)
       - Custom tools: [DocumentSearch, ArtifactGenerator, ThreadSummarizer]

4. Agent SDK sends message to Claude API with tool definitions
   └─> Claude reasons about message, decides if tools needed

5. Claude determines document search is useful
   └─> Claude calls DocumentSearch tool with keywords
   └─> Agent SDK invokes your DocumentSearch function
   └─> DocumentSearch queries SQLite FTS5 for matching document chunks
   └─> Returns top 5 relevant chunks to Agent SDK
   └─> Agent SDK sends tool results back to Claude API

6. Claude generates response incorporating document context
   └─> Claude API streams response tokens
   └─> Agent SDK yields chunks to AI Service
   └─> AI Service streams via SSE to Flutter client

7. Flutter SSE client receives chunks in real-time
   └─> Updates UI progressively (token-by-token display)

8. On completion, FastAPI saves AI response to SQLite
   └─> Returns 200 OK, closes SSE stream
```

**Key Insight:** AI autonomously decides when to search documents. No explicit "search" command needed—agentic behavior.

#### Pattern 2: Artifact Generation Flow

```
1. User requests artifact: "Generate user story"
   └─> Follows same flow as Pattern 1 until...

2. Claude recognizes artifact generation intent
   └─> Calls ArtifactGenerator tool with type + content
   └─> Tool formats output as structured markdown
   └─> Returns formatted artifact to Agent SDK

3. AI Service detects artifact in response
   └─> Saves artifact to SQLite (artifacts table)
   └─> Links artifact to message (message_id foreign key)

4. SSE stream includes artifact event:
   event: artifact
   data: {"artifact_id": "uuid", "type": "user_story", "title": "..."}

5. Flutter receives artifact event
   └─> Displays artifact inline with special formatting
   └─> Enables export button (Markdown, PDF, Word)

6. User clicks export → GET /artifacts/{id}/export?format=pdf
   └─> Backend retrieves artifact markdown from SQLite
   └─> Converts to PDF via WeasyPrint
   └─> Returns file download
```

**Key Insight:** Artifacts are first-class objects, stored separately from messages, exportable on-demand.

#### Pattern 3: Project Document Upload and Indexing

```
1. User uploads document text via Flutter UI
   └─> POST /projects/{id}/documents {"name": "...", "content": "..."}

2. FastAPI validates ownership + input
   └─> Encrypts document content (Fernet symmetric encryption)
   └─> Saves to SQLite documents table
   └─> Triggers FTS5 indexing (SQLite trigger updates documents_fts)

3. FTS5 index updated with document content
   └─> Document now searchable by DocumentSearch tool

4. Returns document metadata to Flutter
   └─> Flutter updates project document list
```

**Key Insight:** Documents indexed immediately, available to AI in next conversation turn.

#### Pattern 4: Cross-Device Synchronization

```
1. User logs in from different device (e.g., mobile after web)
   └─> OAuth flow → JWT token issued

2. Flutter requests projects: GET /projects
   └─> Backend queries SQLite for user's projects
   └─> Returns full project list with metadata

3. User opens project → GET /projects/{id}/threads
   └─> Backend returns threads with AI-generated summaries

4. User opens thread → GET /threads/{id}/messages
   └─> Backend returns full conversation history
   └─> Flutter renders chat interface with history

5. User continues conversation from new device
   └─> Same flow as Pattern 1, seamless continuation
```

**Key Insight:** Stateless backend + centralized database = natural cross-device sync. No special sync logic needed.

### Integration Patterns

#### REST API (Standard CRUD Operations)

**Pattern:** Synchronous request-response for data operations

**Used For:**
- Project/thread/document creation and retrieval
- Authentication flows (OAuth callback, token refresh)
- Artifact export requests

**Example:**
```python
# FastAPI endpoint
@app.post("/projects")
async def create_project(
    project: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_project = Project(
        user_id=user.id,
        name=project.name,
        description=project.description
    )
    db.add(new_project)
    db.commit()
    return new_project
```

**Flutter Client:**
```dart
final response = await dio.post(
  '/projects',
  data: {'name': projectName, 'description': description},
  options: Options(headers: {'Authorization': 'Bearer $token'}),
);
```

#### SSE Streaming (AI Responses)

**Pattern:** Unidirectional server-to-client streaming for real-time updates

**Used For:**
- Streaming AI response tokens as they're generated
- Tool call notifications ("Searching documents...")
- Artifact generation events

**Example:**
```python
# FastAPI SSE endpoint
@app.get("/threads/{thread_id}/stream")
async def stream_ai_response(
    thread_id: str,
    message_id: str,
    user: User = Depends(get_current_user)
):
    async def event_generator():
        yield {"event": "start", "data": {"message_id": message_id}}

        async for chunk in ai_service.process_message(thread_id, message_id):
            if chunk.type == "content":
                yield {"event": "chunk", "data": {"content": chunk.text}}
            elif chunk.type == "tool_call":
                yield {"event": "tool_call", "data": {"tool": chunk.tool_name}}
            elif chunk.type == "artifact":
                yield {"event": "artifact", "data": chunk.artifact_metadata}

        yield {"event": "complete", "data": {"message_id": message_id}}

    return EventSourceResponse(event_generator())
```

**Flutter Client:**
```dart
final sseClient = SseClient(
  Uri.parse('$apiUrl/threads/$threadId/stream?message_id=$messageId'),
);

sseClient.stream.listen((event) {
  if (event.event == 'chunk') {
    setState(() => aiResponse += event.data['content']);
  } else if (event.event == 'tool_call') {
    showToolIndicator(event.data['tool']);
  }
});
```

**Why SSE over WebSockets:**
- Simpler implementation (HTTP-based, no connection upgrade)
- Automatic reconnection on drop
- Works with standard load balancers (no sticky sessions)
- Unidirectional matches use case (server → client streaming)

#### Agent SDK Tool Integration

**Pattern:** Declarative tool definitions with async execution functions

**Used For:**
- Document search during conversations
- Artifact generation with structured formatting
- Thread summarization for UI display

**Example:**
```python
# Custom tool implementation
async def document_search_tool(project_id: str, keywords: str) -> dict:
    """Search project documents for relevant content."""
    # Query SQLite FTS5 index
    query = f"""
        SELECT documents.name, snippet(documents_fts, 1, '<mark>', '</mark>', '...', 30) as snippet
        FROM documents_fts
        JOIN documents ON documents.id = documents_fts.document_id
        WHERE documents.project_id = ? AND documents_fts MATCH ?
        ORDER BY rank
        LIMIT 5
    """
    results = await db.execute(query, (project_id, keywords))

    return {
        "matches": [
            {"document": row.name, "excerpt": row.snippet}
            for row in results
        ]
    }

# Register tool with Agent SDK
tools = [
    {
        "name": "DocumentSearch",
        "description": "Search project documents for relevant information. Use when user question might be answered by uploaded documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "Keywords to search for"},
            },
            "required": ["keywords"]
        },
        "function": lambda keywords: document_search_tool(current_project_id, keywords)
    }
]

# Agent SDK session
async for message in query(
    prompt=user_message,
    options=ClaudeAgentOptions(
        allowed_tools=["DocumentSearch", "ArtifactGenerator"],
        custom_tools=tools
    )
):
    yield message
```

**Key Pattern:** Agent SDK handles tool calling protocol. You provide async functions, SDK manages invocation timing.

#### OAuth 2.0 Authentication

**Pattern:** Authorization code flow with PKCE for mobile

**Flow:**
```
1. User clicks "Sign in with Google"
   └─> Flutter: POST /auth/oauth/google → returns auth_url

2. Flutter opens browser with auth_url
   └─> User authenticates with Google
   └─> Google redirects to /auth/callback?code=...

3. Backend exchanges code for tokens
   └─> POST to Google token endpoint
   └─> Retrieves user profile from Google API
   └─> Creates/updates user in SQLite
   └─> Generates JWT access token
   └─> Redirects to Flutter deep link with token

4. Flutter stores JWT securely
   └─> Attaches to all API requests: Authorization: Bearer {token}

5. FastAPI validates JWT on each request
   └─> Extracts user_id from token payload
   └─> Checks ownership for resource access
```

**Security:** State parameter for CSRF protection, PKCE for mobile apps, JWT for stateless session management.

## Build Order and Dependencies

### Phase 1: Foundation (Weeks 1-2)

**Components:**
1. Database schema + migrations (SQLAlchemy models)
2. Basic FastAPI server with health check
3. Flutter app shell with navigation

**Dependencies:**
- Database must exist before services
- No external service dependencies yet

**Output:** Deployable "hello world" on PaaS

### Phase 2: Authentication (Weeks 2-3)

**Components:**
1. OAuth integration (Google + Microsoft)
2. JWT token generation/validation
3. Flutter OAuth flow (web_auth)
4. Secure token storage

**Dependencies:**
- Requires Phase 1 (database for user storage)
- OAuth credentials from Google/Microsoft consoles

**Output:** Users can sign in, receive JWT, make authenticated requests

### Phase 3: Project Management (Weeks 3-4)

**Components:**
1. Project CRUD endpoints
2. Thread CRUD endpoints
3. Document upload + encryption + FTS5 indexing
4. Flutter project/thread UI

**Dependencies:**
- Requires Phase 2 (authentication for ownership)
- Requires Phase 1 (database for storage)

**Output:** Users can create projects, upload documents, create threads

### Phase 4: AI Service (Weeks 4-6)

**Components:**
1. Claude Agent SDK integration
2. Custom tools (DocumentSearch, ArtifactGenerator)
3. Message persistence
4. Conversation history assembly

**Dependencies:**
- Requires Phase 3 (projects/documents must exist)
- Requires Anthropic API key
- Requires document FTS5 index (Phase 3)

**Output:** AI can respond to messages but not stream yet

### Phase 5: Streaming Interface (Weeks 6-7)

**Components:**
1. SSE endpoint in FastAPI
2. Flutter SSE client integration
3. Real-time UI updates
4. Tool call indicators

**Dependencies:**
- Requires Phase 4 (AI service must generate responses)
- Requires async FastAPI setup (Phase 1)

**Output:** Users see AI responses stream in real-time

### Phase 6: Artifacts (Weeks 7-8)

**Components:**
1. Artifact storage (database model)
2. ArtifactGenerator tool
3. Export endpoints (Markdown, PDF, Word)
4. Flutter artifact display + export UI

**Dependencies:**
- Requires Phase 5 (AI service must be working)
- Document generation libraries (python-docx, WeasyPrint)

**Output:** Users can generate and export artifacts

### Phase 7: Polish (Weeks 8-10)

**Components:**
1. Error handling + user feedback
2. Loading states + animations
3. Thread summaries (ThreadSummarizer tool)
4. Cross-device testing
5. Performance optimization

**Dependencies:**
- Requires all previous phases (full feature set)

**Output:** Production-ready MVP

### Critical Path Analysis

**Longest dependency chain:**
Database → Auth → Projects → Documents → AI Service → Streaming → Artifacts

**Parallel workstreams:**
- Flutter UI can be built alongside backend (mock data initially)
- OAuth setup can happen during Phase 1 (credentials from consoles)
- Error tracking (Sentry) can be added anytime

**Bottleneck risks:**
- Phase 4 (AI Service) is most complex, allow extra time
- Phase 5 (SSE streaming) may require Flutter SSE debugging
- Phase 6 (PDF export) may need layout iteration

## Architectural Patterns to Follow

### Pattern 1: Layered Separation of Concerns

**What:** Clear separation between presentation, business logic, orchestration, and data

**Why:** Each layer has single responsibility, testable independently, replaceable without affecting others

**How:**
```
Presentation (Flutter) → handles only UI and user input
  ↓
Business Logic (FastAPI services) → handles validation, authorization, CRUD
  ↓
Orchestration (Agent SDK) → handles AI reasoning and tool invocation
  ↓
Data (SQLite + Claude API) → handles persistence and LLM inference
```

**Example:**
```python
# BAD: Mixing layers
@app.post("/messages")
async def create_message(content: str):
    # UI logic in backend (wrong layer)
    if len(content) > 1000:
        return {"error": "Too long"}

    # Direct API call (bypassing orchestration layer)
    response = anthropic.messages.create(...)

    # Manual tool handling (duplicating Agent SDK)
    if "search" in content:
        documents = db.query(...)

# GOOD: Proper layering
@app.post("/messages")
async def create_message(
    message: MessageCreate,  # Pydantic validates length
    user: User = Depends(get_current_user),
    project_service: ProjectService = Depends()
):
    # Business logic layer
    thread = project_service.get_thread(message.thread_id)
    project_service.validate_ownership(thread, user)

    # Orchestration layer (Agent SDK handles tools)
    async for chunk in ai_service.process_message(thread, message.content):
        yield chunk
```

### Pattern 2: Agentic Tool Orchestration

**What:** AI decides when to use tools based on context, not explicit user commands

**Why:** More natural conversations, AI uses best judgment, less brittle than keyword matching

**How:**
- Define tools with clear descriptions
- Let Agent SDK manage tool invocation
- AI reasoning determines when tools are useful

**Example:**
```python
# BAD: Manual tool routing
@app.post("/messages")
async def create_message(content: str):
    if "search" in content.lower():
        # Keyword matching is brittle
        docs = search_documents(extract_keywords(content))
        prompt = f"Using these docs: {docs}, answer: {content}"
        response = call_ai(prompt)
    else:
        response = call_ai(content)

# GOOD: Agentic tool selection
tools = [
    Tool(
        name="DocumentSearch",
        description="Search project documents when user question might be answered by uploaded documentation",
        function=search_documents
    )
]

async for message in agent_sdk.query(
    prompt=content,
    tools=tools
):
    # AI decides if/when to call DocumentSearch
    yield message
```

### Pattern 3: Streaming-First Response Design

**What:** Stream AI responses token-by-token instead of waiting for completion

**Why:** Better UX (users see progress), lower perceived latency, handles long responses gracefully

**How:**
- Use SSE for server → client streaming
- Yield chunks from Agent SDK immediately
- Update Flutter UI progressively

**Example:**
```python
# BAD: Buffered response (slow UX)
@app.post("/messages")
async def create_message(content: str):
    full_response = ""
    async for chunk in ai_service.process(content):
        full_response += chunk.text

    # User waits entire time before seeing anything
    return {"response": full_response}

# GOOD: Streaming response
@app.get("/stream")
async def stream_response(message_id: str):
    async def event_stream():
        async for chunk in ai_service.process(message_id):
            # User sees each chunk immediately
            yield {"event": "chunk", "data": chunk.text}

    return EventSourceResponse(event_stream())
```

### Pattern 4: Conversation Context Management

**What:** Include relevant conversation history without exceeding token limits

**Why:** AI needs context for coherent responses, but full history is too expensive

**How:**
- Limit to last 20 messages (configurable)
- Include project metadata (documents available, thread topic)
- Let Agent SDK manage session state

**Example:**
```python
# Context assembly
async def process_message(thread_id: str, user_message: str):
    # Fetch limited history
    history = db.query(Message).filter(
        Message.thread_id == thread_id
    ).order_by(Message.created_at.desc()).limit(20).all()

    # Format for Agent SDK
    conversation = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history)
    ]

    # Add project context
    thread = db.query(Thread).get(thread_id)
    project = db.query(Project).get(thread.project_id)
    documents = db.query(Document).filter(
        Document.project_id == project.id
    ).all()

    system_prompt = f"""You are a business analyst assistant for project: {project.name}.
    Available documents: {[doc.name for doc in documents]}
    Use DocumentSearch tool when user questions might be answered by these documents."""

    # Agent SDK manages the session
    async for chunk in query(
        prompt=user_message,
        system=system_prompt,
        conversation_history=conversation,
        tools=custom_tools
    ):
        yield chunk
```

### Pattern 5: Stateless API with Centralized State

**What:** Backend doesn't hold session state in memory, all state in database

**Why:** Enables horizontal scaling, simplifies deployment, supports cross-device sync naturally

**How:**
- JWT tokens are self-contained (no server-side session storage)
- Conversation state in SQLite
- Agent SDK sessions reconstructed from database on each request

**Example:**
```python
# BAD: In-memory session state
user_sessions = {}  # Lost on restart, doesn't scale

@app.post("/messages")
async def create_message(user_id: str, content: str):
    if user_id not in user_sessions:
        user_sessions[user_id] = create_agent_session()

    session = user_sessions[user_id]
    return session.process(content)

# GOOD: Stateless with database state
@app.post("/messages")
async def create_message(
    message: MessageCreate,
    user: User = Depends(get_current_user),  # JWT validation
    db: Session = Depends(get_db)
):
    # All state from database
    thread = db.query(Thread).get(message.thread_id)
    history = db.query(Message).filter_by(thread_id=thread.id).all()

    # Agent SDK session reconstructed each time
    async for chunk in ai_service.process(thread, message.content, history):
        yield chunk
```

## Architectural Anti-Patterns to Avoid

### Anti-Pattern 1: Manual Tool Loop Implementation

**What:** Implementing agent tool calling loop yourself instead of using Agent SDK

**Why bad:** Complex state management, retry logic, error handling—all solved by SDK

**Consequences:** More bugs, harder maintenance, feature parity takes months

**Instead:** Use Claude Agent SDK with custom tools

**Example:**
```python
# AVOID: Manual tool loop
response = anthropic.messages.create(
    messages=[{"role": "user", "content": prompt}],
    tools=[tool_definitions]
)

while response.stop_reason == "tool_use":
    # You handle tool execution, state tracking, errors
    tool_results = execute_tools(response.content)
    response = anthropic.messages.create(
        messages=conversation + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results}
        ],
        tools=[tool_definitions]
    )

# PREFER: Agent SDK handles loop
async for message in query(
    prompt=prompt,
    tools=custom_tools
):
    # SDK manages tool loop, you just handle results
    yield message
```

### Anti-Pattern 2: Tight Coupling Between Frontend and AI

**What:** Flutter directly calls Claude API or embeds AI logic

**Why bad:** API keys exposed, no centralized control, can't enforce rate limits, expensive

**Consequences:** Security risk, cost overruns, can't add caching/optimization

**Instead:** Always proxy through backend, AI logic in orchestration layer

### Anti-Pattern 3: Synchronous Blocking in SSE Stream

**What:** Blocking operations during SSE event generation (slow database queries, file I/O)

**Why bad:** Blocks event loop, delays stream, poor concurrent user performance

**Consequences:** Users see stuttering AI responses, server can't handle multiple streams

**Instead:** Use async/await throughout, async database queries, async file operations

**Example:**
```python
# AVOID: Blocking in stream
async def event_stream():
    for chunk in ai_service.process():  # Blocking iteration
        result = db.execute(query)  # Blocking query
        with open(file) as f:  # Blocking file I/O
            data = f.read()
        yield chunk

# PREFER: Async streaming
async def event_stream():
    async for chunk in ai_service.process():  # Async iteration
        result = await db.execute(query)  # Async query
        async with aiofiles.open(file) as f:  # Async file I/O
            data = await f.read()
        yield chunk
```

### Anti-Pattern 4: Document Storage Without Encryption

**What:** Storing user documents as plaintext in database

**Why bad:** Compliance risk, security breach impact, user trust violation

**Consequences:** Can't market to enterprises, regulatory penalties, data breach liability

**Instead:** Encrypt at rest with Fernet (or similar), decrypt only when needed

### Anti-Pattern 5: Unbounded Conversation History

**What:** Sending entire conversation history to AI on every message

**Why bad:** Token costs grow linearly with conversation length, eventually hits context limit

**Consequences:** Cost explosion, API errors (context too long), slow responses

**Instead:** Limit history (last 20 messages), implement summarization for very long threads

### Anti-Pattern 6: Mixing Business Logic Across Layers

**What:** UI validation in backend, database queries in AI service, tool logic in FastAPI routes

**Why bad:** Tight coupling, hard to test, duplicate logic, difficult to refactor

**Consequences:** Changes ripple across layers, bugs multiply, testing requires full stack

**Instead:** Clear layer boundaries—validation in Pydantic models, business logic in services, orchestration in Agent SDK

## Validation of User's Chosen Architecture

### Decision: Flutter + FastAPI + Claude Agent SDK + SQLite

**Validation:** EXCELLENT CHOICE ✓

**Alignment with patterns:**
- Layered separation (Flutter/FastAPI/Agent SDK/SQLite) matches best practices
- Agent SDK for orchestration aligns with agentic tool pattern
- SQLite for MVP matches "start simple, scale later" pattern
- FastAPI's async naturally supports SSE streaming pattern

**Strengths:**
1. **Cross-platform from single codebase** (Flutter) maximizes solo developer velocity
2. **Python + Agent SDK** is optimal pairing for AI-heavy application
3. **SQLite** eliminates operational overhead during MVP validation
4. **PaaS deployment** (Railway/Render) matches stateless architecture pattern

**Potential concerns addressed:**
1. **SQLite concurrency:** Acceptable for MVP (<500 concurrent users), clear PostgreSQL migration path
2. **Agent SDK cost:** Token overhead justified by development velocity and behavioral consistency
3. **Flutter web performance:** Not rendering-intensive UI, mobile-first design mitigates

### Critical Architectural Decisions

#### Decision 1: Agent SDK vs Manual Tool Loop

**Chosen:** Agent SDK (Approach 2)

**Rationale:**
- Single code path (simpler maintenance)
- AI autonomy matches "/business-analyst skill" vision
- Built-in session management, streaming, retries
- Development time savings >> token cost difference

**Trade-off accepted:** 10-30% higher token usage for significantly faster development and more consistent behavior

**Validation:** CORRECT ✓ — Manual tool loop would add weeks of development for complex state management

#### Decision 2: SSE vs WebSockets

**Chosen:** Server-Sent Events (SSE)

**Rationale:**
- Unidirectional matches use case (server streams to client)
- Simpler than WebSockets (no connection upgrade, automatic reconnect)
- PaaS-friendly (works with standard load balancers)
- Browser-native (EventSource API)

**Trade-off accepted:** Can't push from client via SSE (but don't need to—user messages are POST requests)

**Validation:** CORRECT ✓ — WebSockets would add complexity without benefit for this streaming pattern

#### Decision 3: SQLite for MVP → PostgreSQL Later

**Chosen:** SQLite initially with explicit migration plan

**Rationale:**
- Zero configuration accelerates MVP development
- Built-in FTS5 for document search
- File-based simplifies PaaS deployment
- SQLAlchemy ORM makes migration straightforward

**Trade-off accepted:** Limited concurrent writes, migration work when scale demands

**Validation:** CORRECT ✓ — Premature PostgreSQL adds operational burden without MVP benefit

#### Decision 4: OAuth Social Login (No Password Auth in MVP)

**Chosen:** Google + Microsoft OAuth 2.0 only

**Rationale:**
- Target users (BAs) typically have work accounts
- Eliminates password reset flows, breach monitoring
- Enterprise-friendly for adoption
- Reduces security liability

**Trade-off accepted:** Users without Google/MS accounts excluded (rare for target demographic)

**Validation:** CORRECT ✓ — Password auth adds development time with little user benefit for BA demographic

## Comparison to Common Alternatives

### Alternative 1: Microservices Architecture

**Pattern:** Separate services for auth, projects, AI, documents with API gateway

**Score:** 60/100 (not recommended for this project)

**When better:** Large teams, independent service scaling, different tech stacks per service

**Why not here:** Operational complexity overkill for solo developer, network overhead, deployment complexity, distributed debugging difficulty

### Alternative 2: Monolithic MVC with Server-Side Rendering

**Pattern:** Django/Rails full-stack with Jinja/ERB templates, traditional page loads

**Score:** 55/100 (not recommended for this project)

**When better:** Admin-heavy applications, SEO-critical content sites, traditional CRUD apps

**Why not here:** No cross-platform mobile, poor real-time streaming UX, doesn't leverage modern frontend patterns

### Alternative 3: Serverless Functions (AWS Lambda + DynamoDB)

**Pattern:** API Gateway → Lambda functions → DynamoDB, no persistent servers

**Score:** 70/100 (viable but not optimal)

**When better:** Extreme variable load, pay-per-invocation critical, massive scale

**Why not here:** Cold start latency hurts streaming, complex AI session management, DynamoDB overkill vs SQLite, more moving parts for solo developer

### Alternative 4: Client-Side AI (Local LLM)

**Pattern:** Run small LLM locally on device, no backend AI calls

**Score:** 40/100 (not recommended for this project)

**When better:** Privacy-critical (medical/legal), no internet access required, cost optimization at scale

**Why not here:** Poor quality (small models worse than Claude Sonnet), huge app bundle size, device compatibility issues, can't leverage latest models

## Scalability Considerations

### At 100 Users (MVP)

**Architecture:** Current design fully adequate

**Bottlenecks:** None expected

**Optimization:** Basic monitoring only

### At 1,000 Users (Beta)

**Architecture:** Same design, consider PostgreSQL migration

**Potential bottlenecks:**
- SQLite write concurrency (monitor slow query logs)
- AI API rate limits (upgrade Anthropic tier)

**Mitigations:**
- Add database connection pooling
- Implement aggressive caching (document search results)
- Optimize FTS5 queries

### At 10,000 Users (V1.0+)

**Architecture changes needed:**
- Migrate SQLite → PostgreSQL (required)
- Add Redis cache layer for hot data
- Horizontal FastAPI scaling (2-4 instances)

**Potential bottlenecks:**
- Database concurrent connections
- AI API token budget
- Document storage (consider S3 migration)

**Mitigations:**
- Read replicas for PostgreSQL
- Rate limiting per user
- CDN for static assets
- Background job queue for exports

### At 100,000 Users (Scale-Up)

**Architecture changes needed:**
- Multi-region deployment
- Dedicated AI service cluster
- Message queue (RabbitMQ/SQS)
- Elasticsearch for document search (FTS5 insufficient)

**Note:** This scale is post-MVP concern. Current architecture handles MVP → Beta → V1.0 without major rewrites.

## Build Order Recommendations for Roadmap

### Critical Path (Must build in order)

1. **Database + Basic API** (Foundation)
   - Cannot build anything without data layer
   - FastAPI server needed before any services

2. **Authentication** (Gatekeeper)
   - Cannot test ownership logic without auth
   - Blocks all user-specific features

3. **Projects + Documents** (Content)
   - AI needs something to search
   - Cannot test document search tool without documents

4. **AI Service** (Core Value)
   - Central product value
   - Cannot stream responses without AI service working

5. **Streaming Interface** (UX Critical)
   - Users expect real-time for AI
   - Without streaming, feels slow/broken

6. **Artifacts** (Differentiation)
   - Key value proposition for BAs
   - Requires working AI service first

### Parallel Workstreams (Can build simultaneously)

**Backend team:**
- Database schema + migrations
- FastAPI endpoints
- OAuth integration
- AI service + Agent SDK

**Frontend team (same person, different time):**
- Flutter app shell + navigation
- Mock UI with fake data
- State management setup
- SSE client integration

**DevOps (setup once):**
- PaaS configuration
- OAuth credentials
- Environment variables
- Sentry error tracking

### Risks Requiring Early Attention

**High risk:**
- Agent SDK tool integration (new technology, allow extra time)
- SSE streaming on Flutter (may need debugging)
- FTS5 document search performance (test with large documents early)

**Medium risk:**
- PDF export layout (may need iteration for professional output)
- OAuth mobile redirect handling (platform-specific quirks)
- Cross-device token refresh (edge cases in token expiration)

**Low risk:**
- Basic CRUD operations (standard patterns)
- Flutter UI implementation (established patterns)
- PaaS deployment (well-documented)

## Sources and Confidence

**Confidence Level:** HIGH

**Sources:**
- Claude Agent SDK official documentation (HIGH confidence)
- Flutter official documentation (HIGH confidence)
- FastAPI documentation for SSE streaming (HIGH confidence)
- Technical specification document (project-specific, HIGH confidence)
- Technology stack recommendations (project-specific, HIGH confidence)
- Architecture patterns from training data (MEDIUM confidence—general best practices)

**Validation:**
- Agent SDK patterns verified against official documentation
- Flutter networking patterns verified against Flutter docs
- Integration patterns align with your technical specification
- Build order validated against dependency graph
- No contradictions found between sources

**Gaps:**
- Specific Agent SDK Python examples (documentation shows patterns but limited production examples)
- FTS5 performance characteristics at scale (SQLite docs provide basics, but real-world testing needed)
- Flutter SSE package performance on web vs mobile (will need testing)

**Recommendation:** Architecture is sound for MVP through Beta. Monitor SQLite performance and AI token costs closely during MVP to inform V1.0 migration timing.
