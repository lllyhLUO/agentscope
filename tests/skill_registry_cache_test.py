# -*- coding: utf-8 -*-
"""Tests for the skill runtime cache."""
import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from agentscope.skill._cache import SkillRuntimeCache


class _FakeCacheRepository:
    """In-memory repository double for runtime cache tests."""

    def __init__(self) -> None:
        self.version_payload = {
            "version": "1.0.0",
            "content_hash": "hash-1",
        }
        self.files_payload = [
            {
                "path": "SKILL.md",
                "file_type": "markdown",
                "content_text": (
                    "---\nname: sql_analyzer\ndescription: Example\n---\n# Title\n"
                ),
                "content_bytes": None,
                "sha256": "sha-skill",
                "size": 58,
            },
            {
                "path": "tool.py",
                "file_type": "text",
                "content_text": "print('hello')\n",
                "content_bytes": None,
                "sha256": "sha-tool",
                "size": 15,
            },
        ]
        self.version_calls: list[tuple[str, str]] = []
        self.file_calls: list[tuple[str, str]] = []

    async def get_skill_version(
        self,
        name: str,
        version: str,
    ) -> dict | None:
        """Return the configured version payload."""
        self.version_calls.append((name, version))
        return self.version_payload

    async def list_skill_files(
        self,
        name: str,
        version: str,
    ) -> list[dict]:
        """Return the configured file payload."""
        self.file_calls.append((name, version))
        return list(self.files_payload)


class SkillRegistryCacheTest(IsolatedAsyncioTestCase):
    """Test cases for managed registry skill cache behavior."""

    async def test_parse_skill_ref_requires_skill_name_and_version(self) -> None:
        """Test parsing only accepts explicit `skill_name@version` refs."""
        repository = _FakeCacheRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SkillRuntimeCache(
                repository=repository,
                cache_dir=temp_dir,
            )

            self.assertEqual(
                cache.parse_skill_ref("sql_analyzer@1.0.0"),
                ("sql_analyzer", "1.0.0"),
            )

            with self.assertRaisesRegex(ValueError, "skill_name@version"):
                cache.parse_skill_ref("sql_analyzer")

    async def test_hydrate_skill_ref_materializes_files(self) -> None:
        """Test a skill version hydrates `SKILL.md` and other files."""
        repository = _FakeCacheRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SkillRuntimeCache(
                repository=repository,
                cache_dir=temp_dir,
            )

            hydrated_path = Path(
                await cache.hydrate_skill_ref("sql_analyzer@1.0.0"),
            )

            self.assertTrue(hydrated_path.joinpath("SKILL.md").is_file())
            self.assertTrue(hydrated_path.joinpath("tool.py").is_file())
            self.assertEqual(
                hydrated_path.joinpath("tool.py").read_text(encoding="utf-8"),
                "print('hello')\n",
            )

    async def test_hydrate_reuses_existing_cache_when_content_hash_matches(
        self,
    ) -> None:
        """Test identical content hash reuses the existing cache directory."""
        repository = _FakeCacheRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SkillRuntimeCache(
                repository=repository,
                cache_dir=temp_dir,
            )

            first_path = Path(
                await cache.hydrate_skill_ref("sql_analyzer@1.0.0"),
            )
            first_mtime = first_path.joinpath("tool.py").stat().st_mtime_ns
            second_path = Path(
                await cache.hydrate_skill_ref("sql_analyzer@1.0.0"),
            )
            second_mtime = second_path.joinpath("tool.py").stat().st_mtime_ns

            self.assertEqual(first_path, second_path)
            self.assertEqual(first_mtime, second_mtime)

    async def test_hydrate_rebuilds_when_content_hash_changes(self) -> None:
        """Test stale cache is replaced when the repository content hash changes."""
        repository = _FakeCacheRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SkillRuntimeCache(
                repository=repository,
                cache_dir=temp_dir,
            )

            first_path = Path(
                await cache.hydrate_skill_ref("sql_analyzer@1.0.0"),
            )
            repository.version_payload = {
                "version": "1.0.0",
                "content_hash": "hash-2",
            }
            repository.files_payload = [
                repository.files_payload[0],
                {
                    "path": "tool.py",
                    "file_type": "text",
                    "content_text": "print('updated')\n",
                    "content_bytes": None,
                    "sha256": "sha-tool-2",
                    "size": 17,
                },
            ]

            second_path = Path(
                await cache.hydrate_skill_ref("sql_analyzer@1.0.0"),
            )

            self.assertNotEqual(first_path, second_path)
            self.assertFalse(first_path.exists())
            self.assertEqual(
                second_path.joinpath("tool.py").read_text(encoding="utf-8"),
                "print('updated')\n",
            )

    async def test_missing_version_raises_before_hydration(self) -> None:
        """Test unknown explicit version raises before cache writes."""
        repository = _FakeCacheRepository()
        repository.version_payload = None
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SkillRuntimeCache(
                repository=repository,
                cache_dir=temp_dir,
            )

            with self.assertRaisesRegex(ValueError, "not found"):
                await cache.hydrate_skill_ref("sql_analyzer@1.0.0")

    async def test_cache_path_contains_skill_name_version_and_content_hash(
        self,
    ) -> None:
        """Test cache path is keyed by skill name, version, and content hash."""
        repository = _FakeCacheRepository()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SkillRuntimeCache(
                repository=repository,
                cache_dir=temp_dir,
            )

            hydrated_path = Path(
                await cache.hydrate_skill_ref("sql_analyzer@1.0.0"),
            )

            self.assertIn("sql_analyzer", hydrated_path.as_posix())
            self.assertIn("1.0.0", hydrated_path.as_posix())
            self.assertIn("hash-1", hydrated_path.as_posix())
