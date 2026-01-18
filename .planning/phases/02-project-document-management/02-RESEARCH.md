# Phase 2: Project & Document Management - Research

**Researched:** 2026-01-18
**Domain:** Database modeling, document storage, full-text search, file uploads
**Confidence:** HIGH

## Summary

Phase 2 introduces project organization with document storage and conversation threads. The research identifies SQLAlchemy's one-to-many relationship patterns with proper cascade configuration, Fernet symmetric encryption for document security, SQLite FTS5 for efficient full-text search, FastAPI's UploadFile API for secure file handling, and Flutter's file_picker package for cross-platform file selection.

**Critical discovery:** SQLite requires explicit foreign key enforcement (`PRAGMA foreign_keys = ON`) and Fernet is memory-constrained (documents must fit in RAM). These limitations are acceptable for MVP text documents (<1MB) but require attention during implementation.

**Primary recommendation:** Use database-level cascade deletes (`ondelete="CASCADE"`) combined with SQLAlchemy relationship configuration for reliable data cleanup. Enable SQLite foreign keys on every connection. Use Fernet for encryption with environment-based key management. Implement FTS5 virtual tables synchronized with document inserts.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ | Database ORM with async support | Industry standard, mature relationships API, async-native |
| cryptography | 47.x | Fernet encryption | PyCA official library, NIST-recommended algorithms, excellent performance |
| aiosqlite | 0.20+ | SQLite async driver | Official SQLAlchemy-recommended driver, maintains FTS5 compatibility |
| FastAPI UploadFile | Built-in | File upload handling | Memory-efficient streaming, spooled files, multipart/form-data support |
| file_picker | 10.3.8+ | Flutter file selection | Official community package, 19k+ pub points, cross-platform native pickers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | Latest | FastAPI form data | Required for File() and Form() parameters |
| aiofiles | Latest | Async file I/O | Optional: for streaming file writes to disk |
| Provider | 6.x | Flutter state management | Already established in Phase 1, reuse for projects/documents state |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fernet | AES-GCM directly | Fernet provides authenticated encryption with simpler API; raw AES requires careful implementation |
| FTS5 | Elasticsearch | FTS5 is zero-config, embedded; Elasticsearch requires separate service, overkill for MVP |
| file_picker | Manual platform channels | file_picker abstracts platform differences, battle-tested across millions of apps |

**Installation:**
```bash
# Backend
pip install cryptography aiosqlite python-multipart aiofiles

# Frontend (pubspec.yaml)
dependencies:
  file_picker: ^10.3.8
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── models.py           # Add Project, Document, Thread, Message models
│   ├── services/
│   │   ├── encryption.py   # Fernet encryption utilities
│   │   └── document_search.py  # FTS5 query helpers
│   └── routes/
│       ├── projects.py     # CRUD endpoints
│       ├── documents.py    # Upload, list, search endpoints
│       └── threads.py      # Thread management endpoints

frontend/
├── lib/
│   ├── models/
│   │   ├── project.dart    # Project model
│   │   ├── document.dart   # Document model
│   │   └── thread.dart     # Thread model
│   ├── providers/
│   │   ├── project_provider.dart     # ChangeNotifier for projects
│   │   ├── document_provider.dart    # Documents per project
│   │   └── thread_provider.dart      # Threads per project
│   ├── screens/
│   │   ├── projects/
│   │   │   ├── project_list_screen.dart
│   │   │   └── project_detail_screen.dart  # Master-detail pattern
│   │   └── documents/
│   │       └── document_upload_screen.dart
│   └── widgets/
│       └── responsive_master_detail.dart  # Reusable layout
```

### Pattern 1: One-to-Many Relationships with Cascade Delete
**What:** Foreign key relationships with proper cascade configuration at both database and ORM levels
**When to use:** Project → Documents, Project → Threads, Thread → Messages relationships

