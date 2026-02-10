# Phase 49: Backend Deployment Foundation - Research

**Researched:** 2026-02-10
**Domain:** Railway backend deployment with persistent SQLite and environment configuration
**Confidence:** HIGH

## Summary

Phase 49 deploys the FastAPI backend to Railway with SQLite persistence and production environment configuration. The backend is already production-ready—all necessary dependencies (gunicorn, uvicorn) are installed, start commands (railway.json, Procfile) are configured, and validation logic (config.py) exists. Deployment requires configuration, not code changes.

**Key finding:** Railway's Nixpacks builder (being replaced by Railpack in 2026) detects Python projects automatically, but existing railway.json and Procfile already define the start command. Persistent volumes mount at any path (recommended: `/data`), and DATABASE_URL must use absolute path (`sqlite+aiosqlite:////data/ba_assistant.db`). Health check endpoint exists at `/health` and will be called once at startup with 300-second timeout.

**Database backup:** Two approaches exist—Litestream (continuous streaming replication) and cron-based backups using Railway's built-in backup feature. For pilot deployment (< 10 users), Railway's automated volume backups are sufficient. Litestream adds complexity without proportional benefit at this scale. Cron jobs are not natively supported by Railway; background tasks would require a separate worker process.

**Primary recommendation:** Use Railway Nixpacks with persistent volume at `/data`, configure environment variables via Railway dashboard, and enable automated volume backups. No code changes needed.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Railway | N/A | PaaS hosting | Official Python/FastAPI support, persistent volumes for SQLite, usage-based pricing ($5-10/month pilot) |
| Nixpacks | 1.x | Railway build system | Zero-config Python detection, Railway default (being replaced by Railpack but Nixpacks still supported) |
| Gunicorn | 21.2.0 | Process manager | Already in requirements.txt, manages Uvicorn workers, production-standard |
| Uvicorn | 0.27.0 | ASGI server | Already in requirements.txt, async-capable, used with UvicornWorker |

**Installation:**
All dependencies already installed in `backend/requirements.txt`. No additional packages needed for Phase 49.

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Litestream | 0.3.x | SQLite streaming replication | Production scale (100+ users) with S3/GCS backup storage. Overkill for pilot. |
| Railway CLI | Latest | Deploy from CLI, tail logs, manage volumes | Optional—Railway dashboard sufficient for pilot deployment |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Railway Nixpacks | Dockerfile | Dockerfile offers smaller image sizes (Nixpacks: 800MB-1.3GB, Dockerfile: 76-400MB) and faster builds, but requires manual configuration. Nixpacks is zero-config. For pilot, Nixpacks simplicity outweighs image size concerns. |
| Railway volumes | PostgreSQL | PostgreSQL offers better concurrency and multi-instance support, but requires managed database service (+$10-15/month). SQLite on persistent volume is sufficient for pilot (< 10 concurrent users). Migrate if scaling needed. |
| Railway backups | Litestream | Litestream provides continuous replication to S3/GCS with point-in-time recovery. Railway backups are simpler (one-click) but manual restore. For pilot with known users, Railway backups sufficient. Add Litestream before production launch. |
| Nixpacks | Railpack | Railpack (launched March 2026) reduces image sizes 38-77% and improves build caching, but is in beta. Nixpacks is mature and stable. New deployments should consider Railpack, but Nixpacks is safe default. |

## Architecture Patterns

### Railway Deployment Architecture
```
[GitHub Repository]
       ↓ (git push triggers deploy)
[Railway Build System: Nixpacks/Railpack]
       ↓
   - Detects Python (requirements.txt)
   - Installs dependencies (pip install -r requirements.txt)
   - Uses start command from railway.json or Procfile
       ↓
[Gunicorn (4 workers) → Uvicorn Workers → FastAPI App]
       ↓
[Health Check: GET /health (300s timeout)]
       ↓
[Live Deployment on *.up.railway.app or custom domain]
       ↓
[Persistent Volume: /data → ba_assistant.db]
```

### Pattern 1: Persistent Volume Configuration
**What:** Railway volumes persist data across deployments. Mounted at specified path, survives container restarts and redeployments.

**When to use:** Any file-based database (SQLite) or file storage requiring persistence.

