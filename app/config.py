import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "beszel"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict[str, Any]:
    """Load config from file."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)  # type: ignore[no-any-return]


def save_config(config: dict[str, Any]) -> None:
    """Save config to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    CONFIG_FILE.chmod(0o600)  # Restrict permissions


def get_token() -> str | None:
    """Get stored auth token."""
    return load_config().get("token")


def set_token(token: str) -> None:
    """Store auth token."""
    config = load_config()
    config["token"] = token
    save_config(config)


def get_url() -> str | None:
    """Get stored URL."""
    return load_config().get("url")


def set_url(url: str) -> None:
    """Store URL."""
    config = load_config()
    config["url"] = url
    save_config(config)


def clear_config() -> None:
    """Clear stored config."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
