"""
AI Service for Claude API integration.

DEPRECATED: This service uses direct Anthropic API.
Use AgentService instead for skill-enhanced conversations.

Kept as fallback for testing and gradual migration.
"""
import warnings
import anthropic
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.config import settings
from app.services.document_search import search_documents
from app.models import Artifact, ArtifactType

# Claude model to use
MODEL = "claude-sonnet-4-5-20250929"

# System prompt for BA assistant behavior
SYSTEM_PROMPT = """You are a Business Analyst AI assistant helping users explore and document software requirements. Your role is to:

1. PROACTIVELY IDENTIFY EDGE CASES: When users describe requirements, think about what could go wrong. Ask questions like "What happens if a user enters invalid data?" or "How should the system behave when the network is unavailable?" without being prompted.

2. ASK CLARIFYING QUESTIONS: Explore requirements deeply. Don't assume - ask about:
   - User personas and their specific needs
   - Error handling and edge cases
   - Performance requirements and constraints
   - Integration points with other systems
   - Security and access control considerations

3. SEARCH DOCUMENTS AUTONOMOUSLY: When users mention anything that might be documented (policies, requirements, specifications, notes), use the search_documents tool to find relevant context. Reference what you find.

4. MAINTAIN CONTEXT: Reference earlier parts of the conversation. Remember decisions made and requirements discussed. Build on previous discussion points.

5. GENERATE ARTIFACTS: When users request documentation (user stories, acceptance criteria, requirements docs), use the save_artifact tool to create professional deliverables. Review the full conversation to ensure comprehensive coverage.

Be conversational but thorough. Help users think through their requirements completely. Your goal is to ensure no important edge case or requirement is missed."""

# Tool definition for document search
DOCUMENT_SEARCH_TOOL = {
    "name": "search_documents",
    "description": """Search project documents for relevant information.

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
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to find relevant documents. Use specific terms from the conversation."
            }
        },
        "required": ["query"]
    }
}

# Tool definition for saving artifacts
SAVE_ARTIFACT_TOOL = {
    "name": "save_artifact",
    "description": """Save a business analysis artifact to the current conversation thread.

USE THIS TOOL WHEN:
- User requests user stories, acceptance criteria, or requirements documents
- You have gathered enough context from conversation and documents
- User asks to "create", "generate", "write", or "document" requirements

BEFORE USING:
- Consider using search_documents first to gather project context
- Review the full conversation for ALL requirements discussed
- Ensure comprehensive coverage, not just recent messages

You may call this tool multiple times to create multiple artifacts.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "artifact_type": {
                "type": "string",
                "enum": ["user_stories", "acceptance_criteria", "requirements_doc"],
                "description": "Type: user_stories (Given/When/Then), acceptance_criteria (testable checklist), requirements_doc (IEEE 830-style)"
            },
            "title": {
                "type": "string",
                "description": "Descriptive title, e.g., 'Login Feature - User Stories'"
            },
            "content_markdown": {
                "type": "string",
                "description": "Full artifact content in markdown with proper headers and formatting"
            }
        },
        "required": ["artifact_type", "title", "content_markdown"]
    }
}


class AIService:
    """Claude AI service for streaming chat with tool use.

    DEPRECATED: Use AgentService for skill-enhanced conversations.
    """

    def __init__(self):
        warnings.warn(
            "AIService is deprecated. Use AgentService for skill-enhanced conversations.",
            DeprecationWarning,
            stacklevel=2
        )
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: dict,
        project_id: str,
        thread_id: str,
        db
    ) -> tuple[str, Optional[dict]]:
        """
        Execute a tool and return result as string plus optional event data.

        Returns:
            tuple: (result_string, optional_event_dict)
            - result_string: Text to send back to Claude
            - optional_event_dict: Event to yield to frontend (e.g., artifact_created)
        """
        if tool_name == "save_artifact":
            artifact = Artifact(
                thread_id=thread_id,
                artifact_type=ArtifactType(tool_input["artifact_type"]),
                title=tool_input["title"],
                content_markdown=tool_input["content_markdown"]
            )
            db.add(artifact)
            await db.commit()
            await db.refresh(artifact)

            # Return success message and event for frontend
            event_data = {
                "id": artifact.id,
                "artifact_type": artifact.artifact_type.value,
                "title": artifact.title
            }
            return (
                f"Artifact saved successfully: '{artifact.title}' (ID: {artifact.id}). "
                "User can now export as PDF, Word, or Markdown from the artifacts list.",
                event_data
            )

        elif tool_name == "search_documents":
            query = tool_input.get("query", "")
            results = await search_documents(db, project_id, query)

            if not results:
                return ("No relevant documents found for this query.", None)

            formatted = []
            for doc_id, filename, snippet, score in results[:5]:
                # Clean up snippet HTML markers for Claude
                clean_snippet = snippet.replace("<mark>", "**").replace("</mark>", "**")
                formatted.append(f"**{filename}**:\n{clean_snippet}")

            return ("\n\n---\n\n".join(formatted), None)

        return (f"Unknown tool: {tool_name}", None)

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        project_id: str,
        thread_id: str,
        db
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response from Claude with tool use.

        Yields SSE-formatted events:
        - text_delta: Incremental text from Claude
        - tool_executing: Tool is being executed
        - artifact_created: An artifact was generated and saved
        - message_complete: Final message with usage stats
        - error: Error occurred
        """
        import json

        try:
            while True:
                async with self.client.messages.stream(
                    model=MODEL,
                    max_tokens=4096,
                    messages=messages,
                    tools=self.tools,
                    system=SYSTEM_PROMPT
                ) as stream:
                    accumulated_text = ""

                    async for text in stream.text_stream:
                        accumulated_text += text
                        yield {
                            "event": "text_delta",
                            "data": json.dumps({"text": text})
                        }

                    final = await stream.get_final_message()

                    # Check if we need to execute tools
                    if final.stop_reason != "tool_use":
                        # Done - yield completion event
                        yield {
                            "event": "message_complete",
                            "data": json.dumps({
                                "content": accumulated_text,
                                "usage": {
                                    "input_tokens": final.usage.input_tokens,
                                    "output_tokens": final.usage.output_tokens
                                }
                            })
                        }
                        return

                    # Execute tools
                    tool_results = []
                    for block in final.content:
                        if block.type == "tool_use":
                            # Show tool-specific status
                            if block.name == "save_artifact":
                                yield {
                                    "event": "tool_executing",
                                    "data": json.dumps({"status": "Generating artifact..."})
                                }
                            else:
                                yield {
                                    "event": "tool_executing",
                                    "data": json.dumps({"status": "Searching project documents..."})
                                }

                            result, event_data = await self.execute_tool(
                                block.name,
                                block.input,
                                project_id,
                                thread_id,
                                db
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })

                            # Emit artifact_created event if artifact was saved
                            if event_data and block.name == "save_artifact":
                                yield {
                                    "event": "artifact_created",
                                    "data": json.dumps(event_data)
                                }

                    # Continue conversation with tool results
                    messages.append({"role": "assistant", "content": final.content})
                    messages.append({"role": "user", "content": tool_results})

                    # Yield accumulated text before tool call
                    if accumulated_text:
                        yield {
                            "event": "text_delta",
                            "data": json.dumps({"text": "\n\n"})
                        }

        except anthropic.APIError as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"AI service error: {str(e)}"})
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Unexpected error: {str(e)}"})
            }
