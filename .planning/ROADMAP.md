# Roadmap: Business Analyst Assistant

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
- 📋 **v2.0 Security Audit & Deployment** - Phases 49-53 (planned)
- 🚧 **v2.1 Rich Document Support** - Phases 54-56 (in progress)

## Phases

### 📋 v2.0 Security Audit & Deployment (Planned)

**Milestone Goal:** Harden the application for production and deploy to live environment with custom domain for pilot group.

- [ ] **Phase 49: Backend Deployment Foundation** - Railway deployment with persistent disk and production environment
- [ ] **Phase 50: Security Hardening** - OWASP-aligned security audit with headers, scanning, and environment-aware OAuth
- [ ] **Phase 51: Custom Domain & SSL** - Domain registration, DNS configuration, SSL, and production OAuth apps
- [ ] **Phase 52: Frontend Deployment** - Flutter production build on Cloudflare Pages with uptime monitoring
- [ ] **Phase 53: Verification & Documentation** - Post-deployment verification, user flow testing, deployment guide, rollback plan

#### Phase 49: Backend Deployment Foundation
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

#### Phase 50: Security Hardening
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

#### Phase 51: Custom Domain & SSL
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

#### Phase 52: Frontend Deployment
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

#### Phase 53: Verification & Documentation
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

### 🚧 v2.1 Rich Document Support (In Progress)

**Milestone Goal:** Replace text-only document uploads with full document parsing supporting Excel, CSV, PDF, and Word files — with AI context integration, visual previews, and export capabilities

- [ ] **Phase 54: Backend Foundation** - Document parsing infrastructure with security validation
- [ ] **Phase 55: Frontend Display & AI Context** - Format-aware rendering and AI integration
- [ ] **Phase 56: Export Features** - Excel and CSV export capabilities

#### Phase 54: Backend Foundation - Document Parsing & Security

**Goal**: Parser infrastructure with text extraction and security validation for Excel, CSV, PDF, and Word formats

**Depends on**: Nothing (first phase of milestone)

**Requirements**: PARSE-01, PARSE-02, PARSE-03, PARSE-04, PARSE-05, PARSE-06, SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, STOR-01, STOR-02, STOR-03

**Success Criteria** (what must be TRUE):
  1. User can upload Excel (.xlsx) files and see extracted text content in Document Viewer
  2. User can upload CSV files with international characters (UTF-8, Windows-1252) and see extracted text
  3. User can upload PDF files and see extracted text content with page information
  4. User can upload Word (.docx) files and see extracted text content with paragraph structure
  5. Malicious files (XXE attacks, zip bombs, oversized files) are rejected with clear error messages
  6. Uploaded rich documents appear in existing full-text search results
  7. Excel data types are preserved (leading zeros in "00123", dates display as formatted, large numbers don't convert to scientific notation)

**Plans**: 3 plans

Plans:
- [ ] 54-01-PLAN.md — Parser infrastructure + file security validator (dependencies, base class, factory, 5 parsers, file_validator)
- [ ] 54-02-PLAN.md — Schema migration + encryption (Document model columns, FTS5 unicode61 upgrade, binary encryption)
- [ ] 54-03-PLAN.md — Route integration (upload/list/get/download endpoints, security validation, dual-column storage, FTS5 indexing)

#### Phase 55: Frontend Display & AI Context Integration

**Goal**: Format-aware rendering with visual table previews, token budget management, and AI document search integration

**Depends on**: Phase 54

**Requirements**: DISP-01, DISP-02, DISP-03, DISP-04, DISP-05, AI-01, AI-02, AI-03

**Success Criteria** (what must be TRUE):
  1. User sees visual table preview with first 10 rows when uploading Excel/CSV files
  2. User can choose which Excel sheets to parse via sheet selector in upload dialog
  3. Document Viewer displays format-appropriate rendering (table grid for Excel/CSV, text with page numbers for PDF, structured paragraphs for Word)
  4. Document Viewer shows metadata (row count for Excel/CSV, page count for PDF, sheet names for Excel)
  5. User can sort and filter table data in Document Viewer without browser freeze (handles 1000+ row Excel files)
  6. AI can search and reference content from all 4 rich document formats in conversations
  7. AI source attribution chips show format-specific information (sheet name for Excel references)
  8. Large documents don't cause "context limit exceeded" errors (token budget allocation working)

**Plans**: TBD

Plans:
- [ ] 55-01: TBD
- [ ] 55-02: TBD
- [ ] 55-03: TBD

#### Phase 56: Export Features

**Goal**: Excel and CSV export for parsed document data and generated artifacts

**Depends on**: Phase 55

**Requirements**: EXP-01, EXP-02

**Success Criteria** (what must be TRUE):
  1. User can export parsed Excel/CSV data back to .xlsx format via Document Viewer
  2. User can export parsed Excel/CSV data to .csv format via Document Viewer
  3. Exported files preserve column structure and data types from original upload

**Plans**: TBD

Plans:
- [ ] 56-01: TBD

## Coverage

### v2.0 Security Audit & Deployment

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

### v2.1 Rich Document Support

**Requirements mapped: 24/24**

| Requirement | Phase | Description |
|-------------|-------|-------------|
| PARSE-01 | 54 | Excel (.xlsx) parsing with text extraction |
| PARSE-02 | 54 | CSV parsing with text extraction |
| PARSE-03 | 54 | PDF parsing with text extraction |
| PARSE-04 | 54 | Word (.docx) parsing with text extraction |
| PARSE-05 | 54 | Excel data type preservation |
| PARSE-06 | 54 | CSV encoding auto-detection |
| SEC-01 | 54 | File type validation via magic number |
| SEC-02 | 54 | 10MB file size limit |
| SEC-03 | 54 | XXE attack protection (defusedxml) |
| SEC-04 | 54 | Zip bomb protection |
| SEC-05 | 54 | Malformed file rejection |
| STOR-01 | 54 | Dual-column storage (binary + text) |
| STOR-02 | 54 | FTS5 indexing of extracted text |
| STOR-03 | 54 | Document metadata storage |
| DISP-01 | 55 | Visual table preview for upload |
| DISP-02 | 55 | Sheet selector for Excel |
| DISP-03 | 55 | Format-aware Document Viewer rendering |
| DISP-04 | 55 | Document metadata display |
| DISP-05 | 55 | Table renderer with virtualization |
| AI-01 | 55 | AI document_search for rich formats |
| AI-02 | 55 | Token budget management |
| AI-03 | 55 | Source attribution with format info |
| EXP-01 | 56 | Export to Excel format |
| EXP-02 | 56 | Export to CSV format |

No orphaned requirements. No duplicate mappings.

## Progress

**Execution Order:** 49 → 50 → 51 → 52 → 53 → 54 → 55 → 56

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 49. Backend Deployment Foundation | v2.0 | 0/2 | Planning complete | - |
| 50. Security Hardening | v2.0 | 0/TBD | Not started | - |
| 51. Custom Domain & SSL | v2.0 | 0/TBD | Not started | - |
| 52. Frontend Deployment | v2.0 | 0/TBD | Not started | - |
| 53. Verification & Documentation | v2.0 | 0/TBD | Not started | - |
| 54. Backend Foundation | v2.1 | 0/3 | Planning complete | - |
| 55. Frontend Display & AI Context | v2.1 | 0/TBD | Not started | - |
| 56. Export Features | v2.1 | 0/TBD | Not started | - |

---

*Roadmap created: 2026-02-09*
*Phase 49 planned: 2026-02-10*
*v2.1 roadmap added: 2026-02-12 — 3 phases from 24 requirements (depth: quick)*
