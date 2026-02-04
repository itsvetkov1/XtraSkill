# Production Implementation Plan: Claude Agent SDK Web Backend

## Executive Summary

This document provides a step-by-step implementation plan for building a web application that wraps Claude Code capabilities behind a custom frontend and FastAPI backend using the `claude-agent-sdk` package.

**Architecture Pattern:** User Browser → Custom Frontend → FastAPI Backend → Claude Agent SDK → Claude Code CLI → Anthropic API

**Estimated Implementation Time:** 2-3 weeks for MVP, 4-6 weeks for production-ready

**Infrastructure Cost Estimate:** $50-200/month (excluding Anthropic API usage)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & Infrastructure](#2-prerequisites--infrastructure)
3. [Server Environment Setup](#3-server-environment-setup)
4. [Claude Code CLI Installation](#4-claude-code-cli-installation)
5. [Project Structure](#5-project-structure)
6. [Backend Implementation](#6-backend-implementation)
7. [Security & Sandboxing](#7-security--sandboxing)
8. [Frontend Integration](#8-frontend-integration)
9. [Deployment Pipeline](#9-deployment-pipeline)
10. [Monitoring & Observability](#10-monitoring--observability)
11. [Testing Strategy](#11-testing-strategy)
12. [Troubleshooting Guide](#12-troubleshooting-guide)

---

## 1. Architecture Overview

### 1.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER'S BROWSER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Your Custom Frontend                             │    │
│  │              (React/Vue/Svelte + WebSocket Client)                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS / WSS
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOAD BALANCER (nginx)                             │
│                         SSL Termination + Rate Limiting                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION SERVERS                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      FastAPI Application                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │    │
│  │  │ REST API    │  │ WebSocket   │  │ Session Manager             │  │    │
│  │  │ Endpoints   │  │ Handler     │  │ (Redis-backed)              │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │    │
│  │                           │                                          │    │
│  │                           ▼                                          │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │              Claude Agent SDK Integration Layer              │    │    │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐  │    │    │
│  │  │  │ Agent Manager │  │ Tool Registry │  │ Event Streamer  │  │    │    │
│  │  │  └───────────────┘  └───────────────┘  └─────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Claude Code CLI (Node.js)                         │    │
│  │              Subprocess spawned per session/request                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ISOLATED SANDBOX ENVIRONMENTS                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Docker      │  │  Docker      │  │  Docker      │  │  Docker      │     │
│  │  Container   │  │  Container   │  │  Container   │  │  Container   │     │
│  │  (User A)    │  │  (User B)    │  │  (User C)    │  │  (User D)    │     │
│  │  /workspace  │  │  /workspace  │  │  /workspace  │  │  /workspace  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUPPORTING SERVICES                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Redis     │  │  PostgreSQL  │  │ Prometheus   │  │   Grafana    │     │
│  │  (Sessions)  │  │  (Users/Logs)│  │  (Metrics)   │  │ (Dashboards) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
1. User sends message via WebSocket
2. FastAPI authenticates & validates request
3. Session manager retrieves/creates user session
4. Claude Agent SDK spawns Claude Code CLI subprocess
5. CLI operates within user's isolated Docker container
6. Events stream back through SDK → WebSocket → Frontend
7. File changes persisted to user's volume
8. Session state cached in Redis
```

### 1.3 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Communication | WebSocket | Real-time streaming of agent events |
| Isolation | Docker per user | Security + resource limits |
| Session Storage | Redis | Fast, supports pub/sub for scaling |
| Database | PostgreSQL | User management, audit logs |
| Process Model | Subprocess per request | SDK architecture requirement |

---

## 2. Prerequisites & Infrastructure

### 2.1 Required Accounts & Credentials

| Item | Purpose | How to Obtain |
|------|---------|---------------|
| Anthropic API Key | Claude API access | https://console.anthropic.com |
| Docker Hub Account | Container registry | https://hub.docker.com |
| Cloud Provider Account | Infrastructure hosting | AWS/GCP/Azure/DigitalOcean |
| Domain Name | HTTPS + DNS | Any registrar |
| SSL Certificate | HTTPS encryption | Let's Encrypt (free) |

### 2.2 Infrastructure Requirements

**Minimum Production Server Specs:**
```yaml
Application Server:
  CPU: 4 vCPUs (8 recommended)
  RAM: 16 GB (32 GB recommended)
  Storage: 100 GB SSD
  OS: Ubuntu 22.04 LTS or Debian 12

Database Server:
  CPU: 2 vCPUs
  RAM: 8 GB
  Storage: 50 GB SSD

Redis Server:
  CPU: 2 vCPUs
  RAM: 4 GB
  Storage: 20 GB SSD
```

**Cloud Provider Equivalents:**
| Provider | Instance Type | Monthly Cost (estimate) |
|----------|---------------|------------------------|
| AWS | t3.xlarge + RDS + ElastiCache | ~$150-200 |
| GCP | e2-standard-4 + Cloud SQL + Memorystore | ~$140-180 |
| DigitalOcean | Premium Droplet + Managed DB + Redis | ~$100-150 |
| Hetzner | CPX41 + Managed Services | ~$50-80 |

### 2.3 Software Dependencies

```yaml
Runtime Requirements:
  - Python: 3.11+
  - Node.js: 20.x LTS (for Claude Code CLI)
  - Docker: 24.x+
  - Docker Compose: 2.x+

Python Packages:
  - fastapi>=0.109.0
  - uvicorn[standard]>=0.27.0
  - claude-agent-sdk>=0.1.22
  - redis>=5.0.0
  - sqlalchemy>=2.0.0
  - asyncpg>=0.29.0
  - python-jose[cryptography]>=3.3.0
  - passlib[bcrypt]>=1.7.4
  - pydantic>=2.5.0
  - python-multipart>=0.0.6

Infrastructure:
  - nginx>=1.24
  - certbot (for SSL)
  - supervisor or systemd (process management)
```

---

## 3. Server Environment Setup

### 3.1 Initial Server Configuration

```bash
#!/bin/bash
# File: scripts/01-server-setup.sh
# Run as root on fresh Ubuntu 22.04 server

set -e

echo "=== Step 1: System Update ==="
apt update && apt upgrade -y

echo "=== Step 2: Install Essential Packages ==="
apt install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    unzip \
    htop \
    tmux \
    vim \
    ufw

echo "=== Step 3: Configure Firewall ==="
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

echo "=== Step 4: Create Application User ==="
useradd -m -s /bin/bash appuser
usermod -aG sudo appuser
usermod -aG docker appuser

echo "=== Step 5: Configure System Limits ==="
cat >> /etc/security/limits.conf << EOF
appuser soft nofile 65536
appuser hard nofile 65536
appuser soft nproc 32768
appuser hard nproc 32768
EOF

echo "=== Step 6: Configure Sysctl ==="
cat >> /etc/sysctl.conf << EOF
# Network optimizations
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535

# Memory optimizations
vm.swappiness = 10
vm.overcommit_memory = 1
EOF
sysctl -p

echo "=== Server base setup complete ==="
```

### 3.2 Install Docker

```bash
#!/bin/bash
# File: scripts/02-install-docker.sh

set -e

echo "=== Installing Docker ==="

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
docker compose version

echo "=== Docker installation complete ==="
```

### 3.3 Install Node.js (Required for Claude Code CLI)

```bash
#!/bin/bash
# File: scripts/03-install-nodejs.sh

set -e

echo "=== Installing Node.js 20.x LTS ==="

# Install via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Verify installation
node --version
npm --version

# Configure npm global directory for appuser
sudo -u appuser mkdir -p /home/appuser/.npm-global
sudo -u appuser npm config set prefix '/home/appuser/.npm-global'

# Add to PATH
echo 'export PATH="/home/appuser/.npm-global/bin:$PATH"' >> /home/appuser/.bashrc

echo "=== Node.js installation complete ==="
```

### 3.4 Install Python Environment

```bash
#!/bin/bash
# File: scripts/04-install-python.sh

set -e

echo "=== Installing Python 3.11 ==="

add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Set as default
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Verify
python --version
pip --version

echo "=== Python installation complete ==="
```

---

## 4. Claude Code CLI Installation

### 4.1 Install Claude Code CLI

```bash
#!/bin/bash
# File: scripts/05-install-claude-cli.sh
# Run as appuser (not root)

set -e

echo "=== Installing Claude Code CLI ==="

# Method 1: Via npm (recommended for servers)
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version

# Test CLI is accessible
which claude

echo "=== Claude Code CLI installation complete ==="
```

### 4.2 Configure Claude Code CLI

```bash
#!/bin/bash
# File: scripts/06-configure-claude.sh
# Run as appuser

set -e

echo "=== Configuring Claude Code CLI ==="

# Create configuration directory
mkdir -p ~/.config/claude-code

# Create configuration file
cat > ~/.config/claude-code/config.json << 'EOF'
{
  "telemetry": false,
  "theme": "dark",
  "model": "claude-sonnet-4-5-20250929",
  "maxTokens": 8192,
  "permissions": {
    "allowFileOperations": true,
    "allowNetworkRequests": false,
    "allowShellCommands": true
  }
}
EOF

echo "=== Claude CLI configuration complete ==="
```

### 4.3 Verify SDK + CLI Integration

```python
#!/usr/bin/env python3
# File: scripts/07-verify-integration.py
# Run as appuser with ANTHROPIC_API_KEY set

import asyncio
import os
from claude_agent_sdk import Agent, AgentOptions

async def verify_integration():
    """Test that Claude Agent SDK can communicate with CLI."""
    
    # Verify API key is set
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    print("✓ API key found")
    
    try:
        # Create agent with minimal configuration
        agent = Agent(AgentOptions(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            allowed_tools=["read_file"]  # Minimal permissions for test
        ))
        
        print("✓ Agent created successfully")
        
        # Send a simple test message
        response = await agent.run("Say 'Hello, integration test!' and nothing else.")
        
        print(f"✓ Agent responded: {response.content[:100]}...")
        print("\n=== Integration verification PASSED ===")
        return True
        
    except FileNotFoundError as e:
        print(f"ERROR: Claude CLI not found - {e}")
        print("Make sure Claude Code CLI is installed and in PATH")
        return False
    except Exception as e:
        print(f"ERROR: Integration test failed - {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_integration())
    exit(0 if success else 1)
```

---

## 5. Project Structure

### 5.1 Directory Layout

```
claude-web-backend/
├── .env.example                 # Environment variables template
├── .env                         # Local environment (gitignored)
├── .gitignore
├── README.md
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── docker-compose.yml          # Local development stack
├── docker-compose.prod.yml     # Production stack
├── Dockerfile                  # Application container
├── Dockerfile.sandbox          # User sandbox container
│
├── alembic/                    # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── nginx/                      # Nginx configuration
│   ├── nginx.conf
│   └── sites/
│       └── app.conf
│
├── scripts/                    # Setup and utility scripts
│   ├── 01-server-setup.sh
│   ├── 02-install-docker.sh
│   ├── 03-install-nodejs.sh
│   ├── 04-install-python.sh
│   ├── 05-install-claude-cli.sh
│   ├── 06-configure-claude.sh
│   └── 07-verify-integration.py
│
├── src/                        # Application source code
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   │
│   ├── api/                    # API layer
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Dependency injection
│   │   ├── middleware.py       # Custom middleware
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── chat.py         # Chat/conversation endpoints
│   │       ├── files.py        # File management endpoints
│   │       ├── health.py       # Health check endpoints
│   │       └── websocket.py    # WebSocket handlers
│   │
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── agent_manager.py    # Claude Agent SDK integration
│   │   ├── sandbox_manager.py  # Docker sandbox management
│   │   ├── session_manager.py  # User session handling
│   │   └── event_handler.py    # Agent event processing
│   │
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── audit_log.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── common.py
│   │
│   ├── services/               # Business services
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── conversation_service.py
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── security.py
│       └── logging.py
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_api/
│   ├── test_core/
│   └── test_integration/
│
└── frontend/                   # Frontend application (optional)
    ├── package.json
    ├── src/
    └── public/
```

### 5.2 Environment Variables

```bash
# File: .env.example

# =============================================================================
# APPLICATION
# =============================================================================
APP_NAME=claude-web-backend
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=your-secret-key-min-32-chars-change-this
APP_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# =============================================================================
# ANTHROPIC
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=8192
CLAUDE_CLI_PATH=/home/appuser/.npm-global/bin/claude

# =============================================================================
# DATABASE
# =============================================================================
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/claude_app
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# =============================================================================
# REDIS
# =============================================================================
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_TTL=3600

# =============================================================================
# SECURITY
# =============================================================================
JWT_SECRET_KEY=your-jwt-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# =============================================================================
# RATE LIMITING
# =============================================================================
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_TOKENS_PER_MINUTE=100000

# =============================================================================
# SANDBOX CONFIGURATION
# =============================================================================
SANDBOX_IMAGE=claude-sandbox:latest
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1.0
SANDBOX_TIMEOUT_SECONDS=300
SANDBOX_VOLUME_BASE=/var/lib/claude-workspaces

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/claude-app/app.log

# =============================================================================
# MONITORING
# =============================================================================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

---

## 6. Backend Implementation

### 6.1 Configuration Module

```python
# File: src/config.py

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "claude-web-backend"
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = Field(..., min_length=32)
    app_allowed_hosts: List[str] = ["localhost"]
    
    # Anthropic
    anthropic_api_key: str = Field(..., pattern=r"^sk-ant-")
    claude_model: str = "claude-sonnet-4-5-20250929"
    claude_max_tokens: int = 8192
    claude_cli_path: Optional[str] = None
    
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 3600
    
    # Security
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_minute: int = 100000
    
    # Sandbox
    sandbox_image: str = "claude-sandbox:latest"
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = 1.0
    sandbox_timeout_seconds: int = 300
    sandbox_volume_base: str = "/var/lib/claude-workspaces"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    
    @field_validator("app_allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [h.strip() for h in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### 6.2 Main Application Entry Point

```python
# File: src/main.py

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import get_settings
from src.api.routes import auth, chat, files, health, websocket
from src.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from src.core.sandbox_manager import SandboxManager
from src.core.session_manager import SessionManager
from src.utils.logging import setup_logging


settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application...")
    
    # Initialize managers
    app.state.session_manager = SessionManager(settings.redis_url)
    app.state.sandbox_manager = SandboxManager(
        image=settings.sandbox_image,
        volume_base=settings.sandbox_volume_base,
        memory_limit=settings.sandbox_memory_limit,
        cpu_limit=settings.sandbox_cpu_limit
    )
    
    await app.state.session_manager.connect()
    logger.info("Session manager connected")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await app.state.session_manager.disconnect()
    await app.state.sandbox_manager.cleanup_all()
    logger.info("Cleanup complete")


def create_app() -> FastAPI:
    """Application factory."""
    setup_logging(settings.log_level, settings.log_format)
    
    app = FastAPI(
        title=settings.app_name,
        description="Claude Code Web Backend API",
        version="1.0.0",
        debug=settings.app_debug,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.app_debug else None,
        redoc_url="/api/redoc" if settings.app_debug else None
    )
    
    # Middleware (order matters - first added = last executed)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_requests_per_minute
    )
    
    # Routes
    app.include_router(health.router, prefix="/api/health", tags=["Health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(files.router, prefix="/api/files", tags=["Files"])
    app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
    
    # Prometheus metrics
    if settings.prometheus_enabled:
        Instrumentator().instrument(app).expose(
            app, endpoint="/metrics", include_in_schema=False
        )
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug,
        workers=4 if not settings.app_debug else 1
    )
```

### 6.3 Claude Agent Manager

```python
# File: src/core/agent_manager.py

import asyncio
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from claude_agent_sdk import Agent, AgentOptions, ClaudeEvent


logger = logging.getLogger(__name__)


class AgentEventType(str, Enum):
    """Types of events emitted by the agent."""
    MESSAGE_START = "message_start"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_COMPLETE = "message_complete"
    TOOL_USE_START = "tool_use_start"
    TOOL_USE_RESULT = "tool_use_result"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class AgentEvent:
    """Structured agent event for frontend consumption."""
    type: AgentEventType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())


@dataclass
class AgentSession:
    """Represents an active agent session."""
    session_id: str
    user_id: str
    agent: Agent
    workspace_path: str
    created_at: float
    last_activity: float
    message_count: int = 0
    token_count: int = 0


class AgentManager:
    """
    Manages Claude Agent SDK instances and their lifecycle.
    
    Responsibilities:
    - Create and configure agent instances
    - Route messages to appropriate agents
    - Stream events back to clients
    - Handle agent lifecycle (create, pause, resume, destroy)
    - Enforce resource limits
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 8192,
        cli_path: Optional[str] = None,
        default_tools: Optional[List[str]] = None
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.cli_path = cli_path
        self.default_tools = default_tools or [
            "read_file",
            "write_file",
            "list_directory",
            "execute_command"
        ]
        
        self._sessions: Dict[str, AgentSession] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        workspace_path: str,
        system_prompt: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None
    ) -> AgentSession:
        """Create a new agent session."""
        async with self._lock:
            if session_id in self._sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            # Configure agent options
            options = AgentOptions(
                model=self.model,
                max_tokens=self.max_tokens,
                allowed_tools=allowed_tools or self.default_tools,
                working_directory=workspace_path,
                system_prompt=system_prompt or self._get_default_system_prompt(),
            )
            
            # Set CLI path if specified
            if self.cli_path:
                options.cli_path = self.cli_path
            
            # Create agent instance
            agent = Agent(options)
            
            # Create session record
            now = asyncio.get_event_loop().time()
            session = AgentSession(
                session_id=session_id,
                user_id=user_id,
                agent=agent,
                workspace_path=workspace_path,
                created_at=now,
                last_activity=now
            )
            
            self._sessions[session_id] = session
            logger.info(f"Created agent session {session_id} for user {user_id}")
            
            return session
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        timeout: float = 300.0
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Send a message to an agent and stream events.
        
        Yields AgentEvent objects as the agent processes the request.
        """
        session = self._sessions.get(session_id)
        if not session:
            yield AgentEvent(
                type=AgentEventType.ERROR,
                data={"error": f"Session {session_id} not found"}
            )
            return
        
        session.last_activity = asyncio.get_event_loop().time()
        session.message_count += 1
        
        try:
            # Run agent with timeout
            async with asyncio.timeout(timeout):
                async for event in session.agent.stream(message):
                    yield self._convert_event(event)
                    
        except asyncio.TimeoutError:
            logger.warning(f"Session {session_id} timed out after {timeout}s")
            yield AgentEvent(
                type=AgentEventType.TIMEOUT,
                data={"timeout_seconds": timeout}
            )
            
        except Exception as e:
            logger.error(f"Error in session {session_id}: {e}", exc_info=True)
            yield AgentEvent(
                type=AgentEventType.ERROR,
                data={"error": str(e)}
            )
    
    async def destroy_session(self, session_id: str) -> bool:
        """Destroy an agent session and cleanup resources."""
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                try:
                    await session.agent.close()
                except Exception as e:
                    logger.warning(f"Error closing agent for session {session_id}: {e}")
                
                logger.info(f"Destroyed session {session_id}")
                return True
            return False
    
    async def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "workspace_path": session.workspace_path,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "message_count": session.message_count,
            "token_count": session.token_count
        }
    
    async def cleanup_idle_sessions(self, max_idle_seconds: float = 1800) -> int:
        """Cleanup sessions that have been idle too long."""
        now = asyncio.get_event_loop().time()
        to_remove = []
        
        async with self._lock:
            for session_id, session in self._sessions.items():
                if now - session.last_activity > max_idle_seconds:
                    to_remove.append(session_id)
        
        for session_id in to_remove:
            await self.destroy_session(session_id)
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} idle sessions")
        
        return len(to_remove)
    
    def _convert_event(self, event: ClaudeEvent) -> AgentEvent:
        """Convert SDK event to our event format."""
        # Map SDK event types to our types
        event_map = {
            "content_block_start": AgentEventType.MESSAGE_START,
            "content_block_delta": AgentEventType.MESSAGE_DELTA,
            "content_block_stop": AgentEventType.MESSAGE_COMPLETE,
            "tool_use": AgentEventType.TOOL_USE_START,
            "tool_result": AgentEventType.TOOL_USE_RESULT,
        }
        
        event_type = event_map.get(event.type, AgentEventType.MESSAGE_DELTA)
        
        return AgentEvent(
            type=event_type,
            data={
                "original_type": event.type,
                "content": getattr(event, "content", None),
                "tool_name": getattr(event, "tool_name", None),
                "tool_input": getattr(event, "tool_input", None),
                "tool_result": getattr(event, "tool_result", None),
            }
        )
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for agents."""
        return """You are a helpful AI coding assistant. You have access to a workspace 
where you can read, write, and execute code. Always explain what you're doing before 
making changes. Be careful with destructive operations and ask for confirmation when 
appropriate.

Guidelines:
- Write clean, well-documented code
- Follow best practices for the language being used
- Explain complex changes step by step
- Test changes when possible before confirming completion
- Respect the user's coding style when modifying existing files"""
```

### 6.4 WebSocket Handler

```python
# File: src/api/routes/websocket.py

import asyncio
import json
import logging
from typing import Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from src.config import get_settings
from src.core.agent_manager import AgentManager, AgentEvent, AgentEventType
from src.core.sandbox_manager import SandboxManager
from src.core.session_manager import SessionManager
from src.api.dependencies import get_current_user_ws


logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class WSMessage(BaseModel):
    """Incoming WebSocket message format."""
    type: str = Field(..., pattern="^(message|command|ping)$")
    content: Optional[str] = None
    metadata: Optional[Dict] = None


class WSResponse(BaseModel):
    """Outgoing WebSocket message format."""
    type: str
    session_id: str
    data: Dict
    timestamp: float


class ConnectionManager:
    """Manages active WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_manager: Optional[AgentManager] = None
        self.sandbox_manager: Optional[SandboxManager] = None
        self.session_manager: Optional[SessionManager] = None
    
    def initialize(
        self,
        agent_manager: AgentManager,
        sandbox_manager: SandboxManager,
        session_manager: SessionManager
    ):
        self.agent_manager = agent_manager
        self.sandbox_manager = sandbox_manager
        self.session_manager = session_manager
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept connection and return session ID."""
        await websocket.accept()
        session_id = str(uuid4())
        self.active_connections[session_id] = websocket
        
        # Store session in Redis
        await self.session_manager.create_session(
            session_id=session_id,
            user_id=user_id,
            data={"status": "connected"}
        )
        
        logger.info(f"WebSocket connected: session={session_id}, user={user_id}")
        return session_id
    
    async def disconnect(self, session_id: str):
        """Handle disconnection cleanup."""
        self.active_connections.pop(session_id, None)
        
        # Cleanup agent session
        if self.agent_manager:
            await self.agent_manager.destroy_session(session_id)
        
        # Cleanup sandbox
        if self.sandbox_manager:
            await self.sandbox_manager.destroy_sandbox(session_id)
        
        # Remove from Redis
        if self.session_manager:
            await self.session_manager.delete_session(session_id)
        
        logger.info(f"WebSocket disconnected: session={session_id}")
    
    async def send_event(self, session_id: str, event: AgentEvent):
        """Send event to specific connection."""
        websocket = self.active_connections.get(session_id)
        if websocket:
            response = WSResponse(
                type=event.type.value,
                session_id=session_id,
                data=event.data,
                timestamp=event.timestamp
            )
            await websocket.send_json(response.model_dump())


manager = ConnectionManager()


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    user: dict = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for real-time chat with Claude agent.
    
    Message flow:
    1. Client connects with auth token
    2. Server creates session and sandbox
    3. Client sends messages
    4. Server streams agent events back
    5. Client can send commands (cancel, clear, etc.)
    """
    session_id = None
    
    try:
        # Initialize managers from app state
        manager.initialize(
            agent_manager=websocket.app.state.agent_manager,
            sandbox_manager=websocket.app.state.sandbox_manager,
            session_manager=websocket.app.state.session_manager
        )
        
        # Accept connection
        session_id = await manager.connect(websocket, user["id"])
        
        # Create sandbox for this session
        workspace_path = await manager.sandbox_manager.create_sandbox(
            session_id=session_id,
            user_id=user["id"]
        )
        
        # Create agent session
        await manager.agent_manager.create_session(
            session_id=session_id,
            user_id=user["id"],
            workspace_path=workspace_path
        )
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "workspace": workspace_path
        })
        
        # Message handling loop
        while True:
            # Receive message
            raw_data = await websocket.receive_text()
            
            try:
                message = WSMessage.model_validate_json(raw_data)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Invalid message format: {e}"
                })
                continue
            
            # Handle different message types
            if message.type == "ping":
                await websocket.send_json({"type": "pong"})
                
            elif message.type == "message":
                if not message.content:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Message content is required"
                    })
                    continue
                
                # Stream agent response
                async for event in manager.agent_manager.send_message(
                    session_id=session_id,
                    message=message.content,
                    timeout=settings.sandbox_timeout_seconds
                ):
                    await manager.send_event(session_id, event)
                
            elif message.type == "command":
                await handle_command(websocket, session_id, message)
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: session={session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error": "Internal server error"
            })
        except:
            pass
    
    finally:
        if session_id:
            await manager.disconnect(session_id)


async def handle_command(websocket: WebSocket, session_id: str, message: WSMessage):
    """Handle control commands from client."""
    command = message.metadata.get("command") if message.metadata else None
    
    if command == "cancel":
        # Cancel current operation
        await manager.agent_manager.cancel_operation(session_id)
        await websocket.send_json({
            "type": "command_result",
            "command": "cancel",
            "success": True
        })
        
    elif command == "clear":
        # Clear conversation history
        await manager.agent_manager.clear_history(session_id)
        await websocket.send_json({
            "type": "command_result",
            "command": "clear",
            "success": True
        })
        
    elif command == "stats":
        # Get session statistics
        stats = await manager.agent_manager.get_session_stats(session_id)
        await websocket.send_json({
            "type": "command_result",
            "command": "stats",
            "data": stats
        })
        
    else:
        await websocket.send_json({
            "type": "error",
            "error": f"Unknown command: {command}"
        })
```

### 6.5 Sandbox Manager

```python
# File: src/core/sandbox_manager.py

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import docker
from docker.errors import NotFound, APIError


logger = logging.getLogger(__name__)


@dataclass
class SandboxInfo:
    """Information about a sandbox container."""
    container_id: str
    session_id: str
    user_id: str
    workspace_path: str
    created_at: datetime
    status: str


class SandboxManager:
    """
    Manages Docker containers for isolated user workspaces.
    
    Each user session gets its own container with:
    - Isolated filesystem
    - Limited resources (CPU, memory)
    - No network access by default
    - Mounted workspace volume
    """
    
    def __init__(
        self,
        image: str = "claude-sandbox:latest",
        volume_base: str = "/var/lib/claude-workspaces",
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
        network_mode: str = "none"
    ):
        self.image = image
        self.volume_base = Path(volume_base)
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.network_mode = network_mode
        
        self._client = docker.from_env()
        self._sandboxes: Dict[str, SandboxInfo] = {}
        self._lock = asyncio.Lock()
        
        # Ensure volume base exists
        self.volume_base.mkdir(parents=True, exist_ok=True)
    
    async def create_sandbox(
        self,
        session_id: str,
        user_id: str,
        initial_files: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a new sandbox container for a session.
        
        Returns the workspace path inside the container.
        """
        async with self._lock:
            if session_id in self._sandboxes:
                raise ValueError(f"Sandbox already exists for session {session_id}")
            
            # Create workspace directory
            workspace_host = self.volume_base / session_id
            workspace_host.mkdir(parents=True, exist_ok=True)
            
            # Copy initial files if provided
            if initial_files:
                for filename, content in initial_files.items():
                    file_path = workspace_host / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)
            
            # Create container
            try:
                container = self._client.containers.create(
                    image=self.image,
                    name=f"claude-sandbox-{session_id[:8]}",
                    command="sleep infinity",  # Keep container running
                    mem_limit=self.memory_limit,
                    cpu_period=100000,
                    cpu_quota=int(self.cpu_limit * 100000),
                    network_mode=self.network_mode,
                    volumes={
                        str(workspace_host): {
                            "bind": "/workspace",
                            "mode": "rw"
                        }
                    },
                    working_dir="/workspace",
                    user="1000:1000",  # Non-root user
                    read_only=False,
                    security_opt=["no-new-privileges:true"],
                    cap_drop=["ALL"],
                    cap_add=["CHOWN", "SETUID", "SETGID"],
                    labels={
                        "claude.session_id": session_id,
                        "claude.user_id": user_id,
                        "claude.created": datetime.utcnow().isoformat()
                    }
                )
                
                # Start container
                container.start()
                
                # Record sandbox info
                sandbox = SandboxInfo(
                    container_id=container.id,
                    session_id=session_id,
                    user_id=user_id,
                    workspace_path=str(workspace_host),
                    created_at=datetime.utcnow(),
                    status="running"
                )
                self._sandboxes[session_id] = sandbox
                
                logger.info(
                    f"Created sandbox for session {session_id}: "
                    f"container={container.short_id}"
                )
                
                return str(workspace_host)
                
            except APIError as e:
                # Cleanup on failure
                shutil.rmtree(workspace_host, ignore_errors=True)
                logger.error(f"Failed to create sandbox: {e}")
                raise
    
    async def destroy_sandbox(self, session_id: str) -> bool:
        """Destroy a sandbox container and cleanup its workspace."""
        async with self._lock:
            sandbox = self._sandboxes.pop(session_id, None)
            if not sandbox:
                return False
            
            try:
                # Stop and remove container
                container = self._client.containers.get(sandbox.container_id)
                container.stop(timeout=5)
                container.remove(force=True)
            except NotFound:
                pass  # Container already gone
            except Exception as e:
                logger.warning(f"Error removing container: {e}")
            
            # Cleanup workspace (optional - keep for debugging)
            # shutil.rmtree(sandbox.workspace_path, ignore_errors=True)
            
            logger.info(f"Destroyed sandbox for session {session_id}")
            return True
    
    async def execute_in_sandbox(
        self,
        session_id: str,
        command: List[str],
        timeout: int = 30
    ) -> tuple[int, str, str]:
        """
        Execute a command inside a sandbox container.
        
        Returns: (exit_code, stdout, stderr)
        """
        sandbox = self._sandboxes.get(session_id)
        if not sandbox:
            raise ValueError(f"No sandbox for session {session_id}")
        
        try:
            container = self._client.containers.get(sandbox.container_id)
            
            # Execute command
            result = container.exec_run(
                cmd=command,
                workdir="/workspace",
                user="1000:1000",
                demux=True
            )
            
            exit_code = result.exit_code
            stdout = result.output[0].decode() if result.output[0] else ""
            stderr = result.output[1].decode() if result.output[1] else ""
            
            return exit_code, stdout, stderr
            
        except Exception as e:
            logger.error(f"Execution error in sandbox {session_id}: {e}")
            raise
    
    async def get_sandbox_status(self, session_id: str) -> Optional[Dict]:
        """Get status of a sandbox."""
        sandbox = self._sandboxes.get(session_id)
        if not sandbox:
            return None
        
        try:
            container = self._client.containers.get(sandbox.container_id)
            stats = container.stats(stream=False)
            
            return {
                "session_id": session_id,
                "container_id": sandbox.container_id[:12],
                "status": container.status,
                "created_at": sandbox.created_at.isoformat(),
                "memory_usage": stats["memory_stats"].get("usage", 0),
                "cpu_usage": stats["cpu_stats"]["cpu_usage"]["total_usage"]
            }
        except Exception as e:
            logger.warning(f"Failed to get sandbox status: {e}")
            return None
    
    async def cleanup_all(self):
        """Cleanup all sandboxes (for shutdown)."""
        session_ids = list(self._sandboxes.keys())
        for session_id in session_ids:
            await self.destroy_sandbox(session_id)
        
        logger.info(f"Cleaned up {len(session_ids)} sandboxes")
    
    async def cleanup_orphaned(self) -> int:
        """Find and cleanup orphaned sandbox containers."""
        cleaned = 0
        
        try:
            containers = self._client.containers.list(
                all=True,
                filters={"label": "claude.session_id"}
            )
            
            for container in containers:
                session_id = container.labels.get("claude.session_id")
                if session_id not in self._sandboxes:
                    logger.info(f"Cleaning up orphaned container: {container.short_id}")
                    container.remove(force=True)
                    cleaned += 1
                    
        except Exception as e:
            logger.error(f"Error cleaning orphaned containers: {e}")
        
        return cleaned
```

---

## 7. Security & Sandboxing

### 7.1 Sandbox Docker Image

```dockerfile
# File: Dockerfile.sandbox

FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install common development tools
RUN apt-get update && apt-get install -y \
    # Languages
    python3.11 \
    python3.11-venv \
    python3-pip \
    nodejs \
    npm \
    # Build tools
    build-essential \
    git \
    curl \
    wget \
    # Utilities
    vim \
    nano \
    jq \
    tree \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 sandbox && \
    useradd -u 1000 -g sandbox -m -s /bin/bash sandbox

# Set up workspace
RUN mkdir -p /workspace && \
    chown -R sandbox:sandbox /workspace

# Security: Remove unnecessary SUID binaries
RUN find / -perm /4000 -type f -exec chmod u-s {} \; 2>/dev/null || true

# Switch to non-root user
USER sandbox
WORKDIR /workspace

# Default command
CMD ["sleep", "infinity"]
```

### 7.2 Build Sandbox Image

```bash
#!/bin/bash
# File: scripts/build-sandbox.sh

set -e

echo "=== Building Sandbox Docker Image ==="

docker build \
    -t claude-sandbox:latest \
    -f Dockerfile.sandbox \
    .

echo "=== Sandbox image built successfully ==="

# Verify image
docker run --rm claude-sandbox:latest python3 --version
docker run --rm claude-sandbox:latest node --version

echo "=== Image verification complete ==="
```

### 7.3 Security Hardening Checklist

```yaml
# File: docs/security-checklist.yaml

container_security:
  - name: "Non-root user"
    status: "✓"
    description: "Containers run as UID 1000, not root"
    
  - name: "Dropped capabilities"
    status: "✓"
    description: "All capabilities dropped except minimal set"
    
  - name: "No new privileges"
    status: "✓"
    description: "security_opt: no-new-privileges:true"
    
  - name: "Network isolation"
    status: "✓"
    description: "network_mode: none by default"
    
  - name: "Resource limits"
    status: "✓"
    description: "Memory and CPU limits enforced"
    
  - name: "Read-only root"
    status: "⚠"
    description: "Consider for production"

api_security:
  - name: "Authentication required"
    status: "✓"
    description: "JWT tokens for all endpoints"
    
  - name: "Rate limiting"
    status: "✓"
    description: "Per-user request limits"
    
  - name: "Input validation"
    status: "✓"
    description: "Pydantic schemas for all inputs"
    
  - name: "CORS configuration"
    status: "✓"
    description: "Restricted to allowed origins"
    
  - name: "HTTPS only"
    status: "✓"
    description: "TLS termination at nginx"

data_security:
  - name: "Workspace isolation"
    status: "✓"
    description: "Each user gets separate volume"
    
  - name: "Session expiry"
    status: "✓"
    description: "Idle sessions cleaned up"
    
  - name: "Secrets management"
    status: "✓"
    description: "Environment variables, not in code"
    
  - name: "Audit logging"
    status: "✓"
    description: "All actions logged to database"
```

---

## 8. Frontend Integration

### 8.1 WebSocket Client (TypeScript)

```typescript
// File: frontend/src/lib/claude-client.ts

export interface WSMessage {
  type: 'message' | 'command' | 'ping';
  content?: string;
  metadata?: Record<string, unknown>;
}

export interface WSResponse {
  type: string;
  session_id: string;
  data: Record<string, unknown>;
  timestamp: number;
}

export interface ClaudeClientOptions {
  url: string;
  token: string;
  onMessage?: (response: WSResponse) => void;
  onError?: (error: Error) => void;
  onConnect?: (sessionId: string) => void;
  onDisconnect?: () => void;
}

export class ClaudeClient {
  private ws: WebSocket | null = null;
  private options: ClaudeClientOptions;
  private sessionId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: NodeJS.Timeout | null = null;

  constructor(options: ClaudeClientOptions) {
    this.options = options;
  }

  async connect(): Promise<string> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${this.options.url}?token=${this.options.token}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        const response: WSResponse = JSON.parse(event.data);

        if (response.type === 'connected') {
          this.sessionId = response.session_id;
          this.options.onConnect?.(response.session_id);
          resolve(response.session_id);
        } else if (response.type === 'pong') {
          // Ping response, connection is alive
        } else {
          this.options.onMessage?.(response);
        }
      };

      this.ws.onerror = (event) => {
        const error = new Error('WebSocket error');
        this.options.onError?.(error);
        reject(error);
      };

      this.ws.onclose = () => {
        this.stopPingInterval();
        this.options.onDisconnect?.();
        this.attemptReconnect();
      };
    });
  }

  async sendMessage(content: string): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    const message: WSMessage = {
      type: 'message',
      content,
    };

    this.ws.send(JSON.stringify(message));
  }

  async sendCommand(command: string, params?: Record<string, unknown>): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    const message: WSMessage = {
      type: 'command',
      metadata: { command, ...params },
    };

    this.ws.send(JSON.stringify(message));
  }

  disconnect(): void {
    this.stopPingInterval();
    this.maxReconnectAttempts = 0; // Prevent reconnection
    this.ws?.close();
    this.ws = null;
    this.sessionId = null;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.options.onError?.(new Error('Max reconnection attempts reached'));
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      this.connect().catch(() => {
        // Will trigger onclose again, which calls attemptReconnect
      });
    }, delay);
  }
}
```

### 8.2 React Chat Component

```tsx
// File: frontend/src/components/ClaudeChat.tsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ClaudeClient, WSResponse } from '../lib/claude-client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status: 'sending' | 'streaming' | 'complete' | 'error';
}

