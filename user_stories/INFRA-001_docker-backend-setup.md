# INFRA-001 | Docker Backend Setup

**Priority:** High
**Status:** In Progress
**Effort:** Medium
**Component:** Infrastructure

---

## User Story

As a developer,
I want the XtraSkill backend containerized with Docker,
so that we can run consistent environments locally and deploy to any cloud platform.

---

## Acceptance Criteria

- [x] AC-1: `Dockerfile` created in `backend/` with Python 3.12, uv, and all dependencies
- [x] AC-2: `docker-compose.yml` created for backend + SQLite (dev) + OpenClaw Gateway
- [x] AC-3: `.dockerignore` excludes node_modules, __pycache__, .env, *.db
- [x] AC-4: Dockerfile uses multi-stage build (builder + runner) for smaller image
- [x] AC-5: Healthcheck endpoint configured (/health already exists)
- [x] AC-6: Environment variables documented in `.env.example`
- [x] AC-7: OpenClaw Gateway can run alongside backend (via docker-compose or host network)
- [ ] AC-8: Production docker-compose with PostgreSQL

## Technical Notes

- Base image: `python:3.12-slim`
- Uses uv for fast dependency installation
- Multi-stage build: builder (dependencies) + runner (minimal)
- Gunicorn with Uvicorn workers
- Production config includes PostgreSQL

## Files Created

- `backend/Dockerfile` — Multi-stage build
- `backend/.dockerignore` — Excludes dev artifacts
- `backend/docker-compose.yml` — Development config
- `backend/docker-compose.prod.yml` — Production config (PostgreSQL)
- `backend/docs/DOCKER.md` — Documentation
- Updated `.env.example` with OpenClaw vars

## Related

- Blocks: INFRA-002 (OpenClaw provider integration)
