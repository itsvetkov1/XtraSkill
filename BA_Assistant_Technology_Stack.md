# Technology Stack Recommendations - Business Analyst Assistant

## Overview

This document provides detailed technology recommendations for each layer of the Business Analyst Assistant architecture, evaluated against simplicity, solo developer capacity, and functional adequacy. Each recommendation includes 1-100 scoring with comprehensive rationale.

**Evaluation Criteria:**
- **Simplicity** (35% weight): Minimal complexity, straightforward implementation, clear patterns
- **Solo Developer Feasibility** (30% weight): One person can build and maintain, good documentation, reasonable learning curve
- **Cost Implications** (15% weight): Predictable costs, free/affordable tiers, value for money
- **Scalability** (10% weight): Handles MVP → Beta → V1.0 growth without major rewrites
- **Maintainability** (10% weight): Easy debugging, good tooling, stable ecosystem

---

## Frontend Framework

### Recommended: Flutter
**Score: 95/100**

**Rationale:**
Flutter provides true cross-platform development from a single Dart codebase, supporting web, Android, and iOS with native performance. Given your existing experience with Flutter from the AI Rhythm Coach project, you avoid the learning curve and can leverage established patterns. Flutter's hot reload dramatically accelerates development iteration, while Material Design 3 support provides professional UI components out-of-the-box. The framework's mature ecosystem includes excellent packages for HTTP communication (Dio), secure storage, and SSE streaming.

For a solo developer building a hybrid app, Flutter eliminates the need to maintain separate codebases for each platform while delivering genuinely native experiences. The single codebase means bug fixes and features deploy across all platforms simultaneously, crucial for maintaining velocity as a solo developer.

**Trade-offs:**
- **Advantages:**
  - Single codebase for web, Android, iOS saves massive development time
  - Your existing experience from AI Rhythm Coach project (zero learning curve)
  - Hot reload enables rapid UI iteration and debugging
  - Material Design 3 components provide professional, consistent UI
  - Strong package ecosystem (Provider, Dio, flutter_secure_storage)
  - Native performance via compiled code (not WebView wrappers)
  - Excellent documentation and community support
- **Disadvantages:**
  - Larger app bundle size than native apps (~20-30MB compressed)
  - Web performance slightly behind React for complex UIs
  - Platform-specific features require separate implementation channels
  - Initial app download size may deter some users on slow connections
- **Best for:** Solo developers building cross-platform apps who value single codebase maintenance and rapid iteration

**Consistency Check:**
Aligns perfectly with your preference for Flutter from AI Rhythm Coach. Provider state management (your established pattern) integrates seamlessly. Works well with FastAPI backend via standard HTTP/SSE. No conflicts with other architectural choices.

### Alternatives Considered

#### React Native
**Score: 78/100**
**Brief rationale:** Strong cross-platform framework with massive ecosystem and JavaScript familiarity. Scored lower because you'd face learning curve (you know Flutter), JavaScript ecosystem complexity, and performance can lag Flutter for animation-heavy UIs. React Native requires more platform-specific code for native features.
**When to choose:** If you already have React web experience or need specific JS libraries unavailable in Dart ecosystem.

#### Native Apps (Kotlin + Swift + React)
**Score: 55/100**
**Brief rationale:** Best performance and platform integration, but requires maintaining three separate codebases. Completely impractical for solo developer—triple the development, testing, and maintenance burden. Would delay MVP by months.
**When to choose:** Only if platform-specific features are core to product (AR, advanced camera, NFC) and you have a team of specialized developers.

#### Progressive Web App (PWA)
**Score: 82/100**
**Brief rationale:** Single web codebase, no app store approval, instant updates. Scored lower because PWA limitations: no true offline mode, limited device API access, iOS Safari restrictions, less "native" feel. Good for web-first products, less ideal for mobile-first BA tool.
**When to choose:** If distribution via app stores is problematic or you want instant deployment without review delays.

---

## Backend Framework

### Recommended: FastAPI (Python)
**Score: 92/100**

**Rationale:**
FastAPI is the ideal choice for this AI-heavy application due to Python's dominant position in the AI ecosystem. The Claude Agent SDK is built for Python (and TypeScript), making integration seamless and natural. FastAPI's modern async/await architecture is perfect for streaming AI responses via SSE—non-blocking I/O ensures multiple users can receive streaming responses simultaneously without thread exhaustion.

The framework's automatic API documentation (Swagger/OpenAPI) accelerates development by providing interactive testing without writing additional code. Type hints via Pydantic models catch errors at development time and provide clear contracts between frontend and backend. For a solo developer, FastAPI's excellent documentation, clear error messages, and "batteries included" approach (validation, serialization, docs) minimize time spent on boilerplate.

Python's extensive ecosystem—SQLAlchemy (ORM), cryptography (encryption), authlib (OAuth)—means established solutions exist for every requirement. Coming from a QA background, you'll appreciate FastAPI's built-in testing utilities and type safety reducing bug surface area.

**Trade-offs:**
- **Advantages:**
  - Seamless Claude Agent SDK integration (primary requirement)
  - Native async/await for SSE streaming and AI service calls
  - Automatic API documentation saves development time
  - Type hints with Pydantic catch errors early
  - Python ecosystem dominates AI/ML space
  - Excellent ORM (SQLAlchemy) for database operations
  - Rich library ecosystem for all requirements
  - Fast development iteration with clear error messages