interface ClaudeChatProps {
  apiUrl: string;
  authToken: string;
}

export const ClaudeChat: React.FC<ClaudeChatProps> = ({ apiUrl, authToken }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  const clientRef = useRef<ClaudeClient | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentMessageRef = useRef<string>('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleMessage = useCallback((response: WSResponse) => {
    switch (response.type) {
      case 'message_start':
        // New assistant message starting
        currentMessageRef.current = '';
        setMessages(prev => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            status: 'streaming',
          },
        ]);
        break;

      case 'message_delta':
        // Streaming content
        const content = response.data.content as string;
        if (content) {
          currentMessageRef.current += content;
          setMessages(prev => {
            const updated = [...prev];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant') {
              lastMsg.content = currentMessageRef.current;
            }
            return updated;
          });
        }
        break;

      case 'message_complete':
        // Message finished
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg?.role === 'assistant') {
            lastMsg.status = 'complete';
          }
          return updated;
        });
        setIsLoading(false);
        break;

      case 'tool_use_start':
        // Tool being used
        const toolName = response.data.tool_name as string;
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg?.role === 'assistant') {
            lastMsg.content += `\n\n🔧 Using tool: ${toolName}...`;
          }
          return updated;
        });
        break;

      case 'error':
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg?.role === 'assistant') {
            lastMsg.status = 'error';
            lastMsg.content = `Error: ${response.data.error}`;
          }
          return updated;
        });
        setIsLoading(false);
        break;
    }
  }, []);

  useEffect(() => {
    const client = new ClaudeClient({
      url: `${apiUrl}/ws/chat`,
      token: authToken,
      onMessage: handleMessage,
      onConnect: (sid) => {
        setSessionId(sid);
        setIsConnected(true);
      },
      onDisconnect: () => {
        setIsConnected(false);
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
      },
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
    };
  }, [apiUrl, authToken, handleMessage]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !clientRef.current?.isConnected() || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
      status: 'complete',
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      await clientRef.current.sendMessage(userMessage.content);
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h1 className="text-xl font-semibold text-white">Claude Code</h1>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-400">
            {isConnected ? `Session: ${sessionId?.slice(0, 8)}` : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-3xl p-4 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              <pre className="whitespace-pre-wrap font-mono text-sm">
                {message.content}
              </pre>
              {message.status === 'streaming' && (
                <span className="inline-block w-2 h-4 ml-1 bg-white animate-pulse" />
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={!isConnected || isLoading}
            className="flex-1 p-3 bg-gray-800 text-white rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
          <button
            onClick={handleSend}
            disabled={!isConnected || isLoading || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

## 9. Deployment Pipeline

### 9.1 Docker Compose (Production)

```yaml
# File: docker-compose.prod.yml

version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: claude-web-backend:latest
    container_name: claude-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
    env_file:
      - .env
    volumes:
      - /var/lib/claude-workspaces:/var/lib/claude-workspaces
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  redis:
    image: redis:7-alpine
    container_name: claude-redis
    restart: unless-stopped
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  postgres:
    image: postgres:15-alpine
    container_name: claude-postgres
    restart: unless-stopped
    ports:
      - "127.0.0.1:5432:5432"
    environment:
      POSTGRES_USER: ${DB_USER:-claude}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-claude_app}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-claude}"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:1.25-alpine
    container_name: claude-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/sites:/etc/nginx/sites-enabled:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - app
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: claude-prometheus
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'

  grafana:
    image: grafana/grafana:10.0.0
    container_name: claude-grafana
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    depends_on:
      - prometheus

volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:
  nginx_logs:

networks:
  default:
    name: claude-network
```

### 9.2 Application Dockerfile

```dockerfile
# File: Dockerfile

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js runtime
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/lib/node_modules /usr/lib/node_modules
COPY --from=builder /usr/bin/node /usr/bin/node

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./

# Set environment
ENV PYTHONPATH=/app
ENV PATH="/usr/lib/node_modules/.bin:$PATH"

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 9.3 Nginx Configuration

```nginx
# File: nginx/sites/app.conf

upstream claude_backend {
    server app:8000;
    keepalive 32;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/claude_access.log;
    error_log /var/log/nginx/claude_error.log;

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_conn conn_limit 10;
        
        proxy_pass http://claude_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # Longer for AI responses
    }

    # WebSocket endpoint
    location /ws/ {
        limit_conn conn_limit 5;
        
        proxy_pass http://claude_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Static files (if serving frontend)
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health check (no rate limit)
    location /api/health {
        proxy_pass http://claude_backend;
        proxy_http_version 1.1;
        access_log off;
    }
}
```

### 9.4 Deployment Script

```bash
#!/bin/bash
# File: scripts/deploy.sh

set -e

echo "=== Claude Web Backend Deployment ==="
echo "Environment: ${APP_ENV:-production}"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
APP_NAME="claude-web-backend"

# Pre-deployment checks
echo "=== Pre-deployment Checks ==="

# Check required files
for file in ".env" "$COMPOSE_FILE" "Dockerfile"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file '$file' not found"
        exit 1
    fi
done

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running"
    exit 1
fi

echo "✓ All pre-deployment checks passed"
echo ""

# Build images
echo "=== Building Images ==="
docker compose -f $COMPOSE_FILE build --no-cache app
docker build -t claude-sandbox:latest -f Dockerfile.sandbox .
echo "✓ Images built successfully"
echo ""

# Database migrations
echo "=== Running Database Migrations ==="
docker compose -f $COMPOSE_FILE run --rm app alembic upgrade head
echo "✓ Migrations complete"
echo ""

# Deploy with zero-downtime
echo "=== Deploying Application ==="

# Scale up new containers
docker compose -f $COMPOSE_FILE up -d --scale app=2 --no-recreate

# Wait for health checks
echo "Waiting for health checks..."
sleep 30

# Check health
if curl -sf http://localhost:8000/api/health > /dev/null; then
    echo "✓ Health check passed"
else
    echo "ERROR: Health check failed"
    docker compose -f $COMPOSE_FILE logs app --tail=50
    exit 1
fi

# Scale down to single instance (or keep 2 for HA)
docker compose -f $COMPOSE_FILE up -d --scale app=1

# Cleanup
echo "=== Cleanup ==="
docker image prune -f
docker container prune -f

echo ""
echo "=== Deployment Complete ==="
echo "Application is running at: https://yourdomain.com"
echo ""

# Show status
docker compose -f $COMPOSE_FILE ps
```

---

## 10. Monitoring & Observability

### 10.1 Prometheus Configuration

```yaml
# File: monitoring/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files: []

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'claude-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
```

### 10.2 Key Metrics to Monitor

```python
# File: src/utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'claude_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'claude_request_latency_seconds',
    'Request latency',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# WebSocket metrics
WS_CONNECTIONS = Gauge(
    'claude_websocket_connections',
    'Active WebSocket connections'
)

WS_MESSAGES = Counter(
    'claude_websocket_messages_total',
    'Total WebSocket messages',
    ['direction']  # 'in' or 'out'
)

# Agent metrics
AGENT_SESSIONS = Gauge(
    'claude_agent_sessions',
    'Active agent sessions'
)

AGENT_TOKENS = Counter(
    'claude_agent_tokens_total',
    'Total tokens used',
    ['type']  # 'input' or 'output'
)

AGENT_LATENCY = Histogram(
    'claude_agent_response_seconds',
    'Agent response time',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# Sandbox metrics
SANDBOX_COUNT = Gauge(
    'claude_sandboxes_active',
    'Active sandbox containers'
)

SANDBOX_MEMORY = Gauge(
    'claude_sandbox_memory_bytes',
    'Sandbox memory usage',
    ['session_id']
)

# Error metrics
ERRORS = Counter(
    'claude_errors_total',
    'Total errors',
    ['type', 'source']
)
```

---

## 11. Testing Strategy

### 11.1 Test Configuration

```python
# File: tests/conftest.py

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.main import create_app
from src.config import Settings


# Test settings override
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        app_env="testing",
        app_debug=True,
        app_secret_key="test-secret-key-for-testing-only-32chars",
        anthropic_api_key="sk-ant-test-key-not-real",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_db",
        redis_url="redis://localhost:6379/1",
        jwt_secret_key="test-jwt-secret-key-for-testing-32chars",
        sandbox_image="claude-sandbox:test",
        sandbox_volume_base="/tmp/claude-test-workspaces"
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def app(test_settings):
    """Create test application."""
    os.environ["APP_ENV"] = "testing"
    application = create_app()
    yield application


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_client(client, test_user) -> AsyncClient:
    """Create authenticated test client."""
    # Login to get token
    response = await client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

### 11.2 Integration Tests

```python
# File: tests/test_integration/test_agent_flow.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_chat_flow(authenticated_client: AsyncClient):
    """Test complete chat flow from connection to response."""
    
    # 1. Create a new conversation
    response = await authenticated_client.post("/api/chat/conversations", json={
        "title": "Test Conversation"
    })
    assert response.status_code == 201
    conversation_id = response.json()["id"]
    
    # 2. Send a message
    response = await authenticated_client.post(
        f"/api/chat/conversations/{conversation_id}/messages",
        json={"content": "Hello, can you create a simple Python file?"}
    )
    assert response.status_code == 200
    
    # 3. Verify response contains expected elements
    message = response.json()
    assert message["role"] == "assistant"
    assert len(message["content"]) > 0
    
    # 4. Check conversation history
    response = await authenticated_client.get(
        f"/api/chat/conversations/{conversation_id}/messages"
    )
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) >= 2  # User message + assistant response


@pytest.mark.asyncio
async def test_sandbox_isolation(authenticated_client: AsyncClient):
    """Test that sandboxes are properly isolated."""
    
    # Create two conversations
    conv1 = await authenticated_client.post("/api/chat/conversations", json={
        "title": "Sandbox Test 1"
    })
    conv2 = await authenticated_client.post("/api/chat/conversations", json={
        "title": "Sandbox Test 2"
    })
    
    conv1_id = conv1.json()["id"]
    conv2_id = conv2.json()["id"]
    
    # Create file in first sandbox
    await authenticated_client.post(
        f"/api/chat/conversations/{conv1_id}/messages",
        json={"content": "Create a file called secret.txt with content 'sandbox1'"}
    )
    
    # Try to read file from second sandbox (should fail)
    response = await authenticated_client.post(
        f"/api/chat/conversations/{conv2_id}/messages",
        json={"content": "Read the file secret.txt"}
    )
    
    # Verify file doesn't exist in second sandbox
    assert "not found" in response.json()["content"].lower() or \
           "doesn't exist" in response.json()["content"].lower()
```

---

## 12. Troubleshooting Guide

### 12.1 Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| CLI not found | `FileNotFoundError: Claude Code not found` | Verify PATH includes Node.js bin directory |
| Connection refused | WebSocket fails to connect | Check nginx WebSocket proxy configuration |
| Sandbox creation fails | Docker API errors | Ensure app has access to Docker socket |
| Memory issues | OOM kills | Increase container memory limits |
| Slow responses | High latency | Check Claude API quotas, optimize prompts |
| Session loss | Users disconnected | Verify Redis connection, check TTL settings |

### 12.2 Debug Commands

```bash
# Check application logs
docker compose -f docker-compose.prod.yml logs -f app

# Check Claude CLI is accessible
docker compose -f docker-compose.prod.yml exec app claude --version

# Test database connection
docker compose -f docker-compose.prod.yml exec app python -c "
from src.config import get_settings
print(get_settings().database_url)
"

# Check Redis connectivity
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# List active sandboxes
docker ps --filter "label=claude.session_id"

# View sandbox resource usage
docker stats --filter "label=claude.session_id"

# Check nginx configuration
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Monitor WebSocket connections
watch -n 1 'ss -s | grep -i websocket'
```

### 12.3 Performance Tuning

```yaml
# Recommended settings for different scales

small_deployment:  # < 100 concurrent users
  app_workers: 4
  redis_maxmemory: 256mb
  postgres_shared_buffers: 256MB
  sandbox_memory_limit: 512m
  sandbox_cpu_limit: 1.0

medium_deployment:  # 100-500 concurrent users
  app_workers: 8
  redis_maxmemory: 1gb
  postgres_shared_buffers: 1GB
  sandbox_memory_limit: 1g
  sandbox_cpu_limit: 2.0

large_deployment:  # 500+ concurrent users
  app_workers: 16
  redis_maxmemory: 4gb
  postgres_shared_buffers: 4GB
  sandbox_memory_limit: 2g
  sandbox_cpu_limit: 4.0
  # Consider horizontal scaling with load balancer
```

---

## Appendix A: Quick Start Checklist

```markdown
## Pre-Launch Checklist

### Infrastructure
- [ ] Server provisioned with required specs
- [ ] Domain name configured
- [ ] SSL certificate obtained
- [ ] Firewall rules configured

### Installation
- [ ] Docker installed and running
- [ ] Node.js 20.x installed
- [ ] Python 3.11 installed
- [ ] Claude Code CLI installed
- [ ] Sandbox image built

### Configuration
- [ ] .env file created with all variables
- [ ] Anthropic API key added
- [ ] Database credentials set
- [ ] JWT secrets generated

### Security
- [ ] Non-root users configured
- [ ] Docker socket permissions set
- [ ] Rate limiting enabled
- [ ] CORS origins restricted

### Deployment
- [ ] Database migrations run
- [ ] Application containers started
- [ ] Health checks passing
- [ ] SSL working (https://)

### Monitoring
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards configured
- [ ] Log aggregation set up
- [ ] Alerts configured

### Testing
- [ ] API endpoints responding
- [ ] WebSocket connections working
- [ ] Agent responses streaming
- [ ] Sandbox isolation verified
```

---

## Appendix B: Cost Estimation

```markdown
## Monthly Cost Breakdown (Estimated)

### Infrastructure (Medium Scale)
| Item | Provider | Spec | Cost/Month |
|------|----------|------|------------|
| Application Server | DigitalOcean | 8 vCPU, 16GB | $96 |
| Database | Managed PostgreSQL | 2 vCPU, 4GB | $60 |
| Redis | Managed Redis | 2GB | $30 |
| Load Balancer | DigitalOcean | Basic | $12 |
| Storage | Block Storage | 100GB | $10 |
| Bandwidth | Included | 5TB | $0 |
| **Subtotal** | | | **$208** |

### Anthropic API (Usage-Based)
| Usage Level | Tokens/Month | Cost/Month |
|-------------|--------------|------------|
| Light | 10M tokens | ~$30 |
| Medium | 50M tokens | ~$150 |
| Heavy | 200M tokens | ~$600 |

### Total Estimated Costs
| Scale | Infrastructure | API | Total |
|-------|---------------|-----|-------|
| Small | $100 | $30 | $130 |
| Medium | $208 | $150 | $358 |
| Large | $500 | $600 | $1,100 |
```

---

*Document Version: 1.0*
*Last Updated: 2026-01-25*
*Author: Claude Assistant*
