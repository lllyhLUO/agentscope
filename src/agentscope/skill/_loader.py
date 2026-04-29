# -*- coding: utf-8 -*-
"""Runtime loader for registry-backed skills."""
import asyncio
import threading
from pathlib import Path
from typing import Any

from ._cache import SkillRuntimeCache
from ._repository import SkillRegistryRepository


class SkillRegistryLoader:
    """Bridge registry-backed skills into local directory registration.

    Args:
        repository (`Any | None`, optional):
            Optional injected repository for tests or custom setups.
        runtime_cache (`SkillRuntimeCache | Any | None`, optional):
            Optional injected runtime cache. If omitted, the loader creates one
            from the repository.
        cache_dir (`str | Path | None`, optional):
            Optional cache directory override when building the default cache.
        database_url (`str | None`, optional):
            Optional database URL used when constructing a default repository.
    """

    def __init__(
        self,
        repository: Any | None = None,
        runtime_cache: SkillRuntimeCache | Any | None = None,
        cache_dir: str | Path | None = None,
        database_url: str | None = None,
    ) -> None:
        """Initialize the skill registry loader."""
        resolved_repository = repository
        if resolved_repository is None and runtime_cache is None:
            resolved_repository = SkillRegistryRepository.from_env(database_url)

        if runtime_cache is None:
            assert resolved_repository is not None
            runtime_cache = SkillRuntimeCache(
                repository=resolved_repository,
                cache_dir=cache_dir,
            )

        self.repository = resolved_repository
        self.runtime_cache = runtime_cache

    @classmethod
    def from_env(
        cls,
        database_url: str | None = None,
        cache_dir: str | Path | None = None,
    ) -> "SkillRegistryLoader":
        """Create a loader from environment-backed defaults."""
        repository = SkillRegistryRepository.from_env(database_url)
        return cls(
            repository=repository,
            runtime_cache=SkillRuntimeCache(
                repository=repository,
                cache_dir=cache_dir,
            ),
        )

    async def resolve_skill_dir(
        self,
        skill_ref: str,
    ) -> str:
        """Resolve a registry skill reference into a hydrated local directory.

        Args:
            skill_ref (`str`):
                Skill reference in explicit `skill_name@version` form.

        Raises:
            `ValueError`:
                Raised when the ref omits the explicit version.

        Returns:
            `str`:
                Hydrated local directory path.
        """
        self._validate_skill_ref(skill_ref)
        return await self.runtime_cache.hydrate_skill_ref(skill_ref)

    def resolve_skill_dir_sync(
        self,
        skill_ref: str,
    ) -> str:
        """Synchronously resolve a skill ref for sync Toolkit integration.

        Args:
            skill_ref (`str`):
                Skill reference in explicit `skill_name@version` form.

        Returns:
            `str`:
                Hydrated local directory path.
        """
        coroutine = self.resolve_skill_dir(skill_ref)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)

        result: dict[str, str] = {}
        error: dict[str, BaseException] = {}

        def _runner() -> None:
            """Run async resolution in an isolated thread loop."""
            try:
                result["value"] = asyncio.run(coroutine)
            except BaseException as exc:  # pragma: no cover - passthrough
                error["value"] = exc

        thread = threading.Thread(target=_runner)
        thread.start()
        thread.join()

        if "value" in error:
            raise error["value"]
        return result["value"]

    @staticmethod
    def _validate_skill_ref(skill_ref: str) -> None:
        """Validate explicit runtime skill ref syntax.

        Args:
            skill_ref (`str`):
                Candidate skill reference.

        Raises:
            `ValueError`:
                Raised when the ref is not in `skill_name@version` form.
        """
        if "@" not in skill_ref:
            raise ValueError(
                "Registry skill refs must use explicit skill_name@version form.",
            )
        skill_name, version = skill_ref.rsplit("@", 1)
        if not skill_name or not version:
            raise ValueError(
                "Registry skill refs must use explicit skill_name@version form.",
            )
