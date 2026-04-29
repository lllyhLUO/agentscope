# -*- coding: utf-8 -*-
"""Tests for registry discovery and install CLI commands."""
from argparse import Namespace
from unittest import IsolatedAsyncioTestCase

from agentscope.skill._cli import (
    run_install_command,
    run_search_command,
    run_show_command,
)


class _FakeDiscoveryRepository:
    """Repository double for discovery CLI tests."""

    def __init__(self) -> None:
        self.search_calls: list[tuple[str, int]] = []
        self.version_calls: list[tuple[str, str]] = []
        self.file_calls: list[tuple[str, str]] = []

    async def search_skills(self, query: str, limit: int) -> list[dict]:
        """Return a single search hit."""
        self.search_calls.append((query, limit))
        return [
            {
                "name": "sql_analyzer",
                "latest_version": "1.0.0",
                "status": "active",
            },
        ]

    async def get_skill_version(self, name: str, version: str) -> dict | None:
        """Return explicit version metadata."""
        self.version_calls.append((name, version))
        return {
            "version": version,
            "description": "SQL analysis skill",
            "content_hash": "hash-1",
            "published_by": "maintainer-1",
        }

    async def list_skill_files(self, name: str, version: str) -> list[dict]:
        """Return file listing for an explicit version."""
        self.file_calls.append((name, version))
        return [
            {"path": "SKILL.md", "file_type": "markdown"},
            {"path": "tool.py", "file_type": "text"},
        ]


class _FakeInstallCache:
    """Runtime cache double for install CLI tests."""

    def __init__(self, hydrated_path: str) -> None:
        self.hydrated_path = hydrated_path
        self.refs: list[str] = []

    async def hydrate_skill_ref(self, skill_ref: str) -> str:
        """Record the ref and return the cache path."""
        self.refs.append(skill_ref)
        return self.hydrated_path


class SkillRegistryCliTest(IsolatedAsyncioTestCase):
    """Test cases for search/show/install command helpers."""

    async def test_search_dispatches_to_repository(self) -> None:
        """Test `search` delegates to repository-backed lookup."""
        repository = _FakeDiscoveryRepository()

        result = await run_search_command(
            Namespace(query="sql", limit=5),
            repository=repository,
        )

        self.assertEqual(repository.search_calls, [("sql", 5)])
        self.assertEqual(result[0]["name"], "sql_analyzer")

    async def test_show_requires_explicit_skill_name_version(self) -> None:
        """Test `show` rejects refs without explicit `@version`."""
        repository = _FakeDiscoveryRepository()

        with self.assertRaisesRegex(ValueError, "@version"):
            await run_show_command(
                Namespace(skill_ref="sql_analyzer"),
                repository=repository,
            )

    async def test_show_returns_version_metadata_and_file_list(self) -> None:
        """Test `show` returns explicit version details and files."""
        repository = _FakeDiscoveryRepository()

        result = await run_show_command(
            Namespace(skill_ref="sql_analyzer@1.0.0"),
            repository=repository,
        )

        self.assertEqual(repository.version_calls, [("sql_analyzer", "1.0.0")])
        self.assertEqual(repository.file_calls, [("sql_analyzer", "1.0.0")])
        self.assertEqual(result["skill_ref"], "sql_analyzer@1.0.0")
        self.assertEqual(result["files"][0]["path"], "SKILL.md")

    async def test_install_requires_explicit_skill_name_version(self) -> None:
        """Test `install` rejects refs without explicit `@version`."""
        repository = _FakeDiscoveryRepository()
        cache = _FakeInstallCache("/tmp/skill")

        with self.assertRaisesRegex(ValueError, "@version"):
            await run_install_command(
                Namespace(skill_ref="sql_analyzer"),
                repository=repository,
                runtime_cache=cache,
            )

    async def test_install_delegates_to_runtime_cache_and_reports_path(
        self,
    ) -> None:
        """Test `install` prewarms the cache and returns the hydrated path."""
        repository = _FakeDiscoveryRepository()
        cache = _FakeInstallCache("/tmp/skill-cache/sql_analyzer/1.0.0/hash-1")

        result = await run_install_command(
            Namespace(skill_ref="sql_analyzer@1.0.0"),
            repository=repository,
            runtime_cache=cache,
        )

        self.assertEqual(cache.refs, ["sql_analyzer@1.0.0"])
        self.assertEqual(result["skill_ref"], "sql_analyzer@1.0.0")
        self.assertEqual(result["hydrated_path"], cache.hydrated_path)
