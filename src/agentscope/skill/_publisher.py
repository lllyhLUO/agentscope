# -*- coding: utf-8 -*-
"""Helpers for preparing local skills for registry publishing."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter


_TRANSIENT_NAMES = {
    ".DS_Store",
}
_TRANSIENT_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
_TRANSIENT_SUFFIXES = {
    ".pyc",
}


@dataclass(frozen=True)
class SkillPublishFile:
    """Serializable file entry for a publish manifest.

    Args:
        path (`str`):
            Relative path within the skill directory.
        file_type (`str`):
            Logical file type used during later persistence.
        content_text (`str | None`):
            UTF-8 text content when the file is text.
        content_bytes (`bytes | None`):
            Raw bytes when the file is binary.
        sha256 (`str`):
            SHA-256 digest of the file contents.
        size (`int`):
            File size in bytes.
    """

    path: str
    file_type: str
    content_text: str | None
    content_bytes: bytes | None
    sha256: str
    size: int


@dataclass(frozen=True)
class SkillPublishManifest:
    """Deterministic manifest for publishing a local skill directory.

    Args:
        skill_name (`str`):
            Globally unique skill name requested by the publisher.
        version (`str`):
            Explicit skill version.
        description (`str`):
            Description from `SKILL.md` frontmatter.
        metadata_json (`dict[str, Any]`):
            Full frontmatter metadata for later persistence.
        source_dir (`Path`):
            Canonical local skill directory path.
        files (`list[SkillPublishFile]`):
            Ordered file entries included in the publish artifact.
        content_hash (`str`):
            Deterministic version-level hash derived from the ordered manifest.
    """

    skill_name: str
    version: str
    description: str
    metadata_json: dict[str, Any]
    source_dir: Path
    files: list[SkillPublishFile]
    content_hash: str


def build_skill_publish_manifest(
    skill_dir: str | Path,
    skill_name: str,
    version: str,
) -> SkillPublishManifest:
    """Validate a local skill directory and build a deterministic manifest.

    Args:
        skill_dir (`str | Path`):
            Path to the local skill directory.
        skill_name (`str`):
            Requested skill name. This must match the `name` field in the
            top-level `SKILL.md` frontmatter.
        version (`str`):
            Explicit publish version string.

    Raises:
        `ValueError`:
            Raised when the directory is invalid, `SKILL.md` is missing, or
            required frontmatter metadata is absent.

    Returns:
        `SkillPublishManifest`:
            Deterministic publish manifest for the local skill directory.
    """
    source_dir = Path(skill_dir).expanduser().resolve()
    if not source_dir.is_dir():
        raise ValueError(
            f"Skill directory '{source_dir}' does not exist or is not a directory.",
        )

    skill_md_path = source_dir / "SKILL.md"
    if not skill_md_path.is_file():
        raise ValueError(
            f"Skill directory '{source_dir}' must contain a top-level SKILL.md file.",
        )

    metadata = _load_skill_metadata(skill_md_path)
    declared_name = metadata["name"]
    description = metadata["description"]

    if declared_name != skill_name:
        raise ValueError(
            "The requested skill name does not match the `name` field in "
            f"SKILL.md: requested skill name '{skill_name}', "
            f"frontmatter name '{declared_name}'.",
        )

    files = [
        _build_publish_file(source_dir, file_path)
        for file_path in _iter_publish_files(source_dir)
    ]
    content_hash = _build_manifest_hash(skill_name, version, files)

    return SkillPublishManifest(
        skill_name=skill_name,
        version=version,
        description=description,
        metadata_json=metadata,
        source_dir=source_dir,
        files=files,
        content_hash=content_hash,
    )


async def publish_skill_directory(
    skill_dir: str | Path,
    skill_name: str,
    version: str,
    repository: Any,
    principal: str,
) -> dict[str, Any]:
    """Publish a validated local skill directory into the registry.

    Args:
        skill_dir (`str | Path`):
            Path to the local skill directory.
        skill_name (`str`):
            Requested registry skill name.
        version (`str`):
            Explicit publish version string.
        repository (`Any`):
            Repository-like object providing registry read/write helpers.
        principal (`str`):
            Maintainer identity performing the publish.

    Raises:
        `ValueError`:
            Raised when the target version already exists with different content.

    Returns:
        `dict[str, Any]`:
            Publish result describing whether a new artifact was created or an
            identical content version was reused.
    """
    manifest = build_skill_publish_manifest(skill_dir, skill_name, version)
    await repository.assert_can_write(skill_name, principal)
    existing_version = await repository.get_skill_version(skill_name, version)
    if existing_version is not None:
        if existing_version["content_hash"] != manifest.content_hash:
            raise ValueError(
                "Cannot publish the same skill_name@version with different "
                f"content: {skill_name}@{version} has different content.",
            )
        return {
            "skill_name": manifest.skill_name,
            "version": manifest.version,
            "content_hash": manifest.content_hash,
            "file_count": len(manifest.files),
            "created": False,
            "idempotent": True,
            "message": "identical content already published",
        }

    return await repository.create_skill_artifact(
        manifest=manifest,
        principal=principal,
    )


def _load_skill_metadata(skill_md_path: Path) -> dict[str, Any]:
    """Load and validate skill frontmatter metadata.

    Args:
        skill_md_path (`Path`):
            Path to the top-level `SKILL.md` file.

    Raises:
        `ValueError`:
            Raised when required frontmatter keys are missing.

    Returns:
        `dict[str, Any]`:
            Parsed frontmatter metadata.
    """
    with skill_md_path.open("r", encoding="utf-8") as handle:
        post = frontmatter.load(handle)

    name = post.get("name")
    description = post.get("description")
    if not name:
        raise ValueError("SKILL.md frontmatter must include a `name` field.")
    if not description:
        raise ValueError(
            "SKILL.md frontmatter must include a `description` field.",
        )
    return dict(post.metadata)


def _iter_publish_files(source_dir: Path) -> list[Path]:
    """Collect stable ordered publish files for a skill directory.

    Args:
        source_dir (`Path`):
            Skill root directory.

    Returns:
        `list[Path]`:
            Sorted file paths relative to the local directory.
    """
    file_paths: list[Path] = []
    for path in source_dir.rglob("*"):
        if path.is_dir():
            continue
        if _is_transient_path(source_dir, path):
            continue
        file_paths.append(path)
    return sorted(
        file_paths,
        key=lambda item: item.relative_to(source_dir).as_posix(),
    )


def _is_transient_path(source_dir: Path, file_path: Path) -> bool:
    """Check whether a path should be excluded from publishing.

    Args:
        source_dir (`Path`):
            Skill root directory.
        file_path (`Path`):
            Candidate file path.

    Returns:
        `bool`:
            `True` when the path is transient local noise.
    """
    relative = file_path.relative_to(source_dir)
    if any(part.startswith(".") for part in relative.parts):
        return True
    if _is_in_nested_git_repository(source_dir, file_path):
        return True
    if file_path.name in _TRANSIENT_NAMES:
        return True
    if file_path.suffix in _TRANSIENT_SUFFIXES:
        return True
    return any(part in _TRANSIENT_DIR_NAMES for part in relative.parts)


def _is_in_nested_git_repository(source_dir: Path, file_path: Path) -> bool:
    """Check whether a file lives inside a nested git repository."""
    for parent in file_path.parents:
        if parent == source_dir:
            return False
        if parent.joinpath(".git").is_dir():
            return True
    return False


def _build_publish_file(
    source_dir: Path,
    file_path: Path,
) -> SkillPublishFile:
    """Build a manifest entry for a single file.

    Args:
        source_dir (`Path`):
            Skill root directory.
        file_path (`Path`):
            Absolute path of the file to include.

    Returns:
        `SkillPublishFile`:
            Manifest entry for the given file.
    """
    raw_bytes = file_path.read_bytes()
    relative_path = file_path.relative_to(source_dir).as_posix()
    file_type = _detect_file_type(relative_path, raw_bytes)
    content_text: str | None
    content_bytes: bytes | None
    if file_type == "binary":
        content_text = None
        content_bytes = raw_bytes
    else:
        content_text = raw_bytes.decode("utf-8")
        content_bytes = None

    return SkillPublishFile(
        path=relative_path,
        file_type=file_type,
        content_text=content_text,
        content_bytes=content_bytes,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        size=len(raw_bytes),
    )


def _detect_file_type(
    relative_path: str,
    raw_bytes: bytes,
) -> str:
    """Detect the logical file type used in the manifest.

    Args:
        relative_path (`str`):
            File path relative to the skill directory.
        raw_bytes (`bytes`):
            Raw file content bytes.

    Returns:
        `str`:
            Logical file type label.
    """
    if relative_path.endswith(".md"):
        return "markdown"
    if b"\x00" in raw_bytes:
        return "binary"
    try:
        raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return "binary"
    return "text"


def _build_manifest_hash(
    skill_name: str,
    version: str,
    files: list[SkillPublishFile],
) -> str:
    """Build a deterministic content hash for a publish manifest.

    Args:
        skill_name (`str`):
            Globally unique skill name.
        version (`str`):
            Explicit version string.
        files (`list[SkillPublishFile]`):
            Ordered file entries.

    Returns:
        `str`:
            SHA-256 digest of the ordered manifest.
    """
    payload = {
        "skill_name": skill_name,
        "version": version,
        "files": [
            {
                "path": item.path,
                "sha256": item.sha256,
                "size": item.size,
            }
            for item in files
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
