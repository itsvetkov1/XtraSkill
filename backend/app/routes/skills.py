"""
Skills discovery routes.

Provides endpoints for discovering available Claude Code skills from .claude/ directory.
"""

import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends

from app.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


def _find_project_root() -> Path:
    """
    Find project root by navigating up from this file.

    Returns:
        Path to project root containing .claude/ directory
    """
    # From backend/app/routes/skills.py, go up 3 levels to project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]  # Up to XtraSkill/

    logger.info(f"Skills API: Using project root: {project_root}")

    # Verify .claude/ exists
    claude_dir = project_root / ".claude"
    if not claude_dir.exists():
        logger.warning(f"Skills API: .claude/ directory not found at {claude_dir}")

    return project_root


def _extract_description_from_skill(skill_path: Path) -> str:
    """
    Extract description from SKILL.md file.

    Args:
        skill_path: Path to SKILL.md file

    Returns:
        First non-empty line after frontmatter and headers
    """
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            in_frontmatter = False
            for line in f:
                stripped = line.strip()

                # Track frontmatter boundaries
                if stripped == '---':
                    in_frontmatter = not in_frontmatter
                    continue

                # Skip frontmatter and headers
                if in_frontmatter or stripped.startswith('#'):
                    continue

                # Return first non-empty content line
                if stripped:
                    return stripped

        return "No description available"
    except Exception as e:
        logger.warning(f"Failed to extract description from {skill_path}: {e}")
        return "No description available"


@router.get("/skills")
async def list_skills(
    current_user: dict = Depends(get_current_user)
):
    """
    List available Claude Code skills discovered from .claude/ directory.

    Scans .claude/ subdirectories for SKILL.md files and extracts metadata.

    Args:
        current_user: Authenticated user from JWT

    Returns:
        List of skills with name, description, and path
    """
    project_root = _find_project_root()
    claude_dir = project_root / ".claude"

    # Return empty list if .claude/ doesn't exist
    if not claude_dir.exists() or not claude_dir.is_dir():
        logger.info("Skills API: .claude/ directory not found, returning empty list")
        return []

    skills = []

    # Scan .claude/ subdirectories
    try:
        for skill_dir in claude_dir.iterdir():
            # Skip non-directories
            if not skill_dir.is_dir():
                continue

            # Look for SKILL.md
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            # Extract metadata
            skill_name = skill_dir.name
            description = _extract_description_from_skill(skill_file)
            skill_path = str(skill_file.relative_to(project_root))

            skills.append({
                "name": skill_name,
                "description": description,
                "skill_path": skill_path
            })

            logger.debug(f"Skills API: Found skill '{skill_name}' at {skill_path}")

    except Exception as e:
        logger.error(f"Skills API: Error scanning .claude/ directory: {e}")
        return []

    logger.info(f"Skills API: Discovered {len(skills)} skills")
    return skills
