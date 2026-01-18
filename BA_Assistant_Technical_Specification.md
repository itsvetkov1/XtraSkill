# Business Analyst Assistant - Complete Technical Specification

## 1. System Purpose and Goals

Business Analyst Assistant is a hybrid mobile and web application designed to augment business analysts during feature discovery meetings. The system provides AI-powered assistance to explore requirements, identify edge cases, and generate structured business documentation.

**Target Users:** Business analysts working in product development, requirements gathering, and stakeholder management roles.

**Primary Objectives:**
- Enable business analysts to capture rough feature ideas and receive intelligent guidance during discovery
- Automatically search and reference relevant project documentation during conversations
- Generate structured artifacts (user stories, acceptance criteria, requirements documents) on demand
- Maintain organized project contexts with multiple conversation threads per project
- Provide cross-device access for seamless workflow from office to client meetings

**Key Success Metrics:**
- Time reduction in requirement documentation creation
- Improved completeness of requirements (fewer missed edge cases)
- User satisfaction with AI guidance quality
- Adoption rate among target BA users

---

## 2. High-Level Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Flutter Web  │  │Flutter Android│ │  Flutter iOS │      │
│  │   (Browser)  │  │     (APK)     │ │ (TestFlight) │      │
│  └──────┬───────┘  └──────┬────────┘ └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    HTTPS / SSE Streaming                     │
└────────────────────────────┼─────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                            │       API Layer                  │
│                    ┌───────▼────────┐                        │
│                    │  FastAPI Server │                        │
│                    │  (Python 3.11+) │                        │
│                    └───────┬────────┘                        │
│                            │                                  │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │              │
│   ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼─────┐       │
│   │   Auth    │    │   Project   │    │    AI     │       │
│   │  Service  │    │   Service   │    │  Service  │       │
│   └─────┬─────┘    └──────┬──────┘    └─────┬─────┘       │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼──────────────┐
│         │                  │                  │  Data Layer   │
│   ┌─────▼─────┐    ┌──────▼──────┐    ┌─────▼─────┐        │
│   │   OAuth   │    │   SQLite    │    │  Claude   │        │
│   │ Providers │    │  Database   │    │ Agent SDK │        │
│   │(Google/MS)│    │  (Encrypted)│    │   (API)   │        │
│   └───────────┘    └─────────────┘    └───────────┘        │
└──────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. User authenticates via social login (Google/Microsoft)
2. Client requests projects, threads, and documents via REST API
3. User initiates conversation with AI assistant
4. Backend routes to Claude Agent SDK with conversation context
5. AI autonomously searches documents when needed using custom tools
6. Responses stream back to client via Server-Sent Events (SSE)
7. Generated artifacts stored in database and exportable in multiple formats

---

## 3. Major Components

### Frontend Application (Flutter)
**Responsibilities:**
- Cross-platform UI rendering (web, Android, iOS)
- User authentication flow management
- Project and thread navigation
- Real-time chat interface with SSE streaming
- Document upload interface
- Artifact viewing and export functionality
- State management with Provider
- Offline-capable UI (graceful degradation)

**Key Technologies:** Flutter 3.x, Provider, Dio (HTTP client), Flutter SSE

### Backend API Server (FastAPI)
**Responsibilities:**
- RESTful API endpoints for CRUD operations
- OAuth 2.0 authentication flow handling
- JWT token generation and validation
- SSE endpoint for streaming AI responses
- Document storage and retrieval with encryption
- Database connection management
- Rate limiting and error handling
- Request validation and sanitization

**Key Technologies:** FastAPI, SQLAlchemy, python-jose (JWT), cryptography

### AI Service Layer
**Responsibilities:**
- Claude Agent SDK session management
- Custom tool implementations (DocumentSearch, ArtifactGenerator, ThreadSummarizer)
- Conversation context assembly
- Streaming response handling
- Token usage tracking
- Error recovery and retry logic
- Cost monitoring

**Key Technologies:** Claude Agent SDK (Python), Anthropic API

### Database Layer (SQLite)
**Responsibilities:**
- User account data storage
- Project metadata persistence
- Document content storage (encrypted)
- Conversation thread and message history
- Session and authentication token management
- Full-text search capability for documents

**Key Technologies:** SQLite 3.x, SQLAlchemy ORM, SQLCipher (encryption extension)

### Authentication Service
**Responsibilities:**
- OAuth 2.0 integration with Google and Microsoft
- User profile creation and management
- JWT token issuance and refresh
- Session management
- Secure credential storage

**Key Technologies:** OAuth 2.0, JWT, python-jose, authlib

---

## 4. Key Technology Choices

### Frontend Framework: Flutter
**Score: 95/100**
**Rationale:** Flutter provides single codebase for web, Android, and iOS with your existing experience from AI Rhythm Coach project. Excellent hot reload for rapid development, strong Material Design support, and native performance. Provider state management aligns with your established patterns.
**Trade-off:** Larger app bundle size than native, but cross-platform efficiency outweighs this for solo development.

### Backend Framework: FastAPI (Python)
**Score: 92/100**
**Rationale:** Python backend enables seamless Claude Agent SDK integration. FastAPI provides async support for SSE streaming, automatic API documentation, and excellent developer experience. Type hints reduce bugs. Native async/await perfect for AI streaming responses.
**Trade-off:** Slightly slower raw performance than Go/Rust, but Python ecosystem and AI library support make this ideal for AI-heavy applications.

### Database: SQLite
**Score: 88/100**
**Rationale:** SQLite on server simplifies MVP deployment with zero-configuration database. File-based storage works well with PaaS hosting. Built-in full-text search (FTS5) for document keyword search. Clear migration path to PostgreSQL when scale demands it.
**Trade-off:** Limited concurrent write performance and no horizontal scaling, but acceptable for MVP user loads.

### AI Integration: Claude Agent SDK (Approach 2)
**Score: 90/100**
**Rationale:** Agent SDK handles tool execution complexity autonomously. Single code path simplifies maintenance. Natural fit with your /business-analyst skill concept. AI decides when to search documents vs respond directly. Consistent behavior across all interactions.
**Trade-off:** Higher API costs than manual tool loops, but development speed and behavioral consistency justify this for MVP.

### Authentication: Social Login (Google/Microsoft OAuth 2.0)
**Score: 93/100**
**Rationale:** Enterprise-friendly authentication for BA professionals. Eliminates password management burden. Faster signup reduces friction. Well-supported libraries in Python and Flutter.
**Trade-off:** Dependency on third-party providers, but OAuth fallback patterns mitigate risk.

### Hosting: Platform-as-a-Service (Railway/Render)
**Score: 94/100**
**Rationale:** Zero-configuration deployment perfect for solo developer. Git-based continuous deployment. Automatic HTTPS. Managed infrastructure reduces operational burden. Simple scaling when needed.
**Trade-off:** Less control than AWS/GCP, but operational simplicity critical for MVP focus.

### Communication Pattern: Server-Sent Events (SSE)
**Score: 91/100**
**Rationale:** SSE provides real-time streaming for AI responses with simpler implementation than WebSockets. Works naturally with Claude API streaming. Compatible with PaaS hosting. One-directional flow perfect for AI → user updates.
**Trade-off:** No bidirectional channel, but not needed for this use case.

---

## 5. Data Flow

### User Authentication Flow
1. User opens app, sees login screen
2. User selects Google or Microsoft login
3. App redirects to OAuth provider
4. User authorizes application
5. OAuth provider redirects back with authorization code
6. Backend exchanges code for access token
7. Backend retrieves user profile from OAuth provider
8. Backend creates/updates user record in database
9. Backend generates JWT token
10. Frontend stores JWT in secure storage
11. App navigates to projects dashboard

