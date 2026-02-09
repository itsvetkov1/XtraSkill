# Architecture Research: Security Hardening & Production Deployment

**Domain:** Security hardening and PaaS deployment for FastAPI + Flutter web application
**Researched:** 2026-02-09
**Confidence:** HIGH

## Standard Architecture

### Production Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION DEPLOYMENT                        │
├─────────────────────────────────────────────────────────────────────┤
│  Railway/Render PaaS                                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ HTTPS Load Balancer (Managed by PaaS)                         │  │
│  │ - Auto SSL/TLS certificates                                   │  │
│  │ - DDoS protection                                              │  │
│  └────────────────┬──────────────────────────────────────────────┘  │
│                   │                                                  │
│  ┌────────────────▼──────────────────────────────────────────────┐  │
│  │ Gunicorn (Process Manager)                                     │  │
│  │ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │  │
│  │ │Uvicorn  │  │Uvicorn  │  │Uvicorn  │  │Uvicorn  │           │  │
│  │ │Worker 1 │  │Worker 2 │  │Worker 3 │  │Worker 4 │           │  │
│  │ └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │  │
│  └──────┼───────────┼────────────┼────────────┼─────────────────┘  │
│         │           │            │            │                     │
│  ┌──────▼───────────▼────────────▼────────────▼─────────────────┐  │
│  │ FastAPI Application (Single Codebase)                         │  │
│  │                                                                │  │
│  │ ┌────────────────────────────────────────────────────────┐    │  │
│  │ │ Security Middleware Layer (Order Matters!)             │    │  │
│  │ │ 1. TrustedHostMiddleware (validate domain)             │    │  │
│  │ │ 2. SecurityHeadersMiddleware (HSTS, CSP, etc.)         │    │  │
│  │ │ 3. RateLimitMiddleware (per-IP/user throttling)        │    │  │
│  │ │ 4. CORSMiddleware (frontend origin only)               │    │  │
│  │ │ 5. LoggingMiddleware (correlation IDs, timing)         │    │  │
│  │ └────────────────────────────────────────────────────────┘    │  │
│  │                                                                │  │
│  │ ┌────────────────────────────────────────────────────────┐    │  │
│  │ │ API Routes                                             │    │  │
│  │ │ - /api/* (authenticated, REST + SSE)                   │    │  │
│  │ │ - /auth/* (OAuth callbacks, JWT generation)            │    │  │
│  │ │ - /health (health checks, no auth)                     │    │  │
│  │ │ - /* (Flutter web static files - FALLBACK)             │    │  │
│  │ └────────────────────────────────────────────────────────┘    │  │
│  │                                                                │  │
│  │ ┌────────────────────────────────────────────────────────┐    │  │
│  │ │ StaticFiles Mount (AFTER API routes)                   │    │  │
│  │ │ app.mount("/", StaticFiles(directory="build/web",      │    │  │
│  │ │           html=True), name="spa")                      │    │  │
│  │ │ - Serves Flutter web build                             │    │  │
│  │ │ - Catch-all index.html for client-side routing         │    │  │
│  │ └────────────────────────────────────────────────────────┘    │  │
│  └────────────────┬───────────────────────────────────────────────┘  │
│                   │                                                  │
│  ┌────────────────▼───────────────────────────────────────────────┐ │
│  │ Database Layer                                                  │ │
│  │ ┌──────────────────┐  ┌──────────────────────────────────────┐ │ │
│  │ │ SQLite + Volume  │  │ PostgreSQL + PgBouncer (Recommended) │ │ │
│  │ │ /data/ba.db      │  │ DATABASE_URL from Railway            │ │ │
│  │ │ (ephemeral OK)   │  │ Connection pooling, backups          │ │ │
│  │ └──────────────────┘  └──────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                      EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │ Google OAuth │  │ MS OAuth     │  │ AI Providers (Anthropic,   │ │
│  │ (prod app)   │  │ (prod app)   │  │ Google, DeepSeek)          │ │
│  │ Redirect:    │  │ Redirect:    │  │ API keys in env vars       │ │
│  │ https://api. │  │ https://api. │  └────────────────────────────┘ │
│  │ domain.com/  │  │ domain.com/  │                                  │
│  │ auth/google/ │  │ auth/ms/     │                                  │
│  │ callback     │  │ callback     │                                  │
│  └──────────────┘  └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Gunicorn** | Process manager for Uvicorn workers, fault isolation, multi-core utilization | `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind [::]:$PORT` |
| **Uvicorn Worker** | Async ASGI server handling concurrent requests within single thread | Auto-spawned by Gunicorn, configured via worker class |
| **TrustedHostMiddleware** | Validates Host header matches allowed domains, prevents host header attacks | `app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.domain.com"])` |
| **SecurityHeadersMiddleware** | Adds HSTS, CSP, X-Frame-Options, X-Content-Type-Options headers | Custom middleware (FastAPI doesn't include built-in) |
| **RateLimitMiddleware** | Throttles requests per-IP or per-user, prevents abuse/DDoS | SlowAPI library (decorator-based) or custom token bucket |
| **CORSMiddleware** | Allows cross-origin requests from production frontend only | `allow_origins=["https://app.domain.com"]` |
| **LoggingMiddleware** | Correlation IDs, request/response timing, structured JSON logs | Existing implementation with structlog integration |
| **StaticFiles Mount** | Serves Flutter web build with SPA routing (catch-all index.html) | Mounted AFTER API routes to avoid conflicts |
| **Database (PostgreSQL)** | Persistent data storage with connection pooling, backups, concurrent access | Railway managed PostgreSQL + PgBouncer |
| **Database (SQLite + Volume)** | Lightweight persistent storage for small-scale deployments | Railway Volume mounted at `/data`, file at `/data/ba_assistant.db` |

## Existing vs. New Components

### EXISTING COMPONENTS (No Changes Needed)
| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI app structure | ✅ Production-ready | Lifespan handlers, router organization, async/await |
| LoggingMiddleware | ✅ Production-ready | Correlation IDs, timing, structlog JSON output |
| CORSMiddleware | ⚠️ Configuration change | Update `cors_origins` from localhost to production domain |
| JWT authentication | ✅ Production-ready | Stateless, signed tokens (ensure SECRET_KEY changed) |
| OAuth flows | ⚠️ Configuration change | Requires separate OAuth apps for production redirect URIs |
| SQLAlchemy async ORM | ✅ Production-ready | Supports both SQLite and PostgreSQL |
| Flutter web build | ✅ Production-ready | Compiles to static HTML/JS/WASM |

### NEW COMPONENTS (Must Add)
| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **TrustedHostMiddleware** | Host header validation | `from fastapi.middleware.trustedhost import TrustedHostMiddleware` |
| **SecurityHeadersMiddleware** | Security headers (HSTS, CSP, X-Frame-Options) | Custom middleware (see pattern below) |
| **RateLimitMiddleware** | Request throttling | SlowAPI library: `pip install slowapi` |
| **Gunicorn** | Process manager | Already in requirements.txt, add start command |
| **StaticFiles mount** | Serve Flutter web | `app.mount("/", StaticFiles(directory="build/web", html=True))` |
| **Environment-based config** | Production vs. development settings | Already partially implemented, expand validation |

### MODIFIED COMPONENTS
| Component | Change Required | Reason |
|-----------|-----------------|--------|
| **main.py** | Add security middleware, StaticFiles mount | Production hardening |
| **config.py** | Add production validation for all secrets | Fail-fast on missing config |
| **database.py** | PostgreSQL connection pooling config | Better concurrency than SQLite |
| **auth.py** | Dynamic OAuth redirect URIs based on BACKEND_URL | Environment-specific redirects |

## Recommended Project Structure

### Backend Structure (Modified)
```
backend/
├── app/
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging_middleware.py       # ✅ Exists
│   │   ├── security_headers.py         # ➕ NEW: HSTS, CSP, etc.
│   │   └── rate_limit.py              # ➕ NEW: SlowAPI wrapper
│   ├── core/
│   │   └── static_files.py            # ➕ NEW: Custom StaticFiles for SPA
│   ├── config.py                       # ⚠️ MODIFY: Production validation
│   └── main.py                         # ⚠️ MODIFY: Add middleware, mount
├── build/                              # ➕ NEW: Flutter web output
│   └── web/
│       ├── index.html
│       ├── flutter.js
│       └── ...
├── Dockerfile                          # ➕ NEW: Multi-stage build
├── railway.toml                        # ➕ NEW: Railway deployment config
├── .env.production                     # ➕ NEW: Production env template
└── gunicorn_conf.py                   # ➕ NEW: Gunicorn config
```

### Frontend Structure (Modified)
```
frontend/
├── lib/
│   ├── core/
│   │   └── config.dart                 # ⚠️ MODIFY: Already uses API_BASE_URL
│   └── services/
│       └── api_client.dart             # ✅ Exists: Correlation ID headers
├── build/web/                          # ⚠️ OUTPUT: Copy to backend/build/web
└── .env.production                     # ➕ NEW: Build-time env vars
```

### Structure Rationale

- **backend/build/web/**: Flutter web output copied here for single-server deployment (avoids CORS complexity)
- **middleware/security_headers.py**: Separate file for clarity, reusable across projects
- **middleware/rate_limit.py**: Wrapper around SlowAPI for consistent configuration
- **Dockerfile**: Multi-stage build (Flutter build → Python runtime) for minimal image size
- **railway.toml**: Infrastructure-as-code for reproducible deployments

## Architectural Patterns

### Pattern 1: Single-Server Deployment (Backend Serves Frontend)

**What:** FastAPI serves both API endpoints and Flutter web static files from the same domain.

**When to use:** Small-to-medium traffic, solo developer, want to avoid CORS complexity, using PaaS with free tier.

**Trade-offs:**
- ✅ **Pros:** No CORS issues, single deployment, shared domain, simpler OAuth redirects, lower cost
- ❌ **Cons:** Mixed concerns (API + static files), API downtime = frontend downtime, harder to scale independently

**Example:**
```python
# main.py (simplified)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 1. Register API routes FIRST
app.include_router(auth.router, prefix="/auth")
app.include_router(api.router, prefix="/api")

# 2. Mount static files LAST (catch-all)
# html=True enables SPA routing (serves index.html for unknown paths)
app.mount("/", StaticFiles(directory="build/web", html=True), name="spa")
```

**Critical:** API routes MUST be registered before StaticFiles mount, otherwise catch-all will intercept API requests.

### Pattern 2: Separate Hosting (CDN for Frontend)

**What:** Flutter web hosted on static hosting (Netlify, Vercel, Cloudflare Pages), FastAPI on separate domain.

**When to use:** High traffic, need CDN edge caching, want independent scaling, team has frontend/backend specialists.

**Trade-offs:**
- ✅ **Pros:** Frontend scales independently, CDN edge caching, API can scale horizontally, clearer separation
- ❌ **Cons:** CORS complexity, separate OAuth callback domains, higher cost, more deployment complexity

**Example:**
```python
# main.py (API-only, separate hosting)
app = FastAPI()

# CORS must allow frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No StaticFiles mount
app.include_router(auth.router, prefix="/auth")
app.include_router(api.router, prefix="/api")
```

**Recommendation for BA Assistant:** Start with Pattern 1 (single-server). Move to Pattern 2 only if traffic demands it or you need CDN edge caching.

### Pattern 3: Environment-Based Configuration

**What:** Different configuration for development vs. production, validated at startup.

**When to use:** Always. Never use development secrets in production.

**Trade-offs:**
- ✅ **Pros:** Fail-fast on missing config, clear separation of environments, secure by default
- ❌ **Cons:** Requires discipline to maintain .env.example, CI/CD must inject secrets

**Example:**
```python
# config.py (enhanced validation)
class Settings(BaseSettings):
    environment: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"
    backend_url: str = ""  # Required in production
    cors_origins: str = "http://localhost:3000"

    # OAuth (separate apps for dev vs. prod)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Database (SQLite dev, PostgreSQL prod)
    database_url: str = "sqlite+aiosqlite:///./ba_assistant.db"

    def validate_required(self) -> None:
        """Fail-fast if production config is invalid."""
        if self.environment == "production":
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be changed for production")
            if not self.backend_url:
                raise ValueError("BACKEND_URL required for OAuth redirects")
            if not self.google_client_id:
                raise ValueError("OAuth credentials required for production")
            if "sqlite" in self.database_url.lower():
                print("⚠️ WARNING: Using SQLite in production. Consider PostgreSQL.")

settings = Settings()
settings.validate_required()  # Called in main.py startup
```

### Pattern 4: OAuth Redirect URI Construction

**What:** OAuth redirect URIs must match registered callbacks exactly. Development uses localhost, production uses deployed domain.

**When to use:** Always when deploying OAuth applications.

**Trade-offs:**
- ✅ **Pros:** Works across environments, no hardcoded URLs, validates deployment config
- ❌ **Cons:** Requires separate OAuth app registrations (Google/Microsoft don't allow localhost in production apps)

**Example:**
```python
# auth.py (dynamic redirect URIs)
from app.config import settings

@router.post("/google/initiate")
async def google_oauth_initiate():
    # Construct redirect URI based on environment
    if settings.environment == "production":
        # Uses BACKEND_URL env var (e.g., https://api.example.com)
        redirect_uri = f"{settings.backend_url}/auth/google/callback"
    else:
        # Development default
        redirect_uri = "http://localhost:8000/auth/google/callback"

    auth_url, state = await oauth_service.get_google_auth_url(redirect_uri)
    return {"auth_url": auth_url, "state": state}
```

**Critical:** Must create SEPARATE OAuth app registrations for production with production redirect URI. Cannot reuse localhost OAuth apps.

### Pattern 5: Flutter Web Environment Variables (Build-Time Only)

**What:** Flutter web cannot read .env files from server. API URL must be baked in at build time using `--dart-define`.

**When to use:** Always when building Flutter web for different environments.

**Trade-offs:**
- ✅ **Pros:** Secure (no .env in web bundle), works with CI/CD, supports multiple environments
- ❌ **Cons:** Must rebuild for each environment, cannot change API URL without rebuild

**Example:**
```dart
// frontend/lib/core/config.dart (existing pattern)
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',  // Development default
  );
}

// Build commands:
// Development: flutter build web
// Production:  flutter build web --dart-define=API_BASE_URL=https://api.example.com
```

**Integration with backend:** Copy `frontend/build/web/` to `backend/build/web/` after production build.

## Data Flow

### Request Flow (Single-Server Deployment)

```
[User Browser]
    ↓ (HTTPS)
[PaaS Load Balancer] → Auto SSL/TLS
    ↓
[Gunicorn Process Manager]
    ↓ (Round-robin to worker)
[Uvicorn Worker] → Async event loop
    ↓
[TrustedHostMiddleware] → Validate Host header
    ↓
[SecurityHeadersMiddleware] → Add HSTS, CSP
    ↓
[RateLimitMiddleware] → Check token bucket
    ↓
[CORSMiddleware] → Check origin (if OPTIONS)
    ↓
[LoggingMiddleware] → Generate correlation ID, log start
    ↓
[Route Matching]
    ├─ /api/* → [API Handler] → [Service Layer] → [Database]
    ├─ /auth/* → [OAuth Handler] → [External OAuth] → [JWT Generation]
    ├─ /health → [Health Check] (no auth)
    └─ /* → [StaticFiles] → Serve index.html (SPA routing)
    ↓
[LoggingMiddleware] → Log completion with timing
    ↓
[Response Headers] → Add X-Correlation-ID, security headers
    ↓
[User Browser]
```

### OAuth Flow (Production)

```
1. User clicks "Login with Google" in Flutter app
    ↓
2. Flutter calls POST /api/auth/google/initiate
    ↓ (Backend constructs redirect URI from BACKEND_URL)
3. Backend returns {auth_url: "https://accounts.google.com/..."}
    ↓
4. Flutter opens auth_url in browser
    ↓
5. User authenticates with Google
    ↓
6. Google redirects to: https://api.example.com/auth/google/callback?code=...
    ↓
7. Backend exchanges code for user info, creates/updates user
    ↓
8. Backend generates JWT token
    ↓
9. Backend redirects to: https://app.example.com/auth/callback?token={jwt}
    ↓ (Frontend origin, not API origin)
10. Flutter CallbackScreen extracts token, stores in FlutterSecureStorage
    ↓
11. Flutter navigates to returnUrl or /home
```

**Critical:** OAuth callbacks go to backend domain, but final redirect goes to frontend domain (or same domain if single-server).

### Environment Variable Flow

```
DEVELOPMENT:
.env file → config.py → settings.environment = "development"
    ↓
- cors_origins = "http://localhost:3000"
- secret_key = "dev-secret-key-change-in-production" (warning logged)
- OAuth redirect = "http://localhost:8000/auth/*/callback"
- database_url = "sqlite+aiosqlite:///./ba_assistant.db"

