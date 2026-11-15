
"""
Handles loading the room configuration and identifying objects based on
the words entered by the player.

All room-specific information is maintained in a JSON configuration file.
This keeps the game engine independent of the actual room contents.

As a result, additional rooms can be introduced by creating new
configuration files without modifying the underlying engine.
"""

import json
from pathlib import Path


CONFIG_FILE = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "game_v2.json"
)


def load_config(path=CONFIG_FILE):
    """Read the game settings from the specified JSON file."""
    with open(path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def clean(text):
    """Normalize player input by removing common introductory words."""

    normalized = (text or "").lower().strip()

    prefixes = ("the ", "a ", "an ", "my ", "that ", "this ")

    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]

    return normalized.strip(" .!?")


def resolve_object(config, word):
    """Identify a room object using its name or any registered alias."""

    search_term = clean(word)

    if not search_term:
        return None

    for object_name, object_data in config["objects"].items():
        if (
            search_term == object_name
            or search_term in object_data["aliases"]
        ):
            return object_name

    return None


def resolve_item(config, word):
    """Find a collectible item by matching its name or alternative names."""

    search_term = clean(word)

    if not search_term:
        return None

    for item_name, item_data in config["items"].items():
        if (
            search_term == item_name
            or search_term in item_data["aliases"]
        ):
            return item_name

    return None


def secret_codes(config):
    """Retrieve the configured puzzle codes for internal game validation."""

    return list(config["codes"].values())
