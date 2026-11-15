
"""Test suite covering the core gameplay rules implemented in engine.py."""

from escape_room.v2.game_engine import apply


def perform_action(state, config, action, **kwargs):
    """Build an intent dictionary and pass it to the game engine."""

    intent = {
        "action": action,
        "target": None,
        "item": None,
        "code": None,
        "reason": None,
    }
    intent.update(kwargs)

    return apply(state, config, intent)


def progress_game(state, config, target_step):
    """
    Execute the valid puzzle sequence until the requested checkpoint.

    The actions are performed in their required order, stopping after
    the specified step has been completed.
    """

    walkthrough = [
        ("bookshelf", dict(action="examine", target="bookshelf")),
        ("books", dict(action="examine", target="books")),
        ("drawer", dict(action="enter_code", target="drawer", code="5286")),
        ("key", dict(action="take", item="key")),
        ("painting", dict(action="use", item="key", target="painting")),
        ("paper", dict(action="take", item="paper")),
        ("read", dict(action="examine", target="paper")),
    ]

    for checkpoint, action_data in walkthrough:
        perform_action(state, config, **action_data)

        if checkpoint == target_step:
            return


# ---------------------------------------------------------------------
# Successful gameplay scenarios
# ---------------------------------------------------------------------

def test_complete_walkthrough_leads_to_escape(state, config):
    progress_game(state, config, "read")

    result = perform_action(
        state, config, "enter_code",
        target="door", code="7314"
    )

    assert result["ok"]
    assert state["escaped"]
    assert state["door_unlocked"]


def test_books_provide_the_drawer_combination(state, config):
    perform_action(state, config, "examine", target="bookshelf")
    result = perform_action(state, config, "examine", target="books")

    assert "5, 2, 8 and 6" in result["facts"]


def test_object_aliases_are_recognized(state, config):
    shelf_result = perform_action(
        state, config, "examine", target="the shelf"
    )
    painting_result = perform_action(
        state, config, "examine", target="picture"
    )

    assert shelf_result["event"] == "examined_bookshelf"
    assert painting_result["event"] == "examined_painting"


def test_look_returns_the_room_description(state, config):
    result = perform_action(state, config, "look")

    assert result["facts"] == config["intro"]


# ---------------------------------------------------------------------
# Puzzle progression and access restrictions
# ---------------------------------------------------------------------

def test_books_cannot_be_examined_before_shelf(state, config):
    result = perform_action(state, config, "examine", target="books")

    assert not result["ok"]
    assert "5" not in result["facts"]


def test_hidden_paper_cannot_be_read_before_collection(state, config):
    result = perform_action(state, config, "examine", target="paper")

    assert not result["ok"]
    assert "7314" not in result["facts"]


def test_key_cannot_be_collected_before_drawer_is_open(state, config):
    result = perform_action(state, config, "take", item="key")

    assert not result["ok"]
    assert state["inventory"] == []


def test_paper_requires_the_hidden_panel_to_be_open(state, config):
    progress_game(state, config, "key")

    result = perform_action(state, config, "take", item="paper")

    assert not result["ok"]
    assert "paper" not in state["inventory"]


# ---------------------------------------------------------------------
# Inventory validation
# ---------------------------------------------------------------------

def test_uncollected_item_cannot_be_used(state, config):
    result = perform_action(
        state, config, "use", item="key", target="painting"
    )

    assert result["event"] == "not_in_inventory"
    assert not state["panel_open"]


def test_duplicate_item_collection_is_prevented(state, config):
    progress_game(state, config, "key")

    result = perform_action(state, config, "take", item="key")

    assert result["event"] == "already_have"
    assert state["inventory"].count("key") == 1


def test_furniture_cannot_be_added_to_inventory(state, config):
    result = perform_action(state, config, "take", item="desk")

    assert result["event"] == "cannot_take"


def test_using_key_on_incorrect_object_has_no_effect(state, config):
    progress_game(state, config, "key")

    result = perform_action(
        state, config, "use", item="key", target="door"
    )

    assert not result["ok"]
    assert not state["door_unlocked"]


