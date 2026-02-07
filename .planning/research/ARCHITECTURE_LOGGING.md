# Architecture Research: Logging Infrastructure

**Domain:** Comprehensive logging for Flutter/FastAPI application
**Researched:** 2026-02-07
**Confidence:** HIGH (based on direct codebase analysis)

---

## Summary

The BA Assistant has a clean layered architecture that logging can integrate with minimal disruption:

1. **Frontend:** Provider pattern with services layer - logging fits as a cross-cutting service
2. **Backend:** FastAPI with services layer - logging integrates via middleware and decorators
3. **Correlation:** HTTP headers carry correlation IDs from frontend to backend
4. **Storage:** Backend file-based storage with admin API for download

**Key architectural decision:** Logging is a cross-cutting concern, not a feature. It should be injectable/toggleable without modifying business logic.

---

## Component Overview

```
+------------------+       +-----------------+       +------------------+
|     FRONTEND     |       |     NETWORK     |       |     BACKEND      |
+------------------+       +-----------------+       +------------------+
|                  |       |                 |       |                  |
| LoggingService   |------>| X-Correlation-ID|------>| LoggingMiddleware|
|    (new)         |       | X-Session-ID    |       |     (new)        |
|                  |       | (HTTP headers)  |       |                  |
+------------------+       +-----------------+       +------------------+
        |                                                    |
        v                                                    v
+------------------+                               +------------------+
| LoggingProvider  |                               | LoggingService   |
|    (new)         |                               |     (new)        |
+------------------+                               +------------------+
        |                                                    |
        | (toggle, buffer)                                   | (write, rotate)
        v                                                    v
+------------------+                               +------------------+
| In-memory buffer |                               | File storage     |
| (until flush)    |                               | logs/app.log     |
+------------------+                               +------------------+
                                                             |
                                                             v
                                                   +------------------+
                                                   | Admin API        |
                                                   | /api/logs        |
                                                   +------------------+
```

---

## Frontend Integration

### New Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `LoggingService` | Core logging logic (levels, formatting, buffer) | `lib/services/logging_service.dart` |
| `LoggingProvider` | State management (enabled toggle, flush) | `lib/providers/logging_provider.dart` |
| `LoggingInterceptor` | Dio interceptor for HTTP logging | `lib/services/logging_interceptor.dart` |

### Modified Components

| Component | Changes | Rationale |
|-----------|---------|-----------|
| `main.dart` | Add LoggingProvider to MultiProvider, initialize correlation ID | Central provider registration |
| `settings_screen.dart` | Add logging toggle switch in Preferences section | User control, follows theme toggle pattern |
| `core/config.dart` | Add logging constants (levels, buffer size) | Centralized configuration |
| All services (Dio-based) | Inject LoggingInterceptor | Automatic HTTP logging |

### Frontend Architecture Pattern

**Follow existing patterns:**

1. **Provider pattern** (like ThemeProvider):
   ```dart
   class LoggingProvider extends ChangeNotifier {
     bool _isEnabled;
     static const String _loggingKey = 'loggingEnabled';

     static Future<LoggingProvider> load(SharedPreferences prefs) async {...}
     Future<void> toggleLogging() async {...}
   }
   ```

2. **Service injection** (like AIService, ThreadService):
   ```dart
   class LoggingService {
     static final LoggingService _instance = LoggingService._internal();
     factory LoggingService() => _instance;

     void log(LogLevel level, String category, String message, [Map<String, dynamic>? data]);
     Future<void> flush();  // Send buffered logs to backend
   }
   ```

3. **Dio interceptor** (new pattern, but follows Dio conventions):
   ```dart
   class LoggingInterceptor extends Interceptor {
     @override
     void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
       options.headers['X-Correlation-ID'] = correlationId;
       LoggingService().log(LogLevel.info, 'HTTP', 'Request: ${options.method} ${options.path}');
       super.onRequest(options, handler);
     }
   }
   ```

### Correlation ID Flow

1. **Session start:** Generate UUID in `main.dart` on app launch
2. **Store globally:** Keep in LoggingService singleton
3. **Attach to requests:** LoggingInterceptor adds `X-Correlation-ID` header
4. **Include in logs:** Every log entry includes correlation ID

---

## Backend Integration

### New Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `LoggingMiddleware` | Extract correlation ID, log requests/responses | `app/middleware/logging.py` |
| `LoggingService` | Core logging with rotation, structured format | `app/services/logging_service.py` |
| `logs.py` (routes) | Admin API for log download | `app/routes/logs.py` |

### Modified Components

| Component | Changes | Rationale |
|-----------|---------|-----------|
| `main.py` | Add LoggingMiddleware to app | Request/response logging |
| `config.py` | Add logging settings (path, rotation, level) | Centralized configuration |

### Backend Architecture Pattern

**Follow existing patterns:**

1. **Middleware** (like CORS middleware in main.py):
   ```python
   from starlette.middleware.base import BaseHTTPMiddleware

   class LoggingMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request: Request, call_next):
           correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
           request.state.correlation_id = correlation_id

           start_time = time.time()
           response = await call_next(request)
           duration = time.time() - start_time

           logging_service.log_request(correlation_id, request, response, duration)
           return response
   ```