### Document Upload and Storage Flow
1. User selects project and initiates document upload
2. Frontend reads text file content
3. Frontend sends POST request with document data and project ID
4. Backend validates JWT token and project ownership
5. Backend encrypts document content using encryption key
6. Backend stores encrypted document in SQLite
7. Backend indexes document content in FTS5 for search
8. Backend returns document metadata to frontend
9. Frontend updates UI with new document in project list

### AI Conversation Flow (with Document Search)
1. User types message in conversation thread
2. Frontend sends message via POST to `/threads/{id}/messages`
3. Backend creates message record in database
4. Backend initiates Agent SDK session with:
   - Conversation history from database
   - Project context (project ID, available documents list)
   - Custom tools: DocumentSearch, ArtifactGenerator, ThreadSummarizer
5. Agent SDK sends message to Claude API with tools available
6. Claude processes message and decides whether to:
   - Respond directly (conversational guidance)
   - Call DocumentSearch tool (retrieves relevant document chunks)
   - Call ArtifactGenerator tool (creates structured document)
7. If tool called, backend executes tool logic:
   - DocumentSearch: Queries SQLite FTS5 index for keywords, returns top N matches
   - ArtifactGenerator: Formats AI output into specified document structure
   - ThreadSummarizer: Analyzes conversation and generates brief summary
8. Tool results sent back to Claude API
9. Claude generates final response incorporating tool results
10. Backend streams response chunks via SSE to frontend
11. Frontend displays streamed text in real-time chat interface
12. On completion, backend saves AI response to database
13. If artifact generated, backend saves artifact with export metadata

### Artifact Export Flow
1. User clicks export button on generated artifact
2. Frontend displays format options (Markdown, PDF, Word)
3. User selects format
4. Frontend sends GET request to `/artifacts/{id}/export?format=pdf`
5. Backend retrieves artifact content from database
6. Backend converts content to requested format:
   - Markdown: Raw text with markdown formatting
   - PDF: Uses reportlab or weasyprint for conversion
   - Word: Uses python-docx for .docx generation
7. Backend returns file as downloadable response
8. Frontend triggers download/save dialog
9. User saves file to local device

### Cross-Device Sync Flow
1. User logs in from different device
2. Backend validates JWT token
3. Frontend requests projects list via GET `/projects`
4. Backend queries SQLite for user's projects
5. Frontend receives and displays projects
6. User opens specific project
7. Frontend requests threads for project via GET `/projects/{id}/threads`
8. Backend retrieves threads with AI-generated summaries
9. Frontend displays threads as cards with summaries
10. User selects thread to continue conversation
11. Full conversation history loads from backend
12. User continues conversation seamlessly from new device

---

## 6. Integration Points

### Google OAuth 2.0
**Purpose:** User authentication via Google accounts
**Integration:** OAuth 2.0 authorization code flow via Google Identity Platform
**Configuration:** OAuth client ID and secret from Google Cloud Console
**Scope:** `openid email profile`

### Microsoft OAuth 2.0
**Purpose:** User authentication via Microsoft/Azure AD accounts
**Integration:** OAuth 2.0 authorization code flow via Microsoft Identity Platform
**Configuration:** Application (client) ID and secret from Azure Portal
**Scope:** `openid email profile User.Read`

### Anthropic Claude API
**Purpose:** AI-powered conversation and artifact generation
**Integration:** Claude Agent SDK (Python) with custom tools
**Configuration:** Anthropic API key from platform.anthropic.com
**Model:** Claude Sonnet 4.5 (cost-performance balance)
**Rate Limits:** Monitor and respect Anthropic tier limits

### PaaS Hosting Platform (Railway/Render)
**Purpose:** Backend and database hosting
**Integration:** Git-based deployment from repository
**Configuration:** Environment variables via platform dashboard
**Services:** Web service (FastAPI) + SQLite database file

---

## 7. Deployment Approach

### Platform
Railway or Render for Platform-as-a-Service deployment

### Strategy
- **Git-Based CD:** Push to `main` branch triggers automatic production deployment
- **Environment Separation:** Separate services for development, staging, and production
- **Database Persistence:** SQLite file stored in persistent volume mounted to container
- **Secrets Management:** Environment variables managed via platform dashboard
- **HTTPS:** Automatic SSL certificate provisioning and renewal

### Environments

**Development:**
- Local FastAPI server (`uvicorn main:app --reload`)
- Local SQLite database file
- Flutter hot reload for frontend
- Mock OAuth for faster iteration (optional)

**Staging:**
- Railway/Render staging service
- Separate SQLite database
- Test OAuth credentials
- Limited to internal testing

**Production:**
- Railway/Render production service
- Production SQLite database with automated backups
- Production OAuth credentials
- Monitoring and logging enabled
- Rate limiting enforced

---

## 8. Detailed Component Specifications

### Frontend Application (Flutter)

**Interface:**
```dart
// Main state providers
ProjectProvider: Manages projects list and current project
ThreadProvider: Manages conversation threads
MessageProvider: Handles message sending and SSE streaming
DocumentProvider: Handles document uploads and listing
AuthProvider: Manages authentication state and token refresh

// Key screens
- LoginScreen: OAuth provider selection and redirect handling
- ProjectListScreen: Card-based project display
- ProjectDetailScreen: Document list + thread list for selected project
- ThreadScreen: Chat interface with streaming AI responses
- ArtifactViewScreen: Formatted artifact display with export options
```

**Internal Logic:**
- Provider pattern for state management across app
- Dio HTTP client with interceptors for JWT token attachment
- SSE client listens for streaming responses on active thread
- Secure storage (flutter_secure_storage) for JWT persistence
- Navigation using Flutter Navigator 2.0
- Material Design 3 components for consistent UI

**Error Handling:**
- Network errors: Display retry button with error message
- Authentication errors: Redirect to login screen
- Validation errors: Display inline form validation
- SSE connection lost: Show "reconnecting" indicator, auto-retry
- Document upload errors: Show error toast with details

**Performance Considerations:**
- Lazy loading for project and thread lists (paginate on scroll)
- Message virtualization for long conversation threads
- Image caching for user avatars
- Debounce text input for search functionality
- Background SSE connection management to prevent battery drain

**Security Considerations:**
- JWT tokens stored in secure encrypted storage
- HTTPS enforced for all API calls
- OAuth redirect URI validation
- No sensitive data in logs or error messages
- Certificate pinning for production builds (optional enhancement)

### Backend API Server (FastAPI)

**Interface:**
```python
# Authentication endpoints
POST /auth/oauth/google - Initiate Google OAuth flow
POST /auth/oauth/microsoft - Initiate Microsoft OAuth flow
GET /auth/callback - OAuth callback handler
POST /auth/refresh - Refresh JWT token

# Project endpoints
GET /projects - List user's projects
POST /projects - Create new project
GET /projects/{id} - Get project details
GET /projects/{id}/documents - List project documents

# Document endpoints
POST /projects/{id}/documents - Upload document (text content)
GET /documents/{id} - Get document content

# Thread endpoints
GET /projects/{id}/threads - List threads for project
POST /projects/{id}/threads - Create new thread
GET /threads/{id} - Get thread details
GET /threads/{id}/messages - Get thread message history

# Message endpoints
POST /threads/{id}/messages - Send user message
GET /threads/{id}/stream - SSE endpoint for AI responses

# Artifact endpoints
GET /artifacts/{id} - Get artifact details
GET /artifacts/{id}/export - Export artifact (format query param)
```

**Internal Logic:**
- Dependency injection for database sessions
- Middleware chain: CORS → authentication → rate limiting → request logging
- OAuth flow: state parameter for CSRF protection, token exchange, user profile retrieval
- JWT generation: HS256 algorithm, 7-day expiration, refresh token support
- SSE streaming: async generator yields chunks from Agent SDK
- Document encryption: Fernet symmetric encryption with environment-stored key
- Database transactions for multi-step operations