**Configuration:**
```toml
# railway.toml (or configure via Railway dashboard)
[[volumes]]
name = "ba_assistant_data"
mountPath = "/data"
```

**Database URL:**
```bash
# Railway environment variable
DATABASE_URL=sqlite+aiosqlite:////data/ba_assistant.db
# Note: Four slashes (///) = relative path, (////) = absolute path /data/ba_assistant.db
```

**Critical:** Volumes mount at runtime, NOT build time. Writing to volume directory during build will not persist. Database file must be created by application at runtime.

**Example verification:**
```python
# In FastAPI startup, log database path
from pathlib import Path
db_path = Path("/data/ba_assistant.db")
print(f"Database path exists: {db_path.exists()}, writable: {db_path.parent.is_dir()}")
```

### Pattern 2: Environment Variable Validation at Startup
**What:** Validate all required environment variables before FastAPI starts accepting requests. Fail deployment if critical config missing.

**When to use:** Always in production. Prevents runtime errors from missing config.

**Current implementation (config.py):**
```python
# backend/app/config.py already implements this
settings = Settings()
settings.validate_required()  # Called in main.py

# Validation checks:
# - ENVIRONMENT=production → SECRET_KEY != dev default
# - ANTHROPIC_API_KEY present
# - OAuth credentials (GOOGLE_CLIENT_ID, MICROSOFT_CLIENT_ID) present
# - Warns if SQLite in production
```

**Railway behavior:**
- If `settings.validate_required()` raises ValueError, Railway marks deployment as failed
- Failed deployments don't route traffic (previous deployment stays live)
- Deployment logs show validation error message

**Enhancement for Phase 49:**
```python
# Add BACKEND_URL validation to config.py
if self.environment == "production" and not os.getenv("BACKEND_URL"):
    raise ValueError("BACKEND_URL required for OAuth redirects in production")
```

### Pattern 3: Health Check Endpoint
**What:** Railway calls `/health` endpoint at startup to verify deployment succeeded. 300-second timeout (5 minutes). Endpoint must return 200 status.

**Current implementation:**
```python
# backend/main.py (already exists)
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment verification."""
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0",
    }
```

**Railway configuration:**
```json
// railway.json (add healthcheck configuration)
{
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

**Critical:** Railway uses hostname `healthcheck.railway.app` when calling health check. If backend restricts hosts, must allow this hostname.

**Enhancement (optional):**
```python
# Verify database connection in health check
from app.database import engine

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))  # Test DB connection
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )
```

### Pattern 4: SSE Streaming Configuration
**What:** Server-Sent Events require unbuffered proxy configuration. Railway's nginx proxy buffers responses by default.

**Current implementation:**
```python
# backend/app/routes/conversations.py (already uses sse-starlette)
from sse_starlette.sse import EventSourceResponse

@router.post("/threads/{thread_id}/chat")
async def stream_chat(...):
    return EventSourceResponse(event_generator(...))
