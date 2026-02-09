# Pitfalls Research

**Domain:** First-Time Deployment — FastAPI + Flutter Web with OAuth
**Researched:** 2026-02-09
**Confidence:** HIGH

---

## Critical Pitfalls

### Pitfall 1: Hardcoded Localhost OAuth Redirects

**What goes wrong:**
OAuth authentication fails completely in production. Google/Microsoft reject all login attempts with "redirect_uri_mismatch" errors. Users cannot authenticate at all.

**Why it happens:**
OAuth redirect URIs are hardcoded to `http://localhost:8000` and `http://localhost:8080` in both backend routes (`backend/app/routes/auth.py` lines 43, 84, 102, 133, 174, 190) and OAuth provider configurations. When deployed with custom domain, OAuth providers reject requests because production domain ≠ localhost.

**Current code evidence:**
```python
# backend/app/routes/auth.py
redirect_uri = "http://localhost:8000/auth/google/callback"  # Line 43, 84
redirect_uri = "http://localhost:8000/auth/microsoft/callback"  # Line 133, 174

# Redirects to frontend also hardcoded:
return RedirectResponse(
    url=f"http://localhost:8080/auth/callback?token={token}"  # Line 102, 190
)
```

**How to avoid:**
1. **Phase 1 (Infrastructure Setup):** Set `BACKEND_URL` and `FRONTEND_URL` environment variables in PaaS platform
2. **Phase 2 (Backend Configuration):** Make redirect URIs environment-aware:
   ```python
   backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
   frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
   redirect_uri = f"{backend_url}/auth/google/callback"
   return RedirectResponse(url=f"{frontend_url}/auth/callback?token={token}")
   ```
3. **Phase 3 (OAuth Registration):** Register production redirect URIs with Google/Microsoft OAuth apps (separate from dev apps)
4. **Phase 4 (Flutter Configuration):** Update `ApiConfig.baseUrl` in `frontend/lib/core/config.dart` to use environment variable

**Warning signs:**
- Testing OAuth with production domain shows "Invalid redirect URI" error
- OAuth consent screen shows localhost URL when testing from custom domain
- Backend logs show "redirect_uri_mismatch" errors from OAuth providers

**Phase to address:**
**Phase 2 (Backend Environment Configuration)** — OAuth redirect URIs must be configurable before deployment

---

### Pitfall 2: Secrets Exposed via .env Commit

**What goes wrong:**
API keys, OAuth secrets, and JWT secret keys get committed to git repository. Anyone with repo access (or if repo is public) gains full access to production credentials. Attackers can impersonate users, access AI services on your billing, and decrypt stored documents.

**Why it happens:**
First-time deployers test with real credentials in `.env` file, then forget to add `.env` to `.gitignore` or accidentally commit with `git add .` while troubleshooting. `.env` files are designed for local development, not production secret management.

**Current code evidence:**
- `.gitignore` exists, but developers may create `.env.production` or similar files not covered
- Sensitive keys in `backend/app/config.py`: `secret_key`, `google_client_secret`, `microsoft_client_secret`, `anthropic_api_key`, `google_api_key`, `deepseek_api_key`, `fernet_key`

**How to avoid:**
1. **Phase 1 (Pre-deployment Audit):**
   - Run `git log --all --full-history -- "*.env*"` to check if secrets were ever committed
   - If found: Rotate ALL secrets immediately, use `git filter-repo` to remove from history
2. **Phase 2 (PaaS Configuration):**
   - Use Railway/Render's built-in environment variable management
   - NEVER store secrets in code or commit them
   - Use separate keys for production vs. development
3. **Phase 3 (Secret Rotation):**
   - Generate new production `SECRET_KEY`: `openssl rand -hex 32`
   - Create production OAuth apps (separate from development)
   - Use production-only AI API keys with usage limits
4. **Phase 4 (Monitoring):**
   - Set up GitGuardian or similar to scan for secret leaks
   - Enable PaaS platform audit logs

**Warning signs:**
- `.env` file appears in `git status` output
- GitHub shows `.env` in commit history
- AI service billing shows unexpected usage from unknown IPs
- Logs contain full API keys (should be redacted)