**Error Handling:**
- HTTPException with appropriate status codes
- Exception handlers for specific error types (SQLAlchemy, OAuth, validation)
- Structured error responses: `{"error": "error_code", "message": "user message", "details": {}}`
- Error logging with context (user ID, request ID, timestamp)
- Rollback transactions on errors
- Graceful degradation for AI service failures

**Performance Considerations:**
- Async/await throughout for non-blocking I/O
- Database connection pooling with SQLAlchemy
- Response compression (gzip) for large payloads
- ETag headers for cacheable resources
- Background tasks for non-critical operations (analytics, logging)
- Query optimization with appropriate indexes

**Security Considerations:**
- JWT validation on protected routes
- CORS restricted to frontend origins
- Rate limiting per user/IP (100 requests/minute)
- Input validation with Pydantic models
- SQL injection prevention via ORM (no raw SQL)
- Secrets loaded from environment variables only
- No stack traces exposed to clients in production

### AI Service Layer

**Interface:**
```python
class AIService:
    async def process_message(
        user_id: str,
        project_id: str,
        thread_id: str,
        message: str,
        conversation_history: List[Message]
    ) -> AsyncGenerator[str, None]:
        """
        Process user message and stream AI response.
        Yields response chunks as they're generated.
        """

    def create_tools(project_id: str) -> List[Tool]:
        """Create Agent SDK tools with project context."""
```

**Internal Logic:**
- Initialize Agent SDK session with conversation history
- Create custom tools bound to current project:
  - **DocumentSearch:** Queries SQLite FTS5 for project documents, returns top 5 matches
  - **ArtifactGenerator:** Formats AI output into structured document (user story, acceptance criteria, etc.)
  - **ThreadSummarizer:** Analyzes full conversation and generates 2-3 sentence summary
- Stream response chunks from Claude API
- Track token usage per request
- Save tool calls and results to database for debugging

**Error Handling:**
- API errors: Exponential backoff retry (3 attempts)
- Rate limit errors: Return 429 with retry-after header
- Timeout errors: Return partial response with error indicator
- Invalid tool calls: Log error, continue without tool result
- Network errors: Save conversation state, allow user retry

**Performance Considerations:**
- Reuse Agent SDK sessions when possible
- Stream responses immediately (don't wait for completion)
- Limit conversation history to last 20 messages to control token usage
- Cache document search results for identical queries (5-minute TTL)

**Security Considerations:**
- Validate project ownership before loading documents
- Sanitize tool outputs before sending to frontend
- No user data in Claude API prompts beyond conversation context
- Monitor for prompt injection attempts in user messages

### Database Layer

**Interface:**
```python
# SQLAlchemy ORM models
User: User accounts and OAuth profiles
Project: Project metadata and owner
Document: Document content (encrypted) and metadata
Thread: Conversation threads within projects
Message: Individual messages in threads
Artifact: Generated artifacts linked to messages
Session: User sessions and JWT refresh tokens
```

**Internal Logic:**
- SQLite with SQLCipher extension for encryption at rest
- SQLAlchemy ORM for all database operations
- FTS5 virtual table for document full-text search
- Alembic for database migrations
- Automatic timestamp fields (created_at, updated_at)
- Soft deletes (deleted_at) for audit trail (post-MVP)

**Error Handling:**
- Integrity errors: Return 409 conflict with details
- Not found errors: Return 404 with clear message
- Connection errors: Retry with exponential backoff
- Lock errors: Retry transaction up to 3 times
- Disk full errors: Return 507 insufficient storage

**Performance Considerations:**
- Indexes on foreign keys and frequently queried fields
- Connection pooling with 10 max connections
- Query optimization: select only needed columns, use joins efficiently
- FTS5 index optimization for document search
- VACUUM on schedule to reclaim space

**Security Considerations:**
- Database file encrypted with SQLCipher
- Connection string includes encryption key from environment
- No direct SQL execution (ORM only)
- Row-level security via application logic (user ID filtering)
- Regular automated backups to encrypted storage

---

## 9. API Contracts and Interfaces

### Authentication API

#### POST /auth/oauth/google
**Purpose:** Initiate Google OAuth flow
**Request:**
```json
{
  "redirect_uri": "string"
}
```
**Response (200):**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```
**Errors:**
- 400: Invalid redirect URI

#### POST /auth/oauth/microsoft
**Purpose:** Initiate Microsoft OAuth flow
**Request:**
```json
{
  "redirect_uri": "string"
}
```
**Response (200):**
```json
{
  "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?..."
}
```
**Errors:**
- 400: Invalid redirect URI

#### GET /auth/callback
**Purpose:** OAuth callback handler
**Query Parameters:**
- `code`: Authorization code from OAuth provider
- `state`: CSRF protection state parameter
- `provider`: "google" or "microsoft"

**Response (302):**
Redirects to frontend with JWT token in query parameter

**Errors:**
- 400: Invalid authorization code or state
- 500: OAuth provider error

#### POST /auth/refresh
**Purpose:** Refresh JWT token
**Request:**
```json
{
  "refresh_token": "string"
}
```
**Response (200):**
```json
{
  "access_token": "string",
  "expires_in": 604800
}
```
**Errors:**
- 401: Invalid or expired refresh token

### Project API

#### GET /projects
**Purpose:** List user's projects
**Authentication:** Required (JWT)
**Response (200):**
```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "document_count": 0,
      "thread_count": 0,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```
**Errors:**
- 401: Unauthorized

#### POST /projects
**Purpose:** Create new project
**Authentication:** Required (JWT)
**Request:**
```json
{
  "name": "string",
  "description": "string (optional)"
}
```
**Response (201):**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "document_count": 0,
  "thread_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```
**Errors:**
- 400: Invalid input (name required)
- 401: Unauthorized

#### GET /projects/{id}
**Purpose:** Get project details
**Authentication:** Required (JWT)
**Response (200):**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "document_count": 0,
  "thread_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```
**Errors:**
- 401: Unauthorized
- 403: Forbidden (not project owner)
- 404: Project not found

#### GET /projects/{id}/documents
**Purpose:** List project documents
**Authentication:** Required (JWT)
**Response (200):**
```json
{
  "documents": [
    {
      "id": "uuid",
      "name": "string",
      "size_bytes": 0,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```
**Errors:**
- 401: Unauthorized
- 403: Forbidden
- 404: Project not found

### Document API

#### POST /projects/{id}/documents
**Purpose:** Upload document to project
**Authentication:** Required (JWT)
**Request:**
```json
{
  "name": "string",
  "content": "string (text content)"
}
```
**Response (201):**
```json
{
  "id": "uuid",
  "name": "string",
  "size_bytes": 0,
  "created_at": "2024-01-01T00:00:00Z"
}
```
**Errors:**
- 400: Invalid input (name and content required)
- 401: Unauthorized
- 403: Forbidden
- 404: Project not found
- 413: Content too large (>10MB limit)

#### GET /documents/{id}
**Purpose:** Get document content
**Authentication:** Required (JWT)
**Response (200):**
```json
{
  "id": "uuid",
  "name": "string",
  "content": "string",
  "size_bytes": 0,
  "created_at": "2024-01-01T00:00:00Z"
}
```
**Errors:**
- 401: Unauthorized
- 403: Forbidden
- 404: Document not found

### Thread API

#### GET /projects/{id}/threads
**Purpose:** List threads for project
**Authentication:** Required (JWT)
**Response (200):**
```json
{
  "threads": [
    {
      "id": "uuid",
      "title": "string (AI-generated summary)",
      "message_count": 0,
      "last_message_at": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```
**Errors:**
- 401: Unauthorized
- 403: Forbidden
- 404: Project not found

#### POST /projects/{id}/threads
**Purpose:** Create new thread
**Authentication:** Required (JWT)
**Request:**
```json
{
  "initial_message": "string"
}
```
**Response (201):**
```json
{
  "id": "uuid",
  "title": "string (AI-generated)",
  "message_count": 1,
  "last_message_at": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```
**Errors:**
- 400: Invalid input (initial_message required)
- 401: Unauthorized
- 403: Forbidden
- 404: Project not found

#### GET /threads/{id}
**Purpose:** Get thread details
**Authentication:** Required (JWT)
**Response (200):**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "title": "string",
  "message_count": 0,
  "last_message_at": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```
**Errors:**
- 401: Unauthorized
- 403: Forbidden
- 404: Thread not found

#### GET /threads/{id}/messages
**Purpose:** Get thread message history
**Authentication:** Required (JWT)
**Query Parameters:**
- `limit`: Number of messages (default 50, max 100)
- `offset`: Pagination offset (default 0)

**Response (200):**
```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user | assistant",
      "content": "string",
      "artifacts": [
        {
          "id": "uuid",
          "type": "user_story | acceptance_criteria | requirements_doc",
          "title": "string"
        }
      ],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 0,
  "has_more": false
}
```
**Errors:**
- 401: Unauthorized
- 403: Forbidden
- 404: Thread not found

### Message API

#### POST /threads/{id}/messages
**Purpose:** Send user message to thread
**Authentication:** Required (JWT)
**Request:**
```json
{
  "content": "string"
}
```
**Response (201):**
```json
{
  "message_id": "uuid",
  "stream_url": "/threads/{id}/stream?message_id={message_id}"
}
```
**Errors:**
- 400: Invalid input (content required)
- 401: Unauthorized
- 403: Forbidden
- 404: Thread not found

#### GET /threads/{id}/stream
**Purpose:** SSE endpoint for streaming AI response
**Authentication:** Required (JWT)
**Query Parameters:**
- `message_id`: Message ID from POST /messages response

**Response (200):**
Content-Type: text/event-stream

**Event Stream:**
```
event: start
data: {"message_id": "uuid"}

