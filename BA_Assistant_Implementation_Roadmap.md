# Implementation Roadmap - Business Analyst Assistant

## Overview

This roadmap outlines the phased approach to building Business Analyst Assistant, optimized for solo developer capacity with focus on market validation before feature expansion.

**Development Approach:** Iterative releases with user feedback incorporation at each phase

**Philosophy:** Ship working software quickly to validate core value proposition, then expand based on real user needs rather than assumptions

**Target Users:** Business analysts in product development, requirements gathering, and stakeholder management roles

**Success Definition:** BAs reduce time spent on requirement documentation while improving completeness through AI-assisted discovery

---

## MVP Phase

### Goal

**Market Validation Objective:** Prove that AI-assisted discovery conversations genuinely help business analysts capture better requirements faster than traditional methods. Validate that BAs will use a mobile/web app during client meetings and that AI guidance improves edge case identification.

**Core Hypothesis to Test:**
- Business analysts find value in AI-powered requirement exploration
- Conversation-based interface is preferable to form-based requirement capture
- Generated artifacts (user stories, acceptance criteria) are high enough quality to use directly
- Cross-device access (desktop planning → mobile meetings) is essential workflow
- Project-based document context improves AI relevance

**Learning Goals:**
- Which artifact types do BAs request most frequently?
- How long are typical discovery conversations (token cost implications)?
- Do BAs primarily use web (office) or mobile (meetings)?
- What document types do BAs upload for context?
- Which features are missing that block adoption?

### Timeline

**Estimated Duration:** 8-10 weeks for solo developer

**Breakdown:**
- Weeks 1-2: Project setup, authentication, database schema
- Weeks 3-4: Project and document management
- Weeks 5-6: Conversation threads with AI integration
- Weeks 7-8: Artifact generation and export
- Weeks 9-10: Testing, bug fixes, beta deployment

**Dependencies:**
- Anthropic API key acquisition (immediate)
- OAuth app setup with Google and Microsoft (week 1)
- PaaS hosting account creation (week 1)
- Flutter development environment (existing)

### Core Features

#### Feature 1: User Authentication (OAuth Social Login)
**Description:** Users sign in with Google or Microsoft work accounts via OAuth 2.0 flow

**Technical Scope:**
- OAuth 2.0 integration with Google Identity Platform
- OAuth 2.0 integration with Microsoft Identity Platform
- JWT token generation and validation
- Secure token storage in Flutter (flutter_secure_storage)
- Token refresh logic when access token expires
- User profile creation from OAuth data (email, name, avatar)

**User Value:** Frictionless signup with existing work credentials, no password to remember, enterprise-friendly

**Complexity:** Medium (OAuth flows well-documented, libraries handle heavy lifting)

**Acceptance Criteria:**
- User can sign in with Google account
- User can sign in with Microsoft account
- Access token refreshes automatically before expiration
- User profile displays name and avatar from OAuth
- Logout clears tokens and returns to login screen

#### Feature 2: Project Management
**Description:** Users create and manage multiple projects, each with isolated context

**Technical Scope:**
- Project CRUD API endpoints (create, read, list)
- Project data model with user ownership
- Project list screen with card-based UI
- Project creation form (name, optional description)
- Project detail screen showing documents and threads

**User Value:** Organize work by client/product/initiative, keep contexts separate

**Complexity:** Low (standard CRUD operations)