**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
from typing import List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),  # Database-level cascade
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # One-to-many relationship with cascade
    documents: Mapped[List["Document"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",  # ORM-level cascade
        passive_deletes=True  # Let database handle cascades for performance
    )

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Many-to-one relationship
    project: Mapped["Project"] = relationship(back_populates="documents")
```

**Critical:** Use both `ondelete="CASCADE"` on ForeignKey AND `cascade="all, delete-orphan"` on relationship for reliability.

### Pattern 2: SQLite Foreign Key Enforcement
**What:** Enable foreign key constraints on every database connection
**When to use:** Application startup, before any database operations

**Example:**
```python
# Source: https://sqlite.org/foreignkeys.html
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

**Why critical:** SQLite disables foreign keys by default. Without this, cascade deletes won't work.

### Pattern 3: Fernet Document Encryption
**What:** Symmetric encryption for documents at rest with environment-based key management
**When to use:** Before storing document content, after retrieving from database

**Example:**
```python
# Source: https://cryptography.io/en/latest/fernet/
import os
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self):
        # Load key from environment variable
        key = os.getenv("FERNET_KEY")
        if not key:
            raise ValueError("FERNET_KEY environment variable not set")
        self.fernet = Fernet(key.encode())

    def encrypt_document(self, plaintext: str) -> bytes:
        """Encrypt document content."""
        return self.fernet.encrypt(plaintext.encode('utf-8'))

    def decrypt_document(self, ciphertext: bytes) -> str:
        """Decrypt document content."""
        return self.fernet.decrypt(ciphertext).decode('utf-8')

# Generate key once (store in .env):
# key = Fernet.generate_key()
# print(key.decode())  # Save this to FERNET_KEY in .env
```

**Limitation:** Documents must fit in memory. Acceptable for text files <1MB (MVP scope).

### Pattern 4: FTS5 Full-Text Search
**What:** Create FTS5 virtual table synchronized with documents table for fast search
**When to use:** Document upload, document search endpoints

**Example:**
```python
# Source: https://sqlite.org/fts5.html
# Create FTS5 table (in Alembic migration)
async with engine.begin() as conn:
    await conn.execute(text("""
        CREATE VIRTUAL TABLE document_fts USING fts5(
            document_id UNINDEXED,
            filename,
            content,
            tokenize = 'porter ascii'
        )
    """))

# Insert document (sync with documents table)
async def index_document(db: AsyncSession, doc_id: str, filename: str, content: str):
    await db.execute(text("""
        INSERT INTO document_fts(document_id, filename, content)
        VALUES (:doc_id, :filename, :content)
    """), {"doc_id": doc_id, "filename": filename, "content": content})

# Search documents with BM25 ranking
async def search_documents(db: AsyncSession, project_id: str, query: str):
    result = await db.execute(text("""
        SELECT d.id, d.filename, d.created_at,
               snippet(fts, 2, '<mark>', '</mark>', '...', 20) as snippet,
               bm25(fts, 10.0, 1.0) as score
        FROM documents d
        JOIN document_fts fts ON d.id = fts.document_id
        WHERE d.project_id = :project_id
          AND fts MATCH :query
        ORDER BY score
        LIMIT 20
    """), {"project_id": project_id, "query": query})
    return result.fetchall()
```

**Note:** Store encrypted content in `documents` table, plaintext in `document_fts` for search. FTS5 tables are not encrypted.

### Pattern 5: FastAPI File Upload with Validation
**What:** Secure file upload with type validation, size limits, and streaming
**When to use:** Document upload endpoints

**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/request-files/
from fastapi import UploadFile, File, HTTPException, Depends
from typing import Annotated

MAX_FILE_SIZE = 1024 * 1024  # 1MB for text files

@router.post("/projects/{project_id}/documents")
async def upload_document(
    project_id: str,
    file: Annotated[UploadFile, File()],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate file type
    allowed_types = ["text/plain", "text/markdown"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, "Only .txt and .md files allowed")

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 1MB)")

    # Decrypt content (comes as bytes)
    text_content = content.decode('utf-8')

    # Encrypt for storage
    encrypted = encryption_service.encrypt_document(text_content)

    # Store in database
    document = Document(
        project_id=project_id,
        filename=file.filename,
        content_encrypted=encrypted,
        created_at=datetime.utcnow()
    )
    db.add(document)
    await db.commit()

    # Index for search
    await index_document(db, document.id, file.filename, text_content)

    return {"id": document.id, "filename": file.filename}
```

### Pattern 6: Flutter File Picker with Upload Progress
**What:** Cross-platform file selection with Dio upload progress tracking
**When to use:** Document upload UI

**Example:**
```dart
// Source: https://pub.dev/packages/file_picker
// Source: https://pub.dev/packages/dio
import 'package:file_picker/file_picker.dart';
import 'package:dio/dio.dart';

class DocumentUploadScreen extends StatefulWidget {
  final String projectId;

  @override
  _DocumentUploadScreenState createState() => _DocumentUploadScreenState();
}

class _DocumentUploadScreenState extends State<DocumentUploadScreen> {
  double _uploadProgress = 0.0;
  bool _uploading = false;

  Future<void> _pickAndUploadFile() async {
    // Pick file with type filter
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['txt', 'md'],
    );

    if (result == null) return;

    final file = result.files.single;

    // Prepare multipart upload
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(
        file.path!,
        filename: file.name,
      ),
    });

    setState(() {
      _uploading = true;
      _uploadProgress = 0.0;
    });

    try {
      final dio = Dio();
      final response = await dio.post(
        'https://api.example.com/projects/${widget.projectId}/documents',
        data: formData,
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
        ),
        onSendProgress: (sent, total) {
          setState(() {
            _uploadProgress = sent / total;
          });
        },
      );

      // Success
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Document uploaded successfully')),
      );
    } catch (e) {
      // Error handling
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Upload failed: $e')),
      );
    } finally {
      setState(() {
        _uploading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ElevatedButton(
          onPressed: _uploading ? null : _pickAndUploadFile,
          child: Text('Upload Document'),
        ),
        if (_uploading)
          LinearProgressIndicator(value: _uploadProgress),
      ],
    );
  }
}
```

### Pattern 7: Async Relationship Loading with selectinload
**What:** Eager load relationships in async queries to avoid lazy loading issues
**When to use:** Any async query that accesses relationships

**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# BAD: Lazy loading fails with async
project = await db.get(Project, project_id)
documents = project.documents  # ERROR: Cannot lazy load in async

# GOOD: Eager load with selectinload
stmt = select(Project).where(Project.id == project_id).options(
    selectinload(Project.documents),
    selectinload(Project.threads)
)
result = await db.execute(stmt)
project = result.scalar_one()
documents = project.documents  # Works! Already loaded
```

