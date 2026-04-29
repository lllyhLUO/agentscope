# -*- coding: utf-8 -*-
"""Managed runtime cache for registry-backed skills."""
import os
import shutil
from pathlib import Path
from typing import Any


class SkillRuntimeCache:
    """Managed cache that hydrates published skills into real directories.

    Args:
        repository (`Any`):
            Repository-like object used to read exact version metadata and file
            contents.
        cache_dir (`str | Path | None`, optional):
            Optional cache root override. Defaults to a managed path outside the
            project working tree.
    """

    _CACHE_ENV = "AGENTSCOPE_SKILL_REGISTRY_CACHE_DIR"

    def __init__(
        self,
        repository: Any,
        cache_dir: str | Path | None = None,
    ) -> None:
        """Initialize the managed runtime cache."""
        self._repository = repository
        resolved_cache_dir = cache_dir or os.environ.get(self._CACHE_ENV)
        self._cache_dir = Path(
            resolved_cache_dir or self._default_cache_dir(),
        ).expanduser().resolve()

    @property
    def cache_dir(self) -> Path:
        """Managed cache root directory."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        return self._cache_dir

    @staticmethod
    def parse_skill_ref(skill_ref: str) -> tuple[str, str]:
        """Parse an explicit registry skill reference.

        Args:
            skill_ref (`str`):
                Skill reference in `skill_name@version` form.

        Raises:
            `ValueError`:
                Raised when the ref does not contain both name and version.

        Returns:
            `tuple[str, str]`:
                Parsed `(skill_name, version)` pair.
        """
        if "@" not in skill_ref:
            raise ValueError(
                "Skill references must use explicit skill_name@version form.",
            )
        skill_name, version = skill_ref.rsplit("@", 1)
        if not skill_name or not version:
            raise ValueError(
                "Skill references must use explicit skill_name@version form.",
            )
        return skill_name, version

    async def hydrate_skill_ref(
        self,
        skill_ref: str,
    ) -> str:
        """Hydrate a registry skill reference into a local execution directory.

        Args:
            skill_ref (`str`):
                Skill reference in `skill_name@version` form.

        Raises:
            `ValueError`:
                Raised when the requested version does not exist.

        Returns:
            `str`:
                Absolute path to the hydrated local skill directory.
        """
        skill_name, version = self.parse_skill_ref(skill_ref)
        version_payload = await self._repository.get_skill_version(
            skill_name,
            version,
        )
        if version_payload is None:
            raise ValueError(
                f"Registry skill ref '{skill_ref}' was not found.",
            )

        content_hash = version_payload["content_hash"]
        version_dir = (
            self.cache_dir
            / self._safe_component(skill_name)
            / self._safe_component(version)
        )
        target_dir = version_dir / content_hash

        self._clear_stale_directories(version_dir, content_hash)
        if target_dir.joinpath("SKILL.md").is_file():
            return str(target_dir)

        file_rows = await self._repository.list_skill_files(skill_name, version)
        self._hydrate_directory(target_dir, file_rows)
        return str(target_dir)

    def _hydrate_directory(
        self,
        target_dir: Path,
        file_rows: list[dict[str, Any]],
    ) -> None:
        """Write repository file rows to the local cache directory.

        Args:
            target_dir (`Path`):
                Directory that will contain the hydrated skill files.
            file_rows (`list[dict[str, Any]]`):
                Serialized registry file rows for the skill version.
        """
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        for file_row in file_rows:
            target_path = target_dir / file_row["path"]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if file_row["content_text"] is not None:
                target_path.write_text(
                    file_row["content_text"],
                    encoding="utf-8",
                )
            else:
                target_path.write_bytes(file_row["content_bytes"] or b"")

    def _clear_stale_directories(
        self,
        version_dir: Path,
        active_hash: str,
    ) -> None:
        """Remove stale cache entries for the same skill/version.

        Args:
            version_dir (`Path`):
                Parent directory for one skill/version.
            active_hash (`str`):
                Content hash that should remain valid.
        """
        version_dir.mkdir(parents=True, exist_ok=True)
        for entry in version_dir.iterdir():
            if entry.name == active_hash:
                continue
            if entry.is_dir():
                shutil.rmtree(entry)

    @staticmethod
    def _safe_component(component: str) -> str:
        """Convert a ref component into a safe cache path segment."""
        return (
            component.replace("/", "__")
            .replace("\\", "__")
            .replace(":", "_")
        )

    @staticmethod
    def _default_cache_dir() -> str:
        """Build the default managed cache root outside the repo tree."""
        if os.name == "nt":
            base_dir = os.environ.get("LOCALAPPDATA")
            if base_dir:
                return str(Path(base_dir) / "agentscope" / "skills")
        base_dir = os.environ.get("XDG_CACHE_HOME")
        if base_dir:
            return str(Path(base_dir) / "agentscope" / "skills")
        return str(Path.home() / ".cache" / "agentscope" / "skills")
