from __future__ import annotations
import datetime
import uuid
from typing import Any
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class SchemaVersion(Base):
    __tablename__ = "schema_version"
    version = Column(Integer, primary_key=True)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)
    icon = Column(String(64), default="Boxes", nullable=False)
    path = Column(Text, nullable=False)
    tags = Column(Text, default="[]", nullable=False)  # JSON list of strings
    favorite = Column(Boolean, default=False, nullable=False)
    sort = Column(Integer, default=0, nullable=False)
    start_mode = Column(String(32), default="ordered", nullable=False)  # "ordered" | "parallel"
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    components = relationship(
        "Component", back_populates="application", cascade="all, delete-orphan", order_by="Component.tier"
    )
    events = relationship("Event", back_populates="application", cascade="all, delete-orphan")


class Component(Base):
    __tablename__ = "components"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(32), nullable=False)  # frontend, backend, database, worker
    name = Column(String(255), nullable=False)
    cwd = Column(Text, nullable=False)
    start_cmd = Column(Text, nullable=False)
    stop_cmd = Column(Text, nullable=True)
    env = Column(Text, default="{}", nullable=False)  # JSON dict
    port = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    health = Column(Text, default="{}", nullable=False)  # JSON dict
    tier = Column(Integer, default=2, nullable=False)  # database 1, backend 2, worker 2, frontend 3
    autorestart = Column(Boolean, default=True, nullable=False)
    max_restarts = Column(Integer, default=5, nullable=False)
    start_on_launch = Column(Boolean, default=False, nullable=False)

    application = relationship("Application", back_populates="components")
    runs = relationship("Run", back_populates="component", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="component", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id = Column(String(36), ForeignKey("components.id", ondelete="CASCADE"), nullable=False)
    pid = Column(Integer, nullable=False)
    create_time = Column(Float, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    exit_code = Column(Integer, nullable=True)
    stop_reason = Column(String(32), nullable=True)  # user, crash, restart, system
    log_path = Column(Text, nullable=False)

    component = relationship("Component", back_populates="runs")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ts = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    level = Column(String(16), nullable=False)  # info, warn, error
    type = Column(String(64), nullable=False)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True)
    component_id = Column(String(36), ForeignKey("components.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    reason = Column(Text, default="", nullable=False)
    detail = Column(Text, default="{}", nullable=False)  # JSON dict/list
    read = Column(Boolean, default=False, nullable=False, index=True)

    application = relationship("Application", back_populates="events")
    component = relationship("Component", back_populates="events")


class Metric1m(Base):
    __tablename__ = "metrics_1m"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    component_id = Column(String(36), nullable=True, index=True)  # None represents machine level
    cpu_pct = Column(Float, default=0.0, nullable=False)
    rss_mb = Column(Float, default=0.0, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)  # JSON-encoded value

