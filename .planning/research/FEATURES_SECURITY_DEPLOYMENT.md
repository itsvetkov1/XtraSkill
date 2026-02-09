# Feature Research: Security Hardening and Production Deployment

**Domain:** Web application deployment and security for FastAPI + Flutter web stack
**Researched:** 2026-02-09
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist for a production web application. Missing these = app feels incomplete or unprofessional.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| HTTPS/SSL Certificate | Standard security expectation for any web app | LOW | Let's Encrypt provides free automated certificates; most PaaS platforms handle this automatically |
| Custom Domain | Users expect branded URL (e.g., ba-assistant.com) not platform subdomain | LOW | DNS A/CNAME record configuration; PaaS platforms provide guides |
| Environment Variables | Secrets management (API keys, OAuth credentials) without hardcoding | LOW | Already partially implemented in codebase; needs production configuration |
| Health Check Endpoint | Load balancers and monitoring systems require this | LOW | Basic /health endpoint exists (main.py:100-111); may need enhancement for dependency checks |
| OAuth Production Redirect URIs | Production OAuth apps require registered redirect URIs | LOW | Requires creating separate OAuth app registrations for production domain |
| Basic Error Pages | User-friendly error messages (not stack traces) | LOW | FastAPI debug mode must be disabled in production (main.py:60) |
| Uptime Monitoring | Detection when service goes down | MEDIUM | External service integration (Better Stack, UptimeRobot, or PaaS built-in) |
| Structured Logging | Production debugging requires searchable logs | LOW | Already implemented via LoggingService; needs configuration for log aggregation |
| Database Backups | Data loss prevention | MEDIUM | SQLite requires special handling (VACUUM INTO, Litestream, or migration to PostgreSQL) |
| CORS Production Config | Restrict API access to production frontend domain | LOW | Already implemented (main.py:64-70); needs production CORS_ORIGINS env var |

### Differentiators (Competitive Advantage)