- **Disadvantages:**
  - Raw performance slower than Go/Rust (200-300ms vs 50-100ms for CPU-intensive tasks)
  - Global Interpreter Lock limits true parallelism (not an issue with async I/O)
  - Requires careful dependency management (virtual environments)
  - Production deployment requires ASGI server (Uvicorn/Gunicorn)
- **Best for:** AI-integrated applications, rapid development, solo developers who value ecosystem richness over raw performance

**Consistency Check:**
Python backend integrates naturally with Claude Agent SDK (Python). Compatible with SQLite via SQLAlchemy ORM. Flutter frontend communicates via standard REST/SSE—language agnostic. No friction points with chosen technologies.

### Alternatives Considered

#### Node.js (Express/NestJS)
**Score: 75/100**
**Brief rationale:** JavaScript full-stack could be attractive for unified language. However, Claude Agent SDK TypeScript support is secondary to Python. Express is minimal (requires many add-ons), NestJS adds complexity. Node.js event loop is good for I/O but Python's async/await is comparable. Python's AI ecosystem advantage (pandas, numpy, ML libraries) tips the scale.
**When to choose:** If you're primarily a JavaScript developer or need tight integration with TypeScript-first libraries.

#### Go (Gin/Echo)
**Score: 68/100**
**Brief rationale:** Excellent raw performance, compiled binaries, simple deployment. Scored lower because Go ecosystem for AI is immature compared to Python. No official Claude Agent SDK. Would require manual tool loop implementation. Steeper learning curve for developer without Go experience. Type system is powerful but verbose.
**When to choose:** When raw performance is critical (>10,000 concurrent users) and AI integration is simple API calls without Agent SDK.

#### Django (Python)
**Score: 70/100**
**Brief rationale:** Mature Python framework with built-in admin panel, ORM, auth. Scored lower because Django is synchronous by default (async support is addon). Heavier framework with many features not needed (admin, templates). FastAPI's API-first design and native async make it better fit for this use case.
**When to choose:** If you need built-in admin panel, traditional server-rendered templates, or prefer Django's "batteries included" philosophy for full-stack web apps.

---

## Database

### Recommended: SQLite (with migration path to PostgreSQL)
**Score: 88/100**

**Rationale:**
SQLite is the optimal choice for MVP due to zero-configuration simplicity—it's a single file requiring no separate database server process. For a solo developer, this eliminates operational complexity during rapid development. SQLite's built-in full-text search (FTS5) provides exactly what's needed for document keyword search without additional infrastructure.

The technology decision accounts for future growth: SQLite is adequate for 50-500 concurrent users (MVP and Beta phases), and SQLAlchemy ORM provides a clean migration path to PostgreSQL when scale demands it. By using an ORM from the start, database migration is mostly configuration changes rather than code rewrites.

File-based architecture works perfectly with PaaS hosting—mount a persistent volume, deploy, done. Daily backups are simple file copies. Your QA background will appreciate SQLite's reliability and data integrity guarantees (ACID compliant). The FTS5 extension for document search is production-ready and performs well for thousands of documents.

**Trade-offs:**
- **Advantages:**
  - Zero configuration—single file, no server setup
  - Perfect for development iteration speed
  - Built-in FTS5 for document full-text search
  - ACID compliant with strong data integrity
  - Excellent for PaaS deployment (persistent volume)
  - Simple backups (file copy)
  - Low operational overhead for solo developer
  - Clear migration path to PostgreSQL via SQLAlchemy
  - Proven reliability (used by billions of devices)
- **Disadvantages:**
  - Limited concurrent write performance (single writer)
  - Not suitable for high-traffic production (>500 concurrent users)
  - No horizontal scaling capability
  - Limited to single server deployment
  - Advanced features (replication, sharding) require PostgreSQL
- **Best for:** MVP and Beta phases with clear migration plan, solo developer minimizing operational complexity

**Consistency Check:**
SQLAlchemy ORM (Python ecosystem) provides excellent SQLite support. Encryption via SQLCipher extension. FastAPI async works with async SQLAlchemy. Migration to PostgreSQL straightforward—change connection string, test, deploy. Aligns with your SQL preference from personal context.

### Alternatives Considered

#### PostgreSQL
**Score: 95/100**
**Brief rationale:** Industry-standard relational database with excellent performance, concurrent access, and scalability. Scored slightly higher overall but not recommended for MVP because setup complexity (separate server, connection management) slows development. Perfect for V1.0 migration when user scale demands it.
**When to choose:** Start of Beta phase if early metrics show rapid growth, or immediately if you expect >500 concurrent users from launch.

#### MongoDB
**Score: 65/100**
**Brief rationale:** Document database with flexible schema could suit varied conversation/document structures. Scored lower because you prefer SQL (personal context), NoSQL doesn't provide significant advantages for this use case (data is relational), and full-text search requires additional setup (Atlas Search or external). Learning curve for developer familiar with SQL.
**When to choose:** If document schemas are highly variable and unpredictable, or you have existing MongoDB expertise.

