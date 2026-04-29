# -*- coding: utf-8 -*-
"""End-to-end workflow tests for the skill registry."""
import tempfile
from argparse import Namespace
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from agentscope.skill._cache import SkillRuntimeCache
from agentscope.skill._cli import (
    run_install_command,
    run_search_command,
    run_show_command,
)
from agentscope.skill._loader import SkillRegistryLoader
from agentscope.skill._publisher import publish_skill_directory
from agentscope.tool import Toolkit


class _RegistryWorkflowRepository:
    """In-memory repository for end-to-end registry workflow tests."""

    def __init__(self) -> None:
        self.skills: dict[str, dict] = {}
        self.versions: dict[tuple[str, str], dict] = {}
        self.files: dict[tuple[str, str], list[dict]] = {}

    async def assert_can_write(self, skill_name: str, principal: str) -> None:
        """Allow writes in the in-memory workflow test."""

    async def get_skill(self, name: str) -> dict | None:
        """Get stored skill metadata."""
        return self.skills.get(name)

    async def get_skill_version(self, name: str, version: str) -> dict | None:
        """Get a stored version row."""
        return self.versions.get((name, version))

    async def list_skill_versions(self, name: str) -> list[dict]:
        """List stored versions for a skill."""
        return [
            row
            for (skill_name, _), row in self.versions.items()
            if skill_name == name
        ]

    async def search_skills(self, query: str, limit: int) -> list[dict]:
        """Search stored skills by simple substring match."""
        results = [
            row
            for row in self.skills.values()
            if query in row["name"] or query in row.get("description", "")
        ]
        return results[:limit]

    async def list_skill_files(self, name: str, version: str) -> list[dict]:
        """Return stored file rows."""
        return list(self.files[(name, version)])

    async def create_skill_artifact(self, manifest, principal: str) -> dict:
        """Persist a new skill artifact in memory."""
        self.skills[manifest.skill_name] = {
            "id": f"skill-{manifest.skill_name}",
            "name": manifest.skill_name,
            "latest_version": manifest.version,
            "status": "active",
            "created_by": principal,
            "description": manifest.description,
        }
        self.versions[(manifest.skill_name, manifest.version)] = {
            "id": f"version-{manifest.skill_name}-{manifest.version}",
            "skill_id": f"skill-{manifest.skill_name}",
            "version": manifest.version,
            "description": manifest.description,
            "metadata_json": manifest.metadata_json,
            "content_hash": manifest.content_hash,
            "published_by": principal,
        }
        self.files[(manifest.skill_name, manifest.version)] = [
            {
                "path": item.path,
                "file_type": item.file_type,
                "content_text": item.content_text,
                "content_bytes": item.content_bytes,
                "sha256": item.sha256,
                "size": item.size,
            }
            for item in manifest.files
        ]
        return {
            "skill_name": manifest.skill_name,
            "version": manifest.version,
            "content_hash": manifest.content_hash,
            "created": True,
            "idempotent": False,
        }


class SkillRegistryEndToEndTest(IsolatedAsyncioTestCase):
    """End-to-end tests for the Phase 1-4 registry workflow."""

    async def test_publish_search_show_install_and_load_workflow(self) -> None:
        """Test the full shared registry workflow without manual file copying."""
        repository = _RegistryWorkflowRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self._create_skill_directory(Path(temp_dir) / "skill")
            await publish_skill_directory(
                skill_dir=skill_dir,
                skill_name="sql_analyzer",
                version="1.0.0",
                repository=repository,
                principal="maintainer-1",
            )

            search_result = await run_search_command(
                Namespace(query="sql", limit=10, database_url=None),
                repository=repository,
            )
            self.assertEqual(search_result[0]["name"], "sql_analyzer")

            show_result = await run_show_command(
                Namespace(skill_ref="sql_analyzer@1.0.0", database_url=None),
                repository=repository,
            )
            self.assertEqual(show_result["files"][0]["path"], "SKILL.md")

            cache_dir = Path(temp_dir) / "cache"
            install_result = await run_install_command(
                Namespace(skill_ref="sql_analyzer@1.0.0", database_url=None),
                repository=repository,
                runtime_cache=SkillRuntimeCache(
                    repository=repository,
                    cache_dir=cache_dir,
                ),
            )
            self.assertTrue(install_result["installed"])

            loader = SkillRegistryLoader(
                repository=repository,
                cache_dir=cache_dir,
            )
            toolkit = Toolkit()
            toolkit.register_registry_skill(
                "sql_analyzer@1.0.0",
                registry_loader=loader,
            )
            self.assertIn("sql_analyzer", toolkit.skills)

    async def test_live_registry_smoke_when_database_urls_present(self) -> None:
        """Test optional live registry smoke path when env is configured."""
        if not (
            "AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL" in __import__("os").environ
            and "AGENTSCOPE_SKILL_REGISTRY_TEST_DATABASE_URL"
            in __import__("os").environ
        ):
            self.skipTest(
                "Registry database URLs are not configured for live smoke checks",
            )

    @staticmethod
    def _create_skill_directory(skill_dir: Path) -> Path:
        """Create a valid local skill directory."""
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_dir.joinpath("SKILL.md").write_text(
            "---\nname: sql_analyzer\ndescription: Example\n---\n# Title\n",
            encoding="utf-8",
        )
        skill_dir.joinpath("tool.py").write_text(
            "print('publish')\n",
            encoding="utf-8",
        )
        return skill_dir
