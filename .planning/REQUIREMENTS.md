# Requirements: Business Analyst Assistant

**Defined:** 2026-02-09
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v2.0 Requirements

Requirements for Security Audit & Deployment milestone. Each maps to roadmap phases.

### Security Hardening

- [ ] **SEC-01**: Security headers middleware (HSTS, CSP, X-Frame-Options, X-Content-Type-Options) added via secure.py
- [ ] **SEC-02**: Static code security scan with bandit passes with no high-severity findings
- [ ] **SEC-03**: Dependency vulnerability scan with pip-audit passes with no known CVEs
- [ ] **SEC-04**: OAuth redirect URIs are environment-aware (BACKEND_URL/FRONTEND_URL env vars replace hardcoded localhost)

### Hosting & Infrastructure

- [ ] **HOST-01**: Backend deployed to Railway with persistent disk for SQLite database
- [ ] **HOST-02**: Frontend deployed to Cloudflare Pages with CDN distribution
- [ ] **HOST-03**: Production environment configured (SECRET_KEY, API keys, CORS origins, debug disabled, log level)
- [ ] **HOST-04**: Database backup strategy implemented (Litestream continuous replication or scheduled backup)

### Domain & OAuth

- [ ] **DOM-01**: Custom domain registered and DNS configured (Cloudflare CNAME flattening for apex domain)
- [ ] **DOM-02**: SSL/HTTPS verified working on custom domain for both backend and frontend
- [ ] **DOM-03**: Production OAuth apps created (Google + Microsoft) with HTTPS redirect URIs
- [ ] **DOM-04**: Uptime monitoring configured (external health check with alerting)

### Verification & Documentation

- [ ] **VER-01**: End-to-end deployment guide documented (zero to live for first-time deployer)
- [ ] **VER-02**: Post-deployment security verification passes (headers, SSL, CORS, error pages)
- [ ] **VER-03**: Full user flow tested in production (auth -> project -> document -> thread -> artifact)
- [ ] **VER-04**: Rollback plan documented and tested

## Future Requirements

Deferred to post-deployment. Tracked but not in current roadmap.

### Post-Launch Hardening

- **FUTURE-01**: API rate limiting (FastAPI-limiter) to prevent abuse
- **FUTURE-02**: CI/CD pipeline with GitHub Actions (automated testing + deployment)
- **FUTURE-03**: Application Performance Monitoring (Sentry or New Relic)
- **FUTURE-04**: Automated backup testing (verify backups are restorable)
- **FUTURE-05**: Real User Monitoring for frontend performance
- **FUTURE-06**: Database migration to PostgreSQL (if SQLite becomes bottleneck)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Kubernetes | Massive overkill for <10 pilot users; PaaS abstracts infrastructure |
| Custom VPS/server | Requires server administration skills; PaaS is operationally simpler |
| Multi-region deployment | Not needed for single-country pilot; adds complexity |
| Advanced secrets management (Vault) | Overkill for pilot; PaaS env vars sufficient |
| Multi-cloud strategy | Increases complexity; single PaaS platform initially |
| Manual penetration testing | $5k-$50k+; premature for pilot; use automated tools instead |
| Staging environment | Solo developer; test locally, deploy to production |
| Feature flags | Not needed for pilot scale |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 50 | Pending |
| SEC-02 | Phase 50 | Pending |
| SEC-03 | Phase 50 | Pending |
| SEC-04 | Phase 50 | Pending |
| HOST-01 | Phase 49 | Pending |
| HOST-02 | Phase 52 | Pending |
| HOST-03 | Phase 49 | Pending |
| HOST-04 | Phase 49 | Pending |
| DOM-01 | Phase 51 | Pending |
| DOM-02 | Phase 51 | Pending |
| DOM-03 | Phase 51 | Pending |
| DOM-04 | Phase 52 | Pending |
| VER-01 | Phase 53 | Pending |
| VER-02 | Phase 53 | Pending |
| VER-03 | Phase 53 | Pending |
| VER-04 | Phase 53 | Pending |

**Coverage:**
- v2.0 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-02-09*
*Last updated: 2026-02-09 — traceability table populated (all 16 requirements mapped to phases 49-53)*
