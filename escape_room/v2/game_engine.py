
"""
Core gameplay logic for Version 2 of the AI Escape Room.

This module is responsible for enforcing the rules and managing
all changes to the game state.

Every player action is processed through apply(). The engine validates
the requested action, checks the current state, performs permitted
updates, and produces a result containing the outcome and relevant facts.

The LLM does not control puzzle outcomes or modify game state.
Its responsibility is limited to presenting the results in natural language.

An unsuccessful action does not modify the game state, apart from
the counter used to track incorrect keypad attempts.
"""

from .game_config import clean, resolve_item, resolve_object


VALID_ACTIONS = {
    "look",
    "examine",
    "take",
    "use",
    "enter_code",
    "inventory",
    "hint",
    "unknown",
}


def _result(success, event, facts):
    """Package the outcome of an action into a consistent structure."""

    return {
        "ok": success,
        "event": event,
        "facts": facts
    }


def apply(state, config, intent):
    """
    Validate and execute a player action using the current game state.

    The action is checked against the supported operations before
    its corresponding handler is called. The resulting event is
    also recorded in the game log.
    """

    action = intent.get("action", "unknown")

    if action not in VALID_ACTIONS:
        action = "unknown"

    state["turns"] += 1

    # Prevent further gameplay actions after the player has escaped.
    if state["escaped"] and action not in ("inventory", "look"):

        outcome = _result(
            False,
            "already_escaped",
            "You have already escaped the library. Press Restart to play again."
        )

    else:

        action_handlers = {
            "look": _look,
            "examine": _examine,
            "take": _take,
            "use": _use,
            "enter_code": _enter_code,
            "inventory": _inventory,
            "hint": _hint,
            "unknown": _unknown,
        }

        handler = action_handlers[action]
        outcome = handler(state, config, intent)

    # Keep a record of the action and its corresponding result.
    state["log"].append(
        f"turn {state['turns']}: {action} -> {outcome['event']}"
    )

    return outcome


# --------------------------------------------------
# Action handlers
# --------------------------------------------------


def _look(state, config, intent):
    """Provide an overview of the room or the player's final location."""

    if state["escaped"]:
        return _result(
            True,
            "look",
            "You are standing outside the library, free."
        )

    return _result(
        True,
        "look",
        config["intro"]
    )


def _examine(state, config, intent):
    """Inspect a room object and return its available description."""

    search_term = intent.get("target") or intent.get("item") or ""

    if search_term.strip().lower() in (
        "room",
        "library",
        "around",
        "everything"
    ):
        return _look(state, config, intent)

    object_name = resolve_object(config, search_term)

    if object_name is None:
        return _result(
            False,
            "no_such_object",
            f"There is no {clean(search_term) or 'such thing'} in this room."
        )

    object_data = config["objects"][object_name]

    # Certain objects become available only after another object is examined.
    prerequisite = object_data.get("needs_examined")

    if prerequisite and prerequisite not in state["examined"]:
        return _result(
            False,
            "not_found_yet",
            f"You don't see any {object_name} yet. Maybe look around first."
        )

    # The paper must be collected before the player can inspect its contents.
    if object_name == "paper" and "paper" not in state["inventory"]:
        return _result(
            False,
            "not_found_yet",
            "You don't have any paper to read."
        )

    # Show the contents of the drawer according to its current state.
    if object_name == "drawer" and state["drawer_unlocked"]:

        description = object_data["open_description"]

        if "key" not in state["inventory"]:
            description += " A small brass key is lying inside."
        else:
            description += " It is empty now."

    # Reveal the hidden contents of the painting after opening its panel.
    elif object_name == "painting" and state["panel_open"]:

        description = object_data["open_description"]

        if "paper" not in state["inventory"]:
            description += " There is a folded piece of paper inside."

    else:
        description = object_data["description"]

    if object_name not in state["examined"]:
        state["examined"].append(object_name)

    return _result(
        True,
        f"examined_{object_name}",
        description
    )


def _take(state, config, intent):
    """Handle attempts to collect items found inside the library."""

    search_term = intent.get("item") or intent.get("target") or ""
    item_name = resolve_item(config, search_term)

    if item_name is None:

        # Distinguish between objects that cannot be carried and missing items.
        room_object = resolve_object(config, search_term)

        if room_object:
            return _result(
                False,
                "cannot_take",
                f"You can't carry the {room_object}."
            )

        return _result(
            False,
            "no_such_item",
            f"There is no {clean(search_term) or 'such thing'} here to take."
        )

    if item_name in state["inventory"]:
        return _result(
            False,
            "already_have",
            f"You already have the {item_name}."
        )

    # Check whether the requested item has been made accessible.
    if item_name == "key" and not state["drawer_unlocked"]:
        return _result(
            False,
            "not_reachable",
            "You don't see a key anywhere you can reach."
        )

    if item_name == "paper" and not state["panel_open"]:
        return _result(
            False,
            "not_reachable",
            "You don't see any paper you can reach."
        )

    state["inventory"].append(item_name)

    item_description = (
        config["items"][item_name]["description"]
        .lower()
        .rstrip(".")
    )

    return _result(
        True,
        f"took_{item_name}",
        f"You pick up {item_description}."
    )