Features that set the deployment apart. Not required, but valuable for reliability and developer experience.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Zero-Downtime Deployment | Updates without service interruption | MEDIUM | PaaS platforms (Railway, Render) provide this automatically via rolling deploys |
| Multi-Region Deployment | Reduced latency for global users | HIGH | Fly.io specializes in this; Railway/Render have limited support; adds complexity |
| Automated SSL Renewal | No manual certificate management | LOW | Built into modern hosting platforms (Let's Encrypt integration) |
| API Rate Limiting | Protection against abuse and DDoS | MEDIUM | Prevents resource exhaustion; recommended for production APIs |
| Secrets Rotation | Automated credential updates | HIGH | Advanced security practice; defer unless compliance required |
| Automated Backup Testing | Verify backups are restorable | HIGH | Best practice but complex to implement; defer to post-launch |
| Real User Monitoring (RUM) | Frontend performance insights | MEDIUM | Shows actual user experience; tools like Sentry, New Relic, or Datadog |
| Application Performance Monitoring (APM) | Backend performance tracing | MEDIUM | Identifies slow database queries, API bottlenecks; useful for optimization |
| CI/CD Pipeline | Automated testing and deployment | MEDIUM | Git push triggers tests and deployment; most PaaS platforms support via GitHub Actions integration |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems for first-time deployers.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Kubernetes | "Industry standard for production" | Massive complexity overkill for small pilot (< 10 users); steep learning curve | Use PaaS (Railway, Render, Fly.io) that abstracts infrastructure |
| Custom Server Setup (VPS) | "More control and cheaper" | Requires server administration skills (security patches, SSL, monitoring); time sink | Use managed PaaS; only consider VPS after product validation |
| Self-Hosted Database | "Avoid vendor lock-in" | Database administration is specialized skill; backup/recovery complexity | Use managed database (PaaS-provided PostgreSQL or stick with SQLite + Litestream) |
| Complex Secrets Management (Vault) | "Enterprise-grade security" | HashiCorp Vault requires operational expertise; overkill for pilot | Use PaaS environment variables initially; upgrade if compliance demands |
| Multi-Cloud Strategy | "Avoid vendor lock-in" | Significantly increases complexity and cost; different APIs/tooling per cloud | Choose one PaaS platform initially; data portability via standard formats (PostgreSQL dump, etc.) |
| Manual Security Audits | "Ensure production safety" | Professional security audits are expensive ($5k-$50k+); premature for pilot | Use automated tools (OWASP ZAP, npm audit, pip-audit); manual audit after product validation |

## Feature Dependencies

```
[HTTPS/SSL Certificate]
    └──requires──> [Custom Domain]
    └──requires──> [DNS Configuration]

[OAuth Production]
    └──requires──> [Custom Domain]
    └──requires──> [HTTPS/SSL Certificate]

[Database Backups]
    └──requires──> [Storage Location] (S3, PaaS storage, or remote server)

[Rate Limiting]
    └──enhances──> [CORS Production Config]
    └──requires──> [Redis or In-Memory Store] (for distributed rate limiting)

[CI/CD Pipeline]
    └──requires──> [Automated Tests]
    └──enhances──> [Zero-Downtime Deployment]

[APM/Monitoring]
    └──requires──> [Structured Logging]

[Multi-Region Deployment] ──conflicts──> [SQLite Database]
```

### Dependency Notes

- **HTTPS/SSL Certificate requires Custom Domain:** SSL certificates are issued for specific domains; must configure DNS first
- **OAuth Production requires HTTPS:** OAuth providers (Google, Microsoft) require HTTPS redirect URIs for production apps
- **Database Backups require Storage Location:** SQLite file must be copied to remote location (S3, remote server, or PaaS storage)
- **Rate Limiting enhances CORS:** Both protect API from abuse; rate limiting adds per-user/IP limits beyond domain restrictions
- **CI/CD requires Automated Tests:** Deployment pipeline needs tests to verify changes before deploying
- **Multi-Region conflicts with SQLite:** SQLite is file-based and doesn't support distributed writes; requires PostgreSQL for multi-region

## MVP Definition: Deployment Readiness

### Launch With (Deployment v1)

Minimum viable deployment — what's needed to get from localhost to accessible production URL for pilot users.

- [x] **Custom Domain Registration** — Users need a real URL (e.g., ba-assistant.com), not localhost
- [x] **PaaS Platform Selection** — Railway, Render, or Fly.io for managed hosting (avoid manual server setup)
- [x] **HTTPS/SSL Certificate** — Required for OAuth and user trust (Let's Encrypt via PaaS)
- [x] **Production Environment Variables** — SECRET_KEY, API keys, OAuth credentials configured securely
- [x] **OAuth Production App Registration** — Separate Google/Microsoft OAuth apps with production redirect URIs
- [x] **CORS Production Configuration** — Restrict API access to production frontend domain only
- [x] **Database Backup Strategy** — Basic SQLite backup script or Litestream for continuous replication
- [x] **Health Check Endpoint** — PaaS platforms use this to verify service is running (already exists)
- [x] **Uptime Monitoring** — External ping to detect downtime (free tier: Better Stack, UptimeRobot)
- [x] **Error Logging** — Capture production errors for debugging (existing LoggingService + optional Sentry)

### Add After Initial Launch (v1.x)

Features to add once core deployment is stable and pilot users are onboarded.

- [ ] **API Rate Limiting** — Add once abuse patterns emerge or user count grows
- [ ] **CI/CD Pipeline** — Automate deployment once manual process is validated
- [ ] **Application Performance Monitoring** — Add when performance issues are reported
- [ ] **Automated Backup Testing** — Verify backups are restorable once backup strategy is proven
- [ ] **Real User Monitoring** — Track frontend performance after initial usage patterns are observed
- [ ] **Database Migration to PostgreSQL** — Consider if SQLite becomes a bottleneck (unlikely for < 10 users)

### Future Consideration (v2+)

Features to defer until product-market fit is established and user base grows.

- [ ] **Multi-Region Deployment** — Only needed if latency issues emerge for global users
- [ ] **Advanced Secrets Management (Vault)** — Only needed if compliance (HIPAA, SOC 2) is required
- [ ] **Custom Monitoring Dashboard** — Use PaaS built-in metrics initially; custom dashboard is premature optimization
- [ ] **Load Balancing** — Not needed until traffic exceeds single-server capacity (100+ concurrent users)
- [ ] **Kubernetes Migration** — Only consider if PaaS becomes limiting (very rare for web apps under 1000 concurrent users)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Custom Domain + HTTPS | HIGH | LOW | P1 |
| Production OAuth Setup | HIGH | LOW | P1 |
| Environment Variables Config | HIGH | LOW | P1 |
| PaaS Platform Deployment | HIGH | MEDIUM | P1 |
| Database Backups | HIGH | MEDIUM | P1 |
| Uptime Monitoring | HIGH | LOW | P1 |
| CORS Production Config | MEDIUM | LOW | P1 |
| Health Check Enhancement | MEDIUM | LOW | P1 |
| API Rate Limiting | MEDIUM | MEDIUM | P2 |
| CI/CD Pipeline | MEDIUM | MEDIUM | P2 |
| APM/Monitoring | MEDIUM | MEDIUM | P2 |
| Real User Monitoring | LOW | MEDIUM | P3 |
| Multi-Region Deployment | LOW | HIGH | P3 |
| Advanced Secrets Management | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for production launch (blocking)
- P2: Should have, add after launch stabilizes (1-2 weeks post-launch)
- P3: Nice to have, defer until proven need emerges

## Deployment Feature Categories

### Category 1: Security Hardening

**Essential for Production:**
- SECRET_KEY rotation (currently "dev-secret-key-change-in-production" in config.py:28)
- Debug mode disabled (main.py:60 conditionally disables /docs)
- CORS origins restricted to production domain
- Environment variable validation (config.py:83-116 already implemented)
- OAuth credentials separated from development

**Recommended Security Enhancements:**
- API rate limiting (prevents brute force, DDoS)
- Request size limits (prevents memory exhaustion)
- Input validation (already implemented via Pydantic models)
- SQL injection protection (using SQLAlchemy ORM provides protection)
- XSS protection (Flutter web handles this on frontend)

**Advanced (Defer):**
- WAF (Web Application Firewall)
- Secrets rotation automation
- Security audit tools integration (OWASP ZAP)
- Penetration testing

### Category 2: Environment Configuration

**Essential for Production:**
- Production .env file creation
- SECRET_KEY generation (openssl rand -hex 32)
- API key configuration (ANTHROPIC_API_KEY, etc.)
- OAuth client credentials (production apps)
- BACKEND_URL environment variable (for OAuth redirects)
- CORS_ORIGINS environment variable (production frontend domain)
- Database URL configuration (stick with SQLite or migrate to PostgreSQL)

**Recommended Configuration:**
- LOG_LEVEL=INFO or WARNING (not DEBUG)
- ENVIRONMENT=production (triggers validation in config.py:89)
- Log aggregation service integration (optional)

**Advanced (Defer):**
- Feature flags system
- A/B testing configuration
- Multi-environment management (staging, production)

### Category 3: Hosting Setup

**PaaS Platform Selection (Choose One):**

| Platform | Best For | Pros | Cons |
|----------|----------|------|------|
| Railway | Simplicity, predictable pricing | Easy setup, $5/month base, usage-based CPU/RAM | Limited free tier, no managed Redis |
| Render | Heroku-like experience | Free tier available, managed PostgreSQL, cron jobs | Cold starts on free tier, slower than Railway |
| Fly.io | Edge computing, global latency | Strong multi-region support, generous free tier | Steeper learning curve, no managed database |

**Essential Hosting Tasks:**
- Create PaaS account
- Connect GitHub repository
- Configure build settings (backend: Python/Uvicorn; frontend: Flutter web build)
- Set environment variables in PaaS dashboard
- Configure custom domain DNS
- Enable automatic SSL certificate

**Recommended Hosting Features:**
- Zero-downtime deployment (most PaaS platforms provide)
- Automatic scaling (if PaaS supports; may not be needed for pilot)
- Log streaming (view logs in PaaS dashboard)

### Category 4: Domain & DNS

**Essential Domain Tasks:**
- Register custom domain (Namecheap, Google Domains, Cloudflare)
- Configure DNS A record for backend (api.example.com → PaaS IP)
- Configure DNS A/CNAME record for frontend (example.com → PaaS host)
- Wait for DNS propagation (can take 24-48 hours)

**DNS Record Types for First-Time Deployers:**
- **A Record:** Maps domain to IPv4 address (e.g., api.example.com → 192.0.2.1)
- **CNAME Record:** Maps subdomain to another domain (e.g., www.example.com → example.com)
- **Apex/Root Domain:** Must use A record, not CNAME (DNS standard)

**SSL/TLS Configuration:**
- PaaS platforms automatically provision Let's Encrypt certificates
- No manual certificate management required
- Certificates auto-renew every 90 days
- Verify HTTPS works before configuring OAuth redirect URIs

### Category 5: OAuth Production

**OAuth App Registration Tasks:**

**Google OAuth:**
1. Create new OAuth 2.0 Client ID in Google Cloud Console (separate from development)
2. Add production redirect URI: `https://api.example.com/auth/google/callback`
3. Copy Client ID and Client Secret to production environment variables
4. Update Authorized JavaScript origins: `https://example.com`

**Microsoft OAuth:**
1. Create new App Registration in Azure Portal (separate from development)
2. Add production redirect URI: `https://api.example.com/auth/microsoft/callback`
3. Copy Application (client) ID and Client Secret to production environment variables
4. Update SPA redirect URIs: `https://example.com/auth/callback`

**Critical OAuth Requirements:**
- Production redirect URIs must use HTTPS (not HTTP)
- Frontend redirect URI must match exactly (trailing slash matters)
- OAuth providers may take 5-10 minutes to propagate changes
- Test OAuth flow thoroughly before launching

### Category 6: Monitoring & Observability

**Essential Monitoring:**
- Health check endpoint (already exists: main.py:100-111)
- Uptime monitoring service (Better Stack, UptimeRobot, or PaaS built-in)
- Error logging (existing LoggingService; consider Sentry for aggregation)

**Recommended Observability:**
- Log aggregation (Papertrail, Logtail, or PaaS built-in)
- Basic metrics (request count, response time, error rate)
- Alerting (email/Slack when service is down)

**Advanced (Defer):**
- Application Performance Monitoring (APM) — New Relic, Datadog
- Distributed tracing (Jaeger, OpenTelemetry)
- Custom dashboards (Grafana)
- Real User Monitoring (RUM)

## Deployment Checklist for First-Time Deployers

### Pre-Deployment (Planning Phase)

- [ ] Choose PaaS platform (Railway, Render, or Fly.io)
- [ ] Register custom domain
- [ ] Create production OAuth apps (Google, Microsoft)
- [ ] Generate production SECRET_KEY (`openssl rand -hex 32`)
- [ ] Document production environment variables

### Deployment Phase

- [ ] Configure DNS A/CNAME records
- [ ] Deploy backend to PaaS platform
- [ ] Configure backend environment variables
- [ ] Verify /health endpoint responds
- [ ] Deploy frontend (Flutter web build to static hosting)
- [ ] Configure frontend environment variables (API_URL)
- [ ] Verify HTTPS works on both domains
- [ ] Update OAuth redirect URIs to production domains
- [ ] Test OAuth login flow end-to-end

### Post-Deployment

- [ ] Set up uptime monitoring
- [ ] Configure database backup strategy
- [ ] Test error logging (trigger error, verify logged)
- [ ] Document deployment process for future updates
- [ ] Share production URL with pilot users

### First-Time Deployer Gotchas

**DNS Propagation:**
- DNS changes can take 24-48 hours to propagate globally
- Use `dig example.com` or online DNS checker to verify propagation
- Don't panic if domain doesn't work immediately

**OAuth Redirect URIs:**
- Trailing slashes matter: `/callback` ≠ `/callback/`
- HTTPS is required for production (OAuth providers reject HTTP)
- Changes to OAuth apps may take 5-10 minutes to propagate

**Environment Variables:**
- PaaS platforms have different interfaces for setting env vars
- Copy-paste carefully (no extra spaces or quotes)
- Restart service after changing env vars (may not auto-restart)

**CORS Configuration:**
- Production CORS_ORIGINS must match exact frontend domain
- `https://example.com` ≠ `https://www.example.com`
- Add both if using www and non-www domains

**SQLite in Production:**
- SQLite file is ephemeral on some PaaS platforms (container restarts lose data)
- Use persistent volumes or migrate to PostgreSQL
- Backup strategy is critical (Litestream or scheduled VACUUM INTO)

## Competitor Feature Analysis

| Feature | Heroku | Railway | Render | Our Approach |
|---------|--------|---------|--------|--------------|
| Automatic SSL | Yes (ACM) | Yes (Let's Encrypt) | Yes (Let's Encrypt) | Use PaaS-provided SSL |
| Database Backups | Automated (PostgreSQL) | Manual or self-managed | Automated (PostgreSQL) | Start with SQLite + Litestream; migrate to managed PostgreSQL if needed |
| Environment Variables | Dashboard UI | Dashboard UI | Dashboard UI | Use PaaS dashboard; document in deployment guide |
| Uptime Monitoring | Add-on (New Relic) | Built-in metrics | Built-in metrics | Use free external service (Better Stack) + PaaS built-in |
| CI/CD | GitHub integration | GitHub integration | GitHub integration | Manual deployment initially; add GitHub Actions after validation |
| Custom Domains | Yes | Yes | Yes | Use PaaS domain configuration |
| Secrets Management | Config vars (plaintext) | Environment variables | Environment variables | Use PaaS env vars initially; upgrade to secrets manager if compliance required |

## Sources

**FastAPI Production Best Practices:**
- [Preparing FastAPI for Production: A Comprehensive Guide](https://medium.com/@ramanbazhanau/preparing-fastapi-for-production-a-comprehensive-guide-d167e693aa2b)
- [FastAPI Best Practices for Production: Complete 2026 Guide](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026)
- [The Ultimate Production Deployment Checklist for FastAPI](https://medium.com/@rameshkannanyt0078/fastapi-production-deployment-checklist-e4daa8752016)
- [FastAPI Production Deployment Best Practices (Render)](https://render.com/articles/fastapi-production-deployment-best-practices)

**Flutter Web Deployment:**
- [Build and release a web app (Official Flutter Docs)](https://docs.flutter.dev/deployment/web)
- [How to Deploy Your Flutter Web App on Netlify](https://medium.com/fludev/how-to-deploy-your-flutter-web-app-on-netlify-fast-free-hosting-fff3a553e521)
- [From Localhost to Live: Deploy Your Flutter Portfolio with Firebase](https://medium.com/@bahtinursinikk/from-localhost-to-live-deploy-your-flutter-portfolio-for-free-with-firebase-b5e89d2da252)

**OAuth Production Setup:**
- [Using OAuth 2.0 for Web Server Applications (Google)](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Redirect URI best practices (Microsoft)](https://learn.microsoft.com/en-us/entra/identity-platform/reply-url)

**PaaS Platform Comparisons:**
- [Railway vs Render (2026): Which cloud platform fits your workflow better](https://northflank.com/blog/railway-vs-render)
- [Comparing top PaaS and deployment providers (Railway Blog)](https://blog.railway.com/p/paas-comparison-guide)
- [Render vs. Heroku vs. Vercel vs. Railway vs. Fly.io vs. AWS](https://ritza.co/articles/gen-articles/render-vs-heroku-vs-vercel-vs-railway-vs-fly-io-vs-aws/)

**Domain & DNS Configuration:**
- [DNS Records Explained 2026: A, CNAME, MX & Setup Guide](https://skynethosting.net/blog/master-dns-configuration-in-2026/)
- [What is a DNS CNAME record? (Cloudflare)](https://www.cloudflare.com/learning/dns/dns-records/dns-cname-record/)

**SSL/TLS Certificates:**
- [Getting Started with Let's Encrypt](https://letsencrypt.org/getting-started/)
- [How It Works - Let's Encrypt](https://letsencrypt.org/how-it-works/)

**Secrets Management:**
- [Secrets Management - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Are environment variables still safe for secrets in 2026?](https://securityboulevard.com/2025/12/are-environment-variables-still-safe-for-secrets-in-2026/)
- [Beyond .env Files: The New Best Practices for Managing Secrets](https://medium.com/@instatunnel/beyond-env-files-the-new-best-practices-for-managing-secrets-in-development-b4b05e0a3055)

**Security Hardening:**
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Complete Web App Security Checklist Using the OWASP Top 10](https://hicronsoftware.com/blog/web-app-security-checklist-owasp-top-10/)
- [A Practical Guide to FastAPI Security](https://davidmuraya.com/blog/fastapi-security-guide/)
- [Securing FastAPI Applications (GitHub)](https://github.com/VolkanSah/Securing-FastAPI-Applications)

**CORS Configuration:**
- [CORS (Cross-Origin Resource Sharing) - FastAPI Official](https://fastapi.tiangolo.com/tutorial/cors/)
- [Secure Configuration of CORS in FastAPI](https://codesignal.com/learn/courses/web-resource-integrity-and-secure-configuration-in-fastapi/lessons/secure-configuration-of-cors-in-fastapi)

**Rate Limiting:**
- [API Rate Limiting Strategies: Preventing DDoS](https://www.apisec.ai/blog/api-rate-limiting-strategies-preventing)
- [How to Configure Rate Limiting for Security](https://oneuptime.com/blog/post/2026-01-24-configure-rate-limiting-security/view)
- [What is rate limiting? (Cloudflare)](https://www.cloudflare.com/learning/bots/what-is-rate-limiting/)

**Database Backups:**
- [Backup strategies for SQLite in production](https://oldmoe.blog/2024/04/30/backup-strategies-for-sqlite-in-production/)
- [SQLite Backup API (Official)](https://www.sqlite.org/backup.html)
- [Backing Up and Restoring SQLite Databases: A Practical Guide](https://www.sqliteforum.com/p/backing-up-and-restoring-sqlite-databases)

**Monitoring & Observability:**
- [Health Endpoint Monitoring pattern (Microsoft Azure)](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring)
- [Get Started with Server Health Checks (Better Stack)](https://betterstack.com/community/guides/monitoring/health-checks/)
- [DevOps Monitoring and Observability 2026](https://vettedoutsource.com/blog/devops-monitoring-observability/)
- [Top 8 Observability Tools for 2026 (TechTarget)](https://www.techtarget.com/searchitoperations/tip/Top-observability-tools)

---
*Feature research for: Security Hardening and Production Deployment (FastAPI + Flutter Web)*
*Researched: 2026-02-09*
*Confidence: HIGH*
