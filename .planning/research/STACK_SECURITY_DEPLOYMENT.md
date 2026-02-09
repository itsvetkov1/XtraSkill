# Stack Research: Security Hardening & Production Deployment

**Domain:** Security audit tooling and first-time production deployment (PaaS)
**Researched:** 2026-02-09
**Confidence:** HIGH

## Recommended Stack

### Security Scanning Tools

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| bandit | >=1.8.6 | Static code security scanner for Python | Industry standard for finding common security issues in Python code (hardcoded passwords, unsafe eval, weak crypto). Maintained by PyCQA, actively updated (latest release Jan 2026). Zero runtime overhead. |
| pip-audit | >=2.9.0 | Dependency vulnerability scanner | Official PyPA tool using Python Packaging Advisory Database. Actively maintained, catches known CVEs in dependencies. More current than safety-db's free tier. |
| secure.py | >=1.0.1 | Security headers middleware | Complete rewrite for Python 3.10+, zero external dependencies. Provides HSTS, CSP, X-Frame-Options, etc. Single middleware for FastAPI with <1ms overhead. |

### PaaS Hosting (Backend)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Railway | N/A | Backend hosting (FastAPI + SQLite) | Usage-based pricing ($2-5/month for pilot scale). Native persistent disk support for SQLite. Auto-deploys from GitHub. Built-in secrets management. Free SSL certificates. CNAME flattening support. Better DX than Render. |
| Cloudflare DNS | N/A | DNS provider with CNAME flattening | Required for apex domain CNAME records (example.com → Railway). Most DNS providers don't support root-level CNAMEs. Cloudflare's CNAME flattening is automatic and free. |

### Static Hosting (Frontend)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|---|
| Cloudflare Pages | N/A | Flutter web static hosting | Free unlimited bandwidth for static content. 200+ edge locations (lowest latency). Auto-deploys from GitHub. Free SSL. Custom domain support. Zero config for Flutter web builds. |

### Production ASGI Configuration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| gunicorn | >=21.2.0 | Process manager | Already in requirements.txt. Manages multiple Uvicorn workers for horizontal scaling. Industry standard for FastAPI production. |
| uvicorn[standard] | >=0.27.0 | ASGI server | Already in requirements.txt. Use with UvicornWorker class for async FastAPI. Worker count = CPU cores (not 2*CPU+1 for async). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | >=2.0.0 | Environment variable management | Already in use via BaseSettings. Validates production environment variables at startup (prevents runtime config errors). |
| python-dotenv | >=1.0.0 | Local .env file loading | Development only. Production uses Railway's native environment variables. Do NOT deploy .env files. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Railway CLI | Deploy from CLI, tail logs, manage secrets | `npm install -g @railway/cli` then `railway login` |
| Flutter build web | Compile production web bundle | `flutter build web --release --dart-define=API_URL=https://api.yourdomain.com` |

## Installation

```bash
# Backend: Security scanning tools (dev dependencies)
cd backend
source venv/bin/activate
pip install bandit>=1.8.6 pip-audit>=2.9.0
pip freeze > requirements-dev.txt  # Separate from production requirements.txt

# Backend: Security headers middleware (production)
pip install secure>=1.0.1
# Add to requirements.txt

# Frontend: No additional Flutter packages needed
# Use --dart-define for production API URL configuration

# Deployment tools
npm install -g @railway/cli  # Railway CLI for backend deployment
# Cloudflare Pages deploys directly from GitHub (no CLI needed)
```

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| PaaS (backend) | Railway | Render | Choose Render if you need predictable fixed pricing or built-in background workers. Render has native cron jobs and persistent volumes without manual service configuration. |
| PaaS (backend) | Railway | Fly.io | Choose Fly.io if you want multi-region deployments or need low-latency edge computing. Best PaaS for SQLite (no ephemeral filesystem issues), but more complex config. |
| Static hosting | Cloudflare Pages | Vercel | Choose Vercel if you need serverless functions alongside static hosting. Better for hybrid Next.js apps. Overkill for pure Flutter web. |
| Static hosting | Cloudflare Pages | Netlify | Choose Netlify if you need built-in form handling or identity management. More mature plugin ecosystem. Similar performance to Cloudflare. |
| Security scanner | pip-audit | safety | Choose safety (paid) if you need CVSS scoring and faster vulnerability updates. Free tier lags behind pip-audit's PyPA database. |
| Dependency check | pip-audit | OWASP Dependency-Check | Avoid OWASP dep-check for Python—experimental support only, requires Java runtime, designed for Java/.NET. Use pip-audit instead. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Heroku | Ephemeral filesystem = SQLite data loss every 24 hours. No free tier since 2022. | Railway (persistent disk for SQLite) |
| SQLite on network-attached storage | SQLite.org explicitly warns against NAS due to unpredictable read/write behavior and locking issues. | Use Railway's local persistent disk, OR migrate to PostgreSQL if multi-instance scaling needed |
| safety (free tier) | Vulnerability database lags behind pip-audit by weeks/months. Paid tier required for timely updates. | pip-audit (free, uses official PyPA database) |
| OWASP Dependency-Check for Python | Experimental Python support, requires Java runtime, designed for Java/.NET. False positives common. | pip-audit (Python-native, official PyPA tool) |
| Environment variables in Flutter web .env files | .env files cannot be read in production builds. Variables must be compile-time. | `flutter build web --dart-define=VAR=value` |
| Shared OAuth credentials across environments | Single redirect URI per OAuth app = production/dev conflicts. Security risk if dev URIs exposed in production config. | Create separate OAuth apps for dev and production |