2. **Service pattern** (like conversation_service.py):
   ```python
   class LoggingService:
       def __init__(self, log_dir: str = "logs"):
           self.log_dir = log_dir
           self.setup_rotation()

       def log(self, level: str, category: str, message: str,
               correlation_id: str = None, data: dict = None):
           entry = self._format_entry(level, category, message, correlation_id, data)
           self._write(entry)
   ```

3. **Routes** (like auth.py, projects.py):
   ```python
   router = APIRouter()

   @router.get("/logs")
   async def get_logs(
       current_user: dict = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ):
       # Admin check
       # Return log file or stream
   ```

### Existing Logging Audit

Current logging in codebase:

| File | Current State |
|------|---------------|
| `main.py` | Uses `logging.getLogger(__name__)` - minimal, only for config validation |
| `agent_service.py` | Uses `logging.getLogger(__name__)` - sparse exception logging |
| `brd_generator.py` | Uses `logging.getLogger(__name__)` - sparse |
| `skill_loader.py` | Uses `logging.getLogger(__name__)` - sparse |
| `conversations.py` | Ad-hoc `import logging` in exception handler only |

**Finding:** Backend has minimal logging infrastructure. New LoggingService should configure Python's logging module properly and unify all existing usage.

---

## Data Flow

### Frontend Log Generation and Transmission

```
1. User action triggers log
   |
   v
2. LoggingService.log() called
   - Adds timestamp, correlation ID, session ID
   - Adds to in-memory buffer
   |
   v
3. Buffer reaches threshold OR app backgrounded
   |
   v
4. LoggingService.flush()
   - POST to /api/logs/ingest with batch
   - Clear buffer on success
   |
   v
5. Backend receives, writes to file
```

### Backend Log Storage

```
1. LoggingMiddleware intercepts request
   - Extracts/generates correlation ID
   - Logs request start
   |
   v
2. Route handler executes
   - May call LoggingService.log() for business events
   |
   v
3. Response returns through middleware
   - Logs response status, duration
   |
   v
4. LoggingService writes to rotating file
   - logs/app.log (current)
   - logs/app.log.1 (rotated)
   - logs/app.log.2 (rotated)
```

### Log File Format (Recommended)

JSON Lines format for easy parsing:

```json
{"timestamp": "2026-02-07T10:30:45.123Z", "level": "INFO", "category": "HTTP", "correlation_id": "abc-123", "message": "POST /api/threads/xyz/chat", "data": {"status": 200, "duration_ms": 1234}}
{"timestamp": "2026-02-07T10:30:46.456Z", "level": "ERROR", "category": "AI", "correlation_id": "abc-123", "message": "Claude API error", "data": {"error": "rate_limit"}}
```

---

## Build Order

Based on dependencies and integration points:

### Phase 1: Backend Logging Foundation
**Rationale:** Backend can be tested independently with curl/Postman. No frontend changes needed.

1. Create `app/services/logging_service.py`
   - Python logging configuration
   - File rotation (RotatingFileHandler)
   - JSON Lines formatter
   - Structured log method

2. Create `app/middleware/logging.py`
   - Correlation ID extraction/generation
   - Request/response timing
   - Attach correlation_id to request.state

3. Modify `main.py`
   - Register LoggingMiddleware
   - Initialize logging on startup

4. Modify `config.py`
   - Add: LOG_DIR, LOG_LEVEL, LOG_ROTATION_SIZE, LOG_BACKUP_COUNT

### Phase 2: Backend Admin API
**Rationale:** Enables log download before frontend UI exists. Testable with curl.

1. Create `app/routes/logs.py`
   - GET /api/logs (list available log files)
   - GET /api/logs/download?file=app.log (download specific file)
   - POST /api/logs/ingest (receive frontend logs) - for Phase 6

2. Modify `main.py`
   - Register logs router

### Phase 3: Frontend Logging Foundation
**Rationale:** Can test with console output before backend integration.

1. Create `lib/services/logging_service.dart`
   - Singleton pattern
   - In-memory buffer (List<LogEntry>)
   - Console output in debug mode
   - Correlation ID generation

2. Create `lib/providers/logging_provider.dart`
   - Enabled toggle with SharedPreferences persistence
   - Follow ThemeProvider pattern exactly

3. Modify `main.dart`
   - Initialize LoggingProvider in load sequence
   - Generate session correlation ID
   - Add LoggingProvider to MultiProvider

### Phase 4: Frontend HTTP Integration
**Rationale:** Automatic logging of all API calls without modifying business logic.

1. Create `lib/services/logging_interceptor.dart`
   - Dio interceptor
   - Add X-Correlation-ID header to all requests
   - Log request start/response/error

2. Create shared Dio instance factory
   - `lib/core/http_client.dart`
   - Returns Dio with LoggingInterceptor attached

