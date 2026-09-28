# `chat_substitution` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3AMessages&oldid=48195) + verified against Zandronum source's `src/chat.cpp:1648-1721`, `src/chat.cpp:1540-1556` (send path, sender-side substitution), `src/chat.cpp:733-737` (macros) and `src/sectinfo.cpp:314-321` (`$location` lookup).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Substitution keywords — Zandronum-specific extension

When enabled, this cvar allows outgoing chat messages to use special keywords that are replaced with runtime values. The replacement runs on the sender's own client, using that client's local player, before the message is sent, so other players receive the already-substituted text. The wiki documents five keywords; **Zandronum adds a sixth, `$location`, absent from the wiki and from UZDoom:**

- `$health`: the sender's current health.
- `$weapon`: the sender's ready weapon. Zandronum prints the weapon's tag (its class name if it has no tag); UZDoom prints the class name. With no weapon, both print `no weapon`.
- `$armor`: the amount of the sender's `BasicArmor` (0 if none).
- `$ammocount`: the ready weapon's primary ammo amount, followed by `/` and the secondary ammo amount when the weapon also uses a secondary ammo type. With no weapon, or a weapon without a primary ammo type, Zandronum prints `no ammo`; UZDoom prints `0`.
- `$ammo`: the ready weapon's ammo type, as `primary/secondary` when it uses two. Zandronum prints each ammo's tag; UZDoom prints class names. With no primary ammo type, both print `no ammo`.
- **`$location`**, *Zandronum-only*: the name the current map's `SECTINFO` lump gives the sector the sender is standing in (see [`SECTINFO`](../../zandronum-lumps/concepts/sectinfo.md)). If that sector has no name, it prints `Unknown Location` in black (`\cm`). Color codes in the name are rendered.

A recognized keyword never becomes empty: a missing value prints the placeholder text above. Keyword matching differs by engine. Zandronum matches case-sensitively by prefix, with no word boundary: `$Health` is left as typed, and `$healthy` becomes the health value followed by `y`. UZDoom matches `$` plus the whole following run of letters, case-insensitively. An unrecognized word is left as typed, except that one of exactly 4, 5, 6 or 9 letters is silently dropped.

## Interaction with chat macros

The `chatmacro0`–`chatmacro9` cvars provide preset strings, sent by pressing Alt plus a digit while the chat prompt is open. If `chat_substitution` is enabled, substitution keywords in a macro's text are replaced the same way as keywords typed directly into chat.
