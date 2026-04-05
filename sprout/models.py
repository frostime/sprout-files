from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


ConflictPolicy = Literal["fail", "overwrite", "skip", "rename"]
InputType = Literal["string", "number", "enum"]
AssetType = Literal["file", "dir"]


class SproutError(Exception):
    """Base error for sprout."""


class DiscoveryError(SproutError):
    """Raised when project discovery fails."""


class ValidationError(SproutError):
    """Raised when configuration or user inputs are invalid."""


class GenerationError(SproutError):
    """Raised when generation cannot proceed safely."""


@dataclass(slots=True)
class InputSpec:
    name: str
    type: InputType = "string"
    required: bool = True
    description: str = ""
    default: Any = None
    enum: list[str] = field(default_factory=list)
    minimum: float | None = None
    maximum: float | None = None


@dataclass(slots=True)
class AssetSpec:
    type: AssetType
    path: str
    template: str | None = None
    content: str | None = None


@dataclass(slots=True)
class CommandSpec:
    name: str
    description: str
    package_dir: Path
    manifest_path: Path
    inputs: list[InputSpec]
    assets: list[AssetSpec]
    conflict: ConflictPolicy | None = None


@dataclass(slots=True)
class ProjectConfig:
    version: int = 1
    conflict: ConflictPolicy = "fail"


@dataclass(slots=True)
class CommandIssue:
    name: str
    source: Path
    message: str


@dataclass(slots=True)
class CommandRegistry:
    root: Path
    sprout_dir: Path
    config: ProjectConfig
    commands: dict[str, CommandSpec]
    invalid: list[CommandIssue] = field(default_factory=list)
    conflicts: list[CommandIssue] = field(default_factory=list)


@dataclass(slots=True)
class GeneratedItem:
    asset_type: AssetType
    requested_path: str
    final_path: Path
    action: Literal["create", "overwrite", "skip", "rename"]


@dataclass(slots=True)
class InitReport:
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