## Stack Patterns by Deployment Scale

**For pilot deployment (< 10 users):**
- Use Railway single-instance with SQLite on persistent disk
- Single Uvicorn worker (Railway starter plans = 1 CPU)
- Cloudflare Pages free tier (unlimited bandwidth)
- Manual secrets management via Railway web UI
- Total cost: ~$5/month (Railway usage-based)

**For production scale (100+ users):**
- Migrate to Railway with PostgreSQL (multi-instance support)
- Gunicorn with N Uvicorn workers (N = CPU cores)
- Consider Cloudflare Pages Pro for advanced analytics
- Add secrets rotation with Doppler or Infisical integration
- Total cost: ~$20-50/month (Railway usage-based + database)

**For enterprise scale (1000+ users):**
- Move to Fly.io with multi-region PostgreSQL (global latency)
- Add Redis for session management
- Implement secrets rotation automation
- Add Cloudflare CDN in front of Railway/Fly.io
- Total cost: $100-300+/month

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| secure.py >=1.0.1 | Python 3.10+ | Complete rewrite requires modern Python features |
| gunicorn 21.2.0 | uvicorn[standard] 0.27.0 | Use `gunicorn -k uvicorn.workers.UvicornWorker` for FastAPI |
| FastAPI >=0.115.0 | secure.py >=1.0.1 | Add as Starlette middleware with `app.add_middleware()` |
| bandit >=1.8.6 | Python 3.8+ | Uses AST parsing, version-agnostic for supported Python versions |

## Production Configuration Requirements

### Backend Environment Variables (Railway)

**Required in production:**
```bash
# Security
SECRET_KEY=<generate with: openssl rand -hex 32>
FERNET_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Environment
ENVIRONMENT=production
BACKEND_URL=https://api.yourdomain.com  # For OAuth redirects
CORS_ORIGINS=https://yourdomain.com  # Frontend URL

# OAuth (create separate production apps)
GOOGLE_CLIENT_ID=<production Google OAuth app>
GOOGLE_CLIENT_SECRET=<production Google OAuth secret>
MICROSOFT_CLIENT_ID=<production Microsoft OAuth app>
MICROSOFT_CLIENT_SECRET=<production Microsoft OAuth secret>

# AI Services
ANTHROPIC_API_KEY=<production key>
GOOGLE_API_KEY=<optional, for Gemini>
DEEPSEEK_API_KEY=<optional, for DeepSeek>

# Database
DATABASE_URL=sqlite+aiosqlite:///./ba_assistant.db  # Railway persistent disk

# Logging
LOG_LEVEL=INFO  # or WARNING for production (reduce noise)
```

**Validation notes:**
- `config.py` already validates SECRET_KEY != dev default in production
- `config.py` already validates ANTHROPIC_API_KEY presence
- `config.py` already validates OAuth credentials presence
- Add validation for FERNET_KEY presence if document encryption used

### Frontend Environment Variables (Cloudflare Pages)

**Build command:**
```bash
flutter build web --release \
  --dart-define=API_URL=https://api.yourdomain.com \
  --dart-define=ENVIRONMENT=production
```

