use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use image::{ImageBuffer, Rgba};

const ICON_SIZE: u32 = 22;
const COLOR_GREEN: [u8; 4] = [0x4C, 0xAF, 0x50, 0xFF];
const COLOR_YELLOW: [u8; 4] = [0xFF, 0xC1, 0x07, 0xFF];
const COLOR_RED: [u8; 4] = [0xF4, 0x43, 0x36, 0xFF];
const COLOR_BG: [u8; 4] = [0x33, 0x33, 0x33, 0xFF];
const COLOR_ERROR: [u8; 4] = [0x88, 0x88, 0x88, 0xFF];
const COLOR_TRANSPARENT: [u8; 4] = [0, 0, 0, 0];

pub fn icon_dir() -> PathBuf {
    PathBuf::from("/tmp/codex-usage-indicator-rust")
}

pub fn ensure_icon_dir() -> Result<PathBuf, String> {
    let dir = icon_dir();
    fs::create_dir_all(&dir)
        .map_err(|err| format!("failed to create icon dir {}: {err}", dir.display()))?;
    Ok(dir)
}

pub fn generate_icon(primary_usage: f64, secondary_usage: f64) -> Result<PathBuf, String> {
    generate_bars_icon(primary_usage, secondary_usage, false)
}

pub fn generate_error_icon() -> Result<PathBuf, String> {
    generate_bars_icon(100.0, 100.0, true)
}

pub fn cleanup_old_icons(current_path: &Path) -> Result<(), String> {
    let dir = icon_dir();
    let entries = fs::read_dir(&dir)
        .map_err(|err| format!("failed to read icon dir {}: {err}", dir.display()))?;
    for entry in entries {
        let entry = entry.map_err(|err| format!("failed to read icon entry: {err}"))?;
        let path = entry.path();
        if path != current_path
            && path.file_name().and_then(|name| name.to_str()).unwrap_or("").starts_with("icon_")
            && path.extension().and_then(|ext| ext.to_str()) == Some("png")
        {
            let _ = fs::remove_file(path);
        }
    }
    Ok(())
}

fn generate_bars_icon(
    primary_usage: f64,
    secondary_usage: f64,
    error_mode: bool,
) -> Result<PathBuf, String> {
    let dir = ensure_icon_dir()?;
    let mut img = ImageBuffer::from_pixel(ICON_SIZE, ICON_SIZE, Rgba(COLOR_TRANSPARENT));

    if error_mode {
        draw_bar(&mut img, 2, 9, 100.0, COLOR_ERROR);
        draw_bar(&mut img, 13, 20, 100.0, COLOR_ERROR);
    } else {
        draw_bar(&mut img, 2, 9, primary_usage, color_for(primary_usage));
        draw_bar(&mut img, 13, 20, secondary_usage, color_for(secondary_usage));
    }

    let icon_path = dir.join(format!("icon_{}.png", unique_millis()?));
    img.save(&icon_path)
        .map_err(|err| format!("failed to save icon {}: {err}", icon_path.display()))?;
    Ok(icon_path)
}

fn draw_bar(
    img: &mut ImageBuffer<Rgba<u8>, Vec<u8>>,
    y_top: u32,
    y_bottom: u32,
    usage: f64,
    fill: [u8; 4],
) {
    fill_rect(img, 0, y_top, ICON_SIZE - 1, y_bottom, COLOR_BG);

    if usage <= 0.0 {
        return;
    }

    let clamped = usage.clamp(0.0, 100.0);
    let width = ((ICON_SIZE - 1) as f64 * clamped / 100.0).floor() as u32;
    let width = width.max(1);
    fill_rect(img, 0, y_top, width, y_bottom, fill);
}

fn fill_rect(
    img: &mut ImageBuffer<Rgba<u8>, Vec<u8>>,
    x0: u32,
    y0: u32,
    x1: u32,
    y1: u32,
    color: [u8; 4],
) {
    for y in y0..=y1 {
        for x in x0..=x1 {
            img.put_pixel(x, y, Rgba(color));
        }
    }
}

fn color_for(usage: f64) -> [u8; 4] {
    if usage < 60.0 {
        COLOR_GREEN
    } else if usage < 85.0 {
        COLOR_YELLOW
    } else {
        COLOR_RED
    }
}

fn unique_millis() -> Result<u128, String> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis())
        .map_err(|err| format!("failed to get current time: {err}"))
}