PRODUCTION:
Railway environment variables → config.py → settings.environment = "production"
    ↓
- cors_origins = "https://app.example.com" (or same domain if single-server)
- secret_key = (from SECRET_KEY env var, validated != dev key)
- OAuth redirect = f"{BACKEND_URL}/auth/*/callback"
- database_url = (from DATABASE_URL, PostgreSQL recommended)
    ↓
settings.validate_required() → Raises ValueError if invalid
    ↓
FastAPI lifespan fails to start if validation fails (fail-fast)
```

### Key Data Flows

1. **API request with JWT:** Frontend includes `Authorization: Bearer {jwt}` → Middleware validates JWT → Extracts user_id → Injects into request.state → Available in handler
2. **Correlation ID tracing:** Frontend generates UUID → Sends in X-Correlation-ID header → Backend extracts or generates → Stores in contextvars → Logs all operations with same ID → Returns in response header
3. **SSE streaming (AI responses):** Frontend opens EventSource connection → Backend streams chunks via `sse-starlette` → Frontend updates UI incrementally → Connection closed on completion
4. **Rate limiting:** Middleware checks Redis (or in-memory) token bucket → If tokens available, decrement and allow → If exhausted, return 429 Too Many Requests

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-100 users** | Single Railway dyno, Gunicorn with 4 workers, SQLite + Volume, no caching. Total cost: ~$5-10/month. |
| **100-1K users** | Upgrade to 2 CPU cores (8 workers), PostgreSQL instead of SQLite, add Redis for rate limiting state. Cost: ~$20-30/month. |
| **1K-10K users** | Horizontal scaling (2-3 Railway dynos), PgBouncer for connection pooling, Redis for session state/rate limits, CDN for Flutter web (separate hosting). Cost: ~$50-100/month. |
| **10K+ users** | Separate frontend (CDN), dedicated database cluster, Redis cluster, horizontal autoscaling, APM monitoring. Consider moving off PaaS to AWS/GCP. Cost: $200+/month. |

### Scaling Priorities

1. **First bottleneck (100-1K users):** SQLite write locks under concurrent load
   - **Fix:** Migrate to PostgreSQL (Railway managed, minimal config change)
   - **How:** Change `DATABASE_URL` to PostgreSQL connection string, run migrations

2. **Second bottleneck (1K-10K users):** Uvicorn worker exhaustion (all workers busy)
   - **Fix:** Horizontal scaling (multiple Railway dynos with load balancer)
   - **How:** Railway scales automatically, ensure rate limiting uses shared Redis (not in-memory)

3. **Third bottleneck (10K+ users):** Database connection pool exhaustion
   - **Fix:** PgBouncer (connection pooler between app and PostgreSQL)
   - **How:** Railway provides managed PostgreSQL + PgBouncer template

## Anti-Patterns

### Anti-Pattern 1: Hardcoded URLs

**What people do:** Hardcode `http://localhost:8000` or `https://api.example.com` in code.

