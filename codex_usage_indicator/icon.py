import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw


logger = logging.getLogger(__name__)

ICON_DIR = Path("/tmp/codex-usage-indicator")
ICON_SIZE = 22

COLOR_GREEN = "#4CAF50"
COLOR_YELLOW = "#FFC107"
COLOR_RED = "#F44336"
COLOR_BG = "#333333"
COLOR_ERROR = "#888888"


def get_bar_color(utilization):
    if utilization < 60:
        return COLOR_GREEN
    if utilization < 85:
        return COLOR_YELLOW
    return COLOR_RED


def ensure_icon_dir():
    ICON_DIR.mkdir(parents=True, exist_ok=True)


def _draw_bar(draw, y_top, y_bottom, utilization):
    draw.rectangle([0, y_top, ICON_SIZE - 1, y_bottom], fill=COLOR_BG)
    if utilization > 0:
        bar_width = max(1, int((ICON_SIZE - 1) * utilization / 100))
        draw.rectangle([0, y_top, bar_width, y_bottom], fill=get_bar_color(utilization))


def generate_icon(primary_usage, secondary_usage):
    ensure_icon_dir()
    try:
        img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        _draw_bar(draw, 2, 9, primary_usage)
        _draw_bar(draw, 13, 20, secondary_usage)
        icon_path = ICON_DIR / f"icon_{int(time.time() * 1000)}.png"
        img.save(str(icon_path))
        return icon_path
    except Exception as exc:
        logger.error("Failed to generate usage icon: %s", exc)
        raise


def generate_error_icon():
    ensure_icon_dir()
    try:
        img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 2, ICON_SIZE - 1, 9], fill=COLOR_ERROR)
        draw.rectangle([0, 13, ICON_SIZE - 1, 20], fill=COLOR_ERROR)
        icon_path = ICON_DIR / f"icon_{int(time.time() * 1000)}.png"
        img.save(str(icon_path))
        return icon_path
    except Exception as exc:
        logger.error("Failed to generate error icon: %s", exc)
        raise


def cleanup_old_icons(current_path):
    for icon_path in ICON_DIR.glob("icon_*.png"):
        if icon_path != current_path:
            try:
                icon_path.unlink()
            except OSError:
                pass

