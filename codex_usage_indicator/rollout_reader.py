from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path


logger = logging.getLogger(__name__)

SESSIONS_DIR = Path.home() / ".codex" / "sessions"
MAX_ROLLOUT_FILES = 20


class UsageDataUnavailableError(RuntimeError):
    """Raised when rollout usage data is not available."""


def _iter_recent_rollouts(limit: int = MAX_ROLLOUT_FILES) -> list[Path]:
    if not SESSIONS_DIR.exists():
        raise UsageDataUnavailableError(f"Sessions directory not found: {SESSIONS_DIR}")

    rollouts = sorted(
        SESSIONS_DIR.rglob("rollout-*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not rollouts:
        raise UsageDataUnavailableError(f"No rollout files found under: {SESSIONS_DIR}")
    return rollouts[:limit]


def _parse_token_count_event(line: str):
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None

    if record.get("type") != "event_msg":
        return None

    payload = record.get("payload")
    if not isinstance(payload, dict) or payload.get("type") != "token_count":
        return None

    return record


def _to_local_iso(timestamp: str | None) -> str | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone().isoformat()
    except ValueError:
        return None


def _epoch_to_local_iso(epoch: int | float | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone().isoformat()


def _parse_timestamp(timestamp: str | None) -> datetime | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_usage() -> dict:
    """Return the latest rollout token_count event with non-null rate_limits."""
    best_record = None
    best_rollout = None
    best_timestamp = None

    for rollout in _iter_recent_rollouts():
        try:
            with rollout.open("r", encoding="utf-8") as fh:
                for line in fh:
                    record = _parse_token_count_event(line)
                    if not record:
                        continue
                    payload = record["payload"]
                    rate_limits = payload.get("rate_limits")
                    if not isinstance(rate_limits, dict):
                        continue
                    timestamp = _parse_timestamp(record.get("timestamp"))
                    if timestamp is None:
                        continue
                    if best_timestamp is None or timestamp >= best_timestamp:
                        best_record = record
                        best_rollout = rollout
                        best_timestamp = timestamp
        except OSError as exc:
            logger.warning("Failed to read rollout: %s (%s)", rollout, exc)

    if not best_record or not best_rollout:
        raise UsageDataUnavailableError("No token_count event with rate_limits found")

    payload = best_record["payload"]
    rate_limits = payload["rate_limits"]
    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}

    primary_used = float(primary.get("used_percent", 0.0))
    secondary_used = float(secondary.get("used_percent", 0.0))

    return {
        "primary_used_percent": primary_used,
        "secondary_used_percent": secondary_used,
        "primary_left_percent": max(0.0, 100.0 - primary_used),
        "secondary_left_percent": max(0.0, 100.0 - secondary_used),
        "primary_resets_at": _epoch_to_local_iso(primary.get("resets_at")),
        "secondary_resets_at": _epoch_to_local_iso(secondary.get("resets_at")),
        "plan_type": rate_limits.get("plan_type"),
        "timestamp": _to_local_iso(best_record.get("timestamp")),
        "source_path": str(best_rollout),
    }


def fetch_usage_mock() -> dict:
    """Return stable mock data for local UI development."""
    now = datetime.now().astimezone()
    return {
        "primary_used_percent": 1.0,
        "secondary_used_percent": 5.0,
        "primary_left_percent": 99.0,
        "secondary_left_percent": 95.0,
        "primary_resets_at": now.isoformat(),
        "secondary_resets_at": now.isoformat(),
        "plan_type": "plus",
        "timestamp": now.isoformat(),
        "source_path": "mock",
    }
