# XtraSkill (BA Assistant) — Project Index
**Last indexed:** 2026-02-27 21:50
**Type:** Full-stack web app (Python FastAPI + Flutter Web)
**Purpose:** AI-powered Business Analyst Assistant — helps BAs reduce time on requirement documentation through AI-assisted discovery conversations that generate production-ready artifacts (BRDs, user stories, acceptance criteria)

## Tech Stack
- **Backend:** Python FastAPI, SQLAlchemy 2.0, Alembic migrations
- **Frontend:** Flutter Web (Dart), Provider state management
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **AI:** Multi-LLM support (Anthropic Claude, Google Gemini, DeepSeek, Claude CLI agent)
- **Auth:** Google OAuth + Microsoft OAuth
- **Hosting:** Railway (planned)

## Key Features
- AI-powered discovery conversations for requirements gathering
- Multi-project workspace with document management
- Thread-based conversations with mode switching (assistant/conversation)
- Document upload + parsing (PDF, Word, Excel, CSV, text)
- Full-text search (FTS5) across documents
- Artifact generation (BRDs, user stories, acceptance criteria) with HTML templates
- Skill system — bind skills to threads for specialized prompts
- Token usage tracking per model/provider
- Conversation export (PDF)

## Project Structure
- `backend/` — FastAPI app (routes, services, models, templates, migrations)
- `frontend/` — Flutter web app (screens, providers, services, widgets, models)
- `user_stories/` — 80+ user stories and bug tickets (BACKLOG.md is the index)
- `test_results/` — Evaluator output from QA testing
- Root docs: BRD.md, CLAUDE.md, README.md, various spec files

## Key URLs
- **Repo:** github.com/itsvetkov1/XtraSkill
- **Codecov:** codecov.io/github/itsvetkov1/XtraSkill

## Documentation
- `BRD.md` — Original business requirements document
- `BA_Assistant_Technical_Specification.md` — Full technical spec
- `BA_Assistant_Technology_Stack.md` — Technology decisions
- `BA_Assistant_Implementation_Roadmap.md` — Implementation phases
- `REGRESSION_TESTS.md` — Regression test plan
- `user_stories/BACKLOG.md` — Complete backlog with status