#### MySQL/MariaDB
**Score: 85/100**
**Brief rationale:** Mature relational databases with good performance and widespread hosting support. Scored lower than PostgreSQL because fewer advanced features (JSON, full-text search less powerful) and PostgreSQL is preferred in Python ecosystem. Better than NoSQL for this use case but PostgreSQL is superior when migrating from SQLite.
**When to choose:** If hosting provider only supports MySQL/MariaDB or you have specific MySQL expertise.

---

## AI Integration

### Recommended: Claude Agent SDK (Python) - Approach 2 (Agent SDK Only Pattern)
**Score: 90/100**

**Rationale:**
The Claude Agent SDK provides exactly the functionality required—autonomous tool execution for document search and artifact generation—without implementing complex agentic loops manually. Approach 2 (Agent SDK Only) is optimal because it creates a single, consistent code path where the AI handles all decision-making about when to use tools versus responding directly.

This approach directly mirrors your /business-analyst skill concept from Claude Code, making the AI behavior familiar and predictable. The Agent SDK manages session state, handles tool execution, and provides streaming responses—all requirements you'd otherwise implement manually. For a solo developer, delegating this complexity to a well-tested SDK accelerates development and reduces bug surface area.

The trade-off of higher API costs (agent loops use more tokens) is acceptable during MVP when you're absorbing costs to validate the product. The cost difference (10-30% more tokens than manual API calls) is offset by development time savings and behavioral consistency. Token usage monitoring helps control costs as you learn usage patterns.

**Trade-offs:**
- **Advantages:**
  - Single code path simplifies testing and debugging
  - AI autonomously decides when to use tools (less brittle than keyword routing)
  - Built-in session management and conversation history
  - Streaming responses handled by SDK
  - Consistent behavior across all interactions
  - Directly mirrors /business-analyst skill you're starting from
  - Reduces custom code for tool execution loops
  - Well-documented with examples from Claude team
- **Disadvantages:**
  - Higher token usage than direct API calls (agent reasoning overhead)
  - Less granular control over tool invocation timing
  - Black-box behavior for tool selection (AI decides, not explicit logic)
  - Debugging requires understanding agent traces
  - Dependency on SDK updates and maintenance
- **Best for:** AI-first applications where autonomous behavior is desired, developers who value consistency over fine-grained control

**Consistency Check:**
Python-based SDK integrates seamlessly with FastAPI backend. Tools implemented as Python async functions. Streaming responses pipe directly to SSE endpoint. No conflicts with other stack choices. Aligns with your vision of AI assistant autonomously searching documents when needed.

### Alternatives Considered

#### Direct Anthropic API with Manual Tool Loop
**Score: 72/100**
**Brief rationale:** Maximum control over tool execution and token usage. Scored lower because you'd implement agentic retry logic, tool management, and session handling yourself—significant development time for solo developer. Better for simple chatbots, overkill for complex tool usage patterns.
**When to choose:** If you need precise control over every API call for cost optimization or have very specific tool execution patterns not supported by Agent SDK.

#### Hybrid Pattern (Simple API + Selective Agent SDK)
**Score: 75/100**
**Brief rationale:** Cost-optimized approach routing simple messages to direct API, complex tasks to Agent SDK. Scored lower because routing logic adds complexity (intent detection, dual code paths) that introduces bugs. Cost savings (15-20%) don't justify added maintenance burden for solo developer in MVP phase.
**When to choose:** If API costs become unsustainable in production and profiling shows many conversations don't need tools.

#### LangChain Agent Framework
**Score: 55/100**
**Brief rationale:** Flexible agent framework with many integrations. Scored much lower because adds abstraction layer over Claude API, learning curve for framework specifics, and Agent SDK is purpose-built for Claude with better integration. LangChain is powerful but overkill for this use case.
**When to choose:** If you need to support multiple LLM providers or require LangChain-specific features like document loaders and vector stores.

---

## State Management (Frontend)

### Recommended: Provider (Flutter)
**Score: 93/100**

**Rationale:**
Provider is Flutter's recommended state management solution, offering the perfect balance of simplicity and capability for this application. Given your established experience with Provider from the AI Rhythm Coach project, you can leverage existing patterns and mental models—zero learning curve means faster development.

Provider's hierarchical approach (context-based state injection) aligns naturally with Flutter's widget tree, making state flow intuitive and debuggable. For a chat application with projects, threads, and messages, Provider's granular rebuild control ensures only affected widgets re-render when state changes—critical for smooth scrolling and animations.

The pattern is lightweight (minimal boilerplate) yet powerful enough for complex state (authentication, navigation, real-time updates). Provider's ChangeNotifier pattern makes state mutations explicit and traceable, appealing to your QA background's emphasis on predictable behavior. Flutter's DevTools provide excellent Provider inspection during debugging.

**Trade-offs:**
- **Advantages:**
  - Your existing experience from AI Rhythm Coach (zero learning curve)
  - Officially recommended by Flutter team
  - Minimal boilerplate compared to Redux/BLoC
  - Granular rebuild control (only changed widgets re-render)
  - Easy testing (inject mock providers)
  - Excellent DevTools integration for debugging
  - Scales well from simple to complex state
  - ChangeNotifier pattern is explicit and traceable