**Phase to address:**
**Phase 1 (Security Audit)** — Must happen BEFORE any deployment attempt

**Recovery cost:** HIGH — requires rotating all secrets, revoking OAuth apps, notifying users if breach occurred

---

### Pitfall 3: SQLite File Loss on Container Redeploy

**What goes wrong:**
All user data (projects, documents, threads, messages) disappears after Railway/Render redeploys container. Database resets to empty state. Users lose all work.

**Why it happens:**
Railway/Render containers use ephemeral file systems. SQLite stores database as file (`backend/ba_assistant.db`). On redeploy, container filesystem is wiped, taking database with it. No persistent volume configured.

**Current code evidence:**
```python
# backend/app/config.py
database_url: str = "sqlite+aiosqlite:///./ba_assistant.db"  # File-based, no persistence
```

Config includes warning comment:
```python
# Line 112-116: Warns about SQLite in production
if "sqlite" in self.database_url.lower():
    print("WARNING: Using SQLite in production...")
```

**How to avoid:**
**Option A: Persistent Volume (Railway/Render-specific)**
1. **Phase 1:** Configure persistent volume mount in Railway/Render
   - Railway: Mount volume at `/data`, set `DATABASE_URL=sqlite+aiosqlite:////data/ba_assistant.db`
   - Render: Use persistent disk, similar configuration
2. **Phase 2:** Test by redeploying and verifying data persists