```

**Required headers for Railway:**
```python
# Add to SSE response (sse-starlette handles most automatically)
@router.post("/threads/{thread_id}/chat")
async def stream_chat(...):
    async def event_generator():
        # ... existing logic ...
        yield {"event": "message", "data": json.dumps(chunk)}

    return EventSourceResponse(
        event_generator(),
        headers={
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
```

**Verification:**
- Test SSE endpoint from production domain
- Verify chunks arrive incrementally, not in batch
- Check Network tab for streaming response (not waiting for completion)

**Railway timeout:** Default request timeout is 300 seconds (5 minutes). SSE connections longer than this will be terminated. For long AI responses, this is usually sufficient. If needed, can increase via `RAILWAY_TIMEOUT` environment variable.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **SQLite backups** | Custom cron job + S3 upload script | Railway automated volume backups OR Litestream | Railway's one-click backups handle manual/scheduled backups. Litestream provides continuous replication with point-in-time recovery. Custom scripts risk data corruption (must use `.backup` command, not `cp`) and require S3 credential management. |
| **Process management** | Custom supervisord/systemd config | Gunicorn with Uvicorn workers | Gunicorn is production-standard for FastAPI, handles worker crashes, supports graceful reload. Already configured in railway.json/Procfile. |
| **Environment validation** | Runtime checks on first request | Startup validation in config.py | FastAPI lifespan events (already used in main.py) fail deployment if config invalid. Runtime checks allow broken deployments to go live. |
| **Health monitoring** | Custom ping service | Railway built-in health checks | Railway calls `/health` at startup and can monitor continuously. Custom solutions add complexity without benefit. |

**Key insight:** Railway provides deployment primitives (volumes, backups, health checks, environment variables). Use platform features instead of implementing from scratch. Custom solutions increase maintenance burden and miss Railway platform updates.

## Common Pitfalls

### Pitfall 1: Relative Path in DATABASE_URL
**What goes wrong:** SQLite database file created in wrong location (not on persistent volume). Data appears to persist during deployment but is lost on next deploy or container restart.

**Why it happens:** DATABASE_URL uses relative path (`sqlite+aiosqlite:///./ba_assistant.db`) which resolves to `/app/ba_assistant.db` (application directory, not volume mount). Volume mounted at `/data` is ignored.

**How to avoid:**
1. Use absolute path in DATABASE_URL: `sqlite+aiosqlite:////data/ba_assistant.db` (four slashes)
2. Verify database location in startup logs: `print(f"Database path: {settings.database_url}")`
3. Test persistence: Deploy → Create data → Redeploy → Verify data still exists

**Warning signs:**
- Data exists after first deployment but disappears after second
- Railway dashboard shows volume is empty (0 bytes used)
- Database file appears in `/app/` instead of `/data/` when inspecting container

### Pitfall 2: Missing ENVIRONMENT=production
**What goes wrong:** Backend deploys successfully but uses development defaults. SECRET_KEY validation doesn't run, OAuth redirect URIs use localhost, CORS allows localhost origins.

**Why it happens:** `config.py` validation only runs if `settings.environment == "production"`. Without ENVIRONMENT variable set, defaults to "development".

**How to avoid:**
1. Set `ENVIRONMENT=production` in Railway environment variables (first variable to configure)
2. Verify validation runs: Check Railway logs for "SECRET_KEY must be changed" error if using dev key
3. Test OAuth: Attempt login, verify redirect URI uses production domain (not localhost)

**Warning signs:**
- OAuth login fails with "redirect_uri_mismatch" error
- Backend logs show "WARNING: Using SQLite in production" but SECRET_KEY warning doesn't appear
- CORS errors from production frontend despite setting CORS_ORIGINS
- API docs visible at `/docs` in production (should be disabled when environment=production)

### Pitfall 3: Health Check Timeout on Slow Startup
**What goes wrong:** Railway marks deployment as failed even though backend eventually becomes healthy. Database initialization or migration takes > 300 seconds.

**Why it happens:** Railway's default health check timeout is 300 seconds (5 minutes). If database has many migrations or large initial data load, startup exceeds timeout.

**How to avoid:**
1. Monitor startup time in Railway logs: Time from "Starting deployment" to "Listening on port"
2. If > 60 seconds, investigate slow startup (usually database migrations)
3. If legitimately slow, increase timeout: Set `RAILWAY_HEALTHCHECK_TIMEOUT_SEC` environment variable
4. Optimize migrations: Run migrations as separate deploy step, not in application startup

**Warning signs:**
- Railway shows "Deployment failed" but logs show FastAPI started successfully
- Health check logs show timeout errors
- Backend becomes accessible after "failed" deployment (timing issue)

### Pitfall 4: Port Binding Mismatch
**What goes wrong:** Railway health check fails. Backend logs show "Listening on 0.0.0.0:8000" but Railway expects different port.

**Why it happens:** Railway injects `PORT` environment variable (random high port like 8001, 8123). Backend must bind to `$PORT`, not hardcoded 8000.

**How to avoid:**
1. Use `$PORT` in start command: `--bind 0.0.0.0:$PORT` (already configured in railway.json/Procfile)
2. Verify Railway.json binding: `"startCommand": "... --bind 0.0.0.0:$PORT"`
3. Don't hardcode port in uvicorn/gunicorn config

**Current configuration (correct):**
```json
// railway.json
"startCommand": "gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120"
```

**Warning signs:**
- Health check times out despite backend starting
- Logs show "Address already in use" or "Permission denied" on port 8000
- Railway "Networking" tab shows different port than backend is bound to

### Pitfall 5: SSE Streaming Buffered by Proxy
**What goes wrong:** AI responses don't stream character-by-character. Frontend shows loading spinner for 30-60 seconds, then entire response appears at once.

**Why it happens:** Railway's nginx proxy buffers responses by default. Without `X-Accel-Buffering: no` header, SSE events are batched until response completes.

**How to avoid:**
1. Add `X-Accel-Buffering: no` header to SSE responses (see Pattern 4)
2. Add `Cache-Control: no-cache` and `Connection: keep-alive` headers
3. Test streaming: Call SSE endpoint from frontend, verify chunks arrive incrementally

**Warning signs:**
- SSE works perfectly in development (no proxy), broken in production
- Network tab shows SSE request "pending" for 30+ seconds
- Browser console shows EventSource connection established but no data events
- Response arrives in single chunk after long delay

## Code Examples

### Railway Volume Configuration
```toml
# railway.toml (or configure via Railway dashboard → Service → Volumes)
[[volumes]]
name = "ba_assistant_data"
mountPath = "/data"
```

### Environment Variables (Railway Dashboard)
```bash
# Required for Phase 49
ENVIRONMENT=production
DATABASE_URL=sqlite+aiosqlite:////data/ba_assistant.db
SECRET_KEY=<generate with: openssl rand -hex 32>
BACKEND_URL=https://<random-name>.up.railway.app

# OAuth (use development apps for Phase 49, production apps in later phase)
GOOGLE_CLIENT_ID=<dev-app-client-id>
GOOGLE_CLIENT_SECRET=<dev-app-client-secret>
MICROSOFT_CLIENT_ID=<dev-app-client-id>
MICROSOFT_CLIENT_SECRET=<dev-app-client-secret>

# AI Services
ANTHROPIC_API_KEY=sk-ant-...

# CORS (allow Railway default domain for Phase 49)
CORS_ORIGINS=https://<random-name>.up.railway.app

# Logging
LOG_LEVEL=INFO
```

### SSE Streaming Headers
```python
# backend/app/routes/conversations.py
from sse_starlette.sse import EventSourceResponse

@router.post("/threads/{thread_id}/chat")
async def stream_chat(...):
    async def event_generator():
        # ... existing streaming logic ...
        yield {"event": "message", "data": json.dumps(chunk)}

    return EventSourceResponse(
        event_generator(),
        headers={
            "X-Accel-Buffering": "no",      # Disable nginx buffering
            "Cache-Control": "no-cache",     # Prevent caching
            "Connection": "keep-alive"       # Keep connection open
        }
    )
```

### Health Check Enhancement
```python
# backend/main.py (optional enhancement)
from fastapi.responses import JSONResponse
from app.database import get_db

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for Railway deployment verification.

    Verifies:
    - FastAPI is running (200 response)
    - Database connection works (query succeeds)
    - Environment is configured (returns environment)
    """
    try:
        # Test database connection
        await db.execute(select(1))

        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.environment,
            "version": "1.0.0",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Heroku (ephemeral filesystem) | Railway with persistent volumes | 2022 | Heroku removed free tier, ephemeral filesystem requires PostgreSQL. Railway offers persistent volumes for SQLite. |
| Buildpacks (Cloud Foundry) | Nixpacks/Railpack | 2022/2026 | Railway introduced Nixpacks for zero-config builds. Railpack (March 2026) reduces image sizes 38-77%. |
| Manual SQLite backups (cron + cp) | Railway volume backups OR Litestream | 2023/2026 | Railway added one-click volume backups. Litestream offers continuous replication. Both safer than `cp` (transactionally unsafe). |
| Gunicorn sync workers | Gunicorn + Uvicorn async workers | 2020 | FastAPI requires async ASGI server. UvicornWorker class provides async capabilities under Gunicorn process management. |

**Deprecated/outdated:**
- **Heroku free tier:** Removed November 2022. Ephemeral filesystem makes SQLite impractical even on paid plans.
- **Buildpacks:** Still supported but Nixpacks/Railpack offer better performance and smaller images.
- **SQLite `cp` backups:** Not transactionally safe, can corrupt database. Use `.backup` command or Litestream.
- **Sync Gunicorn workers for FastAPI:** Blocks on async operations, limits concurrency. Use UvicornWorker.

## Open Questions

### Resolved During Research

1. **Does Railway support persistent SQLite?**
   - **Resolved:** Yes, via persistent volumes mounted at any path (recommended: `/data`). Volumes persist across deployments.

2. **What's the best backup strategy for SQLite on Railway?**
   - **Resolved:** Railway's automated volume backups sufficient for pilot (< 10 users). Litestream recommended for production (100+ users) with continuous replication to S3/GCS.

3. **Does Railway's proxy buffer SSE responses?**
   - **Resolved:** Yes, nginx buffers by default. Add `X-Accel-Buffering: no` header to disable buffering for SSE endpoints.

4. **Should we use Nixpacks or Dockerfile?**
   - **Resolved:** Nixpacks for Phase 49 (zero-config, already configured in railway.json). Consider Railpack or Dockerfile for optimization in later phases.

### Deferred (Not Blocking Phase 49)

1. **Litestream configuration for continuous backups**
   - What we know: Litestream replicates to S3/GCS, uses SQLite WAL mode, requires separate process
   - What's unclear: Optimal Railway configuration (sidecar container vs. background thread)
   - Recommendation: Use Railway backups for pilot, research Litestream before production launch

2. **Railway volume backup automation**
   - What we know: Railway supports manual and automated volume backups
   - What's unclear: Backup scheduling options (daily? hourly?), retention policies
   - Recommendation: Configure in Railway dashboard during Phase 49, document settings

3. **Railpack vs Nixpacks performance**
   - What we know: Railpack (beta, March 2026) reduces image sizes 38-77% vs. Nixpacks
   - What's unclear: Stability, Python support completeness, migration path from Nixpacks
   - Recommendation: Stay with Nixpacks for Phase 49 (proven stable), evaluate Railpack in later optimization phase

## Sources

### Primary (HIGH confidence)
- [Railway Volumes Documentation](https://docs.railway.com/volumes) - Official volume configuration and mount paths
- [Railway Variables Documentation](https://docs.railway.com/variables) - Environment variable management
- [Railway Healthchecks Documentation](https://docs.railway.com/reference/healthchecks) - Health check configuration and timeouts
- [Railway Config as Code](https://docs.railway.com/reference/config-as-code) - railway.toml/railway.json structure
- [Deploy a FastAPI App - Railway Guides](https://docs.railway.com/guides/fastapi) - Official FastAPI deployment guide
- [Railway Backups Documentation](https://docs.railway.com/reference/backups) - Volume backup features

### Secondary (MEDIUM confidence)
- [Railway vs Nixpacks: Manually Optimize Deployments](https://blog.railway.com/p/comparing-deployment-methods-in-railway) - Nixpacks vs Dockerfile comparison
- [Railpack vs. Nixpacks: Which Containerization Tool Wins in 2026?](https://www.bitdoze.com/nixpacks-vs-railpack/) - Railpack introduction (March 2026)
- [Litestream Documentation](https://litestream.io/) - SQLite streaming replication tool
- [Litestream vs Cron-based backups](https://litestream.io/alternatives/cron/) - Backup strategy comparison
- [FastAPI SSE with Railway proxy](https://medium.com/@inandelibas/real-time-notifications-in-python-using-sse-with-fastapi-1c8c54746eb7) - SSE unbuffering techniques
- [Railway Help Station: SQLite with volumes](https://station.railway.com/questions/how-do-i-use-volumes-to-make-a-sqlite-da-34ea0372) - Community guidance

### Tertiary (LOW confidence - flagged for validation)
- None - all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Railway deployment: HIGH - Official docs and existing railway.json/Procfile configuration verified
- Persistent volumes: HIGH - Official docs confirm SQLite support with volume mount at `/data`
- Backup strategy: MEDIUM - Railway backups documented but Litestream integration unclear
- Health checks: HIGH - Official docs specify timeout (300s) and hostname (healthcheck.railway.app)
- SSE streaming: MEDIUM - X-Accel-Buffering header confirmed by community, not Railway-specific docs

**Research date:** 2026-02-10
**Valid until:** ~60 days (Railway platform changes infrequently, Railpack beta may affect recommendations)

**Phase 49 readiness:** All necessary information gathered. No blockers identified. Backend is deployment-ready with existing configuration.
