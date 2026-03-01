"""
OpenClaw Tools Integration.

Maps OpenClaw skills to XtraSkill tools and provides sub-agent spawning.
"""
from .tool_mapper import OpenClawToolMapper
from .subagent import OpenClawSubAgent

__all__ = ["OpenClawToolMapper", "OpenClawSubAgent"]
