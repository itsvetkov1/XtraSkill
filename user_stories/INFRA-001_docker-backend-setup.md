# INFRA-001 | Docker Backend Setup

**Priority:** High
**Status:** Open
**Effort:** Medium
**Component:** Infrastructure

---

## User Story

As a developer,
I want the XtraSkill backend containerized with Docker,
so that we can run consistent environments locally and deploy to any cloud platform.

---

## Acceptance Criteria

- [ ] AC-1: `Dockerfile` created in `backend/` with Python 3.12, uv, and all dependencies
- [ ] AC-2: `docker-compose.yml` created for backend + SQLite (dev) or PostgreSQL (prod)
- [ ] AC-3: `.dockerignore` excludes node_modules, __pycache__, .env, *.db
- [ ] AC-4: Dockerfile uses multi-stage build (builder + runner) for smaller image
- [ ] AC-5: Healthcheck endpoint configured (/health already exists)
- [ ] AC-6: Environment variables documented in `.env.example`
- [ ] AC-7: OpenClaw Gateway can run alongside backend (via docker-compose or host network)

## Technical Notes

- Base image: `python:3.12-slim`
- Use uv for fast dependency installation
- Mount volume for SQLite DB in dev
- Gunicorn with Uvicorn workers (per railway.json)
- Consider adding frontend to compose for full-stack development

## Related

- Blocks: INFRA-002 (OpenClaw provider integration)
