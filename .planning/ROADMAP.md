# Roadmap: BA Assistant v2.0 Security Audit & Deployment

## Milestones

- ✅ **v1.0 MVP** - Phases 1-5 (shipped 2026-01-28)
- ✅ **v1.5 Beta** - Phases 6-10 (shipped 2026-01-30)
- ✅ **v1.6 UX Quick Wins** - Phases 11-14 (shipped 2026-01-30)
- ✅ **v1.7 URL & Deep Links** - Phases 15-18 (shipped 2026-01-31)
- ✅ **v1.8 LLM Provider Switching** - Phases 19-22 (shipped 2026-01-31)
- ✅ **v1.9 UX Improvements** - Phases 23-27 (shipped 2026-02-02)
- ✅ **v1.9.1 Unit Test Coverage** - Phases 28-33 (shipped 2026-02-02)
- ✅ **v1.9.2 Resilience & AI Transparency** - Phases 34-36 (shipped 2026-02-04)
- ✅ **v1.9.3 Document & Navigation Polish** - Phases 37-39 (shipped 2026-02-04)
- ✅ **v1.9.4 Artifact Deduplication** - Phases 40-42 (shipped 2026-02-05)
- ✅ **v1.9.5 Pilot Logging Infrastructure** - Phases 43-48 (shipped 2026-02-08)
- 🚧 **v2.0 Security Audit & Deployment** - Phases 49-53 (in progress)

## Phases

### 🚧 v2.0 Security Audit & Deployment (In Progress)

**Milestone Goal:** Harden the application for production and deploy to live environment with custom domain for pilot group.

- [ ] **Phase 49: Backend Deployment Foundation** - Railway deployment with persistent disk and production environment
- [ ] **Phase 50: Security Hardening** - OWASP-aligned security audit with headers, scanning, and environment-aware OAuth
- [ ] **Phase 51: Custom Domain & SSL** - Domain registration, DNS configuration, SSL, and production OAuth apps
- [ ] **Phase 52: Frontend Deployment** - Flutter production build on Cloudflare Pages with uptime monitoring
- [ ] **Phase 53: Verification & Documentation** - Post-deployment verification, user flow testing, deployment guide, rollback plan

## Phase Details

### Phase 49: Backend Deployment Foundation
**Goal**: Backend is running in production on Railway with persistent data and proper environment configuration
**Depends on**: Nothing (first phase of v2.0)
**Requirements**: HOST-01, HOST-03, HOST-04
**Success Criteria** (what must be TRUE):
  1. Backend API responds to health check requests at the Railway-provided URL
  2. SQLite database persists across Railway deployments (data survives redeploy)
  3. All secrets (SECRET_KEY, API keys) are configured via environment variables with no hardcoded values
  4. Database backup mechanism is operational and has produced at least one successful backup
**Plans**: 2 plans

Plans:
- [ ] 49-01-PLAN.md — Code preparation (railway.json health check config, production-aware database settings)
- [ ] 49-02-PLAN.md — Railway deployment (project creation, env vars, persistent volume, backup, verification)

### Phase 50: Security Hardening
**Goal**: Application passes automated security scans and serves proper security headers in production
**Depends on**: Phase 49 (backend must be deployed to validate headers and scan deployed code)
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. Browser receives HSTS, CSP, X-Frame-Options, and X-Content-Type-Options headers on every response
  2. Bandit static analysis reports zero high-severity findings
  3. pip-audit dependency scan reports zero known CVEs in production dependencies
  4. OAuth redirect URIs are read from environment variables (BACKEND_URL/FRONTEND_URL), not hardcoded to localhost
**Plans**: TBD

Plans:
- [ ] 50-01: TBD
- [ ] 50-02: TBD

