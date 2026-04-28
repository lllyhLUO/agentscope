# -*- coding: utf-8 -*-
"""SQLAlchemy models for the skill registry."""
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base


_SkillRegistryBase: Any = declarative_base()


class _SkillTable(_SkillRegistryBase):
    """Persistent identity row for a published skill."""

    __tablename__ = "skills"

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    latest_version = Column(String(64), nullable=True)
    status = Column(String(64), nullable=False, default="active")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by = Column(String(255), nullable=False)


class _SkillVersionTable(_SkillRegistryBase):
    """Immutable published version row for a skill."""

    __tablename__ = "skill_versions"
    __table_args__ = (
        UniqueConstraint(
            "skill_id",
            "version",
            name="uq_skill_versions_skill_id_version",
        ),
    )

    id = Column(String(255), primary_key=True)
    skill_id = Column(
        String(255),
        ForeignKey("skills.id"),
        nullable=False,
    )
    version = Column(String(64), nullable=False)
    description = Column(Text, nullable=False, default="")
    metadata_json = Column(JSON, nullable=False, default=dict)
    content_hash = Column(String(128), nullable=False)
    published_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    published_by = Column(String(255), nullable=False)


class _SkillFileTable(_SkillRegistryBase):
    """File row stored under a specific published skill version."""

    __tablename__ = "skill_files"
    __table_args__ = (
        UniqueConstraint(
            "skill_version_id",
            "path",
            name="uq_skill_files_skill_version_id_path",
        ),
    )

    id = Column(String(255), primary_key=True)
    skill_version_id = Column(
        String(255),
        ForeignKey("skill_versions.id"),
        nullable=False,
    )
    path = Column(String(1024), nullable=False)
    file_type = Column(String(64), nullable=False)
    content_text = Column(Text, nullable=True)
    content_bytes = Column(LargeBinary, nullable=True)
    sha256 = Column(String(128), nullable=False)
    size = Column(Integer, nullable=False)


class _SkillMaintainerTable(_SkillRegistryBase):
    """Maintainer role row used for write authorization checks."""

    __tablename__ = "skill_maintainers"

    id = Column(String(255), primary_key=True)
    skill_id = Column(
        String(255),
        ForeignKey("skills.id"),
        nullable=False,
    )
    principal = Column(String(255), nullable=False)
    role = Column(String(64), nullable=False, default="maintainer")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
