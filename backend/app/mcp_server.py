"""
FastMCP HTTP server for Assistant thread file generation.

Provides a real MCP server mounted in FastAPI at /mcp. The Claude CLI subprocess
connects to this server via --mcp-config when artifact_generation=True.

Per-request context (db session + thread_id) is propagated via a session token
embedded in the system prompt. The MCP tool resolves it from the session registry.

Phase 72: Backend File Generation
"""
import json
import logging

from mcp.server.fastmcp import FastMCP

from app.models import Artifact, ArtifactType

logger = logging.getLogger(__name__)

# FastMCP server instance — exported for mounting in main.py
mcp_app = FastMCP("assistant-tools")

# Session registry: maps session_token -> {"db": AsyncSession, "thread_id": str}
# Populated by register_mcp_session() before CLI subprocess receives the system prompt.
# Cleaned up by unregister_mcp_session() after the CLI subprocess completes.
_session_registry: dict[str, dict] = {}


def register_mcp_session(token: str, db, thread_id: str) -> None:
    """Register a database session and thread_id for a file generation request.

    Args:
        token: Unique session token embedded in the system prompt.
        db: SQLAlchemy AsyncSession for persisting the artifact.
        thread_id: ID of the Assistant thread owning the artifact.
    """
    _session_registry[token] = {"db": db, "thread_id": thread_id}
    logger.debug(f"Registered MCP session: {token[:8]}... thread_id={thread_id}")


def unregister_mcp_session(token: str) -> None:
    """Remove a session from the registry after the CLI subprocess completes.

    Args:
        token: Session token to remove (no-op if already removed).
    """
    _session_registry.pop(token, None)
    logger.debug(f"Unregistered MCP session: {token[:8]}...")


@mcp_app.tool()
async def save_artifact(session_token: str, title: str, content_markdown: str) -> str:
    """Save a generated file artifact for the current Assistant thread.

    Call ONCE with the session_token from your system prompt, then stop.
    Do not call this tool again after it returns successfully.

    Args:
        session_token: Token from the system prompt identifying the request context.
        title: Title/filename for the generated file artifact.
        content_markdown: Full content of the generated file in markdown format.

    Returns:
        ARTIFACT_CREATED marker string on success, or error string on failure.
    """
    ctx = _session_registry.get(session_token)
    if not ctx:
        logger.warning(f"MCP save_artifact: session not found for token {session_token[:8]}...")
        return "Error: session context not found"

    artifact = Artifact(
        thread_id=ctx["thread_id"],
        artifact_type=ArtifactType.GENERATED_FILE,
        title=title,
        content_markdown=content_markdown,
    )
    ctx["db"].add(artifact)
    await ctx["db"].commit()
    await ctx["db"].refresh(artifact)

    event_data = {
        "id": artifact.id,
        "artifact_type": "generated_file",
        "title": artifact.title,
    }
    logger.info(f"MCP save_artifact: created artifact {artifact.id} for thread {ctx['thread_id']}")
    return f"ARTIFACT_CREATED:{json.dumps(event_data)}|File generated successfully."
