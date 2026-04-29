# -*- coding: utf-8 -*-
"""Minimal CLI entrypoints for the skill registry."""
import argparse
import asyncio
from typing import Any

from ._cache import SkillRuntimeCache
from ._publisher import publish_skill_directory
from ._repository import SkillRegistryRepository


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the minimal skill CLI argument parser.

    Returns:
        `argparse.ArgumentParser`:
            Configured argument parser.
    """
    parser = argparse.ArgumentParser(prog="agentscope-skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("directory")
    publish_parser.add_argument("--name", required=True)
    publish_parser.add_argument("--version", required=True)
    publish_parser.add_argument("--principal", required=True)
    publish_parser.add_argument("--database-url", dest="database_url")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--database-url", dest="database_url")

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("skill_ref")
    show_parser.add_argument("--database-url", dest="database_url")

    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("skill_ref")
    install_parser.add_argument("--database-url", dest="database_url")

    return parser


async def run_publish_command(
    args: argparse.Namespace,
    repository: SkillRegistryRepository | Any | None = None,
) -> dict[str, Any]:
    """Run the publish command.

    Args:
        args (`argparse.Namespace`):
            Parsed CLI arguments.
        repository (`SkillRegistryRepository | Any | None`, optional):
            Optional injected repository for tests or custom flows.

    Returns:
        `dict[str, Any]`:
            Publish result.
    """
    resolved_repository = repository or SkillRegistryRepository.from_env(
        args.database_url,
    )
    return await publish_skill_directory(
        skill_dir=args.directory,
        skill_name=args.name,
        version=args.version,
        repository=resolved_repository,
        principal=args.principal,
    )


async def run_search_command(
    args: argparse.Namespace,
    repository: SkillRegistryRepository | Any | None = None,
) -> list[dict[str, Any]]:
    """Run the search command.

    Args:
        args (`argparse.Namespace`):
            Parsed CLI arguments.
        repository (`SkillRegistryRepository | Any | None`, optional):
            Optional injected repository.

    Returns:
        `list[dict[str, Any]]`:
            Search result rows.
    """
    resolved_repository = repository or SkillRegistryRepository.from_env(
        args.database_url,
    )
    return await resolved_repository.search_skills(args.query, args.limit)


async def run_show_command(
    args: argparse.Namespace,
    repository: SkillRegistryRepository | Any | None = None,
) -> dict[str, Any]:
    """Run the show command.

    Args:
        args (`argparse.Namespace`):
            Parsed CLI arguments.
        repository (`SkillRegistryRepository | Any | None`, optional):
            Optional injected repository.

    Returns:
        `dict[str, Any]`:
            Version metadata and file list for the explicit skill ref.
    """
    skill_name, version = SkillRuntimeCache.parse_skill_ref(args.skill_ref)
    resolved_repository = repository or SkillRegistryRepository.from_env(
        args.database_url,
    )
    version_payload = await resolved_repository.get_skill_version(
        skill_name,
        version,
    )
    if version_payload is None:
        raise ValueError(f"Registry skill ref '{args.skill_ref}' was not found.")
    files = await resolved_repository.list_skill_files(skill_name, version)
    return {
        "skill_ref": args.skill_ref,
        "version": version_payload,
        "files": files,
    }


async def run_install_command(
    args: argparse.Namespace,
    repository: SkillRegistryRepository | Any | None = None,
    runtime_cache: SkillRuntimeCache | Any | None = None,
) -> dict[str, Any]:
    """Run the install command.

    Args:
        args (`argparse.Namespace`):
            Parsed CLI arguments.
        repository (`SkillRegistryRepository | Any | None`, optional):
            Optional injected repository.
        runtime_cache (`SkillRuntimeCache | Any | None`, optional):
            Optional injected runtime cache.

    Returns:
        `dict[str, Any]`:
            Install result describing the hydrated cache path.
    """
    SkillRuntimeCache.parse_skill_ref(args.skill_ref)
    resolved_repository = repository
    resolved_cache = runtime_cache
    if resolved_cache is None:
        resolved_repository = resolved_repository or SkillRegistryRepository.from_env(
            args.database_url,
        )
        resolved_cache = SkillRuntimeCache(
            repository=resolved_repository,
        )

    hydrated_path = await resolved_cache.hydrate_skill_ref(args.skill_ref)
    return {
        "skill_ref": args.skill_ref,
        "hydrated_path": hydrated_path,
        "installed": True,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the minimal skill CLI.

    Args:
        argv (`list[str] | None`, optional):
            Optional argv override.

    Returns:
        `int`:
            Process exit code.
    """
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.command == "publish":
        result = asyncio.run(run_publish_command(args))
        print(
            "Published "
            f"{result['skill_name']}@{result['version']} "
            f"(idempotent={result['idempotent']})",
        )
        return 0

    if args.command == "search":
        results = asyncio.run(run_search_command(args))
        for item in results:
            print(
                f"{item['name']}@{item.get('latest_version', '-')}"
                f" [{item.get('status', 'unknown')}]",
            )
        return 0

    if args.command == "show":
        result = asyncio.run(run_show_command(args))
        version = result["version"]
        print(f"{args.skill_ref}")
        print(f"description: {version.get('description', '')}")
        print(f"content_hash: {version.get('content_hash', '')}")
        print("files:")
        for file_row in result["files"]:
            print(f"- {file_row['path']} ({file_row['file_type']})")
        return 0

    if args.command == "install":
        result = asyncio.run(run_install_command(args))
        print(
            "Installed "
            f"{result['skill_ref']} to {result['hydrated_path']}",
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