**Alternative:** Use `lazy="selectin"` in relationship definition for automatic eager loading.

### Pattern 8: MultiProvider for Multiple State Objects
**What:** Combine multiple ChangeNotifierProviders for different state concerns
**When to use:** Application root to provide project, document, and thread state

**Example:**
```dart
// Source: https://docs.flutter.dev/data-and-backend/state-mgmt/simple
import 'package:provider/provider.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ProjectProvider()),
        ChangeNotifierProvider(create: (_) => DocumentProvider()),
        ChangeNotifierProvider(create: (_) => ThreadProvider()),
      ],
      child: MyApp(),
    ),
  );
}

class ProjectProvider extends ChangeNotifier {
  List<Project> _projects = [];

  List<Project> get projects => _projects;

  Future<void> loadProjects() async {
    _projects = await api.getProjects();
    notifyListeners();
  }

  Future<void> createProject(String name, String description) async {
    final project = await api.createProject(name, description);
    _projects.add(project);
    notifyListeners();
  }
}
```

### Pattern 9: Responsive Master-Detail Layout
**What:** Adaptive layout showing list + detail on large screens, navigation on small screens
**When to use:** Project list/detail, document list/detail views

**Example:**
```dart
// Source: https://dev.to/dariodigregorio/mastering-responsive-uis-in-flutter-the-full-guide-3g6i
class ProjectListScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ResponsiveLayout(
      mobile: ProjectListMobileView(),
      desktop: ProjectMasterDetailView(),
    );
  }
}

class ProjectMasterDetailView extends StatefulWidget {
  @override
  _ProjectMasterDetailViewState createState() => _ProjectMasterDetailViewState();
}

class _ProjectMasterDetailViewState extends State<ProjectMasterDetailView> {
  String? _selectedProjectId;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Master: Project list
        SizedBox(
          width: 300,
          child: ProjectList(
            onProjectSelected: (projectId) {
              setState(() {
                _selectedProjectId = projectId;
              });
            },
          ),
        ),
        VerticalDivider(width: 1),
        // Detail: Project contents
        Expanded(
          child: _selectedProjectId == null
              ? Center(child: Text('Select a project'))
              : ProjectDetailView(projectId: _selectedProjectId!),
        ),
      ],
    );
  }
}
```

