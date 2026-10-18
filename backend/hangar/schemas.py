from __future__ import annotations
import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

# Component and Application statuses
ComponentStatusType = Literal[
    "stopped",
    "starting",
    "running",
    "stopping",
    "crashed",
    "failed",
    "unhealthy",
    "external",
]

ApplicationStatusType = Literal[
    "stopped",
    "partial",
    "running",
    "degraded",
    "problem",
]

ComponentKind = Literal["frontend", "backend", "database", "worker"]
HealthType = Literal["tcp", "http", "process", "command", "file"]
StartMode = Literal["ordered", "parallel"]
EventLevel = Literal["info", "warn", "error"]


class HealthConfig(BaseModel):
    type: HealthType = "process"
    target: str | None = None
    interval_s: float = 5.0
    timeout_s: float = 3.0
    startup_grace_s: float = 30.0


# Component Schemas
class ComponentBase(BaseModel):
    name: str
    kind: ComponentKind
    cwd: str
    start_cmd: str
    stop_cmd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    port: int | None = None
    url: str | None = None
    health: HealthConfig = Field(default_factory=HealthConfig)
    tier: int = 2
    autorestart: bool = True
    max_restarts: int = 5
    start_on_launch: bool = False


class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(BaseModel):
    name: str | None = None
    kind: ComponentKind | None = None
    cwd: str | None = None
    start_cmd: str | None = None
    stop_cmd: str | None = None
    env: dict[str, str] | None = None
    port: int | None = None
    url: str | None = None
    health: HealthConfig | None = None
    tier: int | None = None
    autorestart: bool | None = None
    max_restarts: int | None = None
    start_on_launch: bool | None = None


class ComponentRead(ComponentBase):
    id: str
    application_id: str
    status: ComponentStatusType = "stopped"
    status_reason: str | None = None
    pid: int | None = None
    cpu_pct: float | None = 0.0
    rss_mb: float | None = 0.0
    uptime_s: float | None = None
    active_run_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Application Schemas
class ApplicationBase(BaseModel):
    name: str
    description: str = ""
    icon: str = "Boxes"
    path: str
    tags: list[str] = Field(default_factory=list)
    favorite: bool = False
    sort: int = 0
    start_mode: StartMode = "ordered"


class ApplicationCreate(ApplicationBase):
    components: list[ComponentCreate] = Field(default_factory=list)


class ApplicationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    path: str | None = None
    tags: list[str] | None = None
    favorite: bool | None = None
    sort: int | None = None
    start_mode: StartMode | None = None


class ApplicationRead(ApplicationBase):
    id: str
    created_at: datetime.datetime
    status: ApplicationStatusType = "stopped"
    components: list[ComponentRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Run Schemas
class RunRead(BaseModel):
    id: str
    component_id: str
    pid: int
    create_time: float
    started_at: datetime.datetime
    ended_at: datetime.datetime | None = None
    exit_code: int | None = None
    stop_reason: str | None = None
    log_path: str

    model_config = ConfigDict(from_attributes=True)


# Event Schemas
class EventRead(BaseModel):
    id: str
    ts: datetime.datetime
    level: EventLevel
    type: str
    application_id: str | None = None
    component_id: str | None = None
    title: str
    reason: str
    detail: dict[str, Any] | list[Any] = Field(default_factory=dict)
    read: bool = False

    model_config = ConfigDict(from_attributes=True)


# Metric Schemas
class MetricPoint(BaseModel):
    ts: datetime.datetime
    cpu_pct: float
    rss_mb: float


class MetricsResponse(BaseModel):
    component_id: str | None = None
    range: str
    points: list[MetricPoint]


# Port Schemas
class PortInfo(BaseModel):
    port: int
    pid: int | None = None
    process_name: str | None = None
    cmdline: str | None = None
    managed: bool = False
    application_id: str | None = None
    component_id: str | None = None
    component_name: str | None = None
    conflict: bool = False
    conflict_reason: str | None = None


class KillPortRequest(BaseModel):
    pid: int


# Job Progress Schemas
class JobStep(BaseModel):
    component_id: str
    component_name: str
    action: str  # "start" | "stop"
    status: Literal["pending", "running", "success", "failed", "skipped"]
    error: str | None = None


class JobRead(BaseModel):
    id: str
    application_id: str
    action: str  # "start_app" | "stop_app" | "restart_app"
    status: Literal["running", "completed", "failed", "cancelled"]
    current_step: int = 0
    total_steps: int = 0
    steps: list[JobStep] = Field(default_factory=list)
    error: str | None = None


# Overview Schema
class OverviewResponse(BaseModel):
    app_name: str
    version: str
    total_applications: int
    total_components: int
    running_components: int
    machine_cpu_pct: float
    machine_memory_pct: float
    machine_memory_used_mb: float
    machine_memory_total_mb: float
    status_counts: dict[str, int]
    recent_events: list[EventRead]
    favorites: list[ApplicationRead]
