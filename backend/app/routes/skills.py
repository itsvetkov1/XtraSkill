"""
Skills discovery routes.

Provides endpoints for discovering available Claude Code skills from ~/.claude/ directory.
"""

import logging
import os
from pathlib import Path
from typing import List

import frontmatter
import yaml

from fastapi import APIRouter, Depends

from app.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Directories to skip when scanning ~/.claude/
SKIP_DIRS = {
    "plugins", "get-shit-done", "agents", "commands", "hooks",
    "projects", "tasks", "todos", "cache", "downloads", "debug",
    "file-history", "paste-cache", "plans", "session-env",
    "shell-snapshots", "stats-cache.json", "telemetry",
}


def _get_skills_dir() -> Path:
    """Get skills directory, defaulting to ~/.claude/."""
    env_path = os.environ.get("SKILLS_DIR")
    if env_path:
        return Path(env_path)
    return Path.home() / ".claude"


def _extract_frontmatter(skill_file: Path) -> dict | None:
    """Parse YAML frontmatter from SKILL.md."""
    try:
        with open(skill_file, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        return {
            'name': post.get('name'),
            'description': post.get('description'),
            'features': post.get('features', []),
            'content': post.content,
        }
    except yaml.YAMLError as e:
        logger.warning(f"Malformed YAML in {skill_file}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error parsing {skill_file}: {e}")
        return None


def _get_skill_name(skill_dir: Path, fm: dict | None) -> str:
    """Get name: frontmatter -> directory name transformed -> raw."""
    if fm and fm.get('name'):
        return fm['name']
    return skill_dir.name.replace('-', ' ').title()


def _get_skill_description(fm: dict | None, content: str) -> str:
    """Get description: frontmatter -> first content line -> default."""
    if fm and fm.get('description'):
        return fm['description']
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            return stripped
    return "No description available"


def _get_skill_features(fm: dict | None) -> list[str]:
    """Get features: frontmatter array -> empty array."""
    if fm and fm.get('features'):
        features = fm['features']
        if isinstance(features, list) and all(isinstance(f, str) for f in features):
            return features
        logger.warning(f"Invalid features format: {type(features)}")
    return []


@router.get("/skills")
async def list_skills(current_user: dict = Depends(get_current_user)):
    """List available Claude Code skills from ~/.claude/."""
    skills_dir = _get_skills_dir()

    if not skills_dir.exists() or not skills_dir.is_dir():
        logger.info(f"Skills directory not found: {skills_dir}")
        return []

    skills = []

    try:
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            if skill_dir.name in SKIP_DIRS:
                logger.debug(f"Skipping excluded directory: {skill_dir.name}")
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                logger.debug(f"No SKILL.md in {skill_dir.name}, skipping")
                continue

            # Parse frontmatter
            fm = _extract_frontmatter(skill_file)

            # Read raw content for description fallback
            raw_content = ""
            if fm is None:
                try:
                    raw_content = skill_file.read_text(encoding='utf-8')
                except Exception:
                    raw_content = ""
            else:
                raw_content = fm.get('content', '')

            # Build metadata with fallbacks
            name = _get_skill_name(skill_dir, fm)
            description = _get_skill_description(fm, raw_content)
            features = _get_skill_features(fm)

            # Compute skill_path relative to skills dir parent (i.e., relative to ~)
            skill_path = str(skill_file.relative_to(skills_dir.parent))

            skills.append({
                "name": name,
                "description": description,
                "features": features,
                "skill_path": skill_path,
            })

            logger.debug(f"Found skill: {name} ({skill_dir.name})")

    except Exception as e:
        logger.error(f"Error scanning skills directory: {e}")
        return []

    logger.info(f"Discovered {len(skills)} skills")
    return skills
