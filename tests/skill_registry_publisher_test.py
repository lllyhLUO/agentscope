# -*- coding: utf-8 -*-
"""Tests for local skill publishing manifest preparation."""
import tempfile
from pathlib import Path
from unittest import TestCase

from agentscope.skill._publisher import (
    SkillPublishManifest,
    build_skill_publish_manifest,
)


class SkillRegistryPublisherTest(TestCase):
    """Test cases for skill directory validation and manifest building."""

    def test_missing_top_level_skill_md_raises(self) -> None:
        """Test publish manifest build fails without top-level `SKILL.md`."""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            with self.assertRaisesRegex(ValueError, "SKILL.md"):
                build_skill_publish_manifest(
                    skill_dir,
                    "sql_analyzer",
                    "1.0.0",
                )

    def test_missing_frontmatter_description_raises(self) -> None:
        """Test publish manifest build fails without required metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            skill_dir.joinpath("SKILL.md").write_text(
                "---\nname: sql_analyzer\n---\n# Title\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "description"):
                build_skill_publish_manifest(
                    skill_dir,
                    "sql_analyzer",
                    "1.0.0",
                )

    def test_requested_skill_name_must_match_frontmatter_name(self) -> None:
        """Test requested skill name must match the frontmatter name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            skill_dir.joinpath("SKILL.md").write_text(
                "---\nname: other_name\ndescription: Example\n---\n# Title\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "requested skill name"):
                build_skill_publish_manifest(
                    skill_dir,
                    "sql_analyzer",
                    "1.0.0",
                )

    def test_transient_files_are_ignored(self) -> None:
        """Test transient local artifacts are excluded from the manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            skill_dir.joinpath("SKILL.md").write_text(
                "---\nname: sql_analyzer\ndescription: Example\n---\n# Title\n",
                encoding="utf-8",
            )
            skill_dir.joinpath("tool.py").write_text(
                "print('hello')\n",
                encoding="utf-8",
            )
            skill_dir.joinpath(".DS_Store").write_text(
                "ignored",
                encoding="utf-8",
            )
            pycache_dir = skill_dir.joinpath("__pycache__")
            pycache_dir.mkdir()
            pycache_dir.joinpath("tool.cpython-312.pyc").write_bytes(b"ignored")

            manifest = build_skill_publish_manifest(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
            )

            self.assertEqual(
                [item.path for item in manifest.files],
                ["SKILL.md", "tool.py"],
            )

    def test_manifest_hash_is_deterministic_and_stably_ordered(self) -> None:
        """Test repeated scans return identical ordered manifests and hashes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            skill_dir.joinpath("nested").mkdir()
            skill_dir.joinpath("SKILL.md").write_text(
                "---\nname: sql_analyzer\ndescription: Example\n---\n# Title\n",
                encoding="utf-8",
            )
            skill_dir.joinpath("nested", "b.txt").write_text(
                "b\n",
                encoding="utf-8",
            )
            skill_dir.joinpath("a.txt").write_text(
                "a\n",
                encoding="utf-8",
            )

            first_manifest = build_skill_publish_manifest(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
            )
            second_manifest = build_skill_publish_manifest(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
            )

            self.assertIsInstance(first_manifest, SkillPublishManifest)
            self.assertEqual(
                [item.path for item in first_manifest.files],
                ["SKILL.md", "a.txt", "nested/b.txt"],
            )
            self.assertEqual(
                [item.path for item in first_manifest.files],
                [item.path for item in second_manifest.files],
            )
            self.assertEqual(first_manifest.content_hash, second_manifest.content_hash)

    def test_binary_files_are_preserved_in_manifest(self) -> None:
        """Test binary files are stored in the manifest as bytes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            skill_dir.joinpath("SKILL.md").write_text(
                "---\nname: sql_analyzer\ndescription: Example\n---\n# Title\n",
                encoding="utf-8",
            )
            skill_dir.joinpath("icon.bin").write_bytes(b"\x00\x01\x02")

            manifest = build_skill_publish_manifest(
                skill_dir,
                "sql_analyzer",
                "1.0.0",
            )

            binary_entry = next(
                item for item in manifest.files if item.path == "icon.bin"
            )
            self.assertIsNone(binary_entry.content_text)
            self.assertEqual(binary_entry.content_bytes, b"\x00\x01\x02")