- **Disadvantages:**
  - Less structured than BLoC (more developer discipline required)
  - No built-in middleware (logging, persistence) unlike Redux
  - Large apps may become complex without strict patterns
  - Boilerplate grows with many providers (but manageable for this app)
- **Best for:** Flutter apps with moderate state complexity, developers who value simplicity and directness

**Consistency Check:**
Provider is Flutter-native solution—perfect integration. Works seamlessly with async HTTP calls (Dio) and SSE streams. No conflicts with backend technologies. Aligns with your established patterns from existing projects.

### Alternatives Considered

#### BLoC (Business Logic Component)
**Score: 78/100**
**Brief rationale:** Highly structured pattern with clear separation of business logic and UI. Scored lower because steeper learning curve, more boilerplate than Provider, and overkill for this app's complexity. BLoC shines in large teams needing enforced patterns, less necessary for solo developer.
**When to choose:** If you're building a very complex app with many interconnected states or need strict architectural patterns for team consistency.

#### Riverpod (Provider 2.0)
**Score: 85/100**
**Brief rationale:** Modern evolution of Provider with compile-time safety and better scoping. Scored slightly lower only because it's a new learning curve versus your existing Provider knowledge. Riverpod is technically superior but the migration cost isn't justified for MVP.
**When to choose:** If starting a new Flutter project from scratch with no Provider experience, or if you outgrow Provider's limitations.

#### Redux
**Score: 65/100**
**Brief rationale:** Predictable state management with time-travel debugging. Scored lower because massive boilerplate (actions, reducers, middleware), overkill for this app size, and primarily a web pattern (less Flutter-idiomatic). Better for giant apps with complex state interactions.
**When to choose:** If you're familiar with Redux from web development or building a complex app with intricate state flows requiring time-travel debugging.

---

## Authentication

### Recommended: OAuth 2.0 (Google + Microsoft)
**Score: 93/100**

**Rationale:**
Social login via OAuth 2.0 is the optimal authentication strategy for business analyst users who typically have work accounts with Google Workspace or Microsoft 365. This eliminates password management burden for both users (one less password to remember) and you as developer (no password reset flows, strength requirements, breach monitoring).

OAuth is enterprise-friendly—BAs can sign in with their existing work credentials, making adoption frictionless. Implementation is straightforward with mature libraries (authlib for Python backend, flutter_web_auth for Flutter). Both providers offer generous free tiers and reliable uptime.

From a security perspective, OAuth delegates authentication to providers with vastly more resources for security than a solo developer can provide. You handle authorization (who can access what) while leaving authentication (who are you) to Google/Microsoft. This reduces your security liability and regulatory burden.

**Trade-offs:**
- **Advantages:**
  - No password management (reset flows, strength requirements, breach monitoring)
  - Users leverage existing work credentials (frictionless for BAs)
  - Enterprise-friendly for corporate adoption
  - Delegated security to providers with massive security teams
  - Mature libraries and well-documented flows
  - Free tier with generous limits
  - High reliability (Google/Microsoft uptime)
  - Reduces regulatory burden (no password storage)
- **Disadvantages:**
  - Dependency on third-party providers (outage impacts login)
  - Users without Google/Microsoft accounts excluded (rare for target BAs)
  - OAuth flow slightly more complex than traditional password
  - Privacy-conscious users may hesitate sharing provider data
  - Requires network connection to authenticate (no offline login)
- **Best for:** B2B applications targeting enterprise users, developers who want to minimize security liability

**Consistency Check:**
OAuth flows integrate cleanly with FastAPI backend (authlib library). Flutter has flutter_web_auth for OAuth redirects. JWT tokens for session management post-authentication. No conflicts with other stack choices.

### Alternatives Considered

#### Email/Password Authentication
**Score: 75/100**
**Brief rationale:** Simple, self-contained authentication under your full control. Scored lower because requires password reset flows, strength validation, breach monitoring (Have I Been Pwned), and bcrypt hashing—all development time. Increases security liability. Good fallback if users demand it.
**When to choose:** If target users are privacy-conscious individuals (not enterprise BAs) who don't want social login, or as secondary option alongside OAuth.

#### Magic Link (Passwordless Email)
**Score: 70/100**
**Brief rationale:** User-friendly passwordless flow via email links. Scored lower because requires email infrastructure (SendGrid, Mailgun costs), users must have reliable email access, and phishing risk (malicious links). Less enterprise-appropriate than OAuth for BAs.
**When to choose:** If you want passwordless authentication but target users don't have Google/Microsoft accounts.

#### SAML/Enterprise SSO
**Score: 85/100**
**Brief rationale:** Enterprise standard for large organizations. Scored lower only because overkill for MVP—complex implementation, needed only when selling to enterprises with SSO mandates. Defer to post-MVP when targeting Fortune 500.
**When to choose:** When targeting large enterprises that require SAML for security compliance and won't adopt without it.

---

## Hosting & Deployment

### Recommended: Railway or Render (Platform-as-a-Service)
**Score: 94/100**

**Rationale:**
PaaS platforms like Railway or Render are optimal for solo developer MVP velocity. Git-based deployment means `git push main` triggers automatic build, test, and deploy—zero manual steps. Automatic HTTPS with Let's Encrypt, managed SSL renewal, and built-in health checks eliminate operational burden that would consume development time.