**Why it's wrong:** Breaks when deploying to different environments, requires code changes for each deployment, fails testing in staging environments.

**Do this instead:** Use environment variables for all URLs:
- **Backend:** `BACKEND_URL` env var for OAuth redirect construction
- **Frontend:** `API_BASE_URL` build-time variable (`--dart-define`)
- **Database:** `DATABASE_URL` env var (Railway auto-injects)

### Anti-Pattern 2: Reusing Development OAuth Apps

**What people do:** Use same Google/Microsoft OAuth app for development and production.

**Why it's wrong:** OAuth providers reject localhost redirect URIs in production apps, exposes dev credentials in production, violates OAuth security model.

**Do this instead:** Create separate OAuth app registrations:
- **Development:** Redirect URI = `http://localhost:8000/auth/google/callback`
- **Production:** Redirect URI = `https://api.example.com/auth/google/callback`
- Store credentials in environment-specific .env files (never commit production .env)

### Anti-Pattern 3: SQLite in Production Without Volume

**What people do:** Deploy with SQLite using ephemeral filesystem (no Railway Volume).

**Why it's wrong:** Data deleted on every deployment, database resets on dyno restart, no backup/restore capability.

**Do this instead:**
- **Option 1 (Small scale):** SQLite + Railway Volume mounted at `/data/ba_assistant.db`
- **Option 2 (Recommended):** PostgreSQL (Railway managed, auto-backups, connection pooling)

