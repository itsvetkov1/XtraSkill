# XtraSkill (BA Assistant) — Developer Index
**Last indexed:** 2026-02-27 21:50
**Type:** Full-stack (FastAPI + Flutter Web)

## Architecture
- **Backend:** FastAPI with async SQLAlchemy 2.0, Pydantic Settings, Alembic migrations
- **Frontend:** Flutter Web with Provider pattern for state management
- **LLM Layer:** Adapter pattern — factory selects from Anthropic, Gemini, DeepSeek, Claude CLI/Agent adapters
- **Auth:** OAuth 2.0 (Google + Microsoft) with JWT tokens
- **Database:** SQLite+aiosqlite (dev) / PostgreSQL+asyncpg (prod)

## Backend Structure
```
backend/
├── app/
│   ├── config.py           # Pydantic Settings (env-based config)
│   ├── database.py         # Async SQLAlchemy engine + session
│   ├── models.py           # All SQLAlchemy models (Project, Document, Thread, Message, etc.)
│   ├── routes/
│   │   ├── artifacts.py    # Artifact CRUD + generation endpoints
│   │   ├── auth.py         # OAuth login/callback, token refresh
│   │   ├── conversations.py # Chat/streaming endpoints
│   │   ├── documents.py    # Document upload/download/search
│   │   ├── logs.py         # Request logging endpoints
│   │   ├── projects.py     # Project CRUD
│   │   ├── skills.py       # Skill management endpoints
│   │   └── threads.py      # Thread CRUD, mode switching
│   ├── services/
│   │   ├── ai_service.py       # Core AI orchestration
│   │   ├── agent_service.py    # Claude agent integration
│   │   ├── auth_service.py     # OAuth + JWT logic
│   │   ├── brd_generator.py    # BRD document generation
│   │   ├── conversation_service.py # Conversation management
│   │   ├── document_search.py  # FTS5 full-text search
│   │   ├── encryption.py       # Data encryption
│   │   ├── export_service.py   # PDF/conversation export
│   │   ├── file_validator.py   # Upload validation
│   │   ├── logging_service.py  # Request logging
│   │   ├── mcp_tools.py        # MCP tool integration
│   │   ├── skill_loader.py     # Skill loading/binding
│   │   ├── summarization_service.py # Conversation summarization
│   │   ├── token_tracking.py   # Token usage tracking
│   │   ├── document_parser/    # Multi-format parser (PDF, Word, Excel, CSV, text)
│   │   └── llm/                # LLM adapters
│   │       ├── factory.py          # Provider factory
│   │       ├── base.py             # Abstract adapter
│   │       ├── anthropic_adapter.py
│   │       ├── gemini_adapter.py
│   │       ├── deepseek_adapter.py
│   │       ├── claude_agent_adapter.py
│   │       └── claude_cli_adapter.py
│   ├── templates/artifacts/    # HTML templates for artifact generation
│   ├── middleware/             # Logging middleware
│   └── utils/jwt.py           # JWT encode/decode
├── alembic/                   # Database migrations (5 versions)
├── tests/                     # 52 test files
├── .env.example               # All env vars documented
└── .coveragerc                # Coverage config
```

