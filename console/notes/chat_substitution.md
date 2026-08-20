# `chat_substitution` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3AMessages&oldid=48195) + verified against Zandronum source's `src/chat.cpp:1648-1712`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Substitution keywords — Zandronum-specific extension

When enabled, this cvar allows chat messages to use special keywords that are replaced with runtime values. The wiki documents five keywords; **Zandronum adds a sixth not present in the upstream wiki or ZDoom/GZDoom-family implementations:**

- `$health` — replaced by the sender's current health
- `$weapon` — replaced by the name of the sender's current weapon
- `$armor` — replaced by the sender's current armor count
- `$ammocount` — replaced by the sender's current ammo count for the equipped weapon
- `$ammo` — replaced by the name of the equipped ammo type
- **`$location`** — *Zandronum-specific*: replaced by a descriptive name of the sender's current map location (requires the map to define location names in its MAPINFO or BCS script)

When a chat message is sent with `chat_substitution` enabled, each keyword is replaced atomically; if the replacement would be empty (e.g. `$weapon` when wielding no weapon), the original keyword string is left in place.

## Interaction with chat macros

The `chatmacro0`–`chatmacro9` cvars provide preset strings that can be sent via Alt+number hotkeys. If `chat_substitution` is enabled, substitution keywords in a macro's text are replaced the same way as keywords typed directly into chat.