event: chunk
data: {"content": "partial response text"}

event: tool_call
data: {"tool": "DocumentSearch", "status": "executing"}

event: tool_result
data: {"tool": "DocumentSearch", "result_preview": "Found 3 documents..."}

event: artifact
data: {"artifact_id": "uuid", "type": "user_story", "title": "Feature X"}

event: complete
data: {"message_id": "uuid", "total_tokens": 1500}

event: error
data: {"error": "error_code", "message": "user-friendly message"}
```

**Errors:**
- 401: Unauthorized
- 403: Forbidden
- 404: Thread or message not found

### Artifact API

#### GET /artifacts/{id}
**Purpose:** Get artifact details and content
**Authentication:** Required (JWT)
**Response (200):**
```json
{
  "id": "uuid",
  "type": "user_story | acceptance_criteria | requirements_doc | custom",
  "title": "string",
  "content": "string (formatted markdown)",
  "message_id": "uuid",
  "thread_id": "uuid",
  "created_at": "2024-01-01T00:00:00Z"
}
```
**Errors:**
- 401: Unauthorized
- 403: Forbidden
- 404: Artifact not found

#### GET /artifacts/{id}/export
**Purpose:** Export artifact in specified format
**Authentication:** Required (JWT)
**Query Parameters:**
- `format`: "markdown" | "pdf" | "docx"

**Response (200):**
Content-Type: application/octet-stream (file download)
Content-Disposition: attachment; filename="artifact-{id}.{ext}"

**Errors:**
- 400: Invalid format parameter
- 401: Unauthorized
- 403: Forbidden
- 404: Artifact not found
- 500: Export generation failed

---

## 10. Database Schemas and Data Models

### Users Table

**Table Name:** `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT (UUID) | PRIMARY KEY | User unique identifier |
| email | TEXT | UNIQUE, NOT NULL | User email from OAuth |
| name | TEXT | NOT NULL | Display name from OAuth |
| avatar_url | TEXT | NULL | Profile picture URL |
| oauth_provider | TEXT | NOT NULL | "google" or "microsoft" |
| oauth_id | TEXT | NOT NULL | Provider-specific user ID |
| created_at | TEXT (ISO8601) | NOT NULL | Account creation timestamp |
| updated_at | TEXT (ISO8601) | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_users_email` on `email`
- `idx_users_oauth` on `(oauth_provider, oauth_id)`

**Relationships:**
- One-to-many with `projects`
- One-to-many with `sessions`

### Projects Table

**Table Name:** `projects`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT (UUID) | PRIMARY KEY | Project unique identifier |
| user_id | TEXT (UUID) | FOREIGN KEY (users.id), NOT NULL | Project owner |
| name | TEXT | NOT NULL | Project name |
| description | TEXT | NULL | Optional project description |
| created_at | TEXT (ISO8601) | NOT NULL | Creation timestamp |
| updated_at | TEXT (ISO8601) | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_projects_user` on `user_id`

**Relationships:**
- Many-to-one with `users`
- One-to-many with `documents`
- One-to-many with `threads`

### Documents Table

**Table Name:** `documents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT (UUID) | PRIMARY KEY | Document unique identifier |
| project_id | TEXT (UUID) | FOREIGN KEY (projects.id), NOT NULL | Parent project |
| name | TEXT | NOT NULL | Document filename |
| content_encrypted | BLOB | NOT NULL | Encrypted document content |
| size_bytes | INTEGER | NOT NULL | Original content size |
| created_at | TEXT (ISO8601) | NOT NULL | Upload timestamp |

**Indexes:**
- `idx_documents_project` on `project_id`

**Relationships:**
- Many-to-one with `projects`

**FTS5 Virtual Table:** `documents_fts`
- Columns: `document_id`, `content_plain` (decrypted content for search)
- Synchronized with `documents` table via triggers

### Threads Table

**Table Name:** `threads`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT (UUID) | PRIMARY KEY | Thread unique identifier |
| project_id | TEXT (UUID) | FOREIGN KEY (projects.id), NOT NULL | Parent project |
| title | TEXT | NULL | AI-generated thread summary |
| created_at | TEXT (ISO8601) | NOT NULL | Creation timestamp |
| last_message_at | TEXT (ISO8601) | NOT NULL | Last message timestamp |

**Indexes:**
- `idx_threads_project` on `project_id`
- `idx_threads_last_message` on `last_message_at`

**Relationships:**
- Many-to-one with `projects`
- One-to-many with `messages`

### Messages Table

**Table Name:** `messages`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT (UUID) | PRIMARY KEY | Message unique identifier |
| thread_id | TEXT (UUID) | FOREIGN KEY (threads.id), NOT NULL | Parent thread |
| role | TEXT | NOT NULL | "user" or "assistant" |
| content | TEXT | NOT NULL | Message text content |
| token_count | INTEGER | NULL | Token usage (assistant only) |
| created_at | TEXT (ISO8601) | NOT NULL | Message timestamp |

**Indexes:**
- `idx_messages_thread` on `thread_id`
- `idx_messages_created` on `created_at`

**Relationships:**
- Many-to-one with `threads`
- One-to-many with `artifacts`

### Artifacts Table

**Table Name:** `artifacts`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT (UUID) | PRIMARY KEY | Artifact unique identifier |
| message_id | TEXT (UUID) | FOREIGN KEY (messages.id), NOT NULL | Source message |
| thread_id | TEXT (UUID) | FOREIGN KEY (threads.id), NOT NULL | Parent thread |
| type | TEXT | NOT NULL | Artifact type (user_story, etc.) |
| title | TEXT | NOT NULL | Artifact title |
| content | TEXT | NOT NULL | Formatted artifact content |
| created_at | TEXT (ISO8601) | NOT NULL | Generation timestamp |

**Indexes:**
- `idx_artifacts_message` on `message_id`
- `idx_artifacts_thread` on `thread_id`

**Relationships:**
- Many-to-one with `messages`
- Many-to-one with `threads`

### Sessions Table

**Table Name:** `sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT (UUID) | PRIMARY KEY | Session unique identifier |
| user_id | TEXT (UUID) | FOREIGN KEY (users.id), NOT NULL | Session owner |
| refresh_token | TEXT | UNIQUE, NOT NULL | JWT refresh token |
| expires_at | TEXT (ISO8601) | NOT NULL | Token expiration |
| created_at | TEXT (ISO8601) | NOT NULL | Session start |