### Anti-Pattern 4: StaticFiles Mounted Before API Routes

**What people do:** Mount StaticFiles at root path before registering API routers.

**Why it's wrong:** StaticFiles catch-all intercepts API requests, returns 404 for valid API endpoints, impossible to debug.

**Do this instead:**
```python
# CORRECT ORDER
app.include_router(auth.router, prefix="/auth")  # First
app.include_router(api.router, prefix="/api")    # Second
app.mount("/", StaticFiles(...), name="spa")     # Last (catch-all)
```

### Anti-Pattern 5: Missing Security Headers

**What people do:** Deploy FastAPI with default middleware (CORS only).

**Why it's wrong:** Vulnerable to XSS, clickjacking, MIME-sniffing attacks. Security scanners flag as insecure. Fails compliance requirements.

**Do this instead:** Add security middleware before CORS:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# 1. TrustedHostMiddleware (validate domain)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com"])

# 2. SecurityHeadersMiddleware (HSTS, CSP, X-Frame-Options)
app.add_middleware(SecurityHeadersMiddleware)

# 3. RateLimitMiddleware (throttling)
app.add_middleware(RateLimitMiddleware)

# 4. CORSMiddleware (cross-origin)
app.add_middleware(CORSMiddleware, allow_origins=[...])

# 5. LoggingMiddleware (observability)
app.add_middleware(LoggingMiddleware)
```

### Anti-Pattern 6: No Rate Limiting

**What people do:** Deploy API without rate limiting, assume PaaS DDoS protection is sufficient.

**Why it's wrong:** API abuse drains AI API budgets (Anthropic/Google charges per request), database overwhelmed by spam, single user can exhaust all workers.

**Do this instead:** Add SlowAPI rate limiting per-user and per-IP:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/threads/{thread_id}/chat")
@limiter.limit("10/minute")  # Per-IP limit for AI endpoints
async def chat(thread_id: str, ...):
    ...
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Google OAuth** | Authlib library, server-side token exchange | Separate app registration for production, redirect URI must match exactly |
| **Microsoft OAuth** | Authlib library, Azure AD v2.0 endpoints | Separate app registration for production, tenant-specific or multi-tenant |
| **Anthropic API** | Official `anthropic` SDK, streaming responses | API key from `ANTHROPIC_API_KEY` env var, primary AI provider |
| **Google Gemini** | Official `google-genai` SDK, streaming responses | API key from `GOOGLE_API_KEY` env var, secondary provider |
| **DeepSeek** | OpenAI-compatible SDK, custom base URL | API key from `DEEPSEEK_API_KEY` env var, tertiary provider |
| **Railway PostgreSQL** | SQLAlchemy async engine, asyncpg driver | `DATABASE_URL` auto-injected by Railway, use PgBouncer for connection pooling |
| **Railway Volumes** | Standard filesystem path | Mount at `/data`, SQLite at `/data/ba_assistant.db`, survives deployments |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Frontend ↔ Backend** | HTTPS REST + SSE, JWT auth in Authorization header | Correlation IDs in X-Correlation-ID header for log tracing |
| **Middleware ↔ Routes** | ASGI request/response cycle | Middleware modifies request.state (e.g., user_id) for downstream handlers |
| **Routes ↔ Services** | Direct function calls (async/await) | Service layer handles business logic, routes handle HTTP concerns |
| **Services ↔ Database** | SQLAlchemy async sessions via dependency injection | `get_db()` yields session, auto-commits on success, rolls back on exception |
| **Gunicorn ↔ Uvicorn Workers** | Unix socket or TCP socket | Gunicorn spawns workers, restarts on failure, round-robin load balancing |
| **Backend ↔ OAuth Providers** | HTTPS OAuth 2.0 flow, Authlib library | Server-side token exchange (never expose client secret to frontend) |

## Production Deployment Configuration

### Environment Variables (Backend)

**Required for Production:**
```bash
# Environment
ENVIRONMENT=production