### Anti-Patterns to Avoid

- **Using query.delete() with ORM cascades:** query.delete() bypasses ORM, use session.delete(obj) instead or rely on database cascades
- **Forgetting PRAGMA foreign_keys:** SQLite won't enforce cascades without explicit pragma
- **Lazy loading in async context:** Always use selectinload/joinedload with async queries
- **Hardcoding encryption key:** Use environment variables, never commit keys to git
- **Not validating file types:** Check content_type AND file extension for security
- **Loading entire file into memory:** Use UploadFile's streaming for large files (though MVP is text-only <1MB)
- **Storing plaintext in FTS5 without encryption warning:** Document that FTS5 contains searchable plaintext

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Symmetric encryption | Custom AES implementation | Fernet from cryptography library | Handles IV generation, authentication, key derivation, padding automatically |
| Full-text search | LIKE '%term%' queries | SQLite FTS5 | 100x+ faster, proper tokenization, ranking, phrase search, prefix matching |
| File upload streaming | Reading entire file in endpoint | FastAPI UploadFile | Spooled files (memory→disk), async streaming, multipart handling |
| Cross-platform file picker | Platform channels per OS | file_picker package | Handles iOS/Android/Web differences, native pickers, permission handling |
| Cascade delete logic | Manual deletion loops | Database ON DELETE CASCADE + SQLAlchemy cascade | Atomic operations, handles complex graphs, prevents orphaned records |
| Document search ranking | Manual relevance scoring | FTS5 bm25() function | TF-IDF based ranking, proven algorithm, optimized C implementation |
| Upload progress tracking | Manual chunk counting | Dio onSendProgress | Built-in, accurate, handles compression/buffering |

**Key insight:** Encryption, search, and cascade deletes have subtle edge cases (authentication, tokenization, circular references) that mature libraries handle correctly. Building custom solutions risks security vulnerabilities and performance issues.

## Common Pitfalls

### Pitfall 1: SQLite Foreign Keys Disabled by Default
**What goes wrong:** Cascade deletes don't work, orphaned records accumulate, foreign key constraints ignored
**Why it happens:** SQLite disables foreign keys for backwards compatibility; must enable per connection
**How to avoid:** Use SQLAlchemy event listener to execute `PRAGMA foreign_keys=ON` on every connection
**Warning signs:** Deleting project leaves documents/threads in database, no foreign key errors when inserting invalid IDs

**Code:**
```python
from sqlalchemy import event, Engine

@event.listens_for(Engine, "connect")
def enable_sqlite_fks(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Pitfall 2: Fernet Memory Limitations
**What goes wrong:** Encrypting large files crashes with MemoryError or extremely slow performance
**Why it happens:** Fernet loads entire plaintext + ciphertext into memory simultaneously
**How to avoid:** Enforce strict file size limits (1MB for MVP), validate before encryption, plan for streaming encryption in future phases
**Warning signs:** Backend OOM errors on file upload, slow response times for encryption operations

### Pitfall 3: Async Lazy Loading Failures
**What goes wrong:** Accessing relationship attributes raises "greenlet_spawn has not been called" or similar async errors
**Why it happens:** Async sessions cannot lazy-load relationships (requires synchronous blocking)
**How to avoid:** Always use selectinload/joinedload for relationships, or set `lazy="selectin"` on relationship definition
**Warning signs:** DetachedInstanceError, "Instance is not bound to a Session", async context errors

**Code:**
```python
# WRONG
project = await db.get(Project, project_id)
docs = project.documents  # Fails in async