**Indexes:**
- `idx_sessions_user` on `user_id`
- `idx_sessions_token` on `refresh_token`
- `idx_sessions_expires` on `expires_at`

**Relationships:**
- Many-to-one with `users`

---

## 11. Authentication and Authorization Flows

### User Registration Flow (OAuth)
1. User opens app and sees login screen
2. User taps "Sign in with Google" or "Sign in with Microsoft"
3. Frontend calls `POST /auth/oauth/{provider}` with redirect URI
4. Backend generates OAuth state parameter (CSRF protection)
5. Backend returns OAuth authorization URL
6. Frontend opens system browser with OAuth URL
7. User authenticates with OAuth provider
8. User grants permission to application
9. OAuth provider redirects to backend callback URL with authorization code
10. Backend validates state parameter
11. Backend exchanges authorization code for access token
12. Backend retrieves user profile from OAuth provider API
13. Backend checks if user exists in database (by oauth_provider + oauth_id)
14. If new user:
    - Create user record with profile data
    - Log new user creation
15. If existing user:
    - Update user record with latest profile data (name, avatar)
16. Backend generates JWT access token (7-day expiration)
17. Backend generates refresh token (30-day expiration)
18. Backend creates session record
19. Backend redirects to frontend deep link with tokens
20. Frontend stores tokens in secure storage
21. Frontend navigates to projects dashboard

### Login Flow (Returning User)
1. User opens app
2. Frontend checks secure storage for JWT token
3. If token exists and not expired:
   - Load user data and navigate to dashboard
4. If token expired but refresh token valid:
   - Call `POST /auth/refresh` with refresh token
   - Receive new access token
   - Store new token and navigate to dashboard
5. If no valid tokens:
   - Show login screen (follow Registration Flow)

### Token Refresh Flow
1. API request fails with 401 Unauthorized
2. Frontend checks if refresh token exists and not expired
3. Frontend calls `POST /auth/refresh` with refresh token
4. Backend validates refresh token against sessions table
5. Backend checks expiration
6. Backend generates new JWT access token
7. Backend returns new token
8. Frontend stores new token
9. Frontend retries original API request with new token
10. If refresh fails, redirect to login screen

### Authorization Middleware
1. Request arrives at protected endpoint
2. Middleware extracts JWT from Authorization header
3. Middleware validates JWT signature
4. Middleware decodes JWT payload (user_id, expiration)
5. Middleware checks expiration timestamp
6. If valid:
   - Attach user_id to request context
   - Continue to endpoint handler
7. If invalid or expired:
   - Return 401 Unauthorized
   - Include WWW-Authenticate header

### Resource Authorization
1. Endpoint handler receives request with user_id in context
2. Handler queries database for requested resource
3. Handler checks resource ownership:
   - Projects: `project.user_id == request.user_id`
   - Threads: `thread.project.user_id == request.user_id`
   - Documents: `document.project.user_id == request.user_id`
   - Artifacts: `artifact.thread.project.user_id == request.user_id`
4. If authorized:
   - Process request and return response
5. If not authorized:
   - Return 403 Forbidden

---

## 12. Error Handling Strategies

### Error Categories

#### Validation Errors (400 Bad Request)
**User-Facing Message:** "Please check your input"
**Log Level:** INFO
**Action:**
- Return specific field errors in response body
- Frontend displays inline validation messages
- No retry needed (user must fix input)

**Example Response:**
```json
{
  "error": "validation_error",
  "message": "Invalid input",
  "details": {
    "name": "Project name is required",
    "content": "Content must not be empty"
  }
}
```

#### Authentication Errors (401 Unauthorized)
**User-Facing Message:** "Please log in again"
**Log Level:** WARNING
**Action:**
- Clear stored tokens
- Redirect to login screen
- Attempt token refresh first if applicable

**Example Response:**
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

#### Authorization Errors (403 Forbidden)
**User-Facing Message:** "You don't have permission to access this"
**Log Level:** WARNING
**Action:**
- Display error message
- Provide "Back" button to previous screen
- Log attempt with user ID and resource ID for security audit

**Example Response:**
```json
{
  "error": "forbidden",
  "message": "Access denied"
}
```

#### Not Found Errors (404 Not Found)
**User-Facing Message:** "Resource not found"
**Log Level:** INFO
**Action:**
- Display friendly "not found" message
- Suggest returning to main screen
- May indicate deleted resource or invalid URL

**Example Response:**
```json
{
  "error": "not_found",
  "message": "Project not found"
}
```

#### Rate Limit Errors (429 Too Many Requests)
**User-Facing Message:** "Too many requests, please wait"
**Log Level:** WARNING
**Action:**
- Display countdown timer until retry allowed
- Include Retry-After header in response
- Frontend automatically retries after timeout

**Example Response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

#### AI Service Errors (502 Bad Gateway)
**User-Facing Message:** "AI service temporarily unavailable"
**Log Level:** ERROR
**Action:**
- Save user message to database (not lost)
- Display error with manual retry button
- Log full error details for debugging
- Alert monitoring system

**Example Response:**
```json
{
  "error": "ai_service_error",
  "message": "Unable to process message, please try again"
}
```

#### Server Errors (500 Internal Server Error)
**User-Facing Message:** "Something went wrong on our end"
**Log Level:** CRITICAL
**Action:**
- Log full stack trace with context
- Alert monitoring system immediately
- Display generic error message (no technical details)
- Provide support contact option

**Example Response:**
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "uuid"
}
```

### Error Logging Strategy

**Structured Log Format:**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "ERROR",
  "error_type": "ai_service_error",
  "message": "Claude API timeout",
  "user_id": "uuid",
  "request_id": "uuid",
  "endpoint": "/threads/{id}/messages",
  "context": {
    "thread_id": "uuid",
    "message_length": 150,
    "token_count": 1200
  },
  "stack_trace": "..."
}
```

**Error Tracking:**
- Use Sentry or similar for error aggregation
- Group errors by type and endpoint
- Track error frequency and user impact
- Alert on error rate spikes

### Frontend Error Handling

**Network Errors:**
- Detect connection loss
- Display "offline" indicator
- Queue messages locally
- Auto-retry when connection restored

**SSE Stream Errors:**
- Detect connection drop mid-stream
- Display "reconnecting..." indicator
- Exponential backoff retry (1s, 2s, 4s, 8s)
- Fallback to polling if SSE repeatedly fails

**UI Error Boundaries:**
- React-style error boundaries catch component errors
- Display fallback UI instead of blank screen
- Log error details for debugging
- Provide "retry" or "go back" actions

---

## 13. Security Considerations

### Authentication Security

**OAuth Implementation:**
- State parameter for CSRF protection on OAuth callback
- PKCE (Proof Key for Code Exchange) for mobile apps
- Validate redirect URI against whitelist
- Secure token storage (flutter_secure_storage with encryption)

