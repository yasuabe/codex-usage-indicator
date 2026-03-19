use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};

use chrono::{DateTime, Local, TimeZone, Utc};
use serde::Deserialize;
use walkdir::WalkDir;

#[derive(Debug, Deserialize)]
struct Record {
    timestamp: Option<String>,
    #[serde(rename = "type")]
    record_type: String,
    payload: Option<Payload>,
}

#[derive(Debug, Deserialize)]
struct Payload {
    #[serde(rename = "type")]
    payload_type: String,
    rate_limits: Option<RateLimits>,
}

#[derive(Debug, Deserialize)]
struct RateLimits {
    primary: Option<RateLimitWindow>,
    secondary: Option<RateLimitWindow>,
    plan_type: Option<String>,
}

#[derive(Debug, Deserialize)]
struct RateLimitWindow {
    used_percent: Option<f64>,
    resets_at: Option<i64>,
}

#[derive(Debug)]
pub struct UsageSnapshot {
    pub source_path: PathBuf,
    pub timestamp: DateTime<chrono::FixedOffset>,
    pub primary_used_percent: f64,
    pub secondary_used_percent: f64,
    pub primary_resets_at: Option<DateTime<Local>>,
    pub secondary_resets_at: Option<DateTime<Local>>,
    pub plan_type: Option<String>,
}

pub fn default_sessions_dir() -> PathBuf {
    let home = env::var_os("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("~"));
    home.join(".codex").join("sessions")
}

pub fn find_latest_snapshot(path: &Path) -> Result<UsageSnapshot, String> {
    let rollouts = collect_rollouts(path)?;
    let mut best: Option<UsageSnapshot> = None;

    for rollout in rollouts {
        let file = File::open(&rollout)
            .map_err(|err| format!("failed to open {}: {err}", rollout.display()))?;
        let reader = BufReader::new(file);

        for line in reader.lines() {
            let line =
                line.map_err(|err| format!("failed to read {}: {err}", rollout.display()))?;
            let Some(snapshot) = parse_snapshot_line(&line, &rollout)? else {
                continue;
            };

            let replace = match best.as_ref() {
                None => true,
                Some(current) => snapshot_is_better(&snapshot, current),
            };
            if replace {
                best = Some(snapshot);
            }
        }
    }

    best.ok_or_else(|| "no token_count event with rate_limits found".to_string())
}

pub fn format_percent_left(used_percent: f64) -> String {
    format!("{:.0}% left", (100.0 - used_percent).max(0.0))
}

pub fn format_reset(reset_at: Option<DateTime<Local>>, with_date: bool) -> String {
    match reset_at {
        None => "unknown".to_string(),
        Some(dt) => {
            if with_date {
                dt.format("%Y-%m-%d %H:%M %Z").to_string()
            } else {
                dt.format("%H:%M %Z").to_string()
            }
        }
    }
}

fn collect_rollouts(path: &Path) -> Result<Vec<PathBuf>, String> {
    if path.is_file() {
        return Ok(vec![path.to_path_buf()]);
    }
    if !path.exists() {
        return Err(format!("path not found: {}", path.display()));
    }

    let mut rollouts = Vec::new();
    for entry in WalkDir::new(path) {
        let entry = entry.map_err(|err| format!("failed to walk {}: {err}", path.display()))?;
        if entry.file_type().is_file() {
            let file_name = entry.file_name().to_string_lossy();
            if file_name.starts_with("rollout-") && file_name.ends_with(".jsonl") {
                rollouts.push(entry.into_path());
            }
        }
    }

    rollouts.sort();
    if rollouts.is_empty() {
        return Err(format!("no rollout files found under: {}", path.display()));
    }
    Ok(rollouts)
}

fn parse_snapshot_line(line: &str, source_path: &Path) -> Result<Option<UsageSnapshot>, String> {
    let record: Record = match serde_json::from_str(line) {
        Ok(record) => record,
        Err(_) => return Ok(None),
    };

    if record.record_type != "event_msg" {
        return Ok(None);
    }

    let Some(payload) = record.payload else {
        return Ok(None);
    };
    if payload.payload_type != "token_count" {
        return Ok(None);
    }

    let Some(rate_limits) = payload.rate_limits else {
        return Ok(None);
    };

    let timestamp = record
        .timestamp
        .as_deref()
        .ok_or_else(|| format!("missing timestamp in {}", source_path.display()))
        .and_then(parse_timestamp)?;

    let primary_used_percent = rate_limits
        .primary
        .as_ref()
        .and_then(|window| window.used_percent)
        .unwrap_or(0.0);
    let secondary_used_percent = rate_limits
        .secondary
        .as_ref()
        .and_then(|window| window.used_percent)
        .unwrap_or(0.0);

    let primary_resets_at = rate_limits
        .primary
        .as_ref()
        .and_then(|window| window.resets_at)
        .and_then(epoch_to_local_datetime);
    let secondary_resets_at = rate_limits
        .secondary
        .as_ref()
        .and_then(|window| window.resets_at)
        .and_then(epoch_to_local_datetime);

    Ok(Some(UsageSnapshot {
        source_path: source_path.to_path_buf(),
        timestamp,
        primary_used_percent,
        secondary_used_percent,
        primary_resets_at,
        secondary_resets_at,
        plan_type: rate_limits.plan_type,
    }))
}

fn snapshot_is_better(candidate: &UsageSnapshot, current: &UsageSnapshot) -> bool {
    if candidate.timestamp != current.timestamp {
        return candidate.timestamp > current.timestamp;
    }

    if candidate.primary_used_percent != current.primary_used_percent {
        return candidate.primary_used_percent > current.primary_used_percent;
    }

    if candidate.secondary_used_percent != current.secondary_used_percent {
        return candidate.secondary_used_percent > current.secondary_used_percent;
    }

    false
}

fn parse_timestamp(timestamp: &str) -> Result<DateTime<chrono::FixedOffset>, String> {
    DateTime::parse_from_rfc3339(timestamp)
        .map_err(|err| format!("invalid timestamp {timestamp:?}: {err}"))
}

fn epoch_to_local_datetime(epoch: i64) -> Option<DateTime<Local>> {
    Utc.timestamp_opt(epoch, 0)
        .single()
        .map(|dt| dt.with_timezone(&Local))
}
