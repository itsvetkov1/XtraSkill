# BUG-021: PDF Export Returns 500 Error

**Priority:** High
**Status:** Open
**Component:** Backend / Export Service
**Discovered:** 2026-02-08

---

## User Story

As a user, I want to export my generated artifacts as PDF, so that I can share professional documents with stakeholders.

---

## Problem

Exporting an artifact as PDF returns a 500 server error. The DOCX export for the same artifact works correctly (200).

Additionally, two SQLAlchemy connection leak warnings appeared around this request:
> *"The garbage collector is trying to clean up non-checked-in connection... Please ensure that SQLAlchemy pooled connections are returned to the pool explicitly"*

This suggests the failing export handler is not properly closing its database session, which could compound under repeated requests.

---

## Steps to Reproduce

1. Generate a BRD artifact in a conversation
2. Click export as PDF
3. Observe 500 error
4. Export as DOCX for the same artifact — works fine

---

## Evidence

Log timestamps (2026-02-08 UTC):
- `19:59:17` — `GET /api/artifacts/.../export/pdf` **500** (820ms)
- `19:59:19` — `GET /api/artifacts/.../export/docx` **200** (same artifact)
- `19:59:16-17` — Two SQLAlchemy connection leak warnings

---

## Acceptance Criteria

- [ ] PDF export returns 200 with a valid PDF file
- [ ] No SQLAlchemy connection leak warnings during export operations
- [ ] Error is logged with sufficient detail to diagnose (stack trace, not just status code)

---

## Technical References

- `backend/app/services/export_service.py` — PDF export logic
- `backend/app/routes/` — artifact export endpoint
- Likely cause: missing PDF rendering dependency (`weasyprint`, `pdfkit`, or similar) or uncaught exception in PDF generation