**JWT Tokens:**
- HS256 signing algorithm with 256-bit secret key
- Access token expiration: 7 days
- Refresh token expiration: 30 days
- Include issuer, audience, and issued-at claims
- Revoke tokens on logout

**Token Storage:**
- Flutter: flutter_secure_storage (encrypted keychain/keystore)
- Never store in localStorage or SharedPreferences
- Clear tokens on logout or account deletion

### Authorization Security

**Access Control:**
- All protected endpoints require valid JWT
- Resource ownership verified on every request
- User can only access own projects, threads, documents
- No role-based access (single-user per account in MVP)

**API Security:**
- Rate limiting: 100 requests/minute per user
- Request ID tracking for audit trail
- Input validation on all endpoints
- SQL injection prevention via ORM
- No raw SQL queries

### Data Protection

**Encryption at Rest:**
- Document content encrypted with Fernet (AES-128)
- Encryption key stored in environment variable
- Database file encrypted with SQLCipher
- Regular key rotation (quarterly)

**Encryption in Transit:**
- HTTPS enforced for all API communication
- TLS 1.2+ minimum version
- Certificate validation on client
- No plaintext HTTP fallback

**Password Security:**
- No passwords stored (OAuth only)
- If password auth added post-MVP: bcrypt with cost factor 12

### Input Validation

**Backend Validation:**
- Pydantic models for request validation
- Type checking on all inputs
- Length limits on text fields
- File size limits (10MB per document)
- Sanitize user-generated content before storage

**Frontend Validation:**
- Client-side validation for UX (fast feedback)
- Never trust client validation alone
- Whitelist allowed characters for names/titles
- Prevent XSS in displayed content

### API Security

**CORS Configuration:**
- Restrict origins to production frontend domains
- No wildcard (*) origins in production
- Credentials allowed for cookie-based auth (if added)

**Headers:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Content-Security-Policy: restrictive policy
- Strict-Transport-Security: max-age=31536000

**API Keys:**
- Anthropic API key in environment variable only
- Never expose in logs or error messages
- Rotate quarterly or on suspected compromise
- Monitor usage for anomalies

### Secrets Management

**Environment Variables:**
- All secrets loaded from environment
- Never commit secrets to git
- Use .env.example with placeholder values
- Different secrets per environment (dev/staging/prod)

**Secret Rotation:**
- Database encryption key: quarterly
- JWT signing secret: quarterly
- OAuth credentials: yearly or on compromise
- Document process for zero-downtime rotation

### AI Security

**Prompt Injection Prevention:**
- Sanitize user input before sending to Claude
- System prompts not modifiable by users
- Monitor for suspicious patterns in messages
- Rate limit API calls per user

**Data Privacy:**
- User data only in conversation context
- No sensitive data (passwords, API keys) in prompts
- Claude API configured with data retention policies
- Comply with Anthropic's usage policies

### Audit and Monitoring

**Security Logging:**
- Log all authentication attempts
- Log authorization failures
- Log resource access patterns
- Log API errors and anomalies

**Monitoring Alerts:**
- Multiple failed login attempts from IP
- Unusual API usage patterns
- Error rate spikes
- Unauthorized access attempts

---

## 14. Performance Considerations

### Expected Load

**MVP Phase (0-3 months):**
- 10-50 active users
- ~500 API requests/day
- ~50 AI conversations/day
- 10 concurrent users peak

**Beta Phase (3-6 months):**
- 50-200 active users
- ~5,000 API requests/day
- ~500 AI conversations/day
- 50 concurrent users peak

**V1.0 Phase (6-12 months):**
- 200-1,000 active users
- ~20,000 API requests/day
- ~2,000 AI conversations/day
- 200 concurrent users peak

### Performance Targets

**API Response Times:**
- Simple GET requests: <100ms (p95)
- POST requests: <200ms (p95)
- Document upload: <500ms for 1MB file (p95)
- AI streaming first chunk: <2s (p95)

**Page Load Times:**
- Initial app load: <2s on 3G (p95)
- Project list load: <1s (p95)
- Thread list load: <1s (p95)
- Message history load: <1s for 50 messages (p95)

**Database Query Performance:**
- Simple queries: <10ms (p95)
- Complex joins: <50ms (p95)
- FTS5 document search: <100ms (p95)

### Optimization Strategies

#### Backend Optimizations

**Database:**
- Indexes on all foreign keys
- Composite indexes for common query patterns
- Connection pooling (10 connections max)
- Query result caching for frequently accessed data
- Periodic VACUUM to optimize SQLite file

**API Performance:**
- Response compression (gzip) for payloads >1KB
- ETag headers for cacheable resources
- Pagination for list endpoints (limit: 50 default, 100 max)
- Lazy loading for relationships
- Background tasks for non-critical operations

