# -*- coding: utf-8 -*-
"""Minimal CLI entrypoints for the skill registry."""
import argparse
import asyncio
from typing import Any

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

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
