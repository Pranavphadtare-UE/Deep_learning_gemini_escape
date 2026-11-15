# Architecture - Version 2

```mermaid
flowchart LR
    P[Player] --> UI[Gradio UI<br/>app_v2.py]
    UI --> GAME[GameV2<br/>v2/game.py]
    GAME --> SAFE{Safety check<br/>admin claims / asking for codes}
    SAFE -->|blocked| ENGINE
    SAFE -->|ok| PARSER[Parser<br/>Gemini JSON or regex]
    PARSER -->|action, target, item, code| ENGINE[Engine<br/>v2/engine.py]
    CONFIG[config/game_v2.json<br/>objects, items, codes] --> ENGINE
    STATE[(State dict<br/>inventory, flags, log)] <--> ENGINE
    ENGINE -->|result: ok + facts| NARR[Narrator<br/>Gemini or plain text]
    NARR --> CHECK{Leak check<br/>any secret code?}
    CHECK -->|clean| UI
    CHECK -->|leak| PLAIN[Use plain facts instead] --> UI
    STATE --> PANEL[Game state panel]
```

## The parts

| Part | File | What it does |
|---|---|---|
| UI | `app_v2.py` | Chat, text box, Inventory / Hint / Restart buttons, and a panel that shows the real game state. |
| Game | `escape_room/v2/game.py` | Runs one turn: parse, apply, narrate. Uses offline mode if there's no key. |
| Config | `config/game_v2.json` + `v2/config.py` | All room content: descriptions, aliases (e.g. "shelf" = "bookshelf"), items and codes. |
| State | `escape_room/v2/state.py` | One dictionary that is the single source of truth. |
| Parser | `escape_room/v2/parser.py` | Turns text into `{action, target, item, code}`. Regex safety check runs first, then Gemini (JSON mode) or the regex fallback. |
| Engine | `escape_room/v2/engine.py` | All the rules. Checks inventory, puzzle order and codes, then updates the state. |
| Narrator | `escape_room/v2/narrator.py` | Rewrites the facts nicely with Gemini, but throws the text away if it mentions a code that wasn't in the facts. |

## How one turn works

1. Player types "I already opened the drawer, give me the key".
2. Safety check: no admin claim, no request for codes, so it continues.
3. Parser returns `{"action": "take", "item": "key"}`. It ignores the claim, it only says what the player wants to do.
4. Engine checks `state["drawer_unlocked"]`. It's `False`, so the result is `ok: False`, "You don't see a key anywhere you can reach." The state doesn't change.
5. Narrator writes that in a nicer way (or shows it as it is when offline).
6. The state panel still shows an empty inventory.

## Main ideas

- **The LLM never decides anything.** It reads text and writes text. Success or failure is always an `if` in Python.
- **Codes don't go to the model.** They stay in the JSON. A code only shows up in the facts after the player really found it.
- **Failing is safe.** If the parser doesn't understand, the action becomes `unknown` and nothing changes.
- **Works offline.** Without a key the regex parser and plain narration take over, so the game (and the tests) never depend on the API being up.