## Frontend Structure
```
frontend/lib/
├── main.dart                  # App entry point
├── core/
│   ├── config.dart            # API base URL, constants
│   ├── constants.dart         # App-wide constants
│   └── theme.dart             # Theme definitions
├── models/                    # Data models
│   ├── artifact.dart
│   ├── document.dart
│   ├── message.dart
│   ├── project.dart
│   ├── skill.dart
│   ├── thread.dart
│   ├── thread_sort.dart
│   └── token_usage.dart
├── providers/                 # State management (Provider pattern)
│   ├── auth_provider.dart
│   ├── project_provider.dart
│   ├── thread_provider.dart
│   ├── conversation_provider.dart
│   ├── assistant_conversation_provider.dart
│   ├── document_provider.dart
│   ├── document_column_provider.dart
│   ├── budget_provider.dart
│   ├── chats_provider.dart
│   ├── navigation_provider.dart
│   ├── theme_provider.dart
│   ├── logging_provider.dart
│   └── provider_provider.dart
├── screens/
│   ├── home_screen.dart       # Main workspace
│   ├── chats_screen.dart      # Global chats view
│   ├── settings_screen.dart   # Settings
│   ├── splash_screen.dart     # Loading screen
│   └── not_found_screen.dart  # 404
├── services/                  # API client layer
│   ├── api_client.dart        # HTTP client wrapper
│   ├── ai_service.dart
│   ├── artifact_service.dart
│   ├── auth_service.dart
│   ├── document_service.dart
│   ├── project_service.dart
│   ├── session_service.dart
│   ├── skill_service.dart
│   └── logging_service.dart
└── widgets/                   # Reusable UI widgets (13 files)
    ├── breadcrumb_bar.dart
    ├── delete_confirmation_dialog.dart
    ├── document_preview_dialog.dart
    ├── documents_column.dart
    ├── empty_state.dart
    ├── mode_selector.dart
    ├── responsive_layout.dart
    ├── responsive_master_detail.dart
    └── responsive_scaffold.dart
```

## API Routes
| Method | Path | Purpose |
|--------|------|---------|
| POST | /auth/google/login | Initiate Google OAuth |
| POST | /auth/microsoft/login | Initiate Microsoft OAuth |
| GET | /auth/*/callback | OAuth callbacks |
| POST | /auth/refresh | Refresh JWT token |
| CRUD | /projects/* | Project management |
| CRUD | /threads/* | Thread management |
| POST | /conversations/stream | Streaming chat endpoint |
| CRUD | /documents/* | Document upload/download/search |
| CRUD | /artifacts/* | Artifact generation/management |
| CRUD | /skills/* | Skill management |
| GET | /logs/* | Request logs |

## Database Models
- **Project** — workspace container
- **Document** — uploaded files with parsed content
- **Thread** — conversation thread (belongs to project, has mode + model_provider)
- **Message** — individual messages in a thread
- **Artifact** — generated documents (BRD, user stories, acceptance criteria)
- **Skill** — bindable skill definitions
- **TokenUsage** — per-message token tracking

## Migrations (Alembic)
1. `381a4aba2769` — Initial schema
2. `4c40ac075452` — Add project, document, thread, message tables
3. `b4ef9fb543d5` — Add conversation_mode to threads
4. `c07d77df9b74` — Add model_provider to threads
5. `daca512f660c` — Add FTS5 virtual table for document search
6. `e330b6621b90` — Add thread_type to threads

## Build & Dev
- **Backend:** `uvicorn app:app --reload` (port 8000)
- **Frontend:** `flutter run -d chrome` (port 8080)
- **Tests:** `pytest` (52 test files in backend/tests/)
- **Coverage:** `coverage run -m pytest && coverage report`
- **Migrations:** `alembic upgrade head`
- **Env vars:** See `backend/.env.example` (full list)

## Key Dependencies
| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| sqlalchemy[asyncio] | ORM |
| alembic | Migrations |
| anthropic | Claude API |
| google-generativeai | Gemini API |
| pydantic-settings | Config management |
| python-jose | JWT tokens |
| flutter (3.9.2+) | Frontend framework |
| provider | State management |

## Recent Git History
- `71369d1` chore: archive v3.1.1 milestone (Assistant Conversation Memory)
- `418b7c0` docs(phase-70): complete phase execution
- `f3125f8` docs(70-01): complete performance tuning plan — ClaudeProcessPool pre-warming
- `48f3f7f` feat(70-01): wire process pool into FastAPI lifespan and add 8 unit tests
- `7624ce8` feat(70-01): implement ClaudeProcessPool and integrate pool.acquire()

## Technical Debt
- `backend/app/routes/auth.py:21` — TODO: Move to Redis in production for multi-instance deployments
- `home_screen.dart.old` — Dead file, should be deleted
- 20+ open bug tickets in `user_stories/BUG-*`

## Backlog
- 80+ user stories in `user_stories/` directory
- Master index: `user_stories/BACKLOG.md`
- Naming: `US-NNN_`, `BUG-NNN_`, `ENH-NNN_`, `DOC-NNN_`, etc.
