"""
Shared MCP tool definitions for BA Assistant.

Provides reusable tool definitions for search_documents and save_artifact
that can be used by:
- AgentService (existing SDK-based chat)
- ClaudeAgentAdapter (Phase 58 - SDK multi-turn)
- ClaudeCLIAdapter (Phase 59 - CLI subprocess)

All tools use ContextVars for request-scoped state management.
"""
import json
import logging
from contextvars import ContextVar
from typing import Dict, Any

from claude_agent_sdk import tool, create_sdk_mcp_server

from app.services.document_search import search_documents
from app.models import Artifact, ArtifactType

logger = logging.getLogger(__name__)

# Context variables for passing request context to tools
_db_context: ContextVar[Any] = ContextVar("db_context")
_project_id_context: ContextVar[str] = ContextVar("project_id_context")
_thread_id_context: ContextVar[str] = ContextVar("thread_id_context")
_documents_used_context: ContextVar[list] = ContextVar("documents_used_context")


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

    try:
        db = _db_context.get()
        project_id = _project_id_context.get()
    except LookupError:
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

    formatted = []
    for doc_id, filename, snippet, score, content_type, metadata_json in results[:3]:
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

    # Track documents used for source attribution (PITFALL-05)
    try:
        docs_used = _documents_used_context.get()
        for doc_id, filename, snippet, score, content_type, metadata_json in results[:3]:
            if not any(d['id'] == doc_id for d in docs_used):  # Avoid duplicates
                metadata = json.loads(metadata_json) if metadata_json else {}
                docs_used.append({
                    'id': doc_id,
                    'filename': filename,
                    'content_type': content_type or 'text/plain',
                    'metadata': metadata,
                })
        _documents_used_context.set(docs_used)
    except LookupError:
        pass  # Context not available, skip tracking

    return {
        "content": [{
            "type": "text",
            "text": "\n\n---\n\n".join(formatted)
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
    """Create MCP server with BA Assistant tools for reuse across adapters."""
    return create_sdk_mcp_server(
        name="ba-tools",
        version="1.0.0",
        tools=[search_documents_tool, save_artifact_tool]
    )


__all__ = [
    "search_documents_tool",
    "save_artifact_tool",
    "create_ba_mcp_server",
    "_db_context",
    "_project_id_context",
    "_thread_id_context",
    "_documents_used_context",
]
