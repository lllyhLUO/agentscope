# -*- coding: utf-8 -*-
"""Tests for publishing local skills into the registry."""
import tempfile
from argparse import Namespace
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from agentscope.skill._cli import run_publish_command
from agentscope.skill._publisher import publish_skill_directory


class _FakePublishRepository:
    """In-memory fake repository for publish workflow tests."""

    def __init__(self) -> None:
        self.assert_calls: list[tuple[str, str]] = []
        self.created_artifacts: list[dict] = []
        self.existing_versions: dict[tuple[str, str], dict] = {}
        self.block_write = False

    async def assert_can_write(
        self,
        skill_name: str,
        principal: str,
    ) -> None:
        """Record write checks and optionally raise."""
        self.assert_calls.append((skill_name, principal))
        if self.block_write:
            raise PermissionError("write blocked")

    async def get_skill_version(
        self,
        name: str,
        version: str,
    ) -> dict | None:
        """Return an existing version if present."""
        return self.existing_versions.get((name, version))

    async def create_skill_artifact(
        self,
        manifest,
        principal: str,
    ) -> dict:
        """Store a created artifact result."""
        result = {
            "skill_name": manifest.skill_name,
            "version": manifest.version,
            "content_hash": manifest.content_hash,
            "file_count": len(manifest.files),
            "created_by": principal,
            "created": True,
            "idempotent": False,
        }
        self.existing_versions[(manifest.skill_name, manifest.version)] = {
            "version": manifest.version,
            "content_hash": manifest.content_hash,
        }
        self.created_artifacts.append(result)
        return result


class SkillRegistryPublishCommandTest(IsolatedAsyncioTestCase):
    """Test cases for publish service and command dispatch."""

    async def test_first_publish_creates_registry_artifact(self) -> None:
        """Test initial publish creates a skill version artifact."""
        repository = _FakePublishRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self._create_skill_directory(Path(temp_dir))

            result = await publish_skill_directory(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
                repository,
                "maintainer-1",
            )

        self.assertTrue(result["created"])
        self.assertFalse(result["idempotent"])
        self.assertEqual(result["skill_name"], "sql_analyzer")
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(len(repository.created_artifacts), 1)

    async def test_publish_rejects_same_version_with_different_content(self) -> None:
        """Test conflicting re-publish raises for different content."""
        repository = _FakePublishRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self._create_skill_directory(Path(temp_dir))
            await publish_skill_directory(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
                repository,
                "maintainer-1",
            )
            skill_dir.joinpath("tool.py").write_text(
                "print('different content')\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "different content"):
                await publish_skill_directory(
                    skill_dir,
                    "sql_analyzer",
                    "1.0.0",
                    repository,
                    "maintainer-1",
                )

    async def test_publish_is_idempotent_for_identical_content(self) -> None:
        """Test identical re-publish returns idempotent success."""
        repository = _FakePublishRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self._create_skill_directory(Path(temp_dir))
            await publish_skill_directory(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
                repository,
                "maintainer-1",
            )

            result = await publish_skill_directory(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
                repository,
                "maintainer-1",
            )

        self.assertTrue(result["idempotent"])
        self.assertEqual(result["skill_name"], "sql_analyzer")
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(len(repository.created_artifacts), 1)

    async def test_publish_enforces_maintainer_checks_before_write(self) -> None:
        """Test maintainer checks run before artifact creation."""
        repository = _FakePublishRepository()
        repository.block_write = True
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self._create_skill_directory(Path(temp_dir))

            with self.assertRaises(PermissionError):
                await publish_skill_directory(
                    skill_dir,
                    "sql_analyzer",
                    "1.0.0",
                    repository,
                    "reader-1",
                )

        self.assertEqual(repository.assert_calls, [("sql_analyzer", "reader-1")])
        self.assertEqual(repository.created_artifacts, [])

    async def test_publish_command_dispatch_routes_publish_args(self) -> None:
        """Test the publish command path routes args into the publisher service."""
        repository = _FakePublishRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self._create_skill_directory(Path(temp_dir))
            with patch(
                "agentscope.skill._cli.publish_skill_directory",
                new=AsyncMock(
                    return_value={
                        "skill_name": "sql_analyzer",
                        "version": "1.0.0",
                        "idempotent": False,
                    },
                ),
            ) as publish_mock:
                await run_publish_command(
                    Namespace(
                        directory=str(skill_dir),
                        name="sql_analyzer",
                        version="1.0.0",
                        principal="maintainer-1",
                        database_url="postgresql+asyncpg://skill:secret@localhost:5432/skilldb_dev",
                        command="publish",
                    ),
                    repository=repository,
                )

        publish_mock.assert_awaited_once()
        _, kwargs = publish_mock.await_args
        self.assertEqual(kwargs["skill_name"], "sql_analyzer")
        self.assertEqual(kwargs["version"], "1.0.0")
        self.assertEqual(kwargs["principal"], "maintainer-1")
        self.assertIs(kwargs["repository"], repository)

    def _create_skill_directory(self, root: Path) -> Path:
        """Create a valid skill directory for publish tests."""
        root.joinpath("SKILL.md").write_text(
            "---\nname: sql_analyzer\ndescription: Example\n---\n# Title\n",
            encoding="utf-8",
        )
        root.joinpath("tool.py").write_text(
            "print('publish')\n",
            encoding="utf-8",
        )
        return root