**Acceptance Criteria:**
- User can create new project with name
- User sees list of their projects (not other users')
- User can tap project to view details
- Projects persist across devices (server-stored)
- Empty state shows helpful onboarding message

#### Feature 3: Document Upload and Management
**Description:** Users upload text documents to project for AI context

**Technical Scope:**
- Document upload API endpoint (text content)
- Document storage with encryption at rest (Fernet)
- Document list UI within project
- File picker for text file selection
- Full-text search index (SQLite FTS5) for AI retrieval
- Document metadata (name, size, upload date)

**User Value:** Provide project context (existing requirements, stakeholder notes) to improve AI relevance

**Complexity:** Medium (encryption, FTS5 indexing, file handling)

**Acceptance Criteria:**
- User can upload .txt files to project
- User can upload pasted text as document
- Uploaded documents appear in project document list
- Documents encrypted in database
- Documents searchable by AI (tested via conversation)
- Document size limit enforced (10MB)

#### Feature 4: Conversation Threads
**Description:** Multiple independent conversation threads per project for different feature explorations

**Technical Scope:**
- Thread CRUD API endpoints
- Thread data model with project relationship
- Thread list UI with card display
- Thread creation with initial message
- Message history API with pagination
- Thread detail screen (chat interface)

**User Value:** Keep feature discussions separate, return to specific conversations later

**Complexity:** Medium (chat UI, pagination, state management)

**Acceptance Criteria:**
- User can create new thread in project
- Thread list shows all threads for project
- Each thread displays AI-generated summary title
- User can open thread to view full conversation
- Threads ordered by last message timestamp

#### Feature 5: AI-Powered Conversational Discovery
**Description:** Real-time streaming AI responses with structured BA guidance, edge case exploration, and requirement refinement

**Technical Scope:**
- Claude Agent SDK integration (Python backend)
- Custom tools: DocumentSearch, ArtifactGenerator, ThreadSummarizer
- SSE endpoint for streaming responses
- Flutter SSE client for real-time display
- Conversation history management (last 20 messages)
- Token usage tracking and logging
- AI system prompt based on /business-analyst skill

**User Value:** Intelligent guidance during feature discovery, proactive edge case identification, systematic requirement exploration

**Complexity:** High (Agent SDK integration, streaming, tool implementation)

**Acceptance Criteria:**
- User sends message and sees AI response stream in real-time
- AI asks clarifying questions about feature
- AI identifies potential edge cases
- AI references uploaded documents when relevant
- Conversation maintains context across messages
- Streaming stops gracefully on completion
- Error handling for AI service failures

#### Feature 6: On-Demand Document Search
**Description:** AI autonomously searches project documents when conversation requires context

**Technical Scope:**
- DocumentSearch tool implementation (Python)
- SQLite FTS5 query for keyword matches
- Tool returns top 5 relevant document excerpts
- Context assembly for Claude API with search results
- UI indicator when AI is searching documents (optional MVP, nice-to-have)

**User Value:** AI provides contextually relevant guidance based on existing project knowledge

**Complexity:** Medium (FTS5 queries, tool implementation, result formatting)

**Acceptance Criteria:**
- AI searches documents when user asks questions referencing them
- Search returns relevant document excerpts
- AI incorporates document context in responses
- Search performance <100ms for typical project (dozens of documents)

#### Feature 7: Flexible Artifact Generation
**Description:** AI generates structured business artifacts on user request (user stories, acceptance criteria, requirements documents, etc.)

**Technical Scope:**
- ArtifactGenerator tool implementation
- Artifact data model linked to messages
- Artifact detection in AI response stream
- Artifact storage in database
- Artifact viewing UI (formatted display)

**User Value:** Convert exploratory conversation into shareable, structured documentation

**Complexity:** Medium (artifact parsing, storage, UI formatting)

**Acceptance Criteria:**
- User can request artifact ("generate a user story for this feature")
- AI creates structured artifact based on conversation
- Artifact displays formatted in chat interface
- Artifact persists in database linked to conversation
- Multiple artifacts can exist in single thread

#### Feature 8: Artifact Export (Multiple Formats)
**Description:** Export generated artifacts as Markdown, PDF, or Word documents

**Technical Scope:**
- Export API endpoint with format parameter
- Markdown export (raw text)
- PDF generation via WeasyPrint (HTML → PDF)
- Word generation via python-docx
- File download handling in Flutter
- Artifact formatting templates

**User Value:** Share artifacts with stakeholders, integrate into existing documentation workflow

**Complexity:** Medium (document generation libraries, formatting templates)

**Acceptance Criteria:**
- User can export artifact as Markdown (immediate download)
- User can export artifact as PDF (well-formatted)
- User can export artifact as Word document (.docx)
- Downloaded files open correctly in respective applications
- Formatting is professional and readable

#### Feature 9: AI-Generated Thread Summaries
**Description:** Automatic summary generation for conversation threads to aid quick scanning

**Technical Scope:**
- ThreadSummarizer tool implementation
- Summary generation after initial exchange (e.g., 3+ messages)
- Summary update on significant conversation progression
- Summary storage in thread model
- Summary display in thread list cards

**User Value:** Quickly identify relevant conversations in thread list without opening each

**Complexity:** Low (simple tool implementation, UI display)

**Acceptance Criteria:**
- Threads display 2-3 sentence summaries
- Summaries accurately reflect conversation topic
- Summaries update as conversation evolves
- New threads generate summary after initial messages

### Technical Scope

**What Gets Built:**

**Backend (FastAPI):**
- RESTful API with all CRUD endpoints
- OAuth 2.0 authentication flows (Google, Microsoft)
- JWT token generation and middleware
- SQLite database with SQLAlchemy ORM
- Database encryption (SQLCipher + Fernet)
- Claude Agent SDK integration
- Custom tool implementations (DocumentSearch, ArtifactGenerator, ThreadSummarizer)
- SSE streaming endpoint
- Document export logic (Markdown, PDF, Word)
- Error handling and logging
- Rate limiting middleware

**Frontend (Flutter):**
- Authentication screens (login, OAuth callback)
- Project list and creation screens
- Document upload and list UI
- Thread list with card display
- Chat interface with SSE streaming
- Artifact viewing with formatting
- Export functionality (file download)
- State management with Provider
- Error handling and retry logic
- Loading states and indicators

**Database Schema:**
- Users table (OAuth profiles)
- Projects table (user projects)
- Documents table (encrypted content + FTS5 index)
- Threads table (conversations)
- Messages table (chat history)
- Artifacts table (generated documents)
- Sessions table (JWT refresh tokens)

**Infrastructure:**
- Railway or Render deployment
- Persistent volume for SQLite
- Environment variable configuration
- HTTPS with automatic SSL
- Daily automated backups

**What Gets Deferred:**

**To Beta Phase:**
- Search across projects and threads
- User profile settings page
- Conversation editing (edit past messages)
- Thread deletion
- Project deletion
- Document deletion
- Full conversation export (not just artifacts)
- Push notifications
- Email notifications
- PDF/Word document upload parsing (MVP is text-only)
- Advanced document organization (folders, tags)
- Conversation branching

**To V1.0 Phase:**
- Multi-user collaboration (project sharing)
- Team workspaces
- Admin dashboard
- Usage analytics for users
- Custom AI personality/behavior settings
- Template library for common BA artifacts
- Integration with Jira/Confluence
- Offline mode with sync
- Advanced caching strategies
- PostgreSQL database migration

**Simplifications Applied:**

**No Deletion in MVP:**
- **Simplification:** Users cannot delete projects, threads, documents, or messages
- **Implication:** Database grows but no data loss risk, less code complexity (no cascade deletes, no "are you sure?" flows)
- **Rationale:** MVP focuses on creation workflow; cleanup features added when user requests

**Text-Only Documents:**
- **Simplification:** Only plain text uploads, no PDF/Word parsing
- **Implication:** Users must copy-paste from documents rather than direct upload
- **Rationale:** Parsing libraries add complexity; validate document usefulness first

**No Search in MVP:**
- **Simplification:** No search across projects/threads, users browse manually
- **Implication:** Usability degrades with many projects (10+), but acceptable for MVP with 1-5 projects per user
- **Rationale:** Search is complex (full-text, filtering, ranking); defer until users have enough data to need it

**Basic Error Handling:**
- **Simplification:** Simple error messages with manual retry, no sophisticated auto-retry or queuing
- **Implication:** User experience degrades on network issues, but acceptable for MVP
- **Rationale:** Complex retry logic and offline queues add significant complexity; handle in Beta

**Single AI Personality:**
- **Simplification:** One consistent AI behavior for all users and projects
- **Implication:** AI can't adapt tone/style to user preference or project type
- **Rationale:** Customization is feature expansion, not core validation; add if users request

**No Notifications:**
- **Simplification:** No push or email notifications for any events
- **Implication:** Users must manually check app for updates (not relevant in MVP—no multi-user collaboration)
- **Rationale:** Notifications only valuable for async collaboration; MVP is single-user

### Success Criteria

**Functional:**
- [ ] User can sign in with Google or Microsoft account
- [ ] User can create projects and upload text documents
- [ ] User can start conversation threads within projects
- [ ] AI provides relevant, helpful guidance during discovery conversations
- [ ] AI references uploaded documents when contextually appropriate
- [ ] User can request and receive structured artifacts (user stories, etc.)
- [ ] Artifacts export correctly in Markdown, PDF, and Word formats
- [ ] All data persists and syncs across devices
- [ ] Application handles AI service errors gracefully (retry option)
- [ ] No critical security vulnerabilities (OAuth, JWT, encryption working)

**Non-Functional:**
- [ ] API response time <200ms for CRUD operations (p95)
- [ ] AI streaming first chunk <2s (p95)
- [ ] Application supports 10-50 concurrent users without degradation
- [ ] Mobile app loads in <2s on 3G connection
- [ ] Database queries <50ms (p95)
- [ ] No data loss (backups restore correctly)
- [ ] SSL/HTTPS enforced on all connections

**Business:**
- [ ] 10-20 beta testers recruited (BAs willing to test)
- [ ] Average of 5+ conversation threads per active user (engagement)
- [ ] 70%+ of users generate at least one artifact (core feature validation)
- [ ] User feedback indicates AI guidance is "helpful" or "very helpful" (>4/5 rating)
- [ ] At least 50% of users access from multiple devices (validates cross-device requirement)
- [ ] 60%+ of users return within 7 days (retention signal)
- [ ] Qualitative feedback identifies top 3 missing features for Beta

### Technical Debt Incurred

**Debt 1: SQLite in Production**
- **What was simplified:** Using SQLite instead of PostgreSQL for production database
- **Future Impact:** Limited concurrent write performance (single writer lock), no horizontal scaling, migration required for >500 concurrent users
- **Severity:** Medium - acceptable for MVP/early Beta, becomes critical at scale
- **Payback Timeline:** Beta phase if growth is rapid, otherwise V1.0 phase

**Debt 2: No Deletion Capabilities**
- **What was simplified:** Users cannot delete projects, threads, documents, or messages
- **Future Impact:** Database grows indefinitely, users cannot clean up mistakes or obsolete data, may frustrate power users
- **Severity:** Low - minor UX issue, no technical risk
- **Payback Timeline:** Beta phase based on user feedback priority

**Debt 3: Text-Only Document Upload**
- **What was simplified:** No PDF or Word document parsing, users must paste text manually
- **Future Impact:** User friction for document ingestion, may deter adoption if BAs primarily have documents as PDFs
- **Severity:** Medium - depends on user feedback about workflow friction
- **Payback Timeline:** Beta if users strongly request; V1.0 otherwise

**Debt 4: Basic Error Handling**
- **What was simplified:** Simple error messages with manual retry, no auto-retry or offline queuing
- **Future Impact:** Poor UX during network issues, users may lose messages if connection drops mid-send
- **Severity:** Low-Medium - acceptable for MVP, improves UX significantly when addressed
- **Payback Timeline:** Beta phase for better error recovery

**Debt 5: Agent SDK Token Usage**
- **What was simplified:** Using Agent SDK for all conversations instead of optimized routing to minimize tokens
- **Future Impact:** Higher AI API costs (10-30% more tokens than manual API), cost scales linearly with users
- **Severity:** Medium-High - impacts unit economics, but manageable with monitoring
- **Payback Timeline:** Ongoing monitoring; optimize prompts in Beta if costs exceed projections

**Debt 6: No Search Functionality**
- **What was simplified:** No search across projects, threads, or conversations
- **Future Impact:** Usability degrades as users accumulate projects/threads, power users may churn
- **Severity:** Low - minor friction early, increases with usage
- **Payback Timeline:** Beta phase as users accumulate data

---

## Beta Phase

### Goal

**Refinement and Expansion Objective:** Based on MVP learnings, improve user experience, add high-priority missing features, and optimize performance. Transition from validation mode to early adoption mode—make product polished enough for paying users.

**Key Questions from MVP:**
- Which features did users consistently request?
- Where did users experience friction or confusion?
- What usage patterns emerged (conversation length, artifact types, document sizes)?
- Did AI guidance quality meet expectations?
- What cost per user did we observe?

**Beta Goals:**
- Improve retention (target: 70% 7-day, 40% 30-day)
- Increase engagement (target: 10+ threads per active user)
- Reduce friction in common workflows
- Optimize cost per user (target: <$2/user/month AI costs)
- Prepare for monetization (understand willingness to pay)

### Timeline

**Estimated Duration:** 6-8 weeks

**Breakdown:**
- Weeks 1-2: Deletion and editing features
- Weeks 3-4: Search functionality and document parsing
- Weeks 5-6: Performance optimization and caching
- Weeks 7-8: Polish, testing, expanded beta rollout

**Dependencies:**
- MVP user feedback analysis (week 0)
- Usage metrics and cost data from MVP (week 0)
- Performance profiling results (week 0)

### Additional Features

#### Feature 10: Deletion Capabilities
**Description:** Users can delete projects, threads, documents, and messages with confirmation

**Why Now:** MVP users will accumulate test data and mistakes needing cleanup; requested feature based on early feedback assumption

**Dependencies:** Builds on existing CRUD infrastructure, adds DELETE endpoints

**Complexity:** Low-Medium (cascade deletes, UI confirmation dialogs)

**Technical Scope:**
- DELETE API endpoints for all entities
- Cascade delete logic (deleting project → deletes threads, documents, messages)
- Confirmation dialogs in UI
- Soft delete option for audit trail (deleted_at timestamp)
- Restore from soft delete (optional, if feedback indicates need)

**Success Criteria:**
- Users can delete projects (with "are you sure?" confirmation)
- Deleting project removes all child data (threads, documents)
- Users can delete individual threads and documents
- Deletion is immediate (no undo in Beta, may add later)

#### Feature 11: PDF and Word Document Upload Parsing
**Description:** Direct upload of PDF and Word files with automatic text extraction

**Why Now:** MVP feedback likely shows users want to upload documents directly rather than copy-paste; reduces friction

**Dependencies:** Requires document parsing libraries (PyPDF2, python-docx)

**Complexity:** Medium (parsing libraries, error handling for malformed documents)

**Technical Scope:**
- PDF parsing with PyPDF2 or pdfplumber
- Word parsing with python-docx
- File type detection and validation
- Error handling for password-protected or corrupted files
- Fallback to text-only if parsing fails
- Document preview (first 500 characters) in UI

**Success Criteria:**
- Users can upload PDF files and content is extracted
- Users can upload Word (.docx) files and content is extracted
- Parsing errors show clear messages (e.g., "encrypted PDF")
- Parsed content is searchable by AI
- Upload processing <5s for typical documents (5-20 pages)

#### Feature 12: Search Functionality
**Description:** Search across projects, threads, and conversation content

**Why Now:** Beta users accumulate enough data (10+ projects, dozens of threads) that browsing becomes inefficient

**Dependencies:** Requires extending FTS5 index to conversations, thread titles

**Complexity:** Medium (FTS5 queries across multiple tables, result ranking, UI)

**Technical Scope:**
- Extend FTS5 index to messages table
- Global search API endpoint (across all user's data)
- Project-specific search (within single project)
- Search results UI with highlighting
- Search ranking by relevance and recency
- Debounced search input (300ms delay)

**Success Criteria:**
- Users can search all projects and threads from top-level search
- Search results show relevant matches with context
- Search includes thread titles, messages, and document content
- Results ordered by relevance
- Search performance <200ms for typical user data

#### Feature 13: Conversation Editing
**Description:** Edit or delete individual messages in conversation history

**Why Now:** Users want to correct typos or rephrase questions for better AI responses

**Dependencies:** Message editing impacts conversation context—requires re-sending history to AI

**Complexity:** Medium (edit UI, conversation re-contextualization)

**Technical Scope:**
- Edit message API endpoint
- Delete message API endpoint
- Edit UI in chat interface (long-press or context menu)
- Conversation history update after edit
- Indicator showing message was edited (timestamp)

**Success Criteria:**
- Users can edit their own messages (not AI responses)
- Users can delete their own messages
- Editing doesn't break conversation flow
- Deleted messages show placeholder "[Message deleted]"

#### Feature 14: Full Conversation Export
**Description:** Export entire thread conversation (not just artifacts) as PDF or document

**Why Now:** Users want to share discovery conversations with stakeholders or save for records

**Dependencies:** Builds on artifact export infrastructure

**Complexity:** Low-Medium (format conversation as document, similar to artifact export)

**Technical Scope:**
- Export thread API endpoint
- Conversation formatting (messages with timestamps, user/AI labels)
- PDF generation with conversation formatting
- Markdown export option
- Include artifacts inline in export

**Success Criteria:**
- Users can export full thread conversation
- Export includes all messages with timestamps
- Artifacts embedded in conversation flow
- Exported document is readable and well-formatted

### Technical Improvements

**Architecture Evolution:**
- **Database:** Evaluate PostgreSQL migration if SQLite shows performance issues (>100ms queries) or if concurrent users exceed expectations
- **Caching:** Implement Redis for caching document search results, conversation summaries, frequently accessed projects
- **API Optimization:** Add response caching with ETags, optimize N+1 query problems if discovered

**Performance Optimization:**
- **AI Prompt Optimization:** Reduce token usage by optimizing system prompt, limiting conversation history more aggressively
- **Document Search Caching:** Cache search results for identical queries (5-minute TTL)
- **Frontend Pagination:** Implement virtual scrolling for long message lists (100+ messages)
- **Image Optimization:** Compress user avatars, lazy load images

**Security Hardening:**
- **Rate Limiting:** Implement per-user rate limits (stricter than MVP's per-IP)
- **Input Validation:** Strengthen validation for edge cases discovered in MVP
- **Audit Logging:** Log all deletion actions for security audit trail
- **API Key Rotation:** Implement process for rotating OAuth and API keys without downtime

**Technical Debt Payback:**
- **Deletion Capabilities:** Implemented in Feature 10
- **Document Parsing:** Implemented in Feature 11
- **Search Functionality:** Implemented in Feature 12
- **Error Handling:** Improve retry logic with exponential backoff, add offline message queuing

**Cost Optimization:**
- Monitor token usage per conversation type
- Identify opportunities to use cheaper Claude models for simple tasks
- Implement conversation history truncation more aggressively (test 15 vs 20 messages)
- Cache common AI responses (e.g., initial greeting, help text)

### Success Criteria

**Functional:**
- [ ] All Beta features implemented and tested
- [ ] Users can delete projects, threads, documents cleanly
- [ ] PDF and Word uploads work reliably
- [ ] Search returns relevant results quickly
- [ ] Conversation editing doesn't break AI context
- [ ] Exports include full conversations, not just artifacts
- [ ] No critical bugs from MVP remain unresolved

**Non-Functional:**
- [ ] API response time maintained <200ms (p95) despite added features
- [ ] AI token usage reduced by 15-20% via prompt optimization
- [ ] Database performance adequate for 100-200 concurrent users
- [ ] Search performance <200ms for users with 50+ threads
- [ ] Cost per active user <$2/month (AI + hosting)

**Business:**
- [ ] 50-100 beta users onboarded
- [ ] 70%+ 7-day retention (vs 60% target in MVP)
- [ ] 40%+ 30-day retention
- [ ] Average 10+ threads per active user (vs 5+ in MVP)
- [ ] 80%+ users generate artifacts (vs 70% in MVP)
- [ ] User satisfaction rating >4.2/5.0 (up from MVP)
- [ ] 30%+ users indicate willingness to pay $15-25/month (pricing validation)

### Technical Debt Resolution

**Debt Resolved:**
- ✓ Deletion capabilities implemented
- ✓ Document parsing for PDF/Word added
- ✓ Search functionality built
- ✓ Improved error handling with retry logic

**Remaining Debt:**
- SQLite still in use (migrate if metrics indicate need)
- Agent SDK token usage higher than optimal (monitoring and optimizing)
- No offline mode (defer to V1.0)
- Single AI personality (defer to V1.0)

---

## V1.0 Phase

### Goal

**Production-Ready Objective:** Prepare for public launch and sustainable growth. Polish all rough edges, implement enterprise-grade monitoring, optimize for profitability, and ensure system can scale to 1,000+ active users.

**Key Transition:** Beta → V1.0 moves from "early adopters willing to forgive bugs" to "professional product that justifies paid subscriptions."

**V1.0 Goals:**
- Production-quality stability (99.5% uptime)
- Optimized unit economics (profitable at $20/user/month)
- Enterprise-ready security and compliance
- Scalable infrastructure (handles 10x growth without rewrites)
- Comprehensive documentation (user guides, API docs, onboarding)

### Timeline

**Estimated Duration:** 4-6 weeks

**Breakdown:**
- Weeks 1-2: PostgreSQL migration, infrastructure improvements
- Weeks 3-4: Monitoring, analytics, user onboarding
- Weeks 5-6: Documentation, testing, launch preparation

**Dependencies:**
- Beta usage metrics showing consistent growth
- User feedback indicating product-market fit
- Cost analysis confirming unit economics
- Security audit or self-review

### Feature Completion

#### Feature 15: User Onboarding Flow
**Description:** Guided onboarding for new users explaining features and best practices

**Technical Scope:**
- Onboarding screens in Flutter (swipe-through tutorial)
- Sample project creation with example documents
- Interactive tutorial (create first thread, generate first artifact)
- Tooltips for key features
- "Skip" option for experienced users

**Success Criteria:**
- New users complete onboarding at 70%+ rate
- Users who complete onboarding have 2x higher retention than those who skip

#### Feature 16: User Profile and Settings
**Description:** User profile page with account settings and preferences

**Technical Scope:**
- Profile page UI
- Edit display name and avatar
- Account deletion option (GDPR compliance)
- Notification preferences (for future notifications)
- Privacy settings (data retention preferences)

**Success Criteria:**
- Users can update profile information
- Account deletion works correctly (purges all user data)

#### Feature 17: Usage Analytics Dashboard
**Description:** Users see their own usage stats (threads created, artifacts generated, trends)

**Technical Scope:**
- Analytics data collection (anonymized event tracking)
- Backend analytics API
- Dashboard UI with charts
- Privacy-respecting implementation (no third-party trackers)

**Success Criteria:**
- Users can view personal usage statistics
- Analytics accurately reflect usage patterns

#### Feature 18: In-App Help and Documentation
**Description:** Contextual help, FAQ, and documentation accessible in-app

**Technical Scope:**
- Help center page with searchable FAQ
- Contextual help tooltips
- Video tutorials (optional, if budget allows)
- Support contact form

**Success Criteria:**
- Users can access help without leaving app
- Common questions answered in FAQ

### Technical Maturation

**Architecture Refinements:**
- **PostgreSQL Migration:** Migrate from SQLite to PostgreSQL for production scalability
  - Use SQLAlchemy to minimize code changes
  - Test migration thoroughly in staging
  - Plan maintenance window for cutover
  - Validate data integrity post-migration
- **Connection Pooling:** Optimize database connections for higher concurrency
- **API Versioning:** Implement /v1/ API versioning for future backward compatibility

**Scalability Preparations:**
- **Database Optimization:**
  - Add indexes for all frequently queried fields
  - Optimize slow queries identified in Beta
  - Set up read replicas if needed (PostgreSQL feature)
- **Caching Layer:**
  - Redis for session storage, document search results
  - Cache frequently accessed projects and threads
  - Implement cache invalidation strategy
- **CDN for Static Assets:**
  - Cloudflare CDN for Flutter web assets
  - Reduce latency for global users
  - Optimize image delivery

**Monitoring and Observability:**
- **Logging:**
  - Centralized logging (Papertrail or similar)
  - Structured JSON logs
  - Log rotation and retention (30 days)
- **Metrics:**
  - Track API latency, error rates, throughput
  - AI token usage per user and conversation
  - Database performance metrics
  - User engagement metrics (DAU, WAU, MAU)
- **Alerting:**
  - PagerDuty or similar for critical alerts
  - Alert on error rate >1%, API latency >500ms, database issues
  - On-call rotation (even for solo dev, need notifications)
- **APM (Application Performance Monitoring):**
  - Integrate Sentry performance monitoring
  - Track slow transactions
  - Identify performance bottlenecks

**Documentation Completion:**
- **User Documentation:**
  - Getting started guide
  - Feature tutorials (how to upload documents, start threads, generate artifacts)
  - Best practices for effective AI conversations
  - Troubleshooting common issues
- **API Documentation:**
  - Comprehensive API reference (OpenAPI/Swagger)
  - Authentication guide
  - Rate limiting documentation
  - Example requests/responses
- **Deployment Documentation:**
  - Infrastructure setup guide
  - Environment variable reference
  - Backup and restore procedures
  - Rollback procedures
  - Disaster recovery plan
- **Maintenance Runbooks:**
  - Common operational tasks
  - Troubleshooting database issues
  - Handling AI service outages
  - Scaling procedures

**Testing and Quality:**
- **Backend Testing:**
  - Unit tests for critical business logic (70%+ coverage)
  - Integration tests for API endpoints
  - Load testing (simulate 1,000 concurrent users)
  - Security testing (OWASP top 10)
- **Frontend Testing:**
  - Widget tests for critical UI components
  - Integration tests for user flows
  - Cross-platform testing (web, Android, iOS)
- **End-to-End Testing:**
  - Automated E2E tests for critical paths
  - Manual regression testing before launch
- **Security Audit:**
  - Self-review or third-party audit
  - Penetration testing (if budget allows)
  - Review OAuth implementation
  - Review data encryption
  - Review API security

### Success Criteria

**Functional:**
- [ ] All V1.0 features implemented and tested
- [ ] PostgreSQL migration successful (data integrity verified)
- [ ] Onboarding flow improves user activation
- [ ] User documentation comprehensive and clear
- [ ] No known critical or high-severity bugs

**Non-Functional:**
- [ ] 99.5% uptime over 30 days
- [ ] API response time <200ms (p95) maintained
- [ ] Database handles 1,000 concurrent users without degradation
- [ ] AI token usage optimized to <$1.50/user/month
- [ ] Test coverage >70% for backend critical paths
- [ ] Security audit passed (or self-audit complete)
- [ ] Load testing shows system handles 10x current traffic

**Business:**
- [ ] 200+ active users (paying or free trial)
- [ ] 75%+ 7-day retention
- [ ] 50%+ 30-day retention
- [ ] Conversion rate to paid >20% (for users completing trial)
- [ ] User satisfaction >4.5/5.0
- [ ] Unit economics: profitable at $20/user/month
- [ ] Churn rate <10%/month

### Technical Debt Resolution

**Debt Fully Resolved:**
- ✓ PostgreSQL migration complete (SQLite write limits resolved)
- ✓ Comprehensive monitoring and observability
- ✓ Security hardening complete
- ✓ Documentation comprehensive

**Managed Ongoing Debt:**
- Agent SDK token usage (ongoing optimization, acceptable cost with monitoring)
- Single AI personality (defer customization unless strong user demand)
- No offline mode (consider for V2.0 based on mobile usage patterns)

---

## Post-V1.0 Considerations

### Monitoring Phase Transitions

**When to Revisit Architecture:**
- **User Growth Triggers:**
  - 10x user growth (1,000 → 10,000 active users): Consider microservices, horizontal scaling
  - Geographic expansion: Add regional deployments, CDN optimization
  - Enterprise customers: Evaluate dedicated instances, SLA requirements

- **Performance Triggers:**
  - Database queries consistently >200ms: Optimize schema, add indexes, consider read replicas
  - AI service costs >50% of revenue: Re-evaluate Agent SDK vs manual API, implement aggressive caching
  - API latency increasing: Profile bottlenecks, consider caching layer, optimize N+1 queries

- **Feature Triggers:**
  - Real-time collaboration: Requires WebSockets, operational transforms, significantly different architecture
  - Offline mode: Requires sync engine, conflict resolution, local-first architecture
  - Integrations ecosystem: May require plugin architecture, API versioning, webhook infrastructure

### When to Revisit Technology Choices

**SQLite → PostgreSQL (already planned for V1.0):**
- Triggered by: >500 concurrent users, slow queries, need for advanced features

**Monolith → Microservices:**
- Consider only when: >10,000 active users, team grows beyond solo developer, scaling specific services independently
- Not before: Premature optimization, adds operational complexity

**Agent SDK → Custom Tool Loop:**
- Consider if: AI costs exceed 60% of revenue after optimization
- Likely not worth complexity unless scale is massive (100,000+ conversations/day)

**PaaS → Self-Managed Cloud:**
- Consider when: >5,000 active users and cost optimization justifies DevOps investment
- Monthly savings must exceed $2,000+ to justify time investment

### Potential Future Enhancements

**Features Considered but Deprioritized:**
- **Team Workspaces:** Multi-user collaboration on projects
  - When: Enterprise sales require this feature
  - Complexity: High (permissions, real-time sync, access control)

- **Custom AI Personalities:** Configurable AI behavior per user/project
  - When: User feedback strongly requests this
  - Complexity: Medium (prompt templating, settings UI)

- **Template Library:** Pre-built templates for common BA artifacts
  - When: Users show patterns in artifact types requested
  - Complexity: Low (template storage, selection UI)

- **Jira/Confluence Integration:** Export artifacts directly to Atlassian tools
  - When: Enterprise adoption requires this integration
  - Complexity: High (OAuth apps, API integration, mapping)

- **Offline Mode with Sync:** Full offline capability with background sync
  - When: Mobile usage data shows frequent offline usage attempts
  - Complexity: High (conflict resolution, local database, sync engine)

- **Voice Input:** Speak messages instead of typing (mobile)
  - When: BAs indicate desire to capture notes verbally during meetings
  - Complexity: Medium (speech-to-text API, UI for recording)

- **Advanced Analytics:** Project analytics, requirement coverage analysis
  - When: Users upgrade to "Pro" tier and request deeper insights
  - Complexity: Medium-High (analytics engine, visualization)

**Technical Improvements for Future:**
- **GraphQL API:** Alternative to REST for frontend flexibility
- **WebSockets:** For real-time collaboration features
- **Event-Driven Architecture:** For scaling complex workflows
- **ML Model Fine-Tuning:** Custom-tuned model for BA domain (very long-term)

---

## Development Notes

### Dependencies Between Phases

**MVP → Beta:**
- Beta requires MVP user feedback to prioritize features
- Beta builds directly on MVP codebase (no rewrites)
- Beta features assume core value validated in MVP

**Beta → V1.0:**
- V1.0 requires Beta usage metrics to justify infrastructure investment
- PostgreSQL migration requires testing in Beta environment first
- V1.0 documentation draws from Beta user questions and pain points

**Intra-Phase Dependencies:**
- Document parsing (Feature 11) should complete before search (Feature 12) to test parsing quality
- Deletion (Feature 10) can run parallel to search and document parsing
- Conversation editing (Feature 13) should follow search (Feature 12) to avoid UI conflicts

### Risk Mitigation

**Risk 1: AI Costs Exceed Projections**
- **Mitigation:**
  - Monitor token usage daily in MVP
  - Set budget alerts at $50/day, $100/day thresholds
  - Implement conversation history limits (20 messages initially)
  - Test prompt optimizations in staging before production
  - Have fallback plan: switch to cheaper Claude model for simple conversations
- **Impact:** High - affects unit economics directly

**Risk 2: SQLite Performance Bottleneck Sooner Than Expected**
- **Mitigation:**
  - Profile database queries weekly in Beta
  - Have PostgreSQL migration plan ready
  - Set performance alerts at 100ms query threshold
  - Test PostgreSQL migration in staging environment
- **Impact:** Medium - slows Beta growth but migration path is clear

**Risk 3: OAuth Provider Outage**
- **Mitigation:**
  - Offer both Google and Microsoft (redundancy)
  - Display clear error messages on OAuth failure
  - Monitor OAuth provider status pages
  - Consider adding email/password as fallback in Beta if outages occur
- **Impact:** Medium - prevents new logins but existing users unaffected

**Risk 4: User Adoption Lower Than Expected**
- **Mitigation:**
  - Recruit Beta testers before MVP launch
  - Gather continuous feedback via in-app surveys
  - Iterate quickly on feedback (weekly updates in MVP)
  - Have pivot plan if core hypothesis invalidated
- **Impact:** High - affects entire roadmap and viability

**Risk 5: Solo Developer Velocity Slower Than Estimated**
- **Mitigation:**
  - Build buffer into timeline estimates (8-10 weeks vs 6-8 weeks)
  - De-scope features if timeline slips (protect MVP core)
  - Leverage libraries/tools to maximize productivity
  - Accept technical debt consciously to maintain velocity
- **Impact:** Medium - delays launch but doesn't compromise quality if managed

### Solo Developer Velocity Assumptions

**Productive Hours:**
- 20-30 hours/week dedicated to development
- Assumes part-time development (not full-time)
- Accounts for QA, testing, deployment, bug fixes

**Learning Curve:**
- FastAPI: 1 week to productive (similar to Flask)
- Claude Agent SDK: 3-5 days to integrate effectively
- SSE streaming: 2-3 days to implement correctly
- Document export: 2-3 days for all three formats

**Unknowns Buffer:**
- 20% time buffer for unexpected complexity
- Common unknowns: OAuth edge cases, AI prompt tuning, performance issues

**Velocity Improvers:**
- Your Flutter experience (zero learning curve)
- Your QA background (faster testing, fewer bugs)
- SQLite simplicity (no database admin overhead)
- PaaS deployment (no DevOps overhead)

### Where Simplicity Decisions Impact Later Phases

**Decision: SQLite in MVP**
- **Impact on Beta:** Limits concurrent users, must monitor for performance issues
- **Impact on V1.0:** Requires PostgreSQL migration, non-trivial but manageable

**Decision: Text-Only Documents in MVP**
- **Impact on Beta:** User requests for PDF/Word likely, must implement in Beta
- **Impact on V1.0:** Parsing library choice (PyPDF2 vs pdfplumber) affects quality

**Decision: Agent SDK for All Conversations**
- **Impact on Beta:** Token costs may require optimization
- **Impact on V1.0:** May need hybrid approach if costs unsustainable

**Decision: No Deletion in MVP**
- **Impact on Beta:** Must implement to prevent user frustration with test data
- **Impact on V1.0:** Minimal impact, resolved in Beta

**Decision: PaaS Hosting**
- **Impact on Beta:** Adequate for 100-200 users
- **Impact on V1.0:** Adequate for 1,000+ users, may need migration at 10,000+

**Overall Impact:** Most simplicity decisions are reversible without major rewrites. SQLite → PostgreSQL is largest architectural change, but SQLAlchemy ORM mitigates risk. Other decisions (deletion, document parsing, search) are feature additions, not rewrites.

---

## Roadmap Visualization

```
MVP Phase (8-10 weeks)
│
├─ Authentication (OAuth)
├─ Project Management
├─ Document Upload (text)
├─ Conversation Threads
├─ AI Discovery Conversations
├─ Document Search (AI)
├─ Artifact Generation
├─ Artifact Export
└─ Thread Summaries
│
↓ Beta Testing & Feedback
│
Beta Phase (6-8 weeks)
│
├─ Deletion Capabilities
├─ PDF/Word Parsing
├─ Search Functionality
├─ Conversation Editing
├─ Full Conversation Export
├─ Performance Optimization
└─ Cost Optimization
│
↓ Expanded Beta Testing
│
V1.0 Phase (4-6 weeks)
│
├─ User Onboarding
├─ User Profile/Settings
├─ Usage Analytics
├─ In-App Help
├─ PostgreSQL Migration
├─ Monitoring & Observability
├─ Documentation Complete
└─ Security Audit
│
↓ Public Launch
│
V1.0 Production
│
└─ Continuous improvement based on user feedback
```

**Total Time to V1.0: 18-24 weeks (4.5-6 months)**

---

## Document Maintenance

**Version:** 1.0
**Last Updated:** 2026-01-17
**Next Review:** After MVP launch and user feedback analysis

**Update Triggers:**
- MVP user feedback significantly changes Beta priorities
- Timeline slips require re-estimation
- Technology choices prove problematic (e.g., SQLite bottleneck earlier than expected)
- Market conditions change (e.g., competitor launches similar product)
- Funding/resources change (full-time development vs part-time)

**Owner:** Solo Developer (Ivaylo)
