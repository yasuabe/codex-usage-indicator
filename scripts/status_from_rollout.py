#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print /status-like usage information from a Codex rollout JSONL file."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(Path.home() / ".codex" / "sessions"),
        help="Rollout JSONL file or directory to scan. Defaults to ~/.codex/sessions",
    )
    return parser.parse_args()


def iter_rollouts(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return sorted(path.rglob("rollout-*.jsonl"))


def load_latest_token_count(rollouts: list[Path]) -> tuple[Path, dict[str, Any]]:
    latest_file: Path | None = None
    latest_payload: dict[str, Any] | None = None
    latest_ts: str | None = None

    for rollout in rollouts:
        with rollout.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("type") != "event_msg":
                    continue
                payload = record.get("payload")
                if not isinstance(payload, dict) or payload.get("type") != "token_count":
                    continue
                ts = record.get("timestamp")
                if not isinstance(ts, str):
                    continue
                if latest_ts is None or ts >= latest_ts:
                    latest_ts = ts
                    latest_file = rollout
                    latest_payload = payload

    if latest_file is None or latest_payload is None:
        raise ValueError("No token_count event found")
    return latest_file, latest_payload


def format_reset(epoch: Any) -> str:
    if not isinstance(epoch, (int, float)):
        return "unknown"
    when = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc).astimezone()
    return when.strftime("%Y-%m-%d %H:%M %Z")


def format_percent_left(used_percent: Any) -> str:
    if not isinstance(used_percent, (int, float)):
        return "unknown"
    return f"{max(0.0, 100.0 - float(used_percent)):.0f}% left"


def main() -> int:
    args = parse_args()
    target = Path(args.path).expanduser()
    rollouts = iter_rollouts(target)
    rollout, payload = load_latest_token_count(rollouts)

    info = payload.get("info") or {}
    total_usage = info.get("total_token_usage") or {}
    total_tokens = total_usage.get("total_tokens")
    context_window = info.get("model_context_window")

    print(f"source: {rollout}")
    if (
        isinstance(total_tokens, int)
        and isinstance(context_window, int)
        and 0 < total_tokens <= context_window
    ):
        left_percent = max(0.0, 100.0 - (total_tokens / context_window * 100.0))
        print(
            f"context window: {left_percent:.0f}% left "
            f"({total_tokens:,} used / {context_window:,})"
        )
    elif isinstance(total_tokens, int) and isinstance(context_window, int):
        print(
            "context window: unavailable "
            f"(rollout total_tokens={total_tokens:,} exceeds context_window={context_window:,})"
        )
    else:
        print("context window: unavailable")

    rate_limits = payload.get("rate_limits")
    if isinstance(rate_limits, dict):
        primary = rate_limits.get("primary") or {}
        secondary = rate_limits.get("secondary") or {}
        print(
            f"5h limit: {format_percent_left(primary.get('used_percent'))} "
            f"(resets {format_reset(primary.get('resets_at'))})"
        )
        print(
            f"weekly limit: {format_percent_left(secondary.get('used_percent'))} "
            f"(resets {format_reset(secondary.get('resets_at'))})"
        )
        plan_type = rate_limits.get("plan_type")
        if plan_type:
            print(f"plan: {plan_type}")
    else:
        print("5h limit: unavailable")
        print("weekly limit: unavailable")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
