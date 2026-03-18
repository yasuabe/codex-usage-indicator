use std::env;

use chrono::Local;

use codex_usage_indicator::usage;

fn main() {
    if let Err(err) = run() {
        eprintln!("error: {err}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let input_path = env::args()
        .nth(1)
        .map(std::path::PathBuf::from)
        .unwrap_or_else(usage::default_sessions_dir);

    let snapshot = usage::find_latest_snapshot(&input_path)?;

    println!("source: {}", snapshot.source_path.display());
    println!(
        "5h limit: {} (resets {})",
        usage::format_percent_left(snapshot.primary_used_percent),
        usage::format_reset(snapshot.primary_resets_at, false)
    );
    println!(
        "weekly limit: {} (resets {})",
        usage::format_percent_left(snapshot.secondary_used_percent),
        usage::format_reset(snapshot.secondary_resets_at, true)
    );
    if let Some(plan_type) = snapshot.plan_type.as_deref() {
        println!("plan: {plan_type}");
    }
    println!("timestamp: {}", snapshot.timestamp.with_timezone(&Local).to_rfc3339());

    Ok(())
}
