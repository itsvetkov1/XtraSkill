"""
Shared MCP tool definitions for BA Assistant.

Provides reusable tool definitions for search_documents and save_artifact
that can be used by:
- ClaudeAgentAdapter (Phase 58 - SDK multi-turn) — uses HTTP transport with session registry
- ClaudeCLIAdapter (Phase 59 - CLI subprocess)

Tools support both ContextVar (for backward compatibility) and HTTP header-based context.
"""
import asyncio
import json
import logging
from contextvars import ContextVar
from typing import Dict, Any, Optional

from claude_agent_sdk import tool, create_sdk_mcp_server

from app.services.document_search import search_documents
from app.models import Artifact, ArtifactType

logger = logging.getLogger(__name__)

# Context variables for passing request context to tools (backward compatibility)
_db_context: ContextVar[Any] = ContextVar("db_context")
_project_id_context: ContextVar[str] = ContextVar("project_id_context")
_thread_id_context: ContextVar[str] = ContextVar("thread_id_context")
_documents_used_context: ContextVar[list] = ContextVar("documents_used_context")

# Session registry for HTTP-based context propagation
# Maps session_id -> db session for HTTP MCP transport
_session_registry: Dict[str, Any] = {}

# HTTP MCP server singleton (lazily initialized)
_http_mcp_server_url: Optional[str] = None
_http_mcp_server_task: Optional[asyncio.Task] = None


def register_db_session(session_id: str, db: Any) -> None:
    """
    Register a database session for HTTP MCP transport.

    Args:
        session_id: Unique session identifier
        db: SQLAlchemy AsyncSession
    """
    _session_registry[session_id] = db
    logger.debug(f"Registered db session: {session_id}")


def unregister_db_session(session_id: str) -> None:
    """
    Unregister a database session from HTTP MCP transport.

    Args:
        session_id: Unique session identifier
    """
    if session_id in _session_registry:
        del _session_registry[session_id]
        logger.debug(f"Unregistered db session: {session_id}")


def _get_context_from_headers_or_contextvar(
    args: Dict[str, Any],
    header_prefix: str = "X-"
) -> tuple[Any, str, Optional[int]]:
    """
    Extract context from HTTP headers (if present) or fall back to ContextVar.

    Returns:
        tuple: (db, project_id, max_results)
    """
    # Try to extract from args (HTTP headers passed by SDK)
    # The SDK MCP HTTP transport may pass headers in the args dict
    session_id = args.get("X-DB-Session-ID") or args.get("x-db-session-id")
    project_id = args.get("X-Project-ID") or args.get("x-project-id")
    max_results_str = args.get("X-Max-Results") or args.get("x-max-results")

    max_results = int(max_results_str) if max_results_str else None

    if session_id and project_id:
        # HTTP transport mode
        db = _session_registry.get(session_id)
        if db:
            logger.debug(f"Using HTTP context: session={session_id}, project={project_id}")
            return db, project_id, max_results

    # Fall back to ContextVar
    try:
        db = _db_context.get()
        project_id = _project_id_context.get()
        logger.debug("Using ContextVar context")
        return db, project_id, max_results
    except LookupError:
        return None, None, max_results


# Tool definitions using @tool decorator
@tool(
    "search_documents",
    """Search project documents for relevant information.

USE THIS TOOL WHEN:
- User mentions documents, files, or project materials
- User asks about policies, requirements, or specifications
- User references something that might be in uploaded documents
- You need context about the project to answer accurately
- Discussion involves specific features, constraints, or decisions that may be documented

DO NOT USE WHEN:
- User is asking general questions not related to project documents
- You already have sufficient context from conversation history

Returns: Document snippets with filenames and relevance scores.""",
    {"query": str}
)
async def search_documents_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute document search and return results."""
    query_text = args.get("query", "")

    # Get context from HTTP headers or ContextVar
    db, project_id, max_results = _get_context_from_headers_or_contextvar(args)

    if not db or not project_id:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Search context not available"
            }]
        }

    results = await search_documents(db, project_id, query_text)

    if not results:
        return {
            "content": [{
                "type": "text",
                "text": "No relevant documents found for this query."
            }]
        }

    # Use max_results from HTTP header (default: 3 for ContextVar, 5 for HTTP)
    result_limit = max_results if max_results is not None else 3

    formatted = []
    documents_used = []
    for doc_id, filename, snippet, score, content_type, metadata_json in results[:result_limit]:
        # Clean up snippet HTML markers for readability
        clean_snippet = snippet.replace("<mark>", "**").replace("</mark>", "**")

        # Add format-specific context prefix
        metadata = json.loads(metadata_json) if metadata_json else {}
        if metadata.get('sheet_names'):
            prefix = f"[Sheet: {metadata['sheet_names'][0]}] "
        elif metadata.get('page_count'):
            prefix = ""  # Page markers already in content from PDF parser
        else:
            prefix = ""

        formatted.append(f"**{filename}**: {prefix}\n{clean_snippet}")

        # Track for source attribution
        documents_used.append({
            'id': doc_id,
            'filename': filename,
            'content_type': content_type or 'text/plain',
            'metadata': metadata,
        })

    # Try to update ContextVar for backward compatibility
    try:
        docs_used = _documents_used_context.get()
        for doc in documents_used:
            if not any(d['id'] == doc['id'] for d in docs_used):  # Avoid duplicates
                docs_used.append(doc)
        _documents_used_context.set(docs_used)
    except LookupError:
        pass  # Context not available, skip ContextVar tracking

    # For HTTP transport, embed documents_used in the result with marker
    result_text = "\n\n---\n\n".join(formatted)
    if args.get("X-DB-Session-ID") or args.get("x-db-session-id"):
        # HTTP mode: add DOCUMENTS_USED marker for adapter to parse
        result_text += f"\n\nDOCUMENTS_USED:{json.dumps(documents_used)}|"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }]
    }


@tool(
    "save_artifact",
    """Save a business analysis artifact to the current conversation thread.

