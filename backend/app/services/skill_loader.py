"""
Skill Loader Service for Business-Analyst Skill.

Loads SKILL.md and all reference files to construct a complete
system prompt for Claude Agent SDK integration.
"""
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class SkillLoadError(Exception):
    """Raised when skill files cannot be loaded."""
    pass


def get_skill_directory() -> Path:
    """
    Get the skill directory path.

    Resolves skill_path relative to the project root (parent of backend/).

    Returns:
        Path to skill directory

    Raises:
        SkillLoadError: If directory doesn't exist
    """
    # Backend is in project_root/backend, skill is in project_root/.claude/...
    backend_dir = Path(__file__).parent.parent.parent  # backend/
    project_root = backend_dir.parent  # project root
    skill_dir = project_root / settings.skill_path

    if not skill_dir.exists():
        raise SkillLoadError(f"Skill directory not found: {skill_dir}")

    return skill_dir


def get_skill_references(skill_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Load all reference files from skill's references directory.

    Args:
        skill_dir: Optional skill directory path (uses config if not provided)

    Returns:
        Dict mapping filename (without .md) to file contents

    Raises:
        SkillLoadError: If references directory doesn't exist
    """
    if skill_dir is None:
        skill_dir = get_skill_directory()

    refs_dir = skill_dir / "references"

    if not refs_dir.exists():
        logger.warning(f"References directory not found: {refs_dir}")
        return {}

    references = {}
    for ref_file in refs_dir.glob("*.md"):
        try:
            content = ref_file.read_text(encoding="utf-8")
            # Use stem (filename without extension) as key
            references[ref_file.stem] = content
            logger.debug(f"Loaded reference: {ref_file.stem} ({len(content)} chars)")
        except Exception as e:
            logger.error(f"Failed to load reference {ref_file}: {e}")
            raise SkillLoadError(f"Failed to load reference {ref_file}: {e}")

    return references


@lru_cache(maxsize=1)
def load_skill_prompt() -> str:
    """
    Load complete skill prompt including SKILL.md and all references.

    Constructs a single prompt string that includes:
    1. Main SKILL.md content
    2. All reference files from references/ directory

    The result is cached since skill files don't change at runtime.

    Returns:
        Complete skill prompt string

    Raises:
        SkillLoadError: If skill files cannot be loaded
    """
    skill_dir = get_skill_directory()

    # Load main SKILL.md
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        raise SkillLoadError(f"SKILL.md not found: {skill_file}")

    try:
        skill_content = skill_file.read_text(encoding="utf-8")
        logger.info(f"Loaded SKILL.md ({len(skill_content)} chars)")
    except Exception as e:
        raise SkillLoadError(f"Failed to load SKILL.md: {e}")

    # Load all references
    references = get_skill_references(skill_dir)

    # Construct combined prompt
    combined_parts = [skill_content]

    # Add each reference with a header
    for ref_name, ref_content in references.items():
        combined_parts.append(f"\n\n---\n\n# Reference: {ref_name}\n\n{ref_content}")

    combined_prompt = "".join(combined_parts)

    logger.info(
        f"Constructed skill prompt: {len(combined_prompt)} chars, "
        f"{len(references)} references"
    )

    return combined_prompt


def clear_skill_cache():
    """
    Clear the cached skill prompt.

    Useful for testing or if skill files are updated at runtime.
    """
    load_skill_prompt.cache_clear()
    logger.info("Skill cache cleared")
