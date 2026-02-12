"""
Agent Service using Claude Agent SDK.

Provides AI-powered conversations with business-analyst skill integration.
Uses @tool decorator for search_documents and save_artifact tools.
"""
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from contextvars import ContextVar

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
)
from claude_agent_sdk.types import StreamEvent

from app.config import settings
from app.services.skill_loader import load_skill_prompt
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


class AgentService:
    """
    Claude Agent SDK service for skill-enhanced conversations.

    Uses the business-analyst skill for structured discovery and BRD generation.
    """

    def __init__(self):
        """Initialize agent service with SDK tools and skill prompt."""
        # Create MCP server with tools
        # Note: Using save_artifact_tool for all artifact generation (including BRDs)
        # to prevent duplicate tool confusion
        self.tools_server = create_sdk_mcp_server(
            name="ba-tools",
            version="1.0.0",
            tools=[search_documents_tool, save_artifact_tool]
        )

        # Load skill prompt (cached)
        try:
            self.skill_prompt = load_skill_prompt()
            logger.info(f"Loaded skill prompt ({len(self.skill_prompt)} chars)")
        except Exception as e:
            logger.error(f"Failed to load skill prompt: {e}")
            # Fall back to basic prompt
            self.skill_prompt = self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if skill files cannot be loaded."""
        return """You are a Business Analyst AI assistant helping users explore and document software requirements.

Your role is to:
1. Ask ONE question at a time during discovery
2. Proactively identify edge cases and missing requirements
3. Clarify ambiguous terms before proceeding
4. Redirect technical implementation discussions to business focus
5. Generate comprehensive Business Requirements Documents when requested

Be conversational but thorough. Help users think through their requirements completely."""

    async def stream_chat(
        self,
        messages: list[Dict[str, Any]],
        project_id: str,
        thread_id: str,
        db
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response using Claude Agent SDK.

        Yields SSE-formatted events:
        - text_delta: Incremental text from Claude
        - tool_executing: Tool is being executed
        - artifact_created: An artifact was generated and saved
        - message_complete: Final message with usage stats
        - error: Error occurred

        Args:
            messages: Conversation history in Claude format
            project_id: Project ID for document search context
            thread_id: Thread ID for artifact association
            db: Database session

        Yields:
            Dict with 'event' and 'data' keys for SSE
        """
        # Set context variables for tools
        _db_context.set(db)
        _project_id_context.set(project_id)
        _thread_id_context.set(thread_id)
        _documents_used_context.set([])  # Initialize for source attribution tracking

        # Build the prompt from messages
        # Convert message history to single prompt for SDK
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, str):
                prompt_parts.append(f"[{role.upper()}]: {content}")
            elif isinstance(content, list):
                # Handle tool results or multi-part content
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "tool_result":
                            prompt_parts.append(f"[TOOL_RESULT]: {part.get('content', '')}")
                        elif part.get("type") == "text":
                            prompt_parts.append(f"[{role.upper()}]: {part.get('text', '')}")
                        else:
                            prompt_parts.append(f"[{role.upper()}]: {part.get('content', part.get('text', ''))}")

        full_prompt = "\n\n".join(prompt_parts)

        # Configure SDK options
        # max_turns=3 prevents infinite artifact generation loops
        # Typical flow: 1) search docs, 2) generate artifact, 3) respond - done
        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": self.skill_prompt
            },
            mcp_servers={"ba": self.tools_server},
            allowed_tools=[
                "mcp__ba__search_documents",
                "mcp__ba__save_artifact",
            ],
            permission_mode="acceptEdits",
            include_partial_messages=True,
            model="claude-sonnet-4-5-20250514",
            max_turns=3
        )

        accumulated_text = ""
        usage_data = {"input_tokens": 0, "output_tokens": 0}

        try:
            async for message in query(prompt=full_prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Stream text delta
                            text = block.text
                            accumulated_text += text
                            yield {
                                "event": "text_delta",
                                "data": json.dumps({"text": text})
                            }

                        elif isinstance(block, ToolUseBlock):
                            # Tool being called
                            tool_name = block.name
                            if "save_artifact" in tool_name:
                                yield {
                                    "event": "tool_executing",
                                    "data": json.dumps({"status": "Generating artifact..."})
                                }
                            elif "generate_brd" in tool_name:
                                yield {
                                    "event": "tool_executing",
                                    "data": json.dumps({"status": "Generating Business Requirements Document..."})
                                }
                            else:
                                yield {
                                    "event": "tool_executing",
                                    "data": json.dumps({"status": "Searching project documents..."})
                                }

                        elif isinstance(block, ToolResultBlock):
                            # Tool completed - check for artifact event in result
                            if hasattr(block, 'content'):
                                content = block.content
                                if isinstance(content, str) and "ARTIFACT_CREATED:" in content:
                                    # Parse the artifact event data
                                    try:
                                        marker_start = content.index("ARTIFACT_CREATED:") + len("ARTIFACT_CREATED:")
                                        marker_end = content.index("|", marker_start)
                                        event_json = content[marker_start:marker_end]
                                        event_data = json.loads(event_json)
                                        yield {
                                            "event": "artifact_created",
                                            "data": json.dumps(event_data)
                                        }
                                    except (ValueError, json.JSONDecodeError) as e:
                                        logger.warning(f"Failed to parse artifact event: {e}")

                elif isinstance(message, StreamEvent):
                    # Handle streaming events for partial messages
                    if hasattr(message, 'delta') and message.delta:
                        delta = message.delta
                        if hasattr(delta, 'text'):
                            text = delta.text
                            accumulated_text += text
                            yield {
                                "event": "text_delta",
                                "data": json.dumps({"text": text})
                            }

                elif isinstance(message, ResultMessage):
                    # Final result with usage stats
                    if hasattr(message, 'usage') and message.usage:
                        usage_data = {
                            "input_tokens": getattr(message.usage, 'input_tokens', 0),
                            "output_tokens": getattr(message.usage, 'output_tokens', 0)
                        }

                    # Get final text content if available
                    if hasattr(message, 'result') and message.result:
                        result = message.result
                        if isinstance(result, str):
                            # If result is different from accumulated, use it
                            if result and result != accumulated_text:
                                accumulated_text = result

                    # Get documents used for source attribution
                    try:
                        documents_used = _documents_used_context.get()
                    except LookupError:
                        documents_used = []

                    yield {
                        "event": "message_complete",
                        "data": json.dumps({
                            "content": accumulated_text,
                            "usage": usage_data,
                            "documents_used": documents_used  # SRC-04: empty array when no docs
                        })
                    }
                    return

            # If we didn't get a ResultMessage, yield completion anyway
            # Get documents used for source attribution
            try:
                documents_used = _documents_used_context.get()
            except LookupError:
                documents_used = []

            yield {
                "event": "message_complete",
                "data": json.dumps({
                    "content": accumulated_text,
                    "usage": usage_data,
                    "documents_used": documents_used  # SRC-04: empty array when no docs
                })
            }

        except Exception as e:
            logger.error(f"Agent SDK error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": f"AI service error: {str(e)}"})
            }