# RIGHT
stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.documents))
project = (await db.execute(stmt)).scalar_one()
docs = project.documents  # Works
```

### Pitfall 4: FTS5 Table Desynchronization
**What goes wrong:** Search results include deleted documents or miss newly uploaded documents
**Why it happens:** FTS5 virtual table is separate from documents table; requires manual synchronization
**How to avoid:** Insert/update/delete FTS5 rows in same transaction as documents table operations
**Warning signs:** Search returns wrong counts, missing results for recent uploads, stale results for deleted docs

**Code:**
```python
# Use transaction to keep synchronized
async with db.begin():
    # Insert document
    doc = Document(...)
    db.add(doc)
    await db.flush()  # Get doc.id

    # Insert FTS5 entry in same transaction
    await db.execute(text("""
        INSERT INTO document_fts(document_id, filename, content)
        VALUES (:id, :filename, :content)
    """), {"id": doc.id, "filename": doc.filename, "content": plaintext})
```

### Pitfall 5: Multipart File Upload Header Confusion
**What goes wrong:** File uploads return 422 Unprocessable Entity, "Expected UploadFile, received str"
**Why it happens:** Client sends JSON instead of multipart/form-data, or backend mixes File() with Body()
**How to avoid:** Use FormData on frontend, never mix File() and Body() in same endpoint
**Warning signs:** Content-Type is application/json instead of multipart/form-data

**Frontend:**
```dart
// WRONG: JSON body
dio.post('/upload', data: {'file': base64String});

// RIGHT: FormData
dio.post('/upload', data: FormData.fromMap({
  'file': await MultipartFile.fromFile(path),
}));
```

### Pitfall 6: Encryption Key Loss
**What goes wrong:** All encrypted documents become permanently unreadable
**Why it happens:** Key stored in .env not backed up, lost during redeployment, not synchronized across instances
**How to avoid:** Store key in secure key management system (AWS Secrets Manager, Azure Key Vault), document backup procedures
**Warning signs:** Cannot decrypt documents after server restart, different data on different instances

### Pitfall 7: Thread-Local Encryption State
**What goes wrong:** Encryption/decryption errors in concurrent requests, "cipher already finalized"
**Why it happens:** Fernet objects shared across requests without proper isolation
**How to avoid:** Create new Fernet instance per operation, or use dependency injection to ensure per-request isolation
**Warning signs:** Intermittent decryption failures under load, race conditions in encryption service

## Code Examples

Verified patterns from official sources:

### Database Schema with Proper Relationships
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships with cascade
    documents: Mapped[List["Document"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    threads: Mapped[List["Thread"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    project: Mapped["Project"] = relationship(back_populates="documents")

class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="threads")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at"  # Chronological order
    )

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Relationship
    thread: Mapped["Thread"] = relationship(back_populates="messages")
```

### Complete Document Upload Endpoint
```python
# Source: https://fastapi.tiangolo.com/tutorial/request-files/
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Annotated
import os

router = APIRouter()

class EncryptionService:
    def __init__(self):
        from cryptography.fernet import Fernet
        key = os.getenv("FERNET_KEY")
        if not key:
            raise ValueError("FERNET_KEY not set")
        self.fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> bytes:
        return self.fernet.encrypt(plaintext.encode('utf-8'))

    def decrypt(self, ciphertext: bytes) -> str:
        return self.fernet.decrypt(ciphertext).decode('utf-8')

encryption_service = EncryptionService()

@router.post("/projects/{project_id}/documents")
async def upload_document(
    project_id: str,
    file: Annotated[UploadFile, File()],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project ownership
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    # Validate file type
    if file.content_type not in ["text/plain", "text/markdown"]:
        raise HTTPException(400, "Only .txt and .md files allowed")

    # Read and validate size
    content_bytes = await file.read()
    if len(content_bytes) > 1024 * 1024:  # 1MB
        raise HTTPException(413, "File too large (max 1MB)")

    # Decode and encrypt
    try:
        plaintext = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(400, "File must be valid UTF-8 text")

    encrypted = encryption_service.encrypt(plaintext)

    # Store document
    doc = Document(
        project_id=project_id,
        filename=file.filename or "untitled.txt",
        content_encrypted=encrypted
    )
    db.add(doc)
    await db.flush()  # Get doc.id

    # Index for search (in same transaction)
    await db.execute(text("""
        INSERT INTO document_fts(document_id, filename, content)
        VALUES (:id, :filename, :content)
    """), {"id": doc.id, "filename": doc.filename, "content": plaintext})

    await db.commit()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "created_at": doc.created_at.isoformat()
    }
```