**AI Service:**
- Reuse Agent SDK sessions for same thread
- Limit conversation history to last 20 messages
- Cache document search results (5-minute TTL)
- Stream responses immediately (don't buffer)
- Monitor token usage and optimize prompts

#### Frontend Optimizations

**Network:**
- HTTP/2 connection pooling
- Request deduplication (cancel duplicate requests)
- Optimistic UI updates (don't wait for server)
- Retry failed requests with exponential backoff

**Rendering:**
- Lazy loading for project/thread lists
- Virtual scrolling for long message histories
- Image lazy loading and caching
- Code splitting for large screens
- Minimize widget rebuilds with const constructors

**State Management:**
- Selective widget rebuilds with Provider
- Debounce text input (300ms)
- Throttle scroll events
- Memoize expensive computations

**Asset Optimization:**
- Compress images (WebP format)
- Minimize bundle size (tree shaking)
- Split code by route
- Cache static assets aggressively

### Scalability Considerations

**Database Scaling:**
- SQLite adequate for MVP/Beta loads
- Migrate to PostgreSQL for V1.0+ if >1,000 active users
- Plan for read replicas if needed
- Consider document storage in object storage (S3) for scale

**API Scaling:**
- PaaS auto-scaling based on CPU/memory
- Horizontal scaling via load balancer
- Stateless API design (no in-memory sessions)
- Cache layer (Redis) for high-traffic data

**AI Service Scaling:**
- Rate limiting to prevent API cost spikes
- Queue system for AI requests if needed
- Monitor token usage and optimize prompts
- Consider cached responses for common questions

---

## 15. Monitoring and Observability Approach

### Logging Strategy

**Log Levels:**
- **DEBUG:** Detailed diagnostic info (dev only)
- **INFO:** General informational messages
- **WARNING:** Potential issues (401, 403, rate limits)
- **ERROR:** Errors requiring attention (500, AI failures)
- **CRITICAL:** System failures requiring immediate action

**Structured Logging Format:**
```json
{
  "timestamp": "2024-01-01T00:00:00.000Z",
  "level": "INFO",
  "logger": "api.threads",
  "message": "Message sent to AI",
  "context": {
    "user_id": "uuid",
    "thread_id": "uuid",
    "message_length": 150,
    "request_id": "uuid"
  }
}
```

**What to Log:**
- All API requests (method, endpoint, status, duration)
- Authentication events (login, logout, token refresh)
- Authorization failures
- AI service calls (tokens used, duration)
- Document uploads (size, project)
- Error details with stack traces
- Database query performance (slow queries >100ms)

**Log Storage:**
- Development: Console output
- Production: Centralized logging service (Papertrail, Logtail, CloudWatch)
- Retention: 30 days minimum
- Search and filter capability

### Metrics to Track

#### Application Metrics

**API Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate by endpoint
- Request size distribution
- Response size distribution

**AI Service Metrics:**
- AI requests per day
- Token usage per request (average, p95)
- AI response time (first chunk, total)
- Tool call frequency and success rate
- Cost per conversation

**Database Metrics:**
- Query count and duration
- Slow queries (>100ms)
- Connection pool utilization
- Database file size
- FTS5 query performance

**User Metrics:**
- Active users (daily, weekly, monthly)
- New user registrations
- Projects created per user
- Documents uploaded per project
- Threads created per project
- Messages per thread (average)
- Artifacts generated per thread

#### System Metrics

**Resource Utilization:**
- CPU usage (average, peak)
- Memory usage (average, peak)
- Disk usage and growth rate
- Network bandwidth (inbound, outbound)

**Availability:**
- Uptime percentage
- Response time by region
- Error rate over time

### Alerting Rules

**Critical Alerts (immediate notification):**
- Error rate >5% for 5 minutes
- API response time >1s (p95) for 5 minutes
- Database connection pool exhausted
- Disk usage >90%
- AI service down (all requests failing)
- Application crash or restart

**Warning Alerts (review within hours):**
- Error rate >1% for 15 minutes
- API response time >500ms (p95) for 15 minutes
- Memory usage >80% for 10 minutes
- Slow queries >200ms detected
- AI service latency >5s for first chunk

**Budget Alerts:**
- Daily AI API cost exceeds threshold ($50/day)
- Monthly projected cost exceeds budget
- Hosting cost increase >20%

### Debugging Tools

**Development:**
- FastAPI /docs endpoint (Swagger UI)
- SQLite CLI for database inspection
- Python debugger (pdb) for backend
- Flutter DevTools for frontend
- Postman for API testing

**Production:**
- Error tracking: Sentry or Rollbar
- APM: Built-in PaaS metrics (Railway/Render dashboard)
- Log aggregation: Papertrail or Logtail
- Database monitoring: SQLite query profiler

**Performance Monitoring:**
- Endpoint-level response time tracking
- Database query performance profiler
- AI service latency tracking
- Frontend performance via Flutter DevTools

---

## 16. Deployment and Infrastructure Details

### Infrastructure Components

**Application Server:**
- Platform: Railway or Render
- Runtime: Python 3.11+
- Web server: Uvicorn (ASGI)
- Workers: 2-4 depending on load
- Auto-scaling: Enabled based on CPU >70%

**Database:**
- SQLite file on persistent volume
- Volume size: 10GB (expandable)
- Backup: Daily automated snapshots
- Retention: 30 days

**Static Assets:**
- Flutter web build hosted on same PaaS
- CDN: Cloudflare (optional for performance)

### Deployment Strategy

**Git-Based Continuous Deployment:**
1. Push to GitHub repository
2. PaaS detects commit on main branch
3. Automatic build triggered
4. Run tests (if configured)
5. Build Docker image
6. Deploy to production with zero-downtime
7. Health check before routing traffic
8. Rollback on failure

**Branch Strategy:**
- `main`: Production environment
- `staging`: Staging environment (for testing)
- `develop`: Development branch (local testing)
- Feature branches: Merged to develop, then staging, then main

**Rollback Strategy:**
- Keep last 3 deployments available
- One-click rollback via PaaS dashboard
- Database migrations carefully planned (reversible)
- Monitor error rates post-deployment

### Environments

#### Development Environment
**Setup:**
- Local FastAPI server: `uvicorn main:app --reload`
- Local SQLite database: `./dev.db`
- Flutter: `flutter run -d chrome` (web) or device
- Environment file: `.env.development`

**Configuration:**
- API URL: `http://localhost:8000`
- Database: `sqlite:///./dev.db`
- OAuth: Test credentials or mock auth
- AI API: Development API key
- CORS: Allow localhost origins

**Tools:**
- Hot reload enabled
- Debug logging enabled
- Mock data seeding script

#### Staging Environment
**Setup:**
- Deployed on Railway/Render staging service
- Separate database instance
- Deployed from `staging` branch
- Environment file: `.env.staging`

**Configuration:**
- API URL: `https://ba-assistant-staging.railway.app`
- Database: Staging SQLite file
- OAuth: Test OAuth apps
- AI API: Development API key with rate limits
- CORS: Staging frontend domain only

**Purpose:**
- Test new features before production
- Internal testing and QA
- Beta tester access
- Integration testing

#### Production Environment
**Setup:**
- Deployed on Railway/Render production service
- Production database with backups
- Deployed from `main` branch
- Environment file: `.env.production`

**Configuration:**
- API URL: `https://api.ba-assistant.com`
- Database: Production SQLite with daily backups
- OAuth: Production OAuth apps
- AI API: Production API key with monitoring
- CORS: Production frontend domain only
- HTTPS: Enforced, auto-renewed SSL
- Monitoring: Enabled with alerts

**Security:**
- All secrets in environment variables
- No debug mode
- Error messages sanitized (no stack traces)
- Rate limiting enforced
- Audit logging enabled

### SSL/TLS Setup

**Certificate Management:**
- Automatic via PaaS platform (Let's Encrypt)
- Auto-renewal before expiration
- TLS 1.2+ only
- Strong cipher suites

**HTTPS Enforcement:**
- Redirect HTTP → HTTPS
- HSTS header with 1-year max-age
- Certificate pinning in mobile apps (optional)

### Backup Strategy

**Database Backups:**
- Frequency: Daily at 2 AM UTC
- Retention: 30 days
- Storage: PaaS backup storage or S3
- Format: Compressed SQLite file
- Encryption: At rest with AES-256

**Backup Testing:**
- Monthly restore test to staging environment
- Verify data integrity
- Document restore procedure

**Disaster Recovery:**
- RTO (Recovery Time Objective): 4 hours
- RPO (Recovery Point Objective): 24 hours (daily backups)
- Restore procedure documented
- Failover plan for PaaS outage

### Scaling Plan

**Vertical Scaling (First):**
- Increase PaaS service resources (CPU, RAM)
- Scale from 512MB to 2GB RAM as needed
- Adequate for MVP through Beta phases

**Horizontal Scaling (If Needed):**
- Add multiple API server instances
- Load balancer distributes traffic
- Stateless API design enables this
- Database remains single instance (SQLite limitation)

**Database Migration Trigger:**
- >1,000 active users
- >100 concurrent API requests
- Slow query performance despite optimization
- Migrate SQLite → PostgreSQL with minimal downtime

---

## 17. Environment Configuration Requirements

### Backend Environment Variables

**Required for All Environments:**
```bash
# Application
APP_NAME=BA_Assistant
ENVIRONMENT=development|staging|production
DEBUG=true|false
SECRET_KEY=<random-256-bit-hex-string>

# Database
DATABASE_URL=sqlite:///./ba_assistant.db
DB_ENCRYPTION_KEY=<fernet-key>

# JWT Authentication
JWT_SECRET_KEY=<random-256-bit-hex-string>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7
REFRESH_TOKEN_EXPIRATION_DAYS=30

# OAuth - Google
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>
GOOGLE_REDIRECT_URI=https://api.domain.com/auth/callback/google

# OAuth - Microsoft
MICROSOFT_CLIENT_ID=<microsoft-app-client-id>
MICROSOFT_CLIENT_SECRET=<microsoft-app-client-secret>
MICROSOFT_REDIRECT_URI=https://api.domain.com/auth/callback/microsoft
MICROSOFT_TENANT_ID=common

# Anthropic Claude API
ANTHROPIC_API_KEY=<anthropic-api-key>
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096

# CORS
CORS_ORIGINS=https://app.domain.com,https://staging.domain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
```

**Optional Environment Variables:**
```bash
# Error Tracking
SENTRY_DSN=<sentry-dsn-url>

# Monitoring
DATADOG_API_KEY=<datadog-api-key>

# Storage (if using S3 for documents)
S3_BUCKET_NAME=<bucket-name>
S3_ACCESS_KEY=<access-key>
S3_SECRET_KEY=<secret-key>
S3_REGION=<region>
```

### Frontend Environment Variables

**Development:**
```bash
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
```

**Staging:**
```bash
API_BASE_URL=https://ba-assistant-staging.railway.app
ENVIRONMENT=staging
```

**Production:**
```bash
API_BASE_URL=https://api.ba-assistant.com
ENVIRONMENT=production
```

### Secrets Generation

**Generate SECRET_KEY and JWT_SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Generate DB_ENCRYPTION_KEY (Fernet):**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Configuration Management

**Local Development:**
- Use `.env` file (git-ignored)
- Copy `.env.example` as template
- Never commit secrets to git

**Staging/Production:**
- Set environment variables via PaaS dashboard
- Use PaaS secret management features
- Document all required variables
- Rotate secrets quarterly

**Environment Validation:**
- Startup script validates all required variables present
- Fail fast if critical config missing
- Log warnings for optional missing config

---

## 18. Third-Party Service Integrations

### Anthropic Claude API

**Purpose:** AI-powered conversational assistance and artifact generation

**Configuration:**
- API Key: Environment variable `ANTHROPIC_API_KEY`
- Model: `claude-sonnet-4-5-20250929`
- SDK: `claude-agent-sdk` Python package
- Rate Limits: Respect tier limits (monitor via API headers)

**Cost Structure:**
- Input tokens: ~$3 per million tokens
- Output tokens: ~$15 per million tokens
- Average conversation: 2,000-5,000 tokens (~$0.05-$0.15)
- Estimated MVP cost: $50-150/month based on usage

**Usage Optimization:**
- Limit conversation history to 20 messages
- Cache document search results
- Stream responses to reduce latency perception
- Monitor token usage per request

**Fallback Strategy:**
- Retry with exponential backoff (3 attempts)
- Display error message to user with manual retry
- Log failures for debugging
- Alert if error rate >5%

**Integration Details:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def process_ai_message(prompt, tools):
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=tools,
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096
        )
    ):
        yield message
```

### Google OAuth 2.0

**Purpose:** User authentication via Google accounts

**Configuration:**
- Client ID and Secret: Google Cloud Console
- Redirect URI: `https://api.domain.com/auth/callback/google`
- Scopes: `openid email profile`
- OAuth 2.0 Endpoint: `https://accounts.google.com/o/oauth2/v2/auth`

**Setup Steps:**
1. Create project in Google Cloud Console
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Configure authorized redirect URIs
5. Add to environment variables

**Cost:** Free (no quota limits for authentication)

**Fallback Strategy:**
- If Google OAuth down, display error message
- User can try Microsoft OAuth alternative
- No offline fallback for authentication

### Microsoft OAuth 2.0

**Purpose:** User authentication via Microsoft/Azure AD accounts

**Configuration:**
- Application ID and Secret: Azure Portal
- Redirect URI: `https://api.domain.com/auth/callback/microsoft`
- Scopes: `openid email profile User.Read`
- OAuth 2.0 Endpoint: `https://login.microsoftonline.com/common/oauth2/v2.0/authorize`

**Setup Steps:**
1. Register app in Azure Portal
2. Add platform (Web)
3. Configure redirect URI
4. Generate client secret
5. Add to environment variables

**Cost:** Free (included in Azure AD Free tier)

**Fallback Strategy:**
- If Microsoft OAuth down, display error message
- User can try Google OAuth alternative
- No offline fallback for authentication

### Platform-as-a-Service Hosting (Railway/Render)

**Purpose:** Backend and database hosting

**Configuration:**
- Git repository: Connect to GitHub
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variables: Set via dashboard

**Cost Estimates:**
- **Railway:**
  - Starter: $5/month (512MB RAM, adequate for MVP)
  - Developer: $20/month (2GB RAM, for Beta+)
- **Render:**
  - Starter: $7/month (512MB RAM)
  - Standard: $25/month (2GB RAM)

**Features:**
- Automatic HTTPS with Let's Encrypt
- Git-based continuous deployment
- Automatic health checks
- Zero-downtime deployments
- Built-in metrics and logs

**Monitoring:**
- Built-in dashboard for metrics
- Resource usage alerts
- Deployment history
- Log streaming

---

## 19. Cost Estimates

### MVP Phase (0-3 months)

**Hosting (Railway/Render):**
- Backend service: $5-7/month
- Database: Included
- Bandwidth: Included (generous limits)
- **Subtotal:** $5-7/month

**Third-Party Services:**
- Anthropic Claude API: $50-100/month (estimated 1,000-2,000 conversations)
- Google OAuth: $0 (free)
- Microsoft OAuth: $0 (free)
- Sentry (error tracking): $0 (free developer plan)
- **Subtotal:** $50-100/month

**Development Tools:**
- GitHub: $0 (free for public repos)
- Flutter: $0 (free)
- VSCode/IDE: $0 (free)
- **Subtotal:** $0/month

**Total MVP Monthly Cost: $55-107/month**
**Total MVP Phase Cost (3 months): ~$165-320**

### Beta Phase (3-6 months)

**Hosting:**
- Backend service: $20-25/month (upgraded for more users)
- Database: Included
- Bandwidth: Included
- **Subtotal:** $20-25/month

**Third-Party Services:**
- Anthropic Claude API: $200-400/month (10x traffic from MVP)
- OAuth: $0 (still free)
- Error tracking: $0 (free tier sufficient)
- **Subtotal:** $200-400/month

**Total Beta Monthly Cost: $220-425/month**
**Total Beta Phase Cost (3 months): ~$660-1,275**

### V1.0 Phase (6-12 months)

**Hosting:**
- Backend service: $25-50/month (auto-scaling enabled)
- Database: Consider PostgreSQL migration ($15/month managed)
- CDN (optional): $10-20/month for improved performance
- **Subtotal:** $40-85/month

**Third-Party Services:**
- Anthropic Claude API: $500-1,000/month (2,000+ active users)
- OAuth: $0
- Error tracking: $29/month (team plan for better features)
- Monitoring: $0 (PaaS built-in sufficient)
- **Subtotal:** $529-1,029/month

**Total V1.0 Monthly Cost: $569-1,114/month**

### Cost Optimization Strategies

**AI API Costs:**
- Implement conversation history limits
- Cache common document searches
- Optimize prompt length
- Monitor and alert on unusual usage
- Consider cheaper models for simple tasks

**Hosting Costs:**
- Start with smallest tier
- Scale only when metrics justify it
- Use auto-scaling to handle peaks without over-provisioning
- Review resource usage monthly

**Future Monetization Considerations:**
- MVP cost: ~$100/month sustainable for validation
- Beta cost: ~$400/month requires small user base or angel funding
- V1.0 cost: ~$800/month requires revenue or funding
- Break-even: ~40-50 paid users at $20/month subscription

### Cost Breakdown by Category

**Infrastructure:** 5-10% of total
**AI Services:** 85-90% of total (largest cost driver)
**Other Services:** 5% of total

**Key Insight:** AI API costs dominate the budget. Controlling token usage is critical for profitability. Monitor closely and optimize prompts during MVP.

---

## Document Version and Maintenance

**Document Version:** 1.0
**Last Updated:** 2026-01-17
**Author:** Software Architect AI Assistant
**Project:** Business Analyst Assistant - MVP

**Change History:**
- 2026-01-17: Initial complete technical specification created

**Maintenance Notes:**
- Update as architectural decisions evolve during development
- Refine cost estimates based on actual usage data
- Adjust performance targets based on MVP user feedback
- Document technical debt decisions as they're made
- Review quarterly and update for new technologies or patterns
