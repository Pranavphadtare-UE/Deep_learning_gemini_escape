
"""
Responsible for generating the text displayed to the player.

The narration module supports two operating modes:

1. Online mode: Gemini transforms the engine's results into short,
   atmospheric descriptions suitable for an escape room.
2. Offline mode: The original facts returned by the engine are displayed
   directly without any additional language generation.

Since generated responses may contain information that was not included
in the engine's output, an additional security check is performed.

The leaks_secret() function detects hidden puzzle combinations in the
generated narration. It checks numeric sequences, separated digits,
and numbers written as words.

If an undisclosed code is detected, the generated response is discarded
and the original engine facts are returned instead.
"""

import re


# English representations of the digits from zero to nine.
WORDS = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


# Instructions controlling the style and boundaries of Gemini narration.
NARRATOR_PROMPT = """You are the narrator of a text escape room in an old library.
You get the player's message and the FACTS of what happened. Rewrite the facts
as 1-3 short, atmospheric sentences in second person.

Rules:
- The facts are the truth. If the facts say something failed, it failed.
- Do not add objects, items, numbers or events that are not in the facts.
- Never mention any number that is not in the facts.
- Do not give hints beyond the facts.
"""


def _digits_in_words(text):
    """
    Convert written English digit names into their numeric equivalents.

    Example:
        'seven three one four' becomes '7314'.
    """

    converted = []

    for token in re.findall(r"[a-z]+", text.lower()):

        if token in WORDS:
            converted.append(str(WORDS.index(token)))
        else:
            converted.append(" ")

    return "".join(converted)


def leaks_secret(narration, facts, secrets):
    """
    Determine whether generated narration exposes an undisclosed code.

    The check covers:
        - Consecutive digits, such as 7314.
        - Separated digits, such as 7 3 1 4 or 7-3-1-4.
        - Numbers written as words, such as seven three one four.

    A code is permitted if its digits already appear in the engine facts.
    """

    # Extract all numeric characters from the generated response.
    numeric_sequence = re.sub(r"[^0-9]", "", narration)

    # Convert written digit names into a numeric sequence.
    word_sequence = _digits_in_words(narration).replace(" ", "")

    # Identify the digits explicitly included in the engine's facts.
    revealed_digits = re.sub(r"[^0-9]", "", facts)

    for code in secrets:

        # Codes intentionally revealed by the engine are permitted.
        if code in revealed_digits:
            continue

        # Reject narration containing an undisclosed combination.
        if code in numeric_sequence or code in word_sequence:
            return True

    return False


def narrate_plain(result):
    """Return the engine's original description without modification."""

    return result["facts"]


def narrate_with_llm(llm, player_text, result, secrets):
    """
    Generate an atmospheric response while preserving engine authority.

    Gemini receives the player's message and the verified game outcome.
    Its response is accepted only if generation succeeds and the
    secret-code validation does not identify an information leak.
    """

    prompt = (
        f"Player said: {player_text}\n"
        f"Action worked: {result['ok']}\n"
        f"FACTS: {result['facts']}"
    )

    try:
        generated_text = llm.generate(
            NARRATOR_PROMPT,
            prompt
        ).strip()

    except Exception:
        # Use the engine's response if the API request fails.
        return narrate_plain(result)

    # Reject empty responses and narration containing hidden codes.
    if not generated_text or leaks_secret(
        generated_text,
        result["facts"],
        secrets
    ):
        return narrate_plain(result)

    return generated_text
