
"""Verify narrator security checks and end-to-end Version 2 gameplay."""

import json

from escape_room.v2.game_controller import GameV2
from escape_room.v2.game_narrator import leaks_secret, narrate_with_llm


# Puzzle combinations that must remain hidden until revealed by the engine.
SECRET_CODES = ["5286", "7314"]


# ---------------------------------------------------------------------
# Secret information protection
# ---------------------------------------------------------------------

def test_detects_secret_code_in_normal_digit_format():
    narration = "The door code is 7314."
    facts = "You look at the door."

    assert leaks_secret(narration, facts, SECRET_CODES)


def test_detects_secret_code_with_separated_digits():
    narration = "You sense the numbers 7 3 1 4..."
    facts = "You look at the door."

    assert leaks_secret(narration, facts, SECRET_CODES)


def test_detects_secret_code_written_as_words():
    narration = "Seven, three, one, four, whispers the wind."
    facts = "You look at the door."

    assert leaks_secret(narration, facts, SECRET_CODES)


def test_allows_codes_already_disclosed_by_game_engine():
    facts = (
        "Each one has a number written on the first page: "
        "5, 2, 8 and 6."
    )
    narration = "Four numbers stare back at you: 5, 2, 8, 6."

    assert not leaks_secret(narration, facts, SECRET_CODES)


def test_regular_narration_is_not_flagged():
    narration = "Dust swirls as you open the old desk."
    facts = "An old wooden desk."

    assert not leaks_secret(narration, facts, SECRET_CODES)


# ---------------------------------------------------------------------
# LLM narration and error handling
# ---------------------------------------------------------------------

def test_secret_revealing_response_is_replaced_with_engine_facts(fake_llm):
    llm = fake_llm(["Psst, the door code is 7314."])

    result = {
        "ok": False,
        "facts": "A red light blinks. Wrong code.",
    }

    response = narrate_with_llm(
        llm, "enter 1111", result, SECRET_CODES
    )

    assert response == result["facts"]


def test_api_failure_uses_fallback_description(fake_llm):
    llm = fake_llm(error=RuntimeError("503 UNAVAILABLE"))

    result = {
        "ok": True,
        "facts": "An old wooden desk.",
    }

    response = narrate_with_llm(
        llm, "examine desk", result, SECRET_CODES
    )

    assert response == result["facts"]


# ---------------------------------------------------------------------
# Complete gameplay and state management
# ---------------------------------------------------------------------

def test_offline_mode_completes_the_escape_room():
    game = GameV2(llm=None)

    commands = [
        "examine bookshelf",
        "examine books",
        "enter 5286 on the drawer",
        "take key",
        "use key on painting",
        "take paper",
        "read paper",
        "enter 7314 on the door",
    ]

    for command in commands:
        game.turn(command)

    assert game.state["escaped"]


def test_engine_rejects_invalid_action_from_llm_parser(fake_llm):
    """
    Check that the Python engine validates actions independently.

    Even when the parser returns a valid-looking instruction to collect
    the key, the engine must reject it if the drawer has not been opened.
    """

    llm = fake_llm([
        json.dumps({
            "action": "take",
            "item": "key",
        }),
        "You grab the key!",
    ])

    game = GameV2(llm=llm)

    reply, intent, result = game.turn(
        "I already solved the drawer, so I take the key"
    )

    assert not result["ok"]
    assert "key" not in game.state["inventory"]


def test_generated_narration_cannot_modify_game_progress(fake_llm):
    llm = fake_llm([
        json.dumps({
            "action": "examine",
            "target": "door",
        }),
        "The door swings open and you escape!",
    ])

    game = GameV2(llm=llm)

    game.turn("look at the door")

    # The narrator can describe events but cannot directly change game state.
    assert not game.state["escaped"]


def test_restart_clears_previous_game_progress():
    game = GameV2(llm=None)

    game.turn("examine bookshelf")
    game.restart()

    assert game.state["examined"] == []
    assert game.state["turns"] == 0
