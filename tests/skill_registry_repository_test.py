# -*- coding: utf-8 -*-
"""Tests for the skill registry repository."""
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from agentscope.skill._models import (
    _SkillFileTable,
    _SkillMaintainerTable,
    _SkillTable,
    _SkillVersionTable,
)
from agentscope.skill._repository import SkillRegistryRepository


class _ScalarOneResult:
    """Minimal result object for `scalar_one_or_none()` queries."""

    def __init__(self, row: object | None) -> None:
        self._row = row

    def scalar_one_or_none(self) -> object | None:
        """Return the stored row."""
        return self._row


class _ScalarListWrapper:
    """Minimal wrapper for `.scalars().all()` flows."""

    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        """Return all stored rows."""
        return self._rows


class _ScalarListResult:
    """Minimal result object for `.scalars().all()` queries."""

    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def scalars(self) -> _ScalarListWrapper:
        """Return a scalar wrapper."""
        return _ScalarListWrapper(self._rows)


class _FakeAsyncConnection:
    """Async connection wrapper around a sync SQLAlchemy connection."""

    def __init__(self, sync_connection: object) -> None:
        self._sync_connection = sync_connection

    async def run_sync(self, fn: object) -> object:
        """Run a sync callback with the wrapped connection."""
        return fn(self._sync_connection)


class _FakeAsyncBeginContext:
    """Async context manager for a fake async engine begin block."""

    def __init__(self, sync_engine: object) -> None:
        self._sync_engine = sync_engine
        self._sync_context = None
        self._sync_connection = None

    async def __aenter__(self) -> _FakeAsyncConnection:
        """Open the sync transaction context."""
        self._sync_context = self._sync_engine.begin()
        self._sync_connection = self._sync_context.__enter__()
        return _FakeAsyncConnection(self._sync_connection)

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        tb: object,
    ) -> None:
        """Close the sync transaction context."""
        assert self._sync_context is not None
        self._sync_context.__exit__(exc_type, exc, tb)


class _FakeAsyncEngine(AsyncEngine):
    """Minimal AsyncEngine-compatible test double."""

    def begin(self) -> _FakeAsyncBeginContext:
        """Return an async begin context."""
        return _FakeAsyncBeginContext(self._skill_registry_sync_engine)


def _create_fake_async_engine() -> AsyncEngine:
    """Create a minimal async-engine-compatible test double."""
    sync_engine = create_engine("sqlite:///:memory:")
    engine = object.__new__(_FakeAsyncEngine)
    engine._skill_registry_sync_engine = sync_engine  # type: ignore[attr-defined]
    return engine