def _use(state, config, intent):
    """Apply an inventory item to a selected room object."""

    raw_item = intent.get("item") or ""
    item_name = resolve_item(config, raw_item)

    target_name = resolve_object(
        config,
        intent.get("target") or ""
    )

    if item_name is None:
        return _result(
            False,
            "no_such_item",
            f"You don't have anything called '{clean(raw_item)}'."
        )

    if item_name not in state["inventory"]:
        return _result(
            False,
            "not_in_inventory",
            f"You don't have the {item_name}. You need to find it first."
        )

    if target_name is None:
        return _result(
            False,
            "no_such_object",
            "You're not sure what to use it on."
        )

    # The brass key is designed to unlock the concealed painting panel.
    if item_name == "key" and target_name == "painting":

        if state["panel_open"]:
            return _result(
                False,
                "already_open",
                "The painting is already open."
            )

        state["panel_open"] = True

        return _result(
            True,
            "panel_opened",
            "The key fits the tiny keyhole in the frame. "
            "With a click the painting swings open, "
            "showing a hidden panel with a folded piece of paper inside."
        )

    # The key does not operate the drawer or the main exit door.
    if item_name == "key" and target_name in ("drawer", "door"):
        return _result(
            False,
            "wrong_target",
            f"The key doesn't fit anything on the {target_name}."
        )

    return _result(
        False,
        "nothing_happens",
        f"Using the {item_name} on the {target_name} does nothing."
    )


def _enter_code(state, config, intent):
    """Validate a keypad combination and update the corresponding lock."""

    entered_code = "".join(
        digit
        for digit in str(intent.get("code") or "")
        if digit.isdigit()
    )

    keypad_target = (
        resolve_object(config, intent.get("target") or "") or "door"
    )

    if keypad_target not in config["codes"]:
        return _result(
            False,
            "no_keypad",
            f"There is nowhere to enter a code on the {keypad_target}."
        )

    if len(entered_code) != 4:
        return _result(
            False,
            "bad_format",
            "The lock needs exactly four digits."
        )

    # Process the drawer combination.
    if keypad_target == "drawer":

        if state["drawer_unlocked"]:
            return _result(
                False,
                "already_open",
                "The drawer is already open."
            )

        if entered_code == config["codes"]["drawer"]:

            state["drawer_unlocked"] = True

            return _result(
                True,
                "drawer_unlocked",
                "The lock clicks and the drawer slides open. "
                "Inside is a small brass key."
            )

    # Check the final combination required to escape.
    if keypad_target == "door":

        if entered_code == config["codes"]["door"]:

            state["door_unlocked"] = True
            state["escaped"] = True

            return _result(
                True,
                "escaped",
                "The keypad turns green and the heavy door swings open. "
                "You step outside. You escaped!"
            )

    # Incorrect combinations are recorded for game statistics.
    state["wrong_codes"] += 1

    return _result(
        False,
        "wrong_code",
        f"You type {entered_code} on the {keypad_target}. "
        "A red light blinks. Wrong code."
    )


def _inventory(state, config, intent):
    """Display the items currently collected by the player."""

    collected_items = state["inventory"]

    if not collected_items:
        return _result(
            True,
            "inventory",
            "You aren't carrying anything."
        )

    return _result(
        True,
        "inventory",
        "You are carrying: " + ", ".join(collected_items) + "."
    )


def _hint(state, config, intent):
    """
    Provide guidance based on the player's progress without exposing
    any of the actual puzzle combinations.
    """

    if state["escaped"]:
        hint_text = "You already escaped!"

    elif "bookshelf" not in state["examined"]:
        hint_text = (
            "The carving on the desk mentions books. "
            "Have you looked at the bookshelf?"
        )

    elif "books" not in state["examined"]:
        hint_text = (
            "Some books on the shelf look out of place. "
            "Take a closer look at them."
        )

    elif not state["drawer_unlocked"]:
        hint_text = (
            "Those four numbers from the books might open "
            "something with a four-digit lock nearby."
        )

    elif "key" not in state["inventory"]:
        hint_text = "Something is waiting for you in the open drawer."

    elif not state["panel_open"]:
        hint_text = (
            "Small keys fit small keyholes. "
            "Look closely at the painting."
        )

    elif "paper" not in state["inventory"]:
        hint_text = (
            "The hidden panel behind the painting is holding something."
        )

    elif "paper" not in state["examined"]:
        hint_text = "Read the paper you found."

    else:
        hint_text = "You have everything you need. Try the door."

    return _result(
        True,
        "hint",
        hint_text
    )


def _unknown(state, config, intent):
    """Respond to actions that cannot be handled by the game engine."""

    reason = intent.get("reason") or ""

    if reason == "authority":
        message = (
            "Nobody in this room has special powers, including you. "
            "The door only listens to the right code."
        )

    elif reason == "secret":
        message = (
            "The room keeps its secrets. "
            "You'll have to find the codes yourself."
        )

    else:
        message = (
            "That doesn't do anything here. Try examining things, "
            "taking items, using items or entering a code."
        )

    return _result(
        False,
        "unknown",
        message
    )