**Option B: Migrate to PostgreSQL (recommended for > 10 users)**
1. **Phase 1:** Provision PostgreSQL (Render/Railway managed PostgreSQL)
2. **Phase 2:** Update `DATABASE_URL` environment variable
3. **Phase 3:** Run Alembic migrations: `alembic upgrade head`
4. **Phase 4:** Test concurrent user access (SQLite doesn't handle concurrency well)

**Recommendation for this project:** Option A (persistent volume) is sufficient for pilot (< 10 users). Plan Option B migration if usage grows.

**Warning signs:**
- After redeploy, login shows no projects/documents
- Users report "lost data" after platform maintenance
- Railway/Render dashboard doesn't show persistent storage configured
- Testing redeploy wipes test data

**Phase to address:**
**Phase 2 (Database Persistence Setup)** — Must happen before pilot users create real data

**Recovery cost:** CRITICAL — data is unrecoverable if not backed up

---

### Pitfall 4: CORS Configuration Locked to Localhost

**What goes wrong:**
Frontend deployed to production domain cannot communicate with backend API. All API requests fail with CORS policy errors. App is completely non-functional — users see blank screens or error messages.

**Why it happens:**
CORS middleware is configured to allow only localhost origins. When frontend is deployed to `https://app.example.com`, browser blocks requests to backend API because production domain not in allowlist.

**Current code evidence:**
```python
# backend/app/config.py line 44
cors_origins: str = "http://localhost:3000,http://localhost:8080"

# backend/main.py lines 64-70
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Only localhost!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**How to avoid:**
1. **Phase 1 (Environment Setup):**
   - Set `CORS_ORIGINS` environment variable in PaaS platform:
   ```bash
   CORS_ORIGINS="https://app.example.com,https://www.example.com"
   ```
   - Include both `www` and non-`www` if using both
   - Use `https://` (production), not `http://`
2. **Phase 2 (Testing):**
   - Test from production frontend URL
   - Open browser DevTools → Network tab → verify no CORS errors
   - Test preflight OPTIONS requests succeed
3. **Phase 3 (SSE Streaming):**
   - Verify SSE `/api/threads/{id}/chat` endpoint works cross-origin
   - SSE requires proper CORS for `EventSource` connections

**Warning signs:**
- Browser console shows: `Access to fetch at 'https://api.example.com' from origin 'https://app.example.com' has been blocked by CORS policy`
- Network tab shows requests with status `(failed) net::ERR_FAILED`
- OPTIONS preflight requests return 403 or don't include `Access-Control-Allow-Origin`
- SSE connections fail to establish

**Phase to address:**
**Phase 2 (Backend Configuration)** — Must match frontend deployment URL

---

### Pitfall 5: Flutter Web Debug Build in Production

**What goes wrong:**
App loads extremely slowly (15-30 seconds), bundle size is 6-8MB, fonts fail to load causing indefinite hang, users see blank screen or "Loading..." forever. Screenshots and automated testing time out.

**Why it happens:**
Deploying Flutter debug build (`flutter run -d chrome`) instead of production build (`flutter build web --release`). Debug builds include developer tools, verbose logging, and unoptimized assets. CanvasKit renderer in debug mode has font loading issues.

**Current code evidence:**
- Frontend build process not defined yet
- Risk: Copy debug `build/web` output instead of release build

**How to avoid:**
1. **Phase 1 (Build Configuration):**
   ```bash
   # Production build command (NOT flutter run)
   flutter build web --release --tree-shake-icons
   ```
2. **Phase 2 (Optimization):**
   - Enable tree-shaking: `--tree-shake-icons` removes unused icons
   - Check bundle size: `build/web` directory should be ~2-3MB (not 6-8MB)
3. **Phase 3 (Renderer Selection):**
   - Default `canvaskit` is fine for modern browsers
   - Consider `--web-renderer html` for better compatibility (larger bundle, less features)
4. **Phase 4 (Asset Optimization):**
   - Convert PNGs to WebP where possible
   - Compress images (60% of bundle size)
5. **Phase 5 (Deployment):**
   - Deploy `build/web` directory (output of `flutter build web`)
   - NOT the project root or debug output

**Warning signs:**
- App takes > 10 seconds to show UI
- Browser DevTools → Network shows 6-8MB main.dart.js
- Fonts fail to load, blank screen persists
- `flutter.js` contains debug symbols and stack traces
- Browser console shows "Debug mode" messages

**Phase to address:**
**Phase 3 (Frontend Build & Deployment)** — Build process must use release mode

---

### Pitfall 6: JWT Secret Not Rotated from Default

**What goes wrong:**
Anyone can forge JWT tokens and impersonate users. Attackers gain full access to all user accounts without credentials. They can read projects, documents, messages, and perform actions as any user.

**Why it happens:**
Default `SECRET_KEY` is committed to git (`"dev-secret-key-change-in-production"`) and never changed for production. Developers skip secret generation step or forget to set environment variable.

**Current code evidence:**
```python
# backend/app/config.py line 28
secret_key: str = "dev-secret-key-change-in-production"

# Validation exists but only runs if environment == "production"
if self.secret_key == "dev-secret-key-change-in-production":
    raise ValueError("SECRET_KEY must be changed for production...")
```

**How to avoid:**
1. **Phase 1 (Secret Generation):**
   ```bash
   openssl rand -hex 32
   # Example output: a3f7b9e2c1d6f4a8b7e9c2d5f8a1b4e7c9f2a6d8b3e5f1a7c4d9e6f3a8b2c5f7
   ```
2. **Phase 2 (Environment Configuration):**
   - Set `SECRET_KEY` in Railway/Render environment variables
   - Set `ENVIRONMENT=production` to trigger validation
3. **Phase 3 (Verification):**
   - Backend should fail to start if `SECRET_KEY` is default value
   - Check startup logs for validation errors
   - Test JWT tokens generated in production can't be decoded with dev secret

**Warning signs:**
- Backend starts without error despite default `SECRET_KEY`
- `ENVIRONMENT` is not set to `production`
- `.env` file contains `SECRET_KEY=dev-secret-key-change-in-production`
- JWT tokens look suspiciously similar across environments

**Phase to address:**
**Phase 2 (Security Configuration)** — Before any user authentication

**Recovery cost:** HIGH — all existing tokens must be invalidated, users forced to re-authenticate

---

### Pitfall 7: OAuth State Storage in Memory (Multi-Instance)

**What goes wrong:**
OAuth login fails randomly with "Invalid state parameter" error. Works sometimes, fails other times. Issue worse with PaaS auto-scaling or multiple backend instances.

**Why it happens:**
OAuth state tokens stored in-memory Python dict (`_oauth_states` in `backend/app/routes/auth.py` line 22). With multiple backend instances (load balanced), OAuth initiate and callback may hit different instances. Callback instance doesn't have state token from initiate instance.

**Current code evidence:**
```python
# backend/app/routes/auth.py line 21-22
# TODO comment acknowledges this is a problem!
# TODO: Move to Redis in production for multi-instance deployments
_oauth_states: Dict[str, str] = {}
```

**How to avoid:**
**Short-term fix (single instance pilot):**
1. **Phase 1:** Verify PaaS configured for single instance
   - Railway: Set scaling to 1 instance
   - Render: Use single web service (not autoscaling)
2. **Phase 2:** Document limitation for future scaling

**Long-term fix (if scaling beyond 1 instance):**
1. **Phase 1:** Add Redis to deployment
   - Railway: Provision Redis addon
   - Render: Add Redis managed database
2. **Phase 2:** Replace in-memory dict with Redis:
   ```python
   import redis
   redis_client = redis.from_url(os.getenv("REDIS_URL"))

   # Store: redis_client.setex(state, 600, "google")  # 10min TTL
   # Retrieve: redis_client.get(state)
   ```
3. **Phase 3:** Test OAuth across multiple instances

**Recommendation:** Use short-term fix for pilot (< 10 users, single instance sufficient), plan long-term fix before scaling.

**Warning signs:**
- OAuth fails with "Invalid state parameter" error
- Error occurs intermittently, not consistently
- PaaS dashboard shows > 1 backend instance running
- OAuth works perfectly in development (single process)

**Phase to address:**
**Phase 1 (Deployment Configuration)** — Pin to single instance for pilot
**Later milestone:** Migrate to Redis before scaling

---

### Pitfall 8: Missing HTTPS Enforcement

**What goes wrong:**
OAuth providers reject authentication (Google/Microsoft require HTTPS for production). Browsers show "Not Secure" warning. Users don't trust app. MITM attackers can intercept JWT tokens and session data.

**Why it happens:**
Developers deploy without SSL/TLS certificate, assuming PaaS handles it automatically. Or custom domain added without configuring SSL certificate. OAuth providers whitelist only `https://` redirect URIs in production.

**How to avoid:**
1. **Phase 1 (DNS Setup):**
   - Point custom domain to PaaS platform (A record or CNAME)
   - Wait 24 hours for DNS propagation
2. **Phase 2 (SSL Certificate):**
   - **Railway:** Automatically provisions Let's Encrypt certificate when custom domain added
   - **Render:** Auto-SSL for custom domains
   - Verify certificate issued: `curl -I https://app.example.com`
3. **Phase 3 (HTTP → HTTPS Redirect):**
   - Configure PaaS to redirect HTTP → HTTPS
   - Test: `curl http://app.example.com` should 301 redirect to `https://`
4. **Phase 4 (OAuth Configuration):**
   - Register HTTPS redirect URIs only: `https://app.example.com/auth/callback`
   - Remove HTTP URIs from OAuth provider config
5. **Phase 5 (HSTS - Optional but Recommended):**
   ```python
   # Add to FastAPI middleware
   @app.middleware("http")
   async def add_hsts_header(request, call_next):
       response = await call_next(request)
       response.headers["Strict-Transport-Security"] = "max-age=31536000"
       return response
   ```

**Warning signs:**
- Browser address bar shows "Not Secure"
- OAuth consent screen shows error about HTTP redirect URI
- Certificate warning when accessing site
- `curl https://app.example.com` fails with SSL error
- DNS configured but SSL certificate "pending" for > 24 hours

**Phase to address:**
**Phase 1 (Infrastructure Setup)** — DNS and SSL before OAuth configuration

---

### Pitfall 9: SSE Streaming Broken by Proxy Buffering

**What goes wrong:**
AI responses don't stream character-by-character. Instead, entire response arrives at once after 30-60 seconds (or times out). Streaming indicator spins forever, then massive text dump appears. Poor UX, feels broken.

**Why it happens:**
PaaS reverse proxy (nginx, Envoy) buffers responses by default. SSE requires unbuffered streaming. Proxy waits for response to complete before forwarding, destroying streaming behavior.

**How to avoid:**
1. **Phase 1 (Backend Headers):**
   ```python
   # In SSE endpoint (backend/app/routes/threads.py or conversations.py)
   response.headers["X-Accel-Buffering"] = "no"  # Disables nginx buffering
   response.headers["Cache-Control"] = "no-cache"
   response.headers["Connection"] = "keep-alive"
   ```
2. **Phase 2 (PaaS Configuration):**
   - **Railway:** No configuration needed, respects `X-Accel-Buffering`
   - **Render:** Add to `render.yaml`:
     ```yaml
     services:
       - type: web
         name: backend
         env: python
         buildCommand: pip install -r requirements.txt
         startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
         envVars:
           - key: PROXY_BUFFERING
             value: "off"
     ```
3. **Phase 3 (Timeout Configuration):**
   - Set SSE timeout > 5 minutes (AI responses can be long)
   - Railway: Default timeout 300s (5min), increase if needed
   - Render: Default timeout 30s, must increase for SSE

**Warning signs:**
- Frontend `EventSource` connection established but no `data:` events received
- AI response arrives all at once after long delay
- Network tab shows SSE request "pending" for 30+ seconds
- Works perfectly in local development, broken in production
- Browser console shows SSE connection closed prematurely

**Phase to address:**
**Phase 4 (Streaming Configuration)** — After basic deployment works

---

### Pitfall 10: Environment Variable Typos Break Deployment Silently

**What goes wrong:**
App starts successfully but features fail mysteriously. OAuth shows "configuration error", AI requests fail with "no API key", or app uses default dev values. No startup error, just silent failures.

**Why it happens:**
Environment variable name typo (`ANTRHOPIC_API_KEY` vs `ANTHROPIC_API_KEY`). Pydantic Settings uses default value when env var missing, app starts normally but missing required config.

**Current code evidence:**
```python
# backend/app/config.py — all these have defaults
anthropic_api_key: str = ""  # Empty string default, app starts without error
google_api_key: str = ""
google_client_id: str = ""
# ...
```

Validation only runs for `environment == "production"`, but environment might not be set!

**How to avoid:**
1. **Phase 1 (Explicit Validation):**
   - Always set `ENVIRONMENT=production` in production
   - Validation will catch missing required values:
     ```python
     # config.py line 89-109 validates when environment == "production"
     if not self.anthropic_api_key:
         raise ValueError("ANTHROPIC_API_KEY must be set...")
     ```
2. **Phase 2 (Config Verification Script):**
   ```python
   # verify_config.py
   from app.config import settings
   settings.validate_required()
   print("✓ All required config present")
   ```
   Run during deployment: `python verify_config.py && uvicorn main:app`
3. **Phase 3 (Health Check Enhancement):**
   ```python
   @app.get("/health")
   async def health_check():
       # Check critical config is set
       if not settings.anthropic_api_key:
           return {"status": "unhealthy", "error": "Missing ANTHROPIC_API_KEY"}
       return {"status": "healthy"}
   ```
4. **Phase 4 (Documentation):**
   - Create `.env.example` with all required variables:
     ```bash
     # Required for production
     ENVIRONMENT=production
     SECRET_KEY=<generate with: openssl rand -hex 32>
     ANTHROPIC_API_KEY=sk-ant-...
     GOOGLE_CLIENT_ID=...
     # ...
     ```

**Warning signs:**
- PaaS deployment succeeds but app features don't work
- Logs show "using default config" messages
- OAuth returns "missing client_id" error despite setting env var
- AI requests fail with "authentication error"
- `ENVIRONMENT` not set (check with `echo $ENVIRONMENT` in PaaS shell)

**Phase to address:**
**Phase 2 (Configuration Validation)** — Must validate before considering deployment successful

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| SQLite with persistent volume | Fast deployment, no DB setup | Limited concurrency (< 10 simultaneous users), no replication, manual backups | Pilot phase (< 10 users), migrate to PostgreSQL before scaling |
| In-memory OAuth state | Simple implementation, no Redis cost | Fails with multiple instances, doesn't scale | Single-instance deployment only, must migrate before autoscaling |
| Single backend instance | Avoids state management complexity | No high availability, downtime during deploys | Acceptable for pilot, plan redundancy for production |
| HTTP API → HTTPS via proxy redirect | Works for API calls | JWT tokens briefly transmitted over HTTP (MITM risk window) | Short-term acceptable, add HSTS and enforce HTTPS in app code later |
| Hardcoded 30s SSE timeout | Simple, works for most responses | Long AI responses (complex BRD generation) may timeout | Pilot acceptable, increase timeout if users report cutoff responses |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **Google OAuth** | Registering production domain redirect URI in dev OAuth app | Create separate OAuth app for production with production redirect URIs only |
| **Microsoft OAuth** | Forgetting to configure multi-tenant vs single-tenant | For public app, use "common" tenant in authorization URL |
| **Railway Volumes** | Assuming volume persists across service deletion | Volume data lost if service deleted, must backup before deleting service |
| **Render Persistent Disks** | Not mounting disk, just creating it | Disk must be explicitly mounted to directory path in service config |
| **Let's Encrypt SSL** | Requesting cert before DNS propagates | Wait 24 hours after DNS change, verify with `dig` before adding domain |
| **Flutter Web Fonts** | Using `google_fonts` package without font fallbacks | Define fallback system fonts, preload critical fonts |
| **Anthropic API** | Not handling rate limits in streaming responses | Implement exponential backoff, show user-friendly rate limit message |
| **FastAPI Middleware** | Adding logging after error handlers | Order matters: CORS → Logging → Error Handlers → Routes |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| **SQLite write lock** | Timeout errors during concurrent document uploads | Use PostgreSQL or serialize writes with queue | > 5 concurrent users writing |
| **No database indexes** | Document search slow (> 5 seconds) | Already has FTS5 index (good!), verify with `EXPLAIN QUERY PLAN` | > 100 documents per project |
| **Unbounded AI context** | Token budget exhausted, slow responses | Implement context window management, truncate old messages | Threads > 50 messages |
| **Synchronous file encryption** | Document upload blocks event loop | Already async (good!), verify `await` used correctly | > 10MB document uploads |
| **Flutter web bundle size** | Initial load > 10 seconds on 3G | Tree-shake icons, convert images to WebP, code splitting | Bundle > 3MB |
| **Missing CDN** | Slow static asset load from backend origin | Serve `build/web` from CDN (Cloudflare, AWS CloudFront) | Users outside PaaS region |
| **No SSE connection pooling** | New EventSource for every message | Reuse single EventSource connection per thread | Heavy SSE usage |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| **Committing `.env` to git** | All secrets exposed publicly | Add `.env*` to `.gitignore`, use git-secrets pre-commit hook |
| **Default `SECRET_KEY` in production** | Anyone can forge JWT tokens | Generate with `openssl rand -hex 32`, rotate quarterly |
| **OAuth redirect URI validation bypass** | Authorization code injection attack | Already validates state parameter (good!), ensure HTTPS only |
| **Logging API keys** | Secrets in log files | Already sanitizes logs (good!), verify `logging_service.py` redaction works |
| **No rate limiting** | API abuse, DoS, AI token budget exhaustion | Add rate limiting middleware (10 req/sec per user) |
| **Document encryption key in env** | Key exposure if env leaked | Current approach acceptable for pilot, migrate to KMS later |
| **CORS wildcard `allow_origins=["*"]`** | CSRF attacks | Already uses explicit origins (good!), never use wildcard with `allow_credentials=True` |
| **No HTTPS enforcement** | MITM attacks, token interception | Force HTTPS redirect, add HSTS header |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| **No offline indicator during SSE failure** | Users keep typing, messages lost | Show "Reconnecting..." banner, queue messages |
| **Generic "Something went wrong" errors** | Users don't know if retry will help | Specific messages: "AI service unavailable, try again", "Rate limit exceeded, wait 1 minute" |
| **No loading state during OAuth** | Blank screen for 2-5 seconds | Show "Authenticating with Google..." spinner |
| **AI response cutoff without indication** | Users don't know response is incomplete | If timeout, show "Response truncated, [Retry] button" |
| **No bundle size optimization** | 30-second initial load on slow connections | Show splash screen with progress bar, optimize bundle |
| **Backend error during streaming** | Partial response shown, no error message | Detect SSE error event, show "Generation failed, [Retry] button" |
| **Token budget exhausted mid-response** | Response stops, no explanation | Show budget warning at 80%, disable send at 100% |

---

## "Looks Done But Isn't" Checklist

- [ ] **OAuth Login:** Works with localhost, but redirect URIs not updated for production domain
- [ ] **CORS:** API works in dev, but production frontend origin not in `cors_origins`
- [ ] **SSL Certificate:** Domain added to PaaS, but certificate still "pending" (DNS not propagated)
- [ ] **Database Persistence:** SQLite works, but persistent volume not mounted (data lost on redeploy)
- [ ] **Environment Variables:** All set in PaaS dashboard, but `ENVIRONMENT=production` missing (validation not running)
- [ ] **Flutter Build:** App deployed, but used debug build (slow, large bundle)
- [ ] **SSE Streaming:** Works for short responses, but long responses timeout (no timeout configuration)
- [ ] **Secret Rotation:** `SECRET_KEY` changed, but still using dev OAuth app credentials
- [ ] **Health Check:** Endpoint exists, but doesn't validate critical config (app looks healthy but features broken)
- [ ] **Error Handling:** Generic errors returned, no user-facing messages (users see "500 Internal Server Error")
- [ ] **Logging:** Logs enabled, but writing to ephemeral container filesystem (lost on restart)
- [ ] **Backups:** Database persists, but no backup strategy (data lost if volume corrupted)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| **Hardcoded localhost OAuth** | LOW | Update redirect URIs in code, register production URIs with OAuth providers, redeploy (30 min) |
| **Secrets committed to git** | HIGH | Rotate ALL secrets, rewrite git history (`git filter-repo`), notify users if breach (4+ hours) |
| **SQLite data loss** | CRITICAL | Unrecoverable if no backup, must recreate data from user reports (days of manual work) |
| **CORS misconfiguration** | LOW | Add production origin to `CORS_ORIGINS`, redeploy (5 min) |
| **Flutter debug build** | LOW | Run `flutter build web --release`, redeploy frontend (10 min) |
| **JWT secret leaked** | MEDIUM | Rotate `SECRET_KEY`, invalidate all tokens, users must re-authenticate (1 hour) |
| **OAuth state memory issue** | MEDIUM (single instance) HIGH (multi-instance) | Single instance: Pin to 1 replica (5 min); Multi-instance: Add Redis, refactor code (4 hours) |
| **Missing HTTPS** | MEDIUM | Configure DNS, wait for SSL cert, update OAuth URIs (24 hours for DNS propagation) |
| **SSE buffering** | LOW | Add `X-Accel-Buffering: no` header, redeploy (10 min) |
| **Environment typo** | LOW | Fix typo in PaaS dashboard, redeploy (5 min, but debugging to find typo may take 30 min) |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Hardcoded localhost OAuth | Phase 2 (Backend Config) | Test OAuth flow from production domain |
| Secrets exposed via .env | Phase 1 (Security Audit) | Run `git log` for .env files, scan with GitGuardian |
| SQLite file loss | Phase 2 (Database Persistence) | Test redeploy, verify data persists |
| CORS locked to localhost | Phase 2 (Backend Config) | Test API calls from production frontend, check browser console for CORS errors |
| Flutter debug build | Phase 3 (Frontend Build) | Check bundle size < 3MB, verify `flutter build web --release` used |
| JWT secret not rotated | Phase 2 (Security Config) | Backend fails to start with default SECRET_KEY |
| OAuth state in memory | Phase 1 (Deployment Config) | Verify single instance, document Redis migration needed for scaling |
| Missing HTTPS enforcement | Phase 1 (Infrastructure Setup) | `curl https://app.example.com` succeeds, `curl http://` redirects |
| SSE buffering | Phase 4 (Streaming Config) | Test AI response streams character-by-character |
| Environment variable typos | Phase 2 (Config Validation) | Run `verify_config.py`, health check shows all config present |

---

## Sources

### FastAPI Deployment
- [FastAPI production deployment best practices](https://render.com/articles/fastapi-production-deployment-best-practices) (Render official)
- [The FastAPI Pre-Deployment Checklist You Actually Need | FastroAI Blog](https://fastro.ai/blog/fastapi-deployment-checklist) (2026)
- [FastAPI Best Practices for Production: Complete 2026 Guide](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026) (2026)
- [FastAPI Mistakes That Kill Your Performance | FastroAI Blog](https://fastro.ai/blog/fastapi-mistakes) (2026)

### Flutter Web Deployment
- [Build and release a web app](https://docs.flutter.dev/deployment/web) (Flutter official documentation)
- [Troubleshooting Common Issues in Flutter Web App Deployment](https://moldstud.com/articles/p-troubleshooting-common-issues-in-flutter-web-app-deployment-a-comprehensive-guide)
- [Optimizing Flutter Web for Production: Advanced Techniques](https://medium.com/@reach.subhanu/optimizing-flutter-web-for-production-advanced-techniques-in-code-splitting-seo-and-hosting-a89679afe939)

### OAuth Security
- [How to Fix "Invalid Redirect URI" OAuth2 Errors](https://oneuptime.com/blog/post/2026-01-24-fix-invalid-redirect-uri-oauth2/view) (January 2026)
- [Troubleshooting redirect_uri_mismatch: Step-by-Step for Developers](https://techwarlock.com/troubleshooting-redirect_uri_mismatch-step-by-step-for-developers/)
- [Using OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server) (Google official)

### SQLite in Production
- [Railway vs Render (2026): Which cloud platform fits your workflow better](https://northflank.com/blog/railway-vs-render) (2026)
- [How (and why) to run SQLite in production](https://fractaledmind.com/2023/12/23/rubyconftw/)
- [Self-hosting n8n on Railway — 2026 Guide](https://thinkpeak.ai/self-hosting-n8n-on-railway/) (2026, discusses ephemeral storage)

### Secrets Management
- [Are environment variables still safe for secrets in 2026?](https://securityboulevard.com/2025/12/are-environment-variables-still-safe-for-secrets-in-2026/) (2026)
- [Best Practices for Environment Variables Secrets Management](https://blog.gitguardian.com/secure-your-secrets-with-env/)
- [How Your Environment Variables Can Betray You in Production](https://medium.com/@instatunnel/how-your-environment-variables-can-betray-you-in-production-the-hidden-security-risks-developers-d77200b5cda9)
- [Securing db_password in .env Files: How to Move to Proper Secrets Management in 2026](https://redsentry.com/resources/blog/securing-db-password-in-.env-files-how-to-move-to-proper-secrets-management-in-2026/) (2026)

### HTTPS & SSL
- [Install a TLS/SSL Certificate for Your App - Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/configure-ssl-certificate) (Microsoft official)
- [HTTPS (SSL) | Netlify Docs](https://docs.netlify.com/manage/domains/secure-domains-with-https/https-ssl/) (Netlify official)

### SSE (Server-Sent Events)
- [How to troubleshoot a cross domain server-sent events connection](https://dev.to/mechcloud_academy/how-to-troubleshoot-a-cross-domain-server-sent-events-connection-526m)
- [How to Implement Server-Sent Events (SSE) in React](https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view) (January 2026)
- [Server-Sent Events: A Comprehensive Guide](https://medium.com/@moali314/server-sent-events-a-comprehensive-guide-e4b15d147576)

---

*Pitfalls research for: First-Time FastAPI + Flutter Web Deployment with OAuth*
*Researched: 2026-02-09*
*Context: BA Assistant pilot deployment (< 10 users) to Railway/Render with custom domain*
