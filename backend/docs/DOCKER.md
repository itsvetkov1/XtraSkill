# Docker Development Guide

This document covers running XtraSkill backend with Docker.

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Fill in your API keys in .env

# 3. Start containers
docker-compose up --build

# 4. Access the API
curl http://localhost:8000/health
```

## Development vs Production

| Command | Description |
|---------|-------------|
| `docker-compose up --build` | Development (SQLite) |
| `docker-compose -f docker-compose.prod.yml up -d` | Production (PostgreSQL) |

## Services

### Backend (Port 8000)
- FastAPI application with Gunicorn + Uvicorn workers
- Health check: `/health`
- Volume mounts for data persistence

### OpenClaw Gateway (Port 8080)
- Optional service for INFRA-002
- Used as alternative LLM provider
- Connected via Docker network

### PostgreSQL (Production Only)
- Persistent data volume
- Health checks enabled

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DATABASE_URL` — SQLite (dev) or PostgreSQL (prod)
- `ANTHROPIC_API_KEY` — Required for AI features
- `OPENCLAW_*` — For alternative provider (INFRA-002)

## Troubleshooting

```bash
# View logs
docker-compose logs -f backend

# Rebuild after dependency changes
docker-compose build --no-cache

# Stop all containers
docker-compose down

# Reset database (development)
rm data/xtra.db
docker-compose up
```