class SkillRegistryRepositoryTest(IsolatedAsyncioTestCase):
    """Test cases for the skill registry repository."""

    def setUp(self) -> None:
        """Set up reusable ORM rows and repository test doubles."""
        self.skill = _SkillTable(
            id="skill-1",
            name="sql_analyzer",
            latest_version="1.0.0",
            status="active",
            created_by="maintainer-1",
        )
        self.version = _SkillVersionTable(
            id="version-1",
            skill_id="skill-1",
            version="1.0.0",
            description="SQL analysis skill",
            metadata_json={"tags": ["sql", "analysis"]},
            content_hash="hash-1",
            published_by="maintainer-1",
        )
        self.file = _SkillFileTable(
            id="file-1",
            skill_version_id="version-1",
            path="SKILL.md",
            file_type="markdown",
            content_text="name: sql_analyzer",
            content_bytes=None,
            sha256="sha-1",
            size=18,
        )
        self.maintainer = _SkillMaintainerTable(
            id="maintainer-link-1",
            skill_id="skill-1",
            principal="maintainer-1",
            role="maintainer",
        )

    async def test_init_schema_creates_expected_tables(self) -> None:
        """Test schema initialization creates all registry tables."""
        engine = _create_fake_async_engine()
        repository = SkillRegistryRepository(engine)

        await repository.init_schema()

        sync_engine = engine._skill_registry_sync_engine  # type: ignore[attr-defined]
        table_names = set(inspect(sync_engine).get_table_names())
        self.assertSetEqual(
            table_names,
            {
                "skill_files",
                "skill_maintainers",
                "skill_versions",
                "skills",
            },
        )

    async def test_get_skill_returns_expected_row(self) -> None:
        """Test exact skill lookup by name."""
        session = AsyncSession()
        session.execute = AsyncMock(return_value=_ScalarOneResult(self.skill))  # type: ignore[method-assign]
        repository = SkillRegistryRepository(session)

        result = await repository.get_skill("sql_analyzer")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["name"], "sql_analyzer")
        self.assertEqual(result["latest_version"], "1.0.0")

    async def test_get_skill_version_returns_expected_row(self) -> None:
        """Test exact skill version lookup."""
        session = AsyncSession()
        session.execute = AsyncMock(return_value=_ScalarOneResult(self.version))  # type: ignore[method-assign]
        repository = SkillRegistryRepository(session)

        result = await repository.get_skill_version("sql_analyzer", "1.0.0")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["description"], "SQL analysis skill")

    async def test_search_skills_matches_name_and_description(self) -> None:
        """Test search returns serialized skill rows."""
        session = AsyncSession()
        session.execute = AsyncMock(return_value=_ScalarListResult([self.skill]))  # type: ignore[method-assign]
        repository = SkillRegistryRepository(session)

        result = await repository.search_skills("sql", limit=10)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "sql_analyzer")

    async def test_list_skill_files_returns_version_files(self) -> None:
        """Test listing files for a specific version."""
        session = AsyncSession()
        session.execute = AsyncMock(return_value=_ScalarListResult([self.file]))  # type: ignore[method-assign]
        repository = SkillRegistryRepository(session)

        files = await repository.list_skill_files("sql_analyzer", "1.0.0")

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["path"], "SKILL.md")
        self.assertEqual(files[0]["file_type"], "markdown")

    async def test_is_skill_maintainer_reflects_membership(self) -> None:
        """Test maintainer membership checks."""
        session = AsyncSession()
        session.execute = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                _ScalarOneResult(self.maintainer.id),
                _ScalarOneResult(None),
            ],
        )
        repository = SkillRegistryRepository(session)

        self.assertTrue(
            await repository.is_skill_maintainer(
                "sql_analyzer",
                "maintainer-1",
            ),
        )
        self.assertFalse(
            await repository.is_skill_maintainer(
                "sql_analyzer",
                "reader-1",
            ),
        )

    async def test_assert_can_write_raises_for_non_maintainer(self) -> None:
        """Test non-maintainers are blocked from writes."""
        session = AsyncSession()
        session.execute = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                _ScalarOneResult(self.maintainer.id),
                _ScalarOneResult(None),
            ],
        )
        repository = SkillRegistryRepository(session)

        await repository.assert_can_write("sql_analyzer", "maintainer-1")

        with self.assertRaises(PermissionError):
            await repository.assert_can_write("sql_analyzer", "reader-1")

    async def test_from_env_uses_database_url(self) -> None:
        """Test repository can be created from environment configuration."""
        fake_engine = _create_fake_async_engine()
        os.environ["AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL"] = (
            "postgresql+asyncpg://skill:secret@localhost:5432/skilldb_dev"
        )
        try:
            with patch(
                "agentscope.skill._repository.create_async_engine",
                return_value=fake_engine,
            ) as create_engine_mock:
                repository = SkillRegistryRepository.from_env()
        finally:
            os.environ.pop(
                "AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL",
                None,
            )

        self.assertIsInstance(repository, SkillRegistryRepository)
        create_engine_mock.assert_called_once()

    async def test_postgresql_init_schema_when_test_url_present(self) -> None:
        """Test optional PostgreSQL initialization when env is configured."""
        database_url = os.environ.get(
            "AGENTSCOPE_SKILL_REGISTRY_TEST_DATABASE_URL",
        )
        if database_url is None:
            self.skipTest(
                "AGENTSCOPE_SKILL_REGISTRY_TEST_DATABASE_URL is not set",
            )

        fake_engine = _create_fake_async_engine()
        with patch(
            "agentscope.skill._repository.create_async_engine",
            return_value=fake_engine,
        ):
            repository = SkillRegistryRepository.from_env(database_url)
            await repository.init_schema()