**Cloudflare Pages configuration:**
- Build command: (above)
- Build output directory: `build/web`
- Root directory: `frontend`
- Framework preset: None (static site)

**Note:** Flutter web cannot read .env files at runtime. All config must be compile-time via `--dart-define`. Access in Dart with `String.fromEnvironment('API_URL')`.

## DNS Configuration

### Backend (Railway)

1. **Add custom domain in Railway:** `api.yourdomain.com`
2. **Railway provides CNAME target:** `random-name.up.railway.app`
3. **In Cloudflare DNS:**
   - Type: CNAME
   - Name: `api` (or `@` for apex domain)
   - Target: `random-name.up.railway.app`
   - Proxy status: DNS only (grey cloud)
   - TTL: Auto

4. **Railway auto-issues SSL certificate** after DNS verification (5-10 minutes)

**Apex domain notes:**
- Most DNS providers don't support CNAME at apex (`yourdomain.com`)
- Cloudflare automatically flattens CNAMEs at apex (returns A record to clients)
- GoDaddy, Namecheap, Google Domains do NOT support CNAME flattening
- **Recommendation:** Use subdomain `api.yourdomain.com` OR switch to Cloudflare DNS for apex support

### Frontend (Cloudflare Pages)

1. **Deploy to Cloudflare Pages** (auto-generates `random-name.pages.dev`)
2. **Add custom domain:** `yourdomain.com` or `www.yourdomain.com`
3. **Cloudflare auto-configures DNS** if domain is on Cloudflare
4. **SSL certificate issued automatically** (Let's Encrypt)

**If domain is NOT on Cloudflare:**
- Move nameservers to Cloudflare (required for Cloudflare Pages custom domains)
- OR use CNAME at `www.yourdomain.com` pointing to `random-name.pages.dev`

## Security Headers Configuration

### Add to FastAPI (backend/main.py)

```python
from secure import Secure

# After app = FastAPI(...), before middleware setup
secure_headers = Secure.with_default_headers()

# Customize for BA Assistant requirements
secure_headers.hsts.max_age = 31536000  # 1 year
secure_headers.hsts.include_subdomains = True
secure_headers.hsts.preload = True

secure_headers.csp.script_src = ["'self'", "'unsafe-inline'"]  # Flutter web needs inline scripts
secure_headers.csp.style_src = ["'self'", "'unsafe-inline'"]   # Flutter web needs inline styles
secure_headers.csp.img_src = ["'self'", "data:", "https:"]     # Allow external images
secure_headers.csp.connect_src = ["'self'", "https://api.anthropic.com", "https://generativelanguage.googleapis.com"]  # AI APIs

secure_headers.frame_options.value = "DENY"  # Prevent clickjacking
secure_headers.content_type_options.enabled = True
secure_headers.xss_protection.enabled = False  # Deprecated, CSP handles this

# Add middleware
app.add_middleware(secure_headers.starlette_middleware)
```

**CSP Notes for Flutter Web:**
- Flutter web requires `'unsafe-inline'` for scripts and styles in debug mode
- Production builds can be stricter (hash-based CSP)
- Test CSP with browser console (look for CSP violation errors)

### CORS Configuration (already in main.py)

**Development:**
```python
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Production:**
```python
CORS_ORIGINS=https://yourdomain.com
```

**Security notes:**
- Never use `allow_origins=["*"]` in production
- `allow_credentials=True` requires specific origins (not wildcard)
- CORS is already configured in `main.py` via `settings.cors_origins_list`

## Security Audit Workflow

### Pre-Deployment Checklist

```bash
# 1. Scan Python code for security issues
cd backend
bandit -r app/ -ll  # Only show medium/high severity issues
# Address any findings before deployment

# 2. Scan dependencies for known vulnerabilities
pip-audit --desc  # Shows CVE descriptions
# Update vulnerable packages: pip install --upgrade <package>

# 3. Verify production environment variables
python -c "from app.config import settings; settings.validate_required()"
# Should raise ValueError if any required config missing

# 4. Run existing test suite
pytest  # 471 backend tests should pass

# 5. Build frontend with production config
cd ../frontend
flutter build web --release --dart-define=API_URL=https://api.yourdomain.com
# Verify build/web/ output exists

# 6. Test production build locally
python -m http.server 8080 --directory build/web
# Open browser to http://localhost:8080, verify app loads
```

### Post-Deployment Verification

```bash
# 1. Check SSL certificate
curl -I https://api.yourdomain.com
# Should return HTTP 200, verify SSL in browser (lock icon)

# 2. Verify security headers
curl -I https://api.yourdomain.com | grep -E "(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options)"
# Should see HSTS, X-Frame-Options: DENY, etc.

# 3. Test OAuth flow
# Navigate to https://yourdomain.com, click "Sign in with Google"
# Should redirect to Google, then back to app (check redirect URI)

# 4. Check Railway logs
railway logs --tail
# Verify no startup errors, check for log_level=INFO messages

# 5. Test frontend API connectivity
# In browser console: fetch('https://api.yourdomain.com/health')
# Should return {"status": "healthy", ...}
```

## Common Integration Points

### FastAPI + secure.py Middleware

Already using middleware pattern (see `app/middleware.py` for LoggingMiddleware). Add secure.py similarly:

```python
# backend/main.py (after existing middleware)
from secure import Secure

secure_headers = Secure.with_default_headers()
# ... configure CSP, HSTS as shown above ...
app.add_middleware(secure_headers.starlette_middleware)
```

**Middleware order matters:**
1. CORSMiddleware (first - handles preflight)
2. secure.py middleware (second - adds security headers)
3. LoggingMiddleware (third - logs all requests)

### Railway + GitHub Auto-Deploy

Railway auto-deploys on `git push` when connected to GitHub repo:

1. **Connect repo:** Railway dashboard → New Project → Deploy from GitHub
2. **Select repo:** `XtraSkill` → Select service (`backend`)
3. **Configure build:** Railway auto-detects Python (reads `requirements.txt`)
4. **Set start command:** `gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT`
5. **Environment variables:** Add all production env vars in Railway UI
6. **Add persistent disk:** Settings → Volumes → Create → Mount path `/app` (for ba_assistant.db)

**Note:** Railway sets `$PORT` env var automatically. Gunicorn must bind to `0.0.0.0:$PORT` not `127.0.0.1:8000`.

### Cloudflare Pages + GitHub Auto-Deploy

Cloudflare Pages auto-deploys on `git push` to frontend files:

1. **Connect repo:** Cloudflare dashboard → Pages → Create project → Connect to Git
2. **Select repo:** `XtraSkill`
3. **Build configuration:**
   - Framework preset: None
   - Build command: `cd frontend && flutter build web --release --dart-define=API_URL=https://api.yourdomain.com`
   - Build output directory: `frontend/build/web`
4. **Deploy:** Cloudflare builds and deploys automatically

**Note:** Cloudflare Pages requires Flutter SDK in build environment. Add `flutter` to build command or use Docker build.

### OAuth Production Configuration

**Create separate OAuth apps for production:**

**Google OAuth:**
1. Google Cloud Console → Create new project: "BA Assistant Production"
2. APIs & Services → Credentials → Create OAuth 2.0 Client ID
3. Authorized redirect URIs: `https://api.yourdomain.com/auth/google/callback`
4. Copy CLIENT_ID and CLIENT_SECRET to Railway environment variables

**Microsoft OAuth:**
1. Azure Portal → App registrations → New registration: "BA Assistant Production"
2. Authentication → Add platform → Web → Redirect URI: `https://api.yourdomain.com/auth/microsoft/callback`
3. Certificates & secrets → New client secret
4. Copy Application (client) ID and secret value to Railway environment variables

**Why separate apps:**
- Security: Dev URIs not exposed in production config
- Isolation: Production and dev tokens are separate (can revoke independently)
- Compliance: Some OAuth providers require production app review

## Estimated Costs (Pilot Scale)

| Service | Tier | Monthly Cost | Notes |
|---------|------|--------------|-------|
| Railway (backend) | Hobby | $5-10 | Usage-based: ~$0.01/hour for 512MB RAM, 1 CPU. Includes persistent disk (1GB). |
| Cloudflare Pages (frontend) | Free | $0 | Unlimited bandwidth for static sites. Free SSL. |
| Cloudflare DNS | Free | $0 | CNAME flattening included. |
| Domain registration | N/A | $10-15/year | One-time annual cost (Namecheap, Google Domains, etc.) |
| **Total** | | **~$5-10/month** | |

**Cost increases with usage:**
- Railway: Scales automatically with traffic (more CPU/RAM = higher cost)
- At 100+ concurrent users: ~$20-30/month
- At 1000+ users: ~$100+/month (consider migration to dedicated hosting)

## Sources

**Security Scanning:**
- [Bandit on PyPI](https://pypi.org/project/bandit/) — Latest version 1.8.6 (Jan 2026)
- [Help Net Security: Bandit tool overview](https://www.helpnetsecurity.com/2026/01/21/bandit-open-source-tool-find-security-issues-python-code/) — Tool capabilities and use cases
- [pip-audit on PyPI](https://pypi.org/project/pip-audit/) — Latest version 2.9.0
- [Six Feet Up: Safety vs pip-audit comparison](https://www.sixfeetup.com/blog/safety-pip-audit-python-security-tools) — Why pip-audit over safety free tier
- [secure.py on PyPI](https://pypi.org/project/secure/) — Latest version 1.0.1 with Python 3.10+ rewrite
- [Medium: FastAPI Security Headers](https://medium.com/@npavfan2facts/10-fastapi-security-headers-csp-hsts-without-latency-8228a32bb235) — Performance benchmarks for security middleware

**PaaS Hosting:**
- [Railway vs Render 2026 Comparison](https://thesoftwarescout.com/railway-vs-render-2026-best-platform-for-deploying-apps/) — Feature comparison and pricing analysis
- [Northflank: Railway vs Render](https://northflank.com/blog/railway-vs-render) — Developer experience and workflow differences
- [Railway FastAPI Guide](https://docs.railway.com/guides/fastapi) — Official deployment guide
- [Render: FastAPI deployment options](https://render.com/articles/fastapi-deployment-options) — Alternative deployment configurations

**Production Best Practices:**
- [FastAPI Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/) — Official Gunicorn + Uvicorn configuration
- [Render: FastAPI production best practices](https://render.com/articles/fastapi-production-deployment-best-practices) — Worker configuration and scaling
- [Medium: Mastering Gunicorn and Uvicorn](https://medium.com/@iklobato/mastering-gunicorn-and-uvicorn-the-right-way-to-deploy-fastapi-applications-aaa06849841e) — Worker count formulas for async apps

**Static Hosting:**
- [Vercel vs Netlify vs Cloudflare Pages 2025](https://www.ai-infra-link.com/vercel-vs-netlify-vs-cloudflare-pages-2025-comparison-for-developers/) — Performance and pricing comparison
- [DEV: Deploy Flutter web to Cloudflare Pages](https://dev.to/hrishiksh/deploy-flutter-web-app-to-cloudflare-pages-jcl) — Step-by-step deployment guide

**DNS & SSL:**
- [Railway Domains Documentation](https://docs.railway.com/networking/domains) — Custom domain setup and SSL
- [Cloudflare: CNAME Flattening](https://developers.cloudflare.com/dns/cname-flattening/) — Apex domain CNAME support

**Environment Configuration:**
- [Medium: Managing Environment Variables in Flutter Web](https://medium.com/@akshelar.18119/managing-environment-variables-in-flutter-web-074a01622687) — dart-define for production builds
- [Railway: Using Variables](https://docs.railway.com/guides/variables) — Environment variable management
- [Render: Environment Variables and Secrets](https://render.com/docs/configure-environment-variables) — Secrets management best practices
- [Security Boulevard: Are environment variables still safe for secrets in 2026?](https://securityboulevard.com/2025/12/are-environment-variables-still-safe-for-secrets-in-2026/) — Hybrid approach with secrets managers

**OAuth:**
- [Microsoft: Redirect URI best practices](https://learn.microsoft.com/en-us/entra/identity-platform/reply-url) — Separate apps per environment
- [Google OAuth Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server) — Production redirect URI configuration

**SQLite Production:**
- [Anže's Blog: SQLite in Production Gotchas](https://blog.pecar.me/sqlite-prod) — PaaS filesystem limitations
- [SQLite: Appropriate Uses](https://sqlite.org/whentouse.html) — Official guidance on network-attached storage
- [Render: Persistent Disks](https://render.com/docs/disks) — Volume attachment limitations

---
*Stack research for: Security Hardening & Production Deployment*
*Researched: 2026-02-09*
*Confidence: HIGH — All tools and platforms verified current as of Feb 2026*