### Phase 51: Custom Domain & SSL
**Goal**: Application is accessible via custom domain with HTTPS and production OAuth apps configured
**Depends on**: Phase 50 (OAuth apps need environment-aware config; security must be hardened before public domain)
**Requirements**: DOM-01, DOM-02, DOM-03
**Success Criteria** (what must be TRUE):
  1. Custom domain resolves to the application (both backend API and frontend)
  2. SSL certificate is valid and HTTPS works end-to-end (no mixed content warnings)
  3. Google OAuth login completes successfully using production OAuth app with HTTPS redirect URI
  4. Microsoft OAuth login completes successfully using production OAuth app with HTTPS redirect URI
**Plans**: TBD

Plans:
- [ ] 51-01: TBD

### Phase 52: Frontend Deployment
**Goal**: Flutter web frontend is deployed to Cloudflare Pages and monitored for availability
**Depends on**: Phase 51 (frontend build requires final backend API URL; custom domain must be configured for CORS)
**Requirements**: HOST-02, DOM-04
**Success Criteria** (what must be TRUE):
  1. Flutter web app loads at the Cloudflare Pages URL (or custom domain) with production API URL compiled in
  2. Frontend communicates with backend API without CORS errors
  3. External uptime monitor is checking the application health endpoint and would alert on downtime
**Plans**: TBD

Plans:
- [ ] 52-01: TBD

### Phase 53: Verification & Documentation
**Goal**: Full stack is verified working in production with documented deployment process and rollback plan
**Depends on**: Phase 52 (full stack must be deployed before end-to-end verification)
**Requirements**: VER-01, VER-02, VER-03, VER-04
**Success Criteria** (what must be TRUE):
  1. Security verification passes: headers present, SSL valid, CORS correctly restricted, error pages don't leak stack traces
  2. Complete user flow works in production: OAuth login, create project, upload document, create thread, send message, generate artifact, export
  3. Deployment guide exists that a first-time deployer can follow from zero to live without external help
  4. Rollback plan is documented and has been tested (can revert to previous deployment)
**Plans**: TBD

Plans:
- [ ] 53-01: TBD
- [ ] 53-02: TBD

## Coverage

**Requirements mapped: 16/16**

| Requirement | Phase | Description |
|-------------|-------|-------------|
| SEC-01 | 50 | Security headers middleware |
| SEC-02 | 50 | Static code security scan (bandit) |
| SEC-03 | 50 | Dependency vulnerability scan (pip-audit) |
| SEC-04 | 50 | Environment-aware OAuth redirect URIs |
| HOST-01 | 49 | Backend deployed to Railway with persistent disk |
| HOST-02 | 52 | Frontend deployed to Cloudflare Pages |
| HOST-03 | 49 | Production environment configured |
| HOST-04 | 49 | Database backup strategy implemented |
| DOM-01 | 51 | Custom domain registered and DNS configured |
| DOM-02 | 51 | SSL/HTTPS verified on custom domain |
| DOM-03 | 51 | Production OAuth apps (Google + Microsoft) |
| DOM-04 | 52 | Uptime monitoring configured |
| VER-01 | 53 | End-to-end deployment guide |
| VER-02 | 53 | Post-deployment security verification |
| VER-03 | 53 | Full user flow tested in production |
| VER-04 | 53 | Rollback plan documented and tested |

No orphaned requirements. No duplicate mappings.

## Progress

**Execution Order:** 49 → 50 → 51 → 52 → 53

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 49. Backend Deployment Foundation | v2.0 | 0/2 | Planning complete | - |
| 50. Security Hardening | v2.0 | 0/TBD | Not started | - |
| 51. Custom Domain & SSL | v2.0 | 0/TBD | Not started | - |
| 52. Frontend Deployment | v2.0 | 0/TBD | Not started | - |
| 53. Verification & Documentation | v2.0 | 0/TBD | Not started | - |

---

*Roadmap created: 2026-02-09*
*Phase 49 planned: 2026-02-10 — 2 plans in 2 waves*
*Depth: quick (5 phases from 16 requirements)*
*Research: HIGH confidence, all domains investigated*
