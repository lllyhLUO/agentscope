# -*- coding: utf-8 -*-
"""Repository helpers for the skill registry."""
import os
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ._models import (
    _SkillFileTable,
    _SkillMaintainerTable,
    _SkillRegistryBase,
    _SkillTable,
    _SkillVersionTable,
)


class SkillRegistryRepository:
    """Repository for PostgreSQL-backed skill registry data."""

    _DATABASE_URL_ENV = "AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL"

    def __init__(
        self,
        engine_or_session: AsyncEngine | AsyncSession,
    ) -> None:
        """Initialize the skill registry repository.

        Args:
            engine_or_session (`AsyncEngine | AsyncSession`):
                Async SQLAlchemy engine or session used for registry access.

        Raises:
            `ValueError`:
                Raised when the provided object is not an async engine or
                session.
        """
        if isinstance(engine_or_session, AsyncEngine):
            self._engine: AsyncEngine | None = engine_or_session
            self._session_factory = async_sessionmaker(
                bind=engine_or_session,
                expire_on_commit=False,
            )
            self._db_session: AsyncSession | None = None
        elif isinstance(engine_or_session, AsyncSession):
            self._engine = None
            self._session_factory = None
            self._db_session = engine_or_session
        else:
            raise ValueError(
                "The 'engine_or_session' parameter must be an instance of "
                "sqlalchemy.ext.asyncio.AsyncEngine or AsyncSession.",
            )

    @classmethod
    def from_env(
        cls,
        database_url: str | None = None,
    ) -> "SkillRegistryRepository":
        """Create a repository from environment configuration.

        Args:
            database_url (`str | None`, optional):
                Explicit database URL. If omitted, the value is read from
                `AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL`.

        Raises:
            `ValueError`:
                Raised when no database URL is available.
            `ImportError`:
                Raised when the configured database driver is not installed.

        Returns:
            `SkillRegistryRepository`:
                Repository configured with an async SQLAlchemy engine.
        """
        resolved_url = (
            database_url
            or os.environ.get(cls._DATABASE_URL_ENV)
        )
        if resolved_url is None:
            raise ValueError(
                "Skill registry database URL is not configured. Set "
                f"{cls._DATABASE_URL_ENV} or pass database_url explicitly.",
            )

        try:
            engine = create_async_engine(resolved_url)
        except ModuleNotFoundError as exc:
            raise ImportError(
                "The configured database driver is not installed. Install "
                "the optional dependencies with `agentscope[skill_registry]`.",
            ) from exc

        return cls(engine)

    @property
    def session(self) -> AsyncSession:
        """Get the active async session.

        Returns:
            `AsyncSession`:
                Active SQLAlchemy async session.
        """
        if self._session_factory is None:
            assert self._db_session is not None
            return self._db_session

        if self._db_session is None or not self._db_session.is_active:
            self._db_session = self._session_factory()

        return self._db_session

    async def init_schema(self) -> None:
        """Create the skill registry schema."""
        engine = self._engine
        if engine is None:
            raise ValueError(
                "Skill registry schema initialization requires an async "
                "engine-backed repository.",
            )
        async with engine.begin() as connection:
            await connection.run_sync(_SkillRegistryBase.metadata.create_all)

    async def get_skill(
        self,
        name: str,
    ) -> dict[str, Any] | None:
        """Get a skill row by name.

        Args:
            name (`str`):
                Globally unique skill name.

        Returns:
            `dict[str, Any] | None`:
                Serialized skill row or `None` when not found.
        """
        result = await self.session.execute(
            select(_SkillTable).filter(_SkillTable.name == name),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._serialize_skill(row)

    async def get_skill_version(
        self,
        name: str,
        version: str,
    ) -> dict[str, Any] | None:
        """Get a specific published skill version.

        Args:
            name (`str`):
                Globally unique skill name.
            version (`str`):
                Explicit version string.

        Returns:
            `dict[str, Any] | None`:
                Serialized version row or `None`.
        """
        result = await self.session.execute(
            select(_SkillVersionTable)
            .join(_SkillTable, _SkillVersionTable.skill_id == _SkillTable.id)
            .filter(
                _SkillTable.name == name,
                _SkillVersionTable.version == version,
            ),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._serialize_skill_version(row)

    async def list_skill_versions(
        self,
        name: str,
    ) -> list[dict[str, Any]]:
        """List published versions for a skill.

        Args:
            name (`str`):
                Globally unique skill name.

        Returns:
            `list[dict[str, Any]]`:
                Version rows ordered by publish time descending.
        """
        result = await self.session.execute(
            select(_SkillVersionTable)
            .join(_SkillTable, _SkillVersionTable.skill_id == _SkillTable.id)
            .filter(_SkillTable.name == name)
            .order_by(_SkillVersionTable.published_at.desc()),
        )
        return [
            self._serialize_skill_version(row)
            for row in result.scalars().all()
        ]

    async def search_skills(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search skills by name or latest version description.

        Args:
            query (`str`):
                Search query string.
            limit (`int`, defaults to `20`):
                Maximum number of results to return.

        Returns:
            `list[dict[str, Any]]`:
                Matching skill rows.
        """
        latest_version_join = and_(
            _SkillTable.id == _SkillVersionTable.skill_id,
            _SkillTable.latest_version == _SkillVersionTable.version,
        )
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(_SkillTable)
            .outerjoin(_SkillVersionTable, latest_version_join)
            .filter(
                or_(
                    _SkillTable.name.ilike(pattern),
                    _SkillVersionTable.description.ilike(pattern),
                ),
            )
            .order_by(_SkillTable.name.asc())
            .limit(limit),
        )
        return [
            self._serialize_skill(row)
            for row in result.scalars().all()
        ]

    async def list_skill_files(
        self,
        name: str,
        version: str,
    ) -> list[dict[str, Any]]:
        """List files for a specific skill version.

        Args:
            name (`str`):
                Globally unique skill name.
            version (`str`):
                Explicit version string.

        Returns:
            `list[dict[str, Any]]`:
                Serialized file rows ordered by path.
        """
        result = await self.session.execute(
            select(_SkillFileTable)
            .join(
                _SkillVersionTable,
                _SkillFileTable.skill_version_id == _SkillVersionTable.id,
            )
            .join(_SkillTable, _SkillVersionTable.skill_id == _SkillTable.id)
            .filter(
                _SkillTable.name == name,
                _SkillVersionTable.version == version,
            )
            .order_by(_SkillFileTable.path.asc()),
        )
        return [
            self._serialize_skill_file(row)
            for row in result.scalars().all()
        ]

    async def is_skill_maintainer(
        self,
        skill_name: str,
        principal: str,
    ) -> bool:
        """Check whether a principal may write to a skill.

        Args:
            skill_name (`str`):
                Globally unique skill name.
            principal (`str`):
                Principal identity to check.

        Returns:
            `bool`:
                `True` when the principal is linked as a maintainer.
        """
        result = await self.session.execute(
            select(_SkillMaintainerTable.id)
            .join(_SkillTable, _SkillMaintainerTable.skill_id == _SkillTable.id)
            .filter(
                _SkillTable.name == skill_name,
                _SkillMaintainerTable.principal == principal,
            ),
        )
        return result.scalar_one_or_none() is not None

    async def assert_can_write(
        self,
        skill_name: str,
        principal: str,
    ) -> None:
        """Raise when a principal is not a maintainer.

        Args:
            skill_name (`str`):
                Globally unique skill name.
            principal (`str`):
                Principal identity to validate.

        Raises:
            `PermissionError`:
                Raised when the principal does not have maintainer access.
        """
        if not await self.is_skill_maintainer(skill_name, principal):
            raise PermissionError(
                f"Principal '{principal}' does not have write access to "
                f"skill '{skill_name}'.",
            )

    @staticmethod
    def _serialize_skill(row: _SkillTable) -> dict[str, Any]:
        """Serialize a skill row.

        Args:
            row (`_SkillTable`):
                ORM row to serialize.

        Returns:
            `dict[str, Any]`:
                Serialized skill data.
        """
        return {
            "id": row.id,
            "name": row.name,
            "latest_version": row.latest_version,
            "status": row.status,
            "created_at": row.created_at,
            "created_by": row.created_by,
        }

    @staticmethod
    def _serialize_skill_version(
        row: _SkillVersionTable,
    ) -> dict[str, Any]:
        """Serialize a skill version row.

        Args:
            row (`_SkillVersionTable`):
                ORM row to serialize.

        Returns:
            `dict[str, Any]`:
                Serialized version data.
        """
        return {
            "id": row.id,
            "skill_id": row.skill_id,
            "version": row.version,
            "description": row.description,
            "metadata_json": row.metadata_json,
            "content_hash": row.content_hash,
            "published_at": row.published_at,
            "published_by": row.published_by,
        }

    @staticmethod
    def _serialize_skill_file(
        row: _SkillFileTable,
    ) -> dict[str, Any]:
        """Serialize a skill file row.

        Args:
            row (`_SkillFileTable`):
                ORM row to serialize.

        Returns:
            `dict[str, Any]`:
                Serialized file data.
        """
        return {
            "id": row.id,
            "skill_version_id": row.skill_version_id,
            "path": row.path,
            "file_type": row.file_type,
            "content_text": row.content_text,
            "content_bytes": row.content_bytes,
            "sha256": row.sha256,
            "size": row.size,
        }