USE THIS TOOL WHEN:
- User explicitly requests "create the documentation", "generate the BRD", "build the requirements document"
- You have completed discovery and gathered sufficient business requirements
- User asks to "create", "generate", "write", or "document" requirements

BEFORE USING:
- Verify primary business objective is clearly defined
- Verify target user personas are identified
- Verify key user flows are documented
- Verify success metrics are specified
- Consider using search_documents first to gather project context

CRITICAL: Call this tool ONCE per user request. After saving the artifact:
1. STOP generating - do not call this tool again
2. Present the result to the user
3. Wait for explicit user feedback before taking any further action
4. Do NOT generate additional versions unless user explicitly asks""",
    {
        "artifact_type": str,
        "title": str,
        "content_markdown": str
    }
)
async def save_artifact_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Save artifact to database and return confirmation."""
    # Get context from HTTP headers or ContextVar
    session_id = args.get("X-DB-Session-ID") or args.get("x-db-session-id")
    thread_id_arg = args.get("X-Thread-ID") or args.get("x-thread-id")

    if session_id and thread_id_arg:
        # HTTP transport mode
        db = _session_registry.get(session_id)
        thread_id = thread_id_arg
        if not db:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: Artifact context not available (session not found)"
                }]
            }
    else:
        # ContextVar mode
        try:
            db = _db_context.get()
            thread_id = _thread_id_context.get()
        except LookupError:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: Artifact context not available"
                }]
            }

    try:
        artifact_type = ArtifactType(args["artifact_type"])
    except ValueError:
        # Default to requirements_doc for BRDs
        artifact_type = ArtifactType.REQUIREMENTS_DOC

    artifact = Artifact(
        thread_id=thread_id,
        artifact_type=artifact_type,
        title=args["title"],
        content_markdown=args["content_markdown"]
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    # Store event data as JSON string in the tool result
    # This will be parsed by the streaming handler
    event_data = {
        "id": artifact.id,
        "artifact_type": artifact.artifact_type.value,
        "title": artifact.title
    }

    return {
        "content": [{
            "type": "text",
            "text": f"ARTIFACT_CREATED:{json.dumps(event_data)}|"
                    f"Artifact '{artifact.title}' saved successfully. "
                    "STOP HERE. Your task is complete. "
                    "Say 'Done! I've created [title]. Let me know if you'd like changes.' "
                    "Do NOT call save_artifact again. Do NOT generate more documents."
        }]
    }


def create_ba_mcp_server():
    """Create MCP server with BA Assistant tools for reuse across adapters (ContextVar mode)."""
    return create_sdk_mcp_server(
        name="ba-tools",
        version="1.0.0",
        tools=[search_documents_tool, save_artifact_tool]
    )


async def start_mcp_http_server() -> tuple[str, Any]:
    """
    Start HTTP MCP server for HTTP-based context propagation.

    NOTE: This is a placeholder for Phase 58 POC. Full HTTP MCP server implementation
    requires a separate FastAPI app or HTTP server that implements the MCP protocol over HTTP.
    For now, this returns a dummy URL and the adapter will need to use the in-process
    MCP server with ContextVars as a fallback.

    Returns:
        tuple: (url, server_handle) where server_handle has an async stop() method
    """
    # PLACEHOLDER: Full HTTP MCP server would require:
    # 1. FastAPI or similar HTTP server on a dynamic port
    # 2. MCP protocol implementation over HTTP (SSE or WebSocket)
    # 3. Request handler that extracts headers and calls tools
    # 4. Background task to run the server
    #
    # For POC, we'll use in-process MCP with context propagation via the adapter
    logger.warning("HTTP MCP server not yet implemented - using in-process MCP with ContextVars")
    return ("http://localhost:0/mcp", None)


def get_mcp_http_server_url() -> Optional[str]:
    """
    Get the URL of the HTTP MCP server (singleton, lazily initialized).

    NOTE: Phase 58 POC uses in-process MCP with ContextVars. HTTP server
    implementation is deferred to production hardening phase.

    Returns:
        str: MCP server URL or None if not available
    """
    global _http_mcp_server_url

    if _http_mcp_server_url is None:
        # For POC, return None to signal that HTTP transport is not available
        # The adapter will fall back to in-process MCP
        logger.debug("HTTP MCP server not available - adapter will use in-process MCP")
        _http_mcp_server_url = None

    return _http_mcp_server_url


__all__ = [
    "search_documents_tool",
    "save_artifact_tool",
    "create_ba_mcp_server",
    "register_db_session",
    "unregister_db_session",
    "get_mcp_http_server_url",
    "start_mcp_http_server",
    "_db_context",
    "_project_id_context",
    "_thread_id_context",
    "_documents_used_context",
]