# ---------------------------------------------------------------------
# Combination and keypad validation
# ---------------------------------------------------------------------

def test_invalid_drawer_combination(state, config):
    result = perform_action(
        state, config, "enter_code",
        target="drawer", code="1111"
    )

    assert result["event"] == "wrong_code"
    assert not state["drawer_unlocked"]
    assert state["wrong_codes"] == 1


def test_invalid_door_combination(state, config):
    result = perform_action(
        state, config, "enter_code",
        target="door", code="0000"
    )

    assert result["event"] == "wrong_code"
    assert not state["escaped"]


def test_drawer_combination_cannot_unlock_the_exit(state, config):
    result = perform_action(
        state, config, "enter_code",
        target="door", code="5286"
    )

    assert not result["ok"]
    assert not state["escaped"]


def test_combination_requires_four_digits(state, config):
    result = perform_action(
        state, config, "enter_code",
        target="drawer", code="52"
    )

    assert result["event"] == "bad_format"


def test_painting_does_not_accept_keypad_codes(state, config):
    result = perform_action(
        state, config, "enter_code",
        target="painting", code="5286"
    )

    assert result["event"] == "no_keypad"


def test_combination_with_spaces_is_accepted(state, config):
    result = perform_action(
        state, config, "enter_code",
        target="drawer", code="5 2 8 6"
    )

    assert result["ok"]


# ---------------------------------------------------------------------
# Validation of unknown objects, items, and commands
# ---------------------------------------------------------------------

def test_examination_of_nonexistent_object(state, config):
    result = perform_action(
        state, config, "examine", target="trapdoor"
    )

    assert result["event"] == "no_such_object"
    assert "trapdoor" not in state["examined"]


def test_collection_of_nonexistent_item(state, config):
    result = perform_action(
        state, config, "take", item="crowbar"
    )

    assert result["event"] == "no_such_item"
    assert state["inventory"] == []


def test_unrecognized_action_is_handled_safely(state, config):
    result = perform_action(state, config, "teleport")

    assert result["event"] == "unknown"


# ---------------------------------------------------------------------
# Game state consistency and turn tracking
# ---------------------------------------------------------------------

def test_unsuccessful_actions_do_not_modify_game_flags(state, config):
    initial_state = {
        key: value
        for key, value in state.items()
        if key not in ("turns", "log", "wrong_codes")
    }

    perform_action(
        state, config, "use", item="key", target="painting"
    )
    perform_action(state, config, "take", item="paper")
    perform_action(
        state, config, "enter_code",
        target="door", code="9999"
    )
    perform_action(
        state, config, "unknown", reason="authority"
    )

    final_state = {
        key: value
        for key, value in state.items()
        if key not in ("turns", "log", "wrong_codes")
    }

    assert initial_state == final_state


def test_unlocked_drawer_remains_open(state, config):
    progress_game(state, config, "drawer")

    perform_action(
        state, config, "enter_code",
        target="drawer", code="0000"
    )

    assert state["drawer_unlocked"]


def test_game_rejects_actions_after_escape(state, config):
    progress_game(state, config, "read")

    perform_action(
        state, config, "enter_code",
        target="door", code="7314"
    )

    result = perform_action(
        state, config, "enter_code",
        target="drawer", code="1111"
    )

    assert result["event"] == "already_escaped"
    assert state["wrong_codes"] == 0


def test_every_action_is_recorded_in_the_log(state, config):
    perform_action(state, config, "look")
    perform_action(state, config, "examine", target="desk")

    assert len(state["log"]) == 2
    assert state["turns"] == 2


# ---------------------------------------------------------------------
# Hint system security
# ---------------------------------------------------------------------

def test_hints_do_not_disclose_puzzle_combinations(state, config):
    checkpoints = [
        "bookshelf",
        "books",
        "drawer",
        "key",
        "painting",
        "paper",
        "read",
    ]

    for checkpoint in checkpoints:
        hint_text = perform_action(
            state, config, "hint"
        )["facts"]

        assert "5286" not in hint_text
        assert "7314" not in hint_text

        progress_game(state, config, checkpoint)