# Security
SECRET_KEY=<output of: openssl rand -hex 32>
BACKEND_URL=https://api.example.com  # For OAuth redirect construction

# Database (Railway auto-injects if using managed PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# CORS (frontend domain, or omit if same domain)
CORS_ORIGINS=https://app.example.com

# OAuth - Production Apps (separate registrations!)
GOOGLE_CLIENT_ID=<prod-app-client-id>
GOOGLE_CLIENT_SECRET=<prod-app-client-secret>
MICROSOFT_CLIENT_ID=<prod-app-client-id>
MICROSOFT_CLIENT_SECRET=<prod-app-client-secret>

# AI Providers
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...

# Optional
LOG_LEVEL=INFO
LOG_DIR=logs
```

### Flutter Web Build Command

```bash
# Production build with API URL baked in
flutter build web \
  --release \
  --dart-define=API_BASE_URL=https://api.example.com \
  --web-renderer canvaskit

# Copy output to backend for single-server deployment
cp -r frontend/build/web backend/build/web
```

### Gunicorn Start Command

```bash
# Railway start command (railway.toml or web service config)
gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind [::]:$PORT \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

**Note:** `[::]:$PORT` binds to IPv6 (Railway requirement for inter-service communication), `$PORT` auto-injected by Railway.

### Railway Volume Configuration

