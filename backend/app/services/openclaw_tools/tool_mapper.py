"""
OpenClaw Tool Mapper.

Maps OpenClaw skills to XtraSkill-compatible tool definitions.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class OpenClawToolMapper:
    """
    Maps OpenClaw skills to tool definitions for LLM consumption.
    
    When using OpenClaw as the LLM provider, this class provides
    tool definitions that the agent can use.
    """
    
    # Tool definitions for OpenClaw skills
    TOOL_DEFINITIONS = [
        {
            "name": "search_documents",
            "description": "Search across all documents in the user's project for relevant information. Use this when the user asks about something that might be in uploaded documents.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "save_artifact",
            "description": "Save a generated file or document to the user's project. Use this when the AI creates content the user wants to keep (BRDs, user stories, diagrams, code).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title/name of the artifact"
                    },
                    "content_markdown": {
                        "type": "string",
                        "description": "Content in Markdown format"
                    },
                    "artifact_type": {
                        "type": "string",
                        "description": "Type of artifact",
                        "enum": ["brd", "user_stories", "notes", "other"]
                    }
                },
                "required": ["title", "content_markdown"]
            }
        },
        {
            "name": "send_email",
            "description": "Send an email via the user's configured email account. Requires email skill to be configured in OpenClaw.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        },
        {
            "name": "check_calendar",
            "description": "Check the user's Google Calendar for events. Use this to see today's meetings or upcoming events.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to look ahead",
                        "default": 1
                    }
                }
            }
        },
        {
            "name": "post_twitter",
            "description": "Post content to Twitter/X. Requires Twitter skill to be configured in OpenClaw.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Tweet content (max 280 characters)"
                    }
                },
                "required": ["content"]
            }
        },
        {
            "name": "spawn_subagent",
            "description": "Spawn a specialized sub-agent to handle a specific task in parallel. The sub-agent works independently and reports back.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "description": "Type of agent to spawn",
                        "enum": ["dev", "debugger", "code-reviewer", "architect"]
                    },
                    "task": {
                        "type": "string",
                        "description": "Task description for the sub-agent"
                    }
                },
                "required": ["agent_type", "task"]
            }
        },
        {
            "name": "web_search",
            "description": "Search the web for current information. Use when you need up-to-date data or facts beyond your training data.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    ]
    
    def __init__(self, enabled_tools: Optional[List[str]] = None):
        """
        Initialize tool mapper.
        
        Args:
            enabled_tools: List of tool names to enable. If None, all tools enabled.
        """
        # Use a dict for O(1) lookups
        all_tool_names = {t["name"] for t in self.TOOL_DEFINITIONS}
        if enabled_tools is None:
            enabled_tools = list(all_tool_names)
        
        # Create dict: tool_name -> enabled
        self._enabled_tools: Dict[str, bool] = {
            name: name in enabled_tools for name in all_tool_names
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get enabled tool definitions.
        
        Returns:
            List of tool definitions for LLM
        """
        return [
            tool for tool in self.TOOL_DEFINITIONS
            if self._enabled_tools.get(tool["name"], False)
        ]
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a specific tool is enabled."""
        return self._enabled_tools.get(tool_name, False)
    
    def enable_tool(self, tool_name: str) -> None:
        """Enable a specific tool."""
        if tool_name in self._enabled_tools:
            self._enabled_tools[tool_name] = True
    
    def disable_tool(self, tool_name: str) -> None:
        """Disable a specific tool."""
        if tool_name in self._enabled_tools:
            self._enabled_tools[tool_name] = False


# Default instance
default_tool_mapper = OpenClawToolMapper()