### Flutter Document List with Provider
```dart
// Source: https://docs.flutter.dev/data-and-backend/state-mgmt/simple
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class Document {
  final String id;
  final String filename;
  final DateTime createdAt;

  Document({required this.id, required this.filename, required this.createdAt});

  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'],
      filename: json['filename'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class DocumentProvider extends ChangeNotifier {
  List<Document> _documents = [];
  bool _loading = false;
  String? _error;

  List<Document> get documents => _documents;
  bool get loading => _loading;
  String? get error => _error;

  Future<void> loadDocuments(String projectId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await dio.get('/projects/$projectId/documents');
      _documents = (response.data as List)
          .map((json) => Document.fromJson(json))
          .toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> uploadDocument(String projectId, String filePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });

    final response = await dio.post(
      '/projects/$projectId/documents',
      data: formData,
    );

    final newDoc = Document.fromJson(response.data);
    _documents.add(newDoc);
    notifyListeners();
  }
}

class DocumentListScreen extends StatelessWidget {
  final String projectId;

  const DocumentListScreen({required this.projectId});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => DocumentProvider()..loadDocuments(projectId),
      child: Consumer<DocumentProvider>(
        builder: (context, provider, child) {
          if (provider.loading) {
            return Center(child: CircularProgressIndicator());
          }

          if (provider.error != null) {
            return Center(child: Text('Error: ${provider.error}'));
          }

          return ListView.builder(
            itemCount: provider.documents.length,
            itemBuilder: (context, index) {
              final doc = provider.documents[index];
              return ListTile(
                leading: Icon(Icons.description),
                title: Text(doc.filename),
                subtitle: Text(doc.createdAt.toString()),
                onTap: () {
                  // Navigate to document detail
                },
              );
            },
          );
        },
      ),
    );
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| backref parameter | back_populates on both sides | SQLAlchemy 2.0 (2023) | Better type checking, explicit relationships |
| FTS3/FTS4 | FTS5 | SQLite 3.9.0 (2015) | Better ranking (bm25), column filters, phrase queries |
| Manual cascade delete | Database CASCADE + ORM cascade | SQLAlchemy 1.4+ | Atomic deletes, better performance |
| Synchronous SQLAlchemy | Async SQLAlchemy 2.0 | SQLAlchemy 1.4/2.0 | Non-blocking, better FastAPI integration |
| PyCrypto | cryptography (PyCA) | 2016 | Active maintenance, NIST compliance, better APIs |
| file_picker 4.x | file_picker 10.x | 2024 | Better web support, null safety, unified API |

**Deprecated/outdated:**
- **backref:** Use back_populates for explicit bidirectional relationships (better type hints)
- **FTS3/FTS4:** Use FTS5 for better performance and features
- **PyCrypto:** Unmaintained since 2014, use cryptography library instead
- **Synchronous SQLAlchemy with FastAPI:** Use async sessions to avoid blocking

## Open Questions

Things that couldn't be fully resolved:

1. **FTS5 Encryption Strategy**
   - What we know: FTS5 requires plaintext for indexing, cannot search encrypted content
   - What's unclear: Security implications of storing plaintext in FTS5 table alongside encrypted documents table
   - Recommendation: Document clearly that search requires plaintext storage; consider column-level encryption for FTS5 table at database level (PostgreSQL supports this) or accept tradeoff for MVP. For highly sensitive documents, offer "exclude from search" option.

2. **Encryption Key Rotation**
   - What we know: MultiFernet supports key rotation, old tokens remain decryptable
   - What's unclear: How to batch re-encrypt thousands of documents during rotation without downtime
   - Recommendation: Defer key rotation to post-MVP; for MVP, generate single key and document rotation procedure. Consider background job for gradual re-encryption.

3. **SQLite vs PostgreSQL FTS Performance**
   - What we know: SQLite FTS5 is embedded and fast for <10k documents; PostgreSQL has different FTS
   - What's unclear: At what scale FTS5 performance degrades, migration path to PostgreSQL FTS
   - Recommendation: FTS5 sufficient for MVP (expect <1000 documents per user); when migrating to PostgreSQL, use pg_trgm or external search service (Elasticsearch/Meilisearch). Plan migration as separate research phase.

4. **Mobile Platform File Size Limits**
   - What we know: iOS and Android have different memory constraints for file operations
   - What's unclear: Practical file size limits for mobile uploads without OOM
   - Recommendation: Start with conservative 1MB limit; monitor crash reports; implement client-side validation before upload

## Sources

### Primary (HIGH confidence)
- [SQLAlchemy 2.0 Basic Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html) - Foreign key patterns, back_populates, cascade options
- [SQLAlchemy 2.0 Cascades](https://docs.sqlalchemy.org/en/20/orm/cascades.html) - Delete cascade, delete-orphan, passive_deletes
- [SQLite FTS5 Extension](https://sqlite.org/fts5.html) - Virtual table creation, MATCH queries, bm25() ranking
- [Cryptography Fernet Documentation](https://cryptography.io/en/latest/fernet/) - Key generation, encryption/decryption, limitations
- [FastAPI Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) - UploadFile usage, validation, security
- [file_picker Package](https://pub.dev/packages/file_picker) - Installation, file type filtering, cross-platform support
- [SQLite Foreign Key Support](https://sqlite.org/foreignkeys.html) - PRAGMA foreign_keys, CASCADE actions

### Secondary (MEDIUM confidence)
- [Better Stack FastAPI File Upload Guide](https://betterstack.com/community/guides/scaling-python/uploading-files-using-fastapi/) - Security practices, size limits, streaming
- [SQLAlchemy Async I/O Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - Async session usage, lazy loading issues
- [SQLAlchemy Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html) - selectinload, joinedload patterns
- [Flutter Provider Simple State Management](https://docs.flutter.dev/data-and-backend/state-mgmt/simple) - ChangeNotifier, MultiProvider patterns
- [Dio Package Documentation](https://pub.dev/packages/dio) - File upload, progress tracking
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/en/latest/) - Async SQLite usage

### Tertiary (LOW confidence - WebSearch findings)
- [Advanced SQLAlchemy SelectinLoad Strategies 2025](https://www.johal.in/advanced-sqlalchemy-2-0-selectinload-and-withparent-strategies-2025/) - Performance optimization patterns
- [Mastering Responsive UIs in Flutter Guide](https://dev.to/dariodigregorio/mastering-responsive-uis-in-flutter-the-full-guide-3g6i) - Master-detail layout patterns
- [Building a Secure File Upload API in FastAPI](https://noone-m.github.io/2025-12-10-fastapi-file-upload/) - Security best practices

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries officially documented, widely adopted, proven in production
- Database schema: HIGH - SQLAlchemy 2.0 official patterns, verified cascade behavior
- Encryption: HIGH - PyCA cryptography is NIST-recommended, official documentation
- FTS5: HIGH - SQLite official documentation, proven implementation
- File upload: HIGH - FastAPI official tutorial, established patterns
- Flutter patterns: MEDIUM - file_picker well-documented but fewer official Flutter examples for master-detail
- Architecture: MEDIUM - Patterns synthesized from multiple sources, need validation in context

**Research date:** 2026-01-18
**Valid until:** 60 days (stable technologies, mature libraries, slow-moving standards)

**Key uncertainties flagged for validation:**
- FTS5 plaintext storage security implications (document in requirements)
- Encryption key rotation at scale (defer to post-MVP)
- SQLite→PostgreSQL FTS migration path (research separately when scaling)
- Mobile file size limits (validate empirically during testing)