3. Modify all services to use shared Dio instance:
   - `thread_service.dart`
   - `project_service.dart`
   - `document_service.dart`
   - `auth_service.dart`
   - `artifact_service.dart`
   - `ai_service.dart` (SSE - needs special handling, log connection start/end)

### Phase 5: Frontend Settings UI
**Rationale:** User control, follows existing patterns exactly.

1. Modify `settings_screen.dart`
   - Add "Debug Logging" toggle in Preferences section
   - Consumer<LoggingProvider> pattern
   - Follow theme toggle UI pattern

### Phase 6: Frontend-to-Backend Flush
**Rationale:** Complete the loop - frontend logs arrive at backend.

1. Modify `lib/services/logging_service.dart`
   - Add flush() method
   - POST buffered logs to /api/logs/ingest
   - Retry logic on failure
   - Clear buffer on success

2. Modify `main.dart`
   - Add WidgetsBindingObserver for app lifecycle
   - Flush on app pause/inactive
   - Periodic flush (every 5 minutes or 100 entries)

---

## Integration Points Summary

| Integration Point | Component | Type | Phase |
|-------------------|-----------|------|-------|
| Middleware registration | `main.py` | Modify | 1 |
| Config expansion | `config.py` | Modify | 1 |
| Route registration (logs) | `main.py` | Modify | 2 |
| Provider registration | `main.dart` | Modify | 3 |
| Settings toggle | `settings_screen.dart` | Modify | 5 |
| HTTP interception | All 6 services | Modify | 4 |
| Lifecycle handling | `main.dart` | Modify | 6 |

---

## Existing Patterns to Follow

### Frontend Patterns (from codebase analysis)

1. **Provider with SharedPreferences** (`theme_provider.dart`):
   - Static `load()` factory for async init
   - Private constructor
   - Immediate persistence on toggle
   - `notifyListeners()` after state change

2. **Singleton Service** (pattern seen in Dart):
   - Private named constructor: `LoggingService._internal()`
   - Factory constructor: `factory LoggingService() => _instance`
   - Static instance field

3. **Service with Dio** (`thread_service.dart`, `auth_service.dart`):
   - Constructor with optional Dio parameter for testing
   - Private `_getAuthHeaders()` method
   - DioException catch with status code handling

### Backend Patterns (from codebase analysis)

1. **Middleware** (`main.py` CORS example):
   ```python
   app.add_middleware(
       SomeMiddleware,
       param=value,
   )
   ```

2. **Service Function** (`conversation_service.py`):
   - Module-level functions, not classes
   - Async with db: AsyncSession parameter
   - Clear docstrings

3. **Router** (`auth.py`, `projects.py`):
   - `router = APIRouter()`
   - Depends(get_current_user) for auth
   - Depends(get_db) for database
   - HTTPException for errors

---

## Anti-Patterns to Avoid

### 1. Logging in Business Logic
**Wrong:** Adding log statements inside providers/services
**Right:** Use interceptors/middleware that wrap existing code

### 2. Synchronous File Writes
**Wrong:** Blocking I/O on every log entry
**Right:** Buffer in memory, flush periodically or on thresholds

### 3. Unbounded Buffers
**Wrong:** No limit on in-memory log buffer
**Right:** Max buffer size (e.g., 100 entries), drop oldest on overflow

### 4. Logging Sensitive Data
**Wrong:** Logging full request/response bodies (may contain tokens)
**Right:** Log metadata only (path, status, duration), sanitize if needed

### 5. Breaking on Log Failure
**Wrong:** Throwing exceptions when logging fails
**Right:** Fail silently - logging failures should not affect app functionality

### 6. Tight Coupling
**Wrong:** LoggingService depends on specific services
**Right:** LoggingService is standalone, services optionally use it

---

## Scalability Considerations

| Concern | At MVP | At 100 users | At 1000+ users |
|---------|--------|--------------|----------------|
| Storage | Single log file | Rotating files (7 days) | External log service |
| Query | Admin downloads file | Admin downloads file | Search API or Elasticsearch |
| Frontend buffer | 100 entries max | 100 entries max | Consider web worker |
| Backend write | Sync OK for MVP | Async queue | Dedicated logging service |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Log files fill disk | Medium | High | Rotation with max size + backup count |
| Performance degradation | Low | Medium | Buffering, async writes |
| Sensitive data in logs | Medium | High | Sanitize headers, no body logging |
| Frontend memory bloat | Low | Medium | Max buffer size, drop oldest |
| Correlation ID mismatch | Low | Low | Generate on frontend, always include |

---

## Sources

- Direct codebase analysis (HIGH confidence)
  - `main.dart` - Provider registration pattern
  - `theme_provider.dart` - SharedPreferences persistence pattern
  - `thread_service.dart` - Dio service pattern
  - `main.py` - FastAPI middleware pattern
  - `conversation_service.py` - Backend service pattern
  - `config.py` - Settings pattern
- Python logging module documentation (stdlib)
- FastAPI middleware documentation (official)
- Dio interceptor documentation (pub.dev)
