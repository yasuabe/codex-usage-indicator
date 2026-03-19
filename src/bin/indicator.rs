use std::cell::RefCell;
use std::rc::Rc;

use appindicator3::prelude::AppIndicatorExt;
use appindicator3::{Indicator, IndicatorCategory, IndicatorStatus};
use chrono::{DateTime, FixedOffset, Local};
use codex_usage_indicator::{icon, usage};
use gtk::prelude::*;

const APP_ID: &str = "codex-usage-indicator";

fn main() -> Result<(), glib::BoolError> {
    gtk::init()?;

    let indicator = Indicator::new(
        APP_ID,
        "dialog-information",
        IndicatorCategory::ApplicationStatus,
    );
    indicator.set_status(IndicatorStatus::Active);
    indicator.set_title(Some("Codex Usage Indicator"));
    indicator.set_icon_theme_path(icon::icon_dir().to_string_lossy().as_ref());

    let menu = gtk::Menu::new();

    let item_primary = gtk::MenuItem::with_label("5h:  --% (リセット: --:--)");
    item_primary.set_sensitive(false);
    menu.append(&item_primary);

    let item_secondary = gtk::MenuItem::with_label("7d:  --% (リセット: --/--)");
    item_secondary.set_sensitive(false);
    menu.append(&item_secondary);

    let item_plan = gtk::MenuItem::with_label("Plan: --");
    item_plan.set_sensitive(false);
    menu.append(&item_plan);

    menu.append(&gtk::SeparatorMenuItem::new());

    let item_updated = gtk::MenuItem::with_label("最終更新: --:--");
    item_updated.set_sensitive(false);
    menu.append(&item_updated);

    let item_error = gtk::MenuItem::with_label("usage 情報なし");
    item_error.set_sensitive(false);
    item_error.hide();
    menu.append(&item_error);

    menu.append(&gtk::SeparatorMenuItem::new());

    let item_refresh = gtk::MenuItem::with_label("今すぐ更新");
    menu.append(&item_refresh);

    let item_quit = gtk::MenuItem::with_label("終了");
    item_quit.connect_activate(|_| gtk::main_quit());
    menu.append(&item_quit);

    menu.show_all();
    item_error.hide();

    indicator.set_menu(Some(&menu));

    let state = Rc::new(RefCell::new(MenuState {
        item_primary,
        item_secondary,
        item_plan,
        item_updated,
        item_error,
    }));

    let poll_state = state.clone();
    let poll_indicator = indicator.clone();
    let poll = move || {
        refresh_indicator(&poll_indicator, &poll_state);
        glib::ControlFlow::Continue
    };

    let refresh_indicator_handle = indicator.clone();
    let refresh_state = state.clone();
    item_refresh.connect_activate(move |_| {
        refresh_indicator(&refresh_indicator_handle, &refresh_state);
    });

    refresh_indicator(&indicator, &state);
    glib::timeout_add_seconds_local(30, poll);

    gtk::main();
    Ok(())
}

struct MenuState {
    item_primary: gtk::MenuItem,
    item_secondary: gtk::MenuItem,
    item_plan: gtk::MenuItem,
    item_updated: gtk::MenuItem,
    item_error: gtk::MenuItem,
}

fn refresh_indicator(indicator: &Indicator, state: &Rc<RefCell<MenuState>>) {
    let polled_at = Local::now();
    match usage::find_latest_snapshot(&usage::default_sessions_dir()) {
        Ok(snapshot) => {
            indicator.set_label("", "");
            indicator.set_status(IndicatorStatus::Active);
            if let Ok(icon_path) = icon::generate_icon(
                snapshot.primary_used_percent,
                snapshot.secondary_used_percent,
            ) {
                indicator.set_icon_theme_path("");
                indicator.set_icon_theme_path(icon::icon_dir().to_string_lossy().as_ref());
                if let Some(stem) = icon_path.file_stem().and_then(|stem| stem.to_str()) {
                    indicator.set_icon_full(stem, "Codex usage");
                }
                let _ = icon::cleanup_old_icons(&icon_path);
            }

            let state = state.borrow_mut();
            state.item_primary.set_label(&format!(
                "5h:  {} (リセット: {})",
                format_percent_used(snapshot.primary_used_percent),
                usage::format_reset(snapshot.primary_resets_at, false)
            ));
            state.item_secondary.set_label(&format!(
                "7d:  {} (リセット: {})",
                format_percent_used(snapshot.secondary_used_percent),
                usage::format_reset(snapshot.secondary_resets_at, true)
            ));
            state.item_plan.set_label(&format!(
                "Plan: {}",
                snapshot.plan_type.unwrap_or_else(|| "--".into())
            ));
            state.item_updated.set_label(&format!(
                "最終更新: {} ({})",
                format_timestamp(polled_at, false),
                format_snapshot_timestamp(snapshot.timestamp)
            ));
            state.item_error.hide();
        }
        Err(err) => {
            indicator.set_label("", "");
            indicator.set_status(IndicatorStatus::Active);
            if let Ok(icon_path) = icon::generate_error_icon() {
                indicator.set_icon_theme_path("");
                indicator.set_icon_theme_path(icon::icon_dir().to_string_lossy().as_ref());
                if let Some(stem) = icon_path.file_stem().and_then(|stem| stem.to_str()) {
                    indicator.set_icon_full(stem, "Codex usage unavailable");
                }
                let _ = icon::cleanup_old_icons(&icon_path);
            }
            let state = state.borrow_mut();
            state
                .item_updated
                .set_label(&format!("最終更新: {}", format_timestamp(polled_at, false)));
            state.item_error.set_label(&err);
            state.item_error.show();
        }
    }
}

fn format_timestamp(timestamp: DateTime<Local>, with_seconds: bool) -> String {
    if with_seconds {
        timestamp.format("%H:%M:%S").to_string()
    } else {
        timestamp.format("%H:%M").to_string()
    }
}

fn format_snapshot_timestamp(timestamp: DateTime<FixedOffset>) -> String {
    timestamp
        .with_timezone(&Local)
        .format("%H:%M:%S")
        .to_string()
}

fn format_percent_used(used_percent: f64) -> String {
    format!("{used_percent:.0}%")
}
