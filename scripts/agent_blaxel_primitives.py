"""Blaxel/Baseten agentic-cloud ideas adapted to local zero-cost primitives.

Maps public architectural bets (isolated sandboxes, durable Agent Drive,
connectivity allowlists, efficiency over agent count) onto Random Timer
ops without paying for Baseten/Blaxel cloud.

Fail closed on paid agentic-cloud platforms under the $20/mo budget cap.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ALLOWED_PLATFORMS = frozenset(
    {
        "local_agent_sandbox",
        "local_sandbox",
        "agent_drive_local",
        "agent_blaxel_primitives",
    }
)
DENIED_MARKERS = (
    "baseten",
    "blaxel",
    "agentic_cloud_paid",
    "sandbox_saas",
)
ALLOWED_CONNECTIVITY_PREFIXES = (
    "mcp://user-thumbgate/",
    "mcp://plugin-posthog-posthog/",
    "mcp://plugin-github-github/",
    "mcp://user-browseros-neo/",
    "mcp://cursor-ide-browser/",
    "file://",
    "local://",
)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


@dataclass(frozen=True)
class DriveResult:
    ok: bool
    path: Path
    version: int
    reason: str = ""


@dataclass(frozen=True)
class LifecycleResult:
    ok: bool
    status: str
    idle_cost_usd_per_hour: float
    reason: str = ""
    session_id: str = ""


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(".", "_").replace(" ", "_")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_sandbox",
            ok=True,
            reason="local sandbox + Agent Drive stay under the monthly external spend cap",
        )
    if any(marker in name for marker in DENIED_MARKERS):
        return ControlDecision(
            action="block_paid_agentic_cloud",
            ok=False,
            reason="paid Baseten/Blaxel agentic cloud is denied; steal ideas, not the bill",
        )
    return ControlDecision(
        action="block_paid_agentic_cloud",
        ok=False,
        reason="unknown agentic-cloud platform is denied by default",
    )


def evaluate_connectivity(*, target: str) -> ControlDecision:
    raw = (target or "").strip()
    if not raw:
        return ControlDecision(
            action="block_untrusted_egress",
            ok=False,
            reason="empty connectivity target",
        )
    lowered = raw.lower()
    if any(lowered.startswith(prefix) for prefix in ALLOWED_CONNECTIVITY_PREFIXES):
        return ControlDecision(
            action="allow_isolated_egress",
            ok=True,
            reason="target matches production allowlist",
        )
    return ControlDecision(
        action="block_untrusted_egress",
        ok=False,
        reason="egress outside allowlisted MCP/local schemes is blocked",
    )


class AgentDrive:
    """Durable, versioned artifact store that outlives sandbox work dirs."""

    def __init__(self, *, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        safe = _norm(session_id).replace("/", "_")
        path = self.root / safe
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _versions_dir(self, session_id: str, relative_path: str) -> Path:
        safe_rel = relative_path.replace("\\", "/").lstrip("/")
        path = self._session_dir(session_id) / "versions" / safe_rel
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _latest_pointer(self, session_id: str, relative_path: str) -> Path:
        safe_rel = relative_path.replace("\\", "/").lstrip("/")
        return self._session_dir(session_id) / "latest" / safe_rel

    def put(
        self,
        *,
        session_id: str,
        relative_path: str,
        source: Path,
        content_type: str = "application/octet-stream",
    ) -> DriveResult:
        src = Path(source)
        if not src.is_file():
            return DriveResult(ok=False, path=src, version=0, reason="source missing")
        versions = self._versions_dir(session_id, relative_path)
        existing = sorted(versions.glob("v*.bin"))
        version = len(existing) + 1
        dest = versions / f"v{version}.bin"
        shutil.copy2(src, dest)
        meta = {
            "session_id": session_id,
            "relative_path": relative_path,
            "version": version,
            "content_type": content_type,
            "sha_bytes": dest.stat().st_size,
            "stored_at_utc": _utc_now(),
        }
        (versions / f"v{version}.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        latest = self._latest_pointer(session_id, relative_path)
        latest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, latest)
        return DriveResult(ok=True, path=latest, version=version)

    def get(
        self,
        *,
        session_id: str,
        relative_path: str,
        version: int | None = None,
    ) -> DriveResult:
        if version is None:
            latest = self._latest_pointer(session_id, relative_path)
            if not latest.is_file():
                return DriveResult(ok=False, path=latest, version=0, reason="not found")
            versions = self._versions_dir(session_id, relative_path)
            n = len(list(versions.glob("v*.bin")))
            return DriveResult(ok=True, path=latest, version=n)
        versions = self._versions_dir(session_id, relative_path)
        path = versions / f"v{version}.bin"
        if not path.is_file():
            return DriveResult(ok=False, path=path, version=version, reason="version missing")
        return DriveResult(ok=True, path=path, version=version)


class SandboxSession:
    """Isolated workdir with suspend/resume via Agent Drive (idle cost ≈ $0)."""

    def __init__(
        self,
        *,
        session_id: str,
        work_dir: Path,
        drive: AgentDrive,
        goal: str,
        status: str = "running",
    ) -> None:
        self.session_id = session_id
        self.work_dir = Path(work_dir)
        self.drive = drive
        self.goal = goal
        self.status = status

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        work_dir: Path,
        drive: AgentDrive,
        goal: str,
    ) -> "SandboxSession":
        path = Path(work_dir)
        path.mkdir(parents=True, exist_ok=True)
        return cls(session_id=session_id, work_dir=path, drive=drive, goal=goal, status="running")

    def suspend(self, *, artifact_globs: Sequence[str] = ()) -> LifecycleResult:
        artifacts: list[str] = []
        for pattern in artifact_globs:
            for match in sorted(self.work_dir.glob(pattern)):
                if match.is_file():
                    rel = str(match.relative_to(self.work_dir))
                    self.drive.put(session_id=self.session_id, relative_path=rel, source=match)
                    artifacts.append(rel)
        checkpoint = {
            "session_id": self.session_id,
            "goal": self.goal,
            "status": "suspended",
            "artifacts": artifacts,
            "suspended_at_utc": _utc_now(),
            "idle_cost_usd_per_hour": 0.0,
        }
        ckpt_path = self.work_dir / "_checkpoint.json"
        ckpt_path.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
        self.drive.put(
            session_id=self.session_id,
            relative_path="_sandbox/checkpoint.json",
            source=ckpt_path,
            content_type="application/json",
        )
        # Clear working files so idle holds no workspace weight (near-zero cost).
        for child in list(self.work_dir.iterdir()):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
        self.status = "suspended"
        return LifecycleResult(
            ok=True,
            status="suspended",
            idle_cost_usd_per_hour=0.0,
            reason="checkpointed to Agent Drive; idle compute released",
            session_id=self.session_id,
        )

    @classmethod
    def resume(
        cls,
        *,
        session_id: str,
        work_dir: Path,
        drive: AgentDrive,
    ) -> LifecycleResult:
        ckpt = drive.get(session_id=session_id, relative_path="_sandbox/checkpoint.json")
        if not ckpt.ok:
            return LifecycleResult(
                ok=False,
                status="missing",
                idle_cost_usd_per_hour=0.0,
                reason="no checkpoint on Agent Drive",
                session_id=session_id,
            )
        payload = json.loads(ckpt.path.read_text(encoding="utf-8"))
        path = Path(work_dir)
        path.mkdir(parents=True, exist_ok=True)
        for rel in payload.get("artifacts") or []:
            got = drive.get(session_id=session_id, relative_path=rel)
            if not got.ok:
                continue
            dest = path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(got.path, dest)
        running = {
            **payload,
            "status": "running",
            "resumed_at_utc": _utc_now(),
        }
        (path / "_checkpoint.json").write_text(json.dumps(running, indent=2) + "\n", encoding="utf-8")
        return LifecycleResult(
            ok=True,
            status="running",
            idle_cost_usd_per_hour=0.0,
            reason="restored artifacts from Agent Drive",
            session_id=session_id,
        )


def suspend_resume_roundtrip_ms(
    *,
    session_id: str,
    work_dir: Path,
    resume_dir: Path,
    drive: AgentDrive,
) -> float:
    session = SandboxSession.create(
        session_id=session_id,
        work_dir=work_dir,
        drive=drive,
        goal="perf",
    )
    (session.work_dir / "ping.txt").write_text("pong", encoding="utf-8")
    t0 = time.perf_counter()
    session.suspend(artifact_globs=("ping.txt",))
    SandboxSession.resume(session_id=session_id, work_dir=resume_dir, drive=drive)
    return (time.perf_counter() - t0) * 1000.0


def rank_agent_efficiency(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Prefer high outcome per effort, with improvement_rate as tie-breaker weight.

    Thesis adapted from Blaxel/Baseten: winners are efficient agents that improve
    fastest — not the fleet with the most concurrent agents.
    """
    scored: list[dict[str, Any]] = []
    for row in rows:
        outcome = float(row.get("outcome_weight") or 0.0)
        effort = max(float(row.get("effort_units") or 0.0), 1e-9)
        improve = float(row.get("improvement_rate") or 0.0)
        efficiency = (outcome / effort) * (1.0 + improve)
        scored.append(
            {
                "id": row.get("id"),
                "outcome_weight": outcome,
                "effort_units": effort,
                "improvement_rate": improve,
                "efficiency_score": efficiency,
            }
        )
    scored.sort(key=lambda r: (-r["efficiency_score"], str(r["id"])))
    return scored


__all__ = [
    "AgentDrive",
    "ControlDecision",
    "DriveResult",
    "LifecycleResult",
    "SandboxSession",
    "evaluate_connectivity",
    "evaluate_platform",
    "rank_agent_efficiency",
    "suspend_resume_roundtrip_ms",
]
