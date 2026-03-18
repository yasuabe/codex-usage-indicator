"""codex-usage-indicator main entry point.

Usage:
    python3 -m codex_usage_indicator.main [--mock]
"""

import argparse
import logging
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import AppIndicator3, GLib, Gtk

from . import config, icon, menu, rollout_reader


logger = logging.getLogger(__name__)

INDICATOR_ID = "codex-usage-indicator"


def main():
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Use mock usage data")
    args = parser.parse_args()

    cfg = config.load_config()
    use_mock = args.mock or cfg["mock"]

    icon.ensure_icon_dir()
    icon_path = icon.generate_icon(0, 0)

    indicator = AppIndicator3.Indicator.new(
        INDICATOR_ID,
        str(icon_path.stem),
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_icon_theme_path(str(icon.ICON_DIR))
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    def on_quit(_):
        Gtk.main_quit()

    menu_state = {}

    def poll():
        refs = menu_state["refs"]
        try:
            data = rollout_reader.fetch_usage_mock() if use_mock else rollout_reader.fetch_usage()

            primary_used = data.get("primary_used_percent", 0.0)
            secondary_used = data.get("secondary_used_percent", 0.0)

            new_icon_path = icon.generate_icon(primary_used, secondary_used)
            indicator.set_icon_theme_path("")
            indicator.set_icon_theme_path(str(icon.ICON_DIR))
            indicator.set_icon_full(
                str(new_icon_path.stem),
                f"5h {data.get('primary_left_percent', 0.0):.0f}% left / "
                f"weekly {data.get('secondary_left_percent', 0.0):.0f}% left",
            )
            icon.cleanup_old_icons(new_icon_path)

            menu.update_menu_data(refs, data)
            menu.hide_menu_error(refs)
        except rollout_reader.UsageDataUnavailableError as exc:
            logger.info("Usage data unavailable: %s", exc)
            menu.show_menu_error(refs, "usage 情報なし")
        except Exception as exc:
            logger.exception("Polling error")
            try:
                error_icon_path = icon.generate_error_icon()
                indicator.set_icon_theme_path("")
                indicator.set_icon_theme_path(str(icon.ICON_DIR))
                indicator.set_icon_full(str(error_icon_path.stem), "error")
                icon.cleanup_old_icons(error_icon_path)
            except Exception:
                pass
            menu.show_menu_error(refs, str(exc))

        return True

    def on_refresh(_):
        poll()

    menu_obj, menu_state["refs"] = menu.build_menu(on_refresh, on_quit)
    indicator.set_menu(menu_obj)

    logger.info(
        "Starting indicator (mock=%s, polling_interval=%s)",
        use_mock,
        cfg["polling_interval"],
    )

    poll()
    GLib.timeout_add_seconds(cfg["polling_interval"], poll)
    Gtk.main()


if __name__ == "__main__":
    main()
