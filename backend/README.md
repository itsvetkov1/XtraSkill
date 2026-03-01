# XtraSkill Backend

## Quick Start

### Option 1: Deploy Script (Recommended)

```bash
cd backend

# Start development environment
./deploy.sh start

# View logs
./deploy.sh logs

# Stop services
./deploy.sh stop

# Production
./deploy.sh start prod
```

### Option 2: Docker Compose Directly

```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI application |
| OpenClaw Gateway | 8080 | Alternative LLM provider |
| PostgreSQL | 5432 | Production database only |

## Environment Variables

See `.env.example` for all configuration options.

Required:
- `ANTHROPIC_API_KEY` - For AI features

Optional (for alternatives):
- `GOOGLE_API_KEY` - Gemini support
- `DEEPSEEK_API_KEY` - DeepSeek support
- `OPENCLAW_API_KEY` - OpenClaw alternative provider
- `OPENCLAW_GATEWAY_URL` - OpenClaw Gateway URL (default: http://localhost:8080)

## OpenClaw Integration (INFRA-002)

To use OpenClaw as an LLM provider:

1. Set environment variables:
```bash
OPENCLAW_API_KEY=your-key
OPENCLAW_GATEWAY_URL=http://localhost:8080
OPENCLAW_AGENT_ID=dev
```

2. Select "openclaw" as provider in XtraSkill settings

## Deployment Commands

| Command | Description |
|---------|-------------|
| `./deploy.sh start` | Start dev environment |
| `./deploy.sh start prod` | Start production |
| `./deploy.sh stop` | Stop all services |
| `./deploy.sh restart` | Restart services |
| `./deploy.sh build` | Rebuild images |
| `./deploy.sh logs` | View logs |
| `./deploy.sh status` | Show status |
| `./deploy.sh clean` | Remove everything |

## Development

```bash
# Run backend locally (without Docker)
cd ..
source .venv/bin/activate
cd backend
uvicorn main:app --reload
```
