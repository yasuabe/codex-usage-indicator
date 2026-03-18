import configparser
import logging
import os


logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/codex-usage-indicator/config.ini")

DEFAULTS = {
    "polling_interval": 30,
    "mock": False,
}


def load_config(path=None):
    """Load config values, falling back to defaults on any issue."""
    config_path = path or DEFAULT_CONFIG_PATH
    values = dict(DEFAULTS)

    if not os.path.exists(config_path):
        logger.info("Config file not found, using defaults: %s", config_path)
        return values

    parser = configparser.ConfigParser()
    try:
        with open(config_path, encoding="utf-8") as fp:
            parser.read_file(fp)
    except (OSError, configparser.Error) as exc:
        logger.warning("Failed to read config file, using defaults: %s (%s)", config_path, exc)
        return values

    try:
        polling_interval = parser.getint(
            "general", "polling_interval", fallback=DEFAULTS["polling_interval"]
        )
    except (ValueError, configparser.Error) as exc:
        logger.warning("Invalid polling_interval, using default: %s", exc)
        polling_interval = DEFAULTS["polling_interval"]

    if not 10 <= polling_interval <= 300:
        logger.warning(
            "polling_interval out of range (10-300), using default: %s",
            polling_interval,
        )
        polling_interval = DEFAULTS["polling_interval"]

    try:
        mock = parser.getboolean("general", "mock", fallback=DEFAULTS["mock"])
    except (ValueError, configparser.Error) as exc:
        logger.warning("Invalid mock value, using default: %s", exc)
        mock = DEFAULTS["mock"]

    values["polling_interval"] = polling_interval
    values["mock"] = mock
    return values

