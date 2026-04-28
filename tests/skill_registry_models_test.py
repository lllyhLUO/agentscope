# -*- coding: utf-8 -*-
"""Tests for the skill registry SQLAlchemy models."""
from unittest import TestCase

from agentscope.skill._models import (
    _SkillRegistryBase,
    _SkillFileTable,
    _SkillMaintainerTable,
    _SkillTable,
    _SkillVersionTable,
)


class SkillRegistryModelsTest(TestCase):
    """Test cases for registry model metadata and constraints."""

    def test_expected_table_names_exist(self) -> None:
        """Test registry metadata exposes the expected tables."""
        self.assertSetEqual(
            set(_SkillRegistryBase.metadata.tables.keys()),
            {
                "skills",
                "skill_versions",
                "skill_files",
                "skill_maintainers",
            },
        )

    def test_skill_name_column_is_unique(self) -> None:
        """Test the skill name column is unique."""
        self.assertTrue(_SkillTable.__table__.c.name.unique)

    def test_skill_version_uniqueness_constraint_exists(self) -> None:
        """Test `(skill_id, version)` uniqueness exists."""
        constraint_columns = {
            tuple(column.name for column in constraint.columns)
            for constraint in _SkillVersionTable.__table__.constraints
            if getattr(constraint, "columns", None)
        }
        self.assertIn(("skill_id", "version"), constraint_columns)

    def test_skill_file_uniqueness_constraint_exists(self) -> None:
        """Test `(skill_version_id, path)` uniqueness exists."""
        constraint_columns = {
            tuple(column.name for column in constraint.columns)
            for constraint in _SkillFileTable.__table__.constraints
            if getattr(constraint, "columns", None)
        }
        self.assertIn(("skill_version_id", "path"), constraint_columns)

    def test_version_foreign_key_points_to_skills(self) -> None:
        """Test version rows reference the `skills` table."""
        foreign_keys = {
            foreign_key.target_fullname
            for foreign_key in _SkillVersionTable.__table__.c.skill_id.foreign_keys
        }
        self.assertEqual(foreign_keys, {"skills.id"})

    def test_file_foreign_key_points_to_skill_versions(self) -> None:
        """Test file rows reference the `skill_versions` table."""
        foreign_keys = {
            foreign_key.target_fullname
            for foreign_key in _SkillFileTable.__table__.c.skill_version_id.foreign_keys
        }
        self.assertEqual(foreign_keys, {"skill_versions.id"})

    def test_maintainer_foreign_key_points_to_skills(self) -> None:
        """Test maintainer rows reference the `skills` table."""
        foreign_keys = {
            foreign_key.target_fullname
            for foreign_key in _SkillMaintainerTable.__table__.c.skill_id.foreign_keys
        }
        self.assertEqual(foreign_keys, {"skills.id"})
