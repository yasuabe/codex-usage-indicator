import logging
from datetime import datetime

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


logger = logging.getLogger(__name__)


def build_menu(on_refresh, on_quit):
    menu = Gtk.Menu()

    item_primary = Gtk.MenuItem(label="5h limit: --")
    item_primary.set_sensitive(False)
    menu.append(item_primary)

    item_secondary = Gtk.MenuItem(label="Weekly limit: --")
    item_secondary.set_sensitive(False)
    menu.append(item_secondary)

    item_plan = Gtk.MenuItem(label="Plan: --")
    item_plan.set_sensitive(False)
    menu.append(item_plan)

    menu.append(Gtk.SeparatorMenuItem())

    item_last_update = Gtk.MenuItem(label="更新: --:--")
    item_last_update.set_sensitive(False)
    menu.append(item_last_update)

    item_error = Gtk.MenuItem(label="usage 情報なし")
    item_error.set_sensitive(False)
    item_error.hide()
    menu.append(item_error)

    menu.append(Gtk.SeparatorMenuItem())

    item_refresh = Gtk.MenuItem(label="今すぐ更新")
    item_refresh.connect("activate", on_refresh)
    menu.append(item_refresh)

    item_quit = Gtk.MenuItem(label="終了")
    item_quit.connect("activate", on_quit)
    menu.append(item_quit)

    menu.show_all()
    item_error.hide()

    refs = {
        "item_primary": item_primary,
        "item_secondary": item_secondary,
        "item_plan": item_plan,
        "item_last_update": item_last_update,
        "item_error": item_error,
    }
    return menu, refs


def _format_reset_time(reset_at, with_date):
    if not reset_at:
        return "--"

    try:
        dt = datetime.fromisoformat(reset_at).astimezone()
    except ValueError:
        logger.warning("Invalid reset time format: %s", reset_at)
        return "--"

    if with_date:
        return dt.strftime("%m/%d %H:%M %Z")
    return dt.strftime("%H:%M %Z")


def update_menu_data(refs, data):
    primary_left = data.get("primary_left_percent", 0.0)
    secondary_left = data.get("secondary_left_percent", 0.0)
    primary_reset = _format_reset_time(data.get("primary_resets_at"), with_date=False)
    secondary_reset = _format_reset_time(data.get("secondary_resets_at"), with_date=True)
    plan_type = (data.get("plan_type") or "--").capitalize()

    refs["item_primary"].set_label(
        f"5h limit: {int(primary_left)}% left (resets {primary_reset})"
    )
    refs["item_secondary"].set_label(
        f"Weekly limit: {int(secondary_left)}% left (resets {secondary_reset})"
    )
    refs["item_plan"].set_label(f"Plan: {plan_type}")
    refs["item_last_update"].set_label(f"更新: {datetime.now().strftime('%H:%M')}")
    hide_menu_error(refs)


def show_menu_error(refs, message):
    refs["item_error"].set_label(message)
    refs["item_error"].show()


def hide_menu_error(refs):
    refs["item_error"].hide()