**For SQLite persistence:**
```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind [::]:$PORT"

[[volumes]]
name = "ba_assistant_data"
mountPath = "/data"
```

**Update database URL:**
```bash
# In Railway environment variables
DATABASE_URL=sqlite+aiosqlite:////data/ba_assistant.db
```

## Sources

**FastAPI Production Deployment:**
- [FastAPI production deployment best practices - Render](https://render.com/articles/fastapi-production-deployment-best-practices)
- [Deploy a FastAPI App - Railway Guides](https://docs.railway.com/guides/fastapi)
- [FastAPI Best Practices for Production: Complete 2026 Guide](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026)

**Flutter Web Hosting:**
- [Build and release a web app - Flutter Docs](https://docs.flutter.dev/deployment/web)
- [Where to Host Your Flutter Web App: Complete Guide](https://stfalcon.com/en/blog/post/hosting-options-for-your-flutter-web-app)

**Security Headers:**
- [FastAPI Security Headers - Compile N Run](https://www.compilenrun.com/docs/framework/fastapi/fastapi-security/fastapi-security-headers/)
- [10 FastAPI Security Headers (CSP/HSTS) Without Latency - Medium](https://medium.com/@npavfan2facts/10-fastapi-security-headers-csp-hsts-without-latency-8228a32bb235)
- [Advanced Middleware - FastAPI Official Docs](https://fastapi.tiangolo.com/advanced/middleware/)

**Static File Serving:**
- [Static Files - FastAPI Official Docs](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Serving a static frontend with app.mount() - FastAPI Discussion](https://github.com/fastapi/fastapi/discussions/5443)

**OAuth Production Configuration:**
- [Railway Help: Google Drive API OAuth Redirect Issue](https://station.railway.com/questions/bug-report-google-drive-api-o-auth-redir-10e36397)
- [Using OAuth 2.0 for Web Server Applications - Google Developers](https://developers.google.com/identity/protocols/oauth2/web-server)

**Database & Connection Pooling:**
- [How to Handle Database Connection Pooling - Railway Blog](https://blog.railway.com/p/database-connection-pooling)
- [PostgreSQL - Railway Docs](https://docs.railway.com/databases/postgresql)
- [asyncpg Usage Documentation](https://magicstack.github.io/asyncpg/current/usage.html)

**Railway Volumes:**
- [Railway Volumes - Grokipedia](https://grokipedia.com/page/Railway_Volumes)
- [General question about persistence SQLite - Railway Help Station](https://station.railway.com/questions/general-question-about-persistence-sq-lit-c90a760f)

**Rate Limiting:**
- [GitHub - laurentS/slowapi: A rate limiter for Starlette and FastAPI](https://github.com/laurentS/slowapi)
- [Using SlowAPI in FastAPI: Mastering Rate Limiting Like a Pro - Medium](https://shiladityamajumder.medium.com/using-slowapi-in-fastapi-mastering-rate-limiting-like-a-pro-19044cb6062b)
- [Building Production-Ready APIs with FastAPI - Medium](https://dev-faizan.medium.com/building-production-ready-apis-with-fastapi-complete-guide-with-authentication-rate-limiting-and-391028cc623c)

**Flutter Environment Variables:**
- [Managing Environment Variables in Flutter Web - Medium](https://medium.com/@akshelar.18119/managing-environment-variables-in-flutter-web-074a01622687)
- [Configure a Flutter App with dart-define environment variable](https://thiele.dev/blog/part-1-configure-a-flutter-app-with-dart-define-environment-variable/)
- [Environment Variables in Flutter: Development & Production - KindaCode](https://www.kindacode.com/article/environment-variables-in-flutter)

---
*Architecture research for: Security hardening and production deployment integration with existing FastAPI + Flutter web architecture*
*Researched: 2026-02-09*
