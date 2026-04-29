# -*- coding: utf-8 -*-
"""Tests for runtime loading of registry-backed skills."""
import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from agentscope.skill._loader import SkillRegistryLoader
from agentscope.tool import Toolkit


class _FakeRuntimeCache:
    """Runtime cache double for loader tests."""

    def __init__(self, hydrated_dir: str) -> None:
        self.hydrated_dir = hydrated_dir
        self.refs: list[str] = []

    async def hydrate_skill_ref(self, skill_ref: str) -> str:
        """Record the requested skill ref and return the hydrated path."""
        self.refs.append(skill_ref)
        return self.hydrated_dir


class SkillRegistryLoaderTest(IsolatedAsyncioTestCase):
    """Async tests for the registry loader."""

    async def test_invalid_ref_without_version_raises(self) -> None:
        """Test loader rejects refs without explicit version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = SkillRegistryLoader(
                repository=object(),
                runtime_cache=_FakeRuntimeCache(temp_dir),
            )

            with self.assertRaisesRegex(ValueError, "@version"):
                await loader.resolve_skill_dir("sql_analyzer")

    async def test_loader_asks_cache_for_hydrated_path(self) -> None:
        """Test loader delegates hydration to the runtime cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = _FakeRuntimeCache(temp_dir)
            loader = SkillRegistryLoader(
                repository=object(),
                runtime_cache=cache,
            )

            result = await loader.resolve_skill_dir("sql_analyzer@1.0.0")

        self.assertEqual(result, temp_dir)
        self.assertEqual(cache.refs, ["sql_analyzer@1.0.0"])

    async def test_loader_accepts_injected_repository_and_cache(self) -> None:
        """Test loader supports injected collaborators for tests."""
        fake_repository = object()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = _FakeRuntimeCache(temp_dir)
            loader = SkillRegistryLoader(
                repository=fake_repository,
                runtime_cache=cache,
            )

            self.assertIs(loader.repository, fake_repository)
            self.assertIs(loader.runtime_cache, cache)
            await loader.resolve_skill_dir("sql_analyzer@1.0.0")


class SkillRegistryToolkitIntegrationTest(TestCase):
    """Sync tests for Toolkit registry skill integration."""

    def test_register_registry_skill_calls_register_agent_skill(self) -> None:
        """Test Toolkit delegates to `register_agent_skill()` after loading."""
        toolkit = Toolkit()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = _FakeRuntimeCache(temp_dir)
            loader = SkillRegistryLoader(
                repository=object(),
                runtime_cache=cache,
            )

            with patch.object(toolkit, "register_agent_skill") as register_mock:
                toolkit.register_registry_skill(
                    "sql_analyzer@1.0.0",
                    registry_loader=loader,
                )

        register_mock.assert_called_once_with(temp_dir)

    def test_register_registry_skill_end_to_end_adds_skill(self) -> None:
        """Test registry skill registration hydrates into normal Toolkit flow."""
        toolkit = Toolkit()
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            skill_dir.joinpath("SKILL.md").write_text(
                "---\nname: sql_analyzer\ndescription: Example\n---\n# Title\n",
                encoding="utf-8",
            )
            loader = SkillRegistryLoader(
                repository=object(),
                runtime_cache=_FakeRuntimeCache(temp_dir),
            )

            toolkit.register_registry_skill(
                "sql_analyzer@1.0.0",
                registry_loader=loader,
            )

        self.assertIn("sql_analyzer", toolkit.skills)
