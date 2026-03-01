"""
OpenClaw Sub-Agent Spawner.

Provides functionality to spawn OpenClaw sub-agents from XtraSkill.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OpenClawSubAgent:
    """
    Spawns and manages OpenClaw sub-agents.
    
    When the LLM needs to delegate work to a specialized agent,
    this class handles spawning and communication.
    """
    
    VALID_AGENTS = ["dev", "debugger", "code-reviewer", "architect"]
    
    def __init__(
        self,
        gateway_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize sub-agent spawner.
        
        Args:
            gateway_url: OpenClaw Gateway URL
            api_key: OpenClaw API key
        """
        self._gateway_url = gateway_url or settings.openclaw_gateway_url
        self._api_key = api_key or settings.openclaw_api_key
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._gateway_url.rstrip("/"),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def spawn(
        self,
        agent_type: str,
        task: str,
        mode: str = "run",
        thread: bool = False,
    ) -> Dict[str, Any]:
        """
        Spawn a sub-agent to handle a task.
        
        Args:
            agent_type: Type of agent (dev, debugger, code-reviewer, architect)
            task: Task description for the agent
            mode: "run" (one-shot) or "session" (persistent)
            thread: Whether to use thread-bound session
            
        Returns:
            Result from the agent
            
        Raises:
            ValueError: If agent_type is invalid
        """
        if agent_type not in self.VALID_AGENTS:
            raise ValueError(
                f"Invalid agent type: {agent_type}. "
                f"Valid types: {', '.join(self.VALID_AGENTS)}"
            )
        
        client = await self._get_client()
        
        payload = {
            "task": task,
            "mode": mode,
            "thread": thread,
        }
        
        # Map agent_type to label
        label_map = {
            "dev": "backend-worker",
            "debugger": "debugger",
            "code-reviewer": "code-reviewer",
            "architect": "architect",
        }
        payload["label"] = label_map.get(agent_type, agent_type)
        
        try:
            response = await client.post(
                "/api/sessions/spawn",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to spawn sub-agent: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def send_message(
        self,
        session_key: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send a message to an existing session.
        
        Args:
            session_key: Session to send to
            message: Message content
            
        Returns:
            Agent response
        """
        client = await self._get_client()
        
        payload = {
            "message": message,
        }
        
        try:
            response = await client.post(
                f"/api/sessions/{session_key}/send",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to send message: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def list_sessions(
        self,
        active_only: bool = True,
    ) -> Dict[str, Any]:
        """
        List active sessions.
        
        Args:
            active_only: Only return active sessions
            
        Returns:
            List of sessions
        """
        client = await self._get_client()
        
        params = {}
        if active_only:
            params["activeMinutes"] = 60
        
        try:
            response = await client.get(
                "/api/sessions",
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to list sessions: {e}")
            return {"sessions": [], "error": str(e)}


# Default instance
default_subagent = OpenClawSubAgent()