For a solo developer without DevOps expertise, PaaS abstracts infrastructure complexity while providing enough control (environment variables, scaling, logs). The flat monthly pricing ($5-25 depending on resources) is predictable and affordable for MVP validation. When you need to scale, adjust sliders in dashboard—no server provisioning or load balancer configuration.

Both Railway and Render support persistent volumes for SQLite file storage, automatic backups, and one-click rollbacks. Built-in monitoring dashboards provide basic metrics without configuring external services. For an AI-heavy app where development time should focus on features (not infrastructure), PaaS maximizes productivity.

**Trade-offs:**
- **Advantages:**
  - Zero-configuration deployment (git push → live)
  - Automatic HTTPS with managed SSL certificates
  - Built-in health checks and auto-restart
  - Simple scaling via dashboard sliders
  - Persistent volumes for SQLite database
  - Automated daily backups
  - One-click rollback on bad deploys
  - Built-in monitoring and log aggregation
  - Predictable flat monthly pricing
  - No DevOps expertise required
- **Disadvantages:**
  - Less control than AWS/GCP (can't optimize every setting)
  - Limited to platform's available services
  - Vendor lock-in (some lock-in, but migration is feasible)
  - Pricing less efficient at very high scale (>100K users)
  - Regional availability may be limited
- **Best for:** Solo developers and small teams prioritizing speed over control, MVP through Beta phases

**Consistency Check:**
Railway/Render support Python FastAPI deployment with Uvicorn. Git-based deployment works with any repository. Environment variable management for secrets. No conflicts with technology stack. Aligns perfectly with solo developer constraints.

### Alternatives Considered

#### AWS/Google Cloud/Azure
**Score: 78/100**
**Brief rationale:** Maximum control and optimization, best pricing at very high scale, widest service offerings. Scored lower for MVP because significant DevOps complexity (VPC, load balancers, IAM, monitoring)—too much infrastructure overhead for solo developer. Save for post-V1.0 scale.
**When to choose:** When you have 10,000+ active users and cost optimization justifies DevOps time investment, or you need specialized services (ML training, specific regional compliance).

#### Heroku
**Score: 88/100**
**Brief rationale:** Original PaaS, mature platform, very simple deployment. Scored slightly lower than Railway/Render only because Heroku was acquired by Salesforce and free tier eliminated—less generous pricing. Otherwise excellent choice.
**When to choose:** If you already know Heroku or prefer its ecosystem of add-ons.

#### DigitalOcean App Platform
**Score: 85/100**
**Brief rationale:** Simple PaaS with good pricing and DigitalOcean's reliable infrastructure. Scored lower because slightly less polished deployment experience than Railway/Render and fewer managed services. Good middle ground between PaaS and IaaS.
**When to choose:** If you prefer DigitalOcean's ecosystem or want slight more control than pure PaaS.

#### VPS (DigitalOcean Droplet, Linode)
**Score: 60/100**
**Brief rationale:** Full server control, cheapest raw compute. Scored much lower because you manage everything—OS updates, security patches, deployment automation, SSL, monitoring. Too much operational burden for solo developer focused on product. Only if you're an experienced sysadmin.
**When to choose:** If you have strong Linux/DevOps skills and want maximum cost efficiency, or need very specific server configurations.

---

## Communication Pattern (Real-time)

### Recommended: Server-Sent Events (SSE)
**Score: 91/100**

**Rationale:**
SSE is the ideal real-time communication pattern for streaming AI responses from backend to frontend. Unlike WebSockets (bidirectional), SSE is unidirectional (server → client), which perfectly matches this use case—AI generates responses and streams them to users, but users send messages via standard HTTP POST.

SSE's simplicity shines for solo developers: it's built on standard HTTP, requires no special server infrastructure (works on any PaaS), and automatically reconnects on connection drop. The protocol is browser-native (EventSource API) and Flutter has excellent SSE packages. Claude API's streaming responses map naturally to SSE's event-based model—each token chunk is an SSE event.

For PaaS deployment, SSE is more reliable than WebSockets because it doesn't require sticky sessions or WebSocket-aware load balancers. The unidirectional nature reduces complexity—no need to handle bidirectional message synchronization or complex state management.

**Trade-offs:**
- **Advantages:**
  - Built on standard HTTP (works everywhere, PaaS-friendly)
  - Automatic reconnection on connection drop
  - Simpler than WebSockets (unidirectional = less complexity)
  - Browser-native EventSource API
  - Perfect for AI streaming (Claude API → SSE naturally)
  - No sticky sessions or special load balancing required
  - Easy to test with curl/Postman
  - Lower server resource usage than WebSockets
- **Disadvantages:**
  - Unidirectional only (client can't push to server via SSE)
  - Text-only (binary data requires encoding, not needed here)
  - Some older proxies may interfere (rare in 2024)
  - HTTP/1.1 connection limits (6 per domain, but HTTP/2 fixes this)
- **Best for:** Server-to-client streaming (AI responses, notifications, live updates), applications on standard HTTP infrastructure

**Consistency Check:**
FastAPI has excellent SSE support with async generators. Flutter SSE package (flutter_client_sse) handles EventSource. User messages sent via standard REST POST. Clean separation of concerns. No conflicts with stack.

### Alternatives Considered

#### WebSockets
**Score: 82/100**
**Brief rationale:** Bidirectional real-time communication with full-duplex channels. Scored lower because bidirectional capability is overkill—users send messages via HTTP POST, don't need continuous channel. WebSockets add complexity (connection management, heartbeats) without benefit for this use case. Better for multi-user collaboration or gaming.
**When to choose:** If you need true bidirectional real-time communication (collaborative editing, real-time games, live cursors).

#### HTTP Long Polling
**Score: 65/100**
**Brief rationale:** Older real-time technique where client polls server repeatedly. Scored lower because inefficient (many HTTP requests), higher latency than SSE, and outdated approach. Only advantage is universal compatibility with ancient infrastructure.
**When to choose:** Only if deploying to legacy environments where SSE and WebSockets are blocked by corporate proxies (very rare).

#### gRPC Streaming
**Score: 70/100**
**Brief rationale:** High-performance bidirectional streaming via HTTP/2. Scored lower because Protocol Buffers add complexity, less browser-friendly than SSE, and overkill for this use case. Better for microservice communication than frontend-backend.
**When to choose:** If building microservices architecture with tight performance requirements and binary data streaming.

---

## Document Export

### Recommended: Python Libraries (python-docx + ReportLab/WeasyPrint)
**Score: 87/100**

**Rationale:**
Python-native libraries for document generation provide the best balance of simplicity, control, and cost for MVP. `python-docx` creates Word documents with straightforward API (paragraphs, styles, tables), while `ReportLab` or `WeasyPrint` generate PDFs from HTML/markdown. All libraries run in your backend without external service dependencies or per-export costs.

For a solo developer, these libraries mean artifact export is a pure code problem with no ongoing service costs or API limits. The learning curve is manageable—extensive documentation and Stack Overflow coverage. Output quality is professional (not amateur-looking exports), which matters for business analysts sharing documents with stakeholders.

The Markdown export is trivial (artifacts already stored as markdown), PDF uses WeasyPrint (renders HTML/CSS to PDF), and Word uses python-docx. All three formats from single markdown source with different renderers. No vendor lock-in, predictable behavior, and complete control over formatting.

**Trade-offs:**
- **Advantages:**
  - Zero per-export costs (no API fees)
  - No rate limits or quotas
  - Full control over document formatting and styling
  - Works offline (no external service dependency)
  - Python-native (integrates seamlessly with backend)
  - Extensive documentation and examples
  - Professional output quality
  - Can customize templates per artifact type
- **Disadvantages:**
  - Code-based styling (not WYSIWYG editor)
  - Learning curve for complex layouts
  - PDF rendering can be slow for large documents (seconds vs milliseconds)
  - Memory usage for large document generation
  - You maintain export code (vs SaaS abstracts it)
- **Best for:** Applications needing document generation without ongoing costs, developers who want control over output

**Consistency Check:**
Python libraries integrate perfectly with FastAPI backend. Async export generation prevents blocking other requests. Artifacts stored as markdown (source of truth), rendered on-demand in requested format. No external dependencies or conflicts.

### Alternatives Considered

#### Document Generation API (DocRaptor, PDF.co)
**Score: 72/100**
**Brief rationale:** SaaS for HTML → PDF with professional output and no code complexity. Scored lower because per-export costs add up ($0.01-0.05 per document), rate limits constrain usage, and external dependency (service downtime blocks exports). Good if export quality is critical and you want zero maintenance.
**When to choose:** If document formatting is complex (intricate layouts, charts) and export quality is critical enough to justify per-document costs.

#### LibreOffice Headless
**Score: 65/100**
**Brief rationale:** LibreOffice in server mode can generate documents programmatically. Scored lower because significant resource overhead (heavyweight process), complex setup, and brittle—updates can break generation. Overkill for this use case.
**When to choose:** If you need perfect Microsoft Office compatibility or very complex document features (pivot tables, macros).

#### LaTeX for PDF Generation
**Score: 60/100**
**Brief rationale:** Excellent typography and professional academic documents. Scored lower because steep learning curve (LaTeX syntax), overkill for business documents, and slow compilation. Only justified for mathematical or scientific documents.
**When to choose:** If generating documents with extensive mathematical notation or requiring academic publication standards.

---

## Error Tracking

### Recommended: Sentry (Free Tier)
**Score: 92/100**

**Rationale:**
Sentry provides production-grade error tracking without cost for MVP-scale usage (free tier: 5,000 events/month). The platform automatically captures unhandled exceptions, groups similar errors, and provides full stack traces with context—essential for solo developer debugging production issues remotely.

Sentry's integrations with FastAPI (Python SDK) and Flutter (sentry_flutter package) mean errors from both frontend and backend appear in single dashboard. Source maps link errors to exact code lines. The slack/email alerting means you learn about critical errors immediately, not from user complaints.

For a QA professional like yourself, Sentry's structured error data (breadcrumbs, user context, tags) provides excellent debugging information. The release tracking correlates errors with specific deployments, making it easy to identify if a deployment introduced new bugs. This supports your systematic testing approach.

**Trade-offs:**
- **Advantages:**
  - Free tier adequate for MVP (5,000 errors/month)
  - Both backend (Python) and frontend (Flutter) SDKs
  - Automatic error grouping and deduplication
  - Full stack traces with source code context
  - Alert on new/frequent errors (Slack, email)
  - Release tracking correlates errors with deployments
  - Breadcrumbs show events leading to error
  - Performance monitoring included (free tier has limits)
  - Excellent documentation and setup guides
- **Disadvantages:**
  - Free tier limits (5,000 events/month, may need paid if hit)
  - Complex UI can be overwhelming initially
  - Source maps required for minified code (extra setup)
  - Privacy considerations (error data sent to third party)
- **Best for:** Production applications needing proactive error monitoring, solo developers who can't manually test all scenarios

**Consistency Check:**
Sentry has official SDKs for both Python (FastAPI) and Flutter. No conflicts with other technologies. Integrates via simple SDK initialization. Complements (doesn't replace) application logging.

### Alternatives Considered

#### Rollbar
**Score: 88/100**
**Brief rationale:** Similar to Sentry with good error tracking and grouping. Scored slightly lower only because Sentry has larger market share (more tutorials, community), better Flutter support, and more generous free tier. Rollbar is excellent alternative if you prefer its UI.
**When to choose:** If you find Rollbar's UI more intuitive or already use it for other projects.

#### LogRocket
**Score: 75/100**
**Brief rationale:** Session replay in addition to error tracking—see exactly what user did before error. Scored lower because primarily web-focused (less mobile support), more expensive (less generous free tier), and heavier client-side SDK. Overkill for MVP.
**When to choose:** If debugging complex UI interactions and need to replay exact user sessions.

#### Self-Hosted (Sentry Open Source)
**Score: 55/100**
**Brief rationale:** Full control and privacy by hosting your own Sentry instance. Scored much lower because operational burden (server maintenance, updates, scaling) is significant for solo developer. SaaS free tier is simpler.
**When to choose:** Only if you have strict data privacy requirements preventing use of third-party SaaS.

---

## Overall Stack Consistency Analysis

### Technology Synergies

**Flutter + FastAPI:**
- Clean separation: Flutter (presentation) and FastAPI (business logic)
- Standard HTTP/SSE communication (language-agnostic)
- Both support async/await patterns naturally
- FastAPI auto-generates OpenAPI docs that inform Flutter API client development

**Python + Claude Agent SDK:**
- Native integration (SDK built for Python first)
- Python's AI ecosystem (pandas, numpy) available for future features
- Async Python matches async FastAPI perfectly
- Type hints in both (Pydantic models) ensure contract consistency

**SQLite + SQLAlchemy:**
- ORM abstracts database specifics
- Single file simplifies PaaS deployment
- FTS5 extension for document search built-in
- Clear migration to PostgreSQL when needed (change connection string)

**OAuth + JWT:**
- OAuth for initial authentication (provider handles credentials)
- JWT for session management (stateless API)
- Standard patterns with excellent library support
- Secure storage in Flutter (flutter_secure_storage)

**PaaS + Git:**
- Git-based deployment workflow (git push → deploy)
- Environment variables for secrets (12-factor app)
- No manual server configuration required
- Automatic SSL and health checks

### Potential Friction Points

**Flutter Web Performance:**
- Flutter web can be slower than React for very complex UIs
- Mitigation: Keep UI reasonably simple, focus on mobile-first design
- Impact: Low—this app's UI isn't rendering-intensive

**SQLite Write Concurrency:**
- Single writer limitation could bottleneck at scale
- Mitigation: Plan PostgreSQL migration when metrics show need
- Impact: Medium—acceptable for MVP/Beta, requires attention for V1.0

**AI Token Costs:**
- Agent SDK uses more tokens than minimal API calls
- Mitigation: Monitor usage, optimize prompts, implement caching
- Impact: High—largest operational cost, requires active management

**SSE Browser Limits:**
- HTTP/1.1 limits concurrent SSE connections per domain
- Mitigation: Use HTTP/2 (automatic with modern hosting), or connection pooling
- Impact: Low—rare edge case, only if user opens many threads simultaneously

### Overall Simplicity Score: 88/100

**Rationale:** The stack maximizes simplicity by choosing technologies that integrate naturally (Python ecosystem for AI, Flutter for cross-platform, PaaS for deployment) while avoiding over-engineering (no microservices, no Kubernetes, no complex state management). Each component choice reduces complexity in another area (PaaS eliminates DevOps, Agent SDK eliminates tool loop code, SQLite eliminates database ops).

Solo developer feasibility is high—every technology has excellent documentation, community support, and clear tutorials. The learning curve is minimized by leveraging your existing Flutter/Provider experience. Where new technologies are introduced (FastAPI, Claude Agent SDK), they're chosen for their explicit goal of developer productivity and clear error messages.

### Solo Developer Feasibility: High

**Confidence Assessment:**
- **Can build MVP in 8-10 weeks:** YES
- **Can maintain in production:** YES
- **Can debug issues remotely:** YES (Sentry, logs)
- **Can scale to Beta:** YES (PaaS scaling, SQLite adequate)
- **Can migrate to V1.0:** YES (PostgreSQL migration path clear)

**Risk Factors:**
- AI cost management requires vigilance (monitor token usage)
- SQLite migration timing must be data-driven (not "gut feel")
- OAuth dependency means provider outages affect login (low risk, high reliability)

Overall, this stack is optimized for solo developer velocity while maintaining production quality and clear scaling paths.

---

## Explicit Recommendation

After evaluating all options, the recommended technology stack for Business Analyst Assistant is:

**Frontend:** Flutter (Score: 95/100)
**Backend:** FastAPI (Python) (Score: 92/100)
**Database:** SQLite → PostgreSQL (Score: 88/100)
**AI Integration:** Claude Agent SDK - Approach 2 (Score: 90/100)
**State Management:** Provider (Score: 93/100)
**Authentication:** OAuth 2.0 (Google + Microsoft) (Score: 93/100)
**Hosting:** Railway or Render (PaaS) (Score: 94/100)
**Real-time Communication:** Server-Sent Events (Score: 91/100)
**Document Export:** Python Libraries (Score: 87/100)
**Error Tracking:** Sentry (Score: 92/100)

**Overall Stack Score: 91/100**

### Rationale for This Combination

This specific technology combination is optimal for Business Analyst Assistant because:

1. **Leverages Your Experience:** Flutter and Provider match your existing skillset from AI Rhythm Coach, eliminating learning curves where they don't add value.

2. **AI-First Architecture:** Python backend with Claude Agent SDK provides the best integration for AI-heavy workload. Python dominates AI ecosystem, and Agent SDK handles complex tool usage patterns you'd otherwise implement manually.

3. **Solo Developer Optimized:** Every choice minimizes operational burden—PaaS deployment, zero-config database, social login (no password reset flows), managed error tracking. Development time focuses on product features, not infrastructure.

4. **Clear Scaling Path:** SQLite → PostgreSQL migration is straightforward with SQLAlchemy ORM. PaaS supports vertical then horizontal scaling. No architectural rewrites needed for Beta → V1.0 transition.

5. **Cost-Effective MVP:** Free/low-cost options for everything except AI API. Total monthly MVP cost ~$100, sustainable for validation phase while absorbing costs.

6. **Cross-Platform Reality:** Flutter delivers genuine "write once, run everywhere" for web/Android/iOS. Not a compromise—native performance with single codebase maintenance.

7. **Production-Grade from Start:** Choices like OAuth, encrypted database, Sentry error tracking mean MVP is production-ready, not throwaway prototype. You can scale the same codebase rather than rewriting.

8. **Alignment with Vision:** Agent SDK with autonomous tool selection matches your /business-analyst skill concept. AI proactively searches documents and generates artifacts—exactly the experience you described.

### Technical Debt Accepted

**SQLite in Production:**
- **Debt:** Limited concurrent writes, no horizontal scaling
- **Payback:** Migrate to PostgreSQL when metrics show >500 concurrent users or slow queries
- **Timeline:** Likely Beta phase based on growth projections
- **Effort:** Low (ORM makes migration mostly configuration)

**Agent SDK Token Usage:**
- **Debt:** Higher AI costs than minimal API implementation
- **Payback:** Monitor token usage, optimize prompts, implement caching if costs exceed budget
- **Timeline:** Ongoing during MVP, optimize based on usage data
- **Effort:** Medium (requires prompt engineering and usage analysis)

**Text-Only Document Upload:**
- **Debt:** Users can't upload PDF/Word directly, must copy-paste text
- **Payback:** Add PDF/Word parsing when user feedback indicates high demand
- **Timeline:** Beta or V1.0 based on user requests
- **Effort:** Medium (integrate PyPDF2/python-docx parsers)

**No Deletion/Editing:**
- **Debt:** Users can't delete projects or edit messages in MVP
- **Payback:** Add CRUD operations when user feedback requests it
- **Timeline:** Beta phase
- **Effort:** Low (standard CRUD implementation)

This technical debt is consciously accepted to maximize MVP development velocity. All debt items have clear payback paths and known effort estimates.

### Success Criteria for This Stack

**Development Velocity:**
- MVP buildable in 8-10 weeks by solo developer
- New features deployable in hours (git push → live)
- Bug fixes don't require multi-service coordination

**Operational Simplicity:**
- No manual infrastructure management required
- Deployment via git push (no complex CI/CD pipelines)
- Monitoring via built-in dashboards + Sentry alerts

**User Experience:**
- Cross-device access (web, mobile) from single codebase
- Real-time AI streaming responses (<2s first chunk)
- Professional document exports (Word, PDF, Markdown)

**Cost Management:**
- MVP phase: <$150/month total operational cost
- Predictable scaling costs (no surprise bills)
- Token usage monitoring prevents runaway AI costs

**Scalability:**
- Handles 50-200 concurrent users in Beta without changes
- Clear migration path (SQLite → PostgreSQL) for growth
- PaaS autoscaling supports traffic spikes

This technology stack delivers on all success criteria while maintaining solo developer feasibility.

---

## Document Maintenance

**Version:** 1.0
**Last Updated:** 2026-01-17
**Next Review:** After MVP launch (user feedback may inform technology adjustments)

**Update Triggers:**
- Major version updates to key dependencies (Flutter, FastAPI, Claude SDK)
- Technology choices proving problematic in practice (e.g., SQLite bottleneck earlier than expected)
- New technologies emerging that significantly improve stack (evaluate quarterly)
- User scale requiring migration (SQLite → PostgreSQL threshold reached)
