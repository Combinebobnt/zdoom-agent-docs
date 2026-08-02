# `int GetPlayerInput(int player, int input)`

Returns raw or post-processed input state for a player at the current tic. Compiler builtin
(`PCD_GETPLAYERINPUT`, `zt-bcc/src/builtin.c:164`: `{ "getplayerinput", "i;ii" }`), implementation
in `p_acs.cpp:5174-5234` (helper `DLevelScript::GetPlayerInput`, called from the
`PCD_GETPLAYERINPUT` case at `p_acs.cpp:12375-12378`).

**Bucket:** compiler builtin.

- **`player` semantics diverge from the wiki when `player < 0` and there's no activator.** The
  wiki says "Use -1 to specify the script activator instead," implying `-1` always means "the
  activator." The actual fork logic (`p_acs.cpp:5178-5198`) for any negative `player`:
  - If the script has a real activator (`activator != NULL`), it uses `activator->player` — this
    part matches the wiki.
  - If there's **no** activator (e.g. a world-activated script) and the engine is *not* in
    Zandronum's client-prediction mode (`NETWORK_InClientMode()` false — i.e. normal
    single-player/listen-server execution), the function returns `0` rather than falling back to
    any player. **This has no equivalent in the ZDoom wiki page at all** — it's a Zandronum
    multiplayer-specific branch, since ZDoom has no separate client/server input replication to
    disambiguate.
  - If there's no activator **and** `NETWORK_InClientMode()` is true (this fork's clientside
    prediction path), it substitutes `consoleplayer`'s input instead of returning 0 — and for a
    spectating console player, it additionally forces `inputnum` up into the `MODINPUT_*` range
    (`inputnum += MODINPUT_OLDBUTTONS`) even if an `INPUT_*` constant was requested, because raw
    (pre-processing) input isn't tracked for spectators. A world-activated `CLIENTSIDE` script
    calling `GetPlayerInput(-1, INPUT_BUTTONS)` for a spectator therefore silently gets
    `MODINPUT_BUTTONS` data instead.
  - Net effect: `GetPlayerInput(-1, ...)` only reliably means "the activating player" when the
    script actually has an activator. For world-activated scripts, whether you get `0` or
    `consoleplayer`'s (possibly modinput-substituted) input depends on client-vs-server execution
    context — verify which context a given script type runs in (see `../concepts/` for script-type
    execution model, if present) before relying on `-1` there.
  - For `player >= 0`: matches the wiki exactly — invalid index or a slot with no player in game
    (`playernum >= MAXPLAYERS || !playeringame[playernum]`) returns `0`.
- **All `INPUT_*`/`MODINPUT_*` constants the wiki lists are implemented and mapped 1:1** to the
  underlying `ucmd`/`original_cmd` fields (`p_acs.cpp:5214-5230`): `OLDBUTTONS`, `BUTTONS`,
  `PITCH`, `YAW`, `ROLL`, `FORWARDMOVE`, `SIDEMOVE`, `UPMOVE`, in both the raw (`INPUT_*`) and
  post-processed (`MODINPUT_*`) varieties. `INPUT_ROLL`/`MODINPUT_ROLL` are present and wired to
  real fields despite the wiki noting the underlying `roll` field is "not currently used" by
  gameplay — the function will still read and return it (currently always `0` in practice, not
  because the case is missing). An unrecognized `input` value returns `0` (`default:` case,
  `p_acs.cpp:5232`), not an error.
- **`BT_RUN` does not exist in this fork at all — genuine ZDoom-vs-Zandronum divergence, not just
  an implementation quirk.** The wiki documents `BT_RUN` as a `*BUTTONS` bit distinct from
  `BT_SPEED`, reflecting actual running/walking state (relevant with autorun). Grepped for
  `BT_RUN` across both the zt-bcc source (no such constant in `zcommon.bcs`'s `BT_*` enum,
  `zt-bcc/lib/zcommon.bcs:165-189`) and all of the Zandronum source (no match anywhere, not even
  as an internal-only bit) — it isn't just unexposed to ACS, the fork's input model has no
  equivalent bit at all. Every other `BT_*` name the wiki lists (`BT_FORWARD` through `BT_USER4`,
  including `BT_SHOWSCORES`) is present in `zcommon.bcs` with matching bit values. Don't reference
  `BT_RUN` in BCS code targeting this fork; if you need to distinguish "actually running" from "speed key held,"
  you'll need to derive it yourself (e.g. from player speed/velocity) rather than reading a button
  bit.
- **Reading buttons vs. axes, and the `==`/`!=` warning, are general ACS advice, not
  fork-specific** — not re-verified here since they're just "how bitmasks work," per the
  authoring rule's bar for what needs source-checking.

**Example:**

```
int buttons = GetPlayerInput(-1, INPUT_BUTTONS);
if (buttons & BT_FORWARD)
{
    Log(s:"pressing forward");
}
```

**Returns:** `int` — a bitmask of `BT_*` flags for `*BUTTONS` inputs, or a scalar axis value for
everything else; `0` for an invalid/out-of-game player, an unrecognized `input` constant, or (see
above) certain no-activator world-script cases.

**Provenance:** wiki page `GetPlayerInput - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=54772`) + source-verified (`p_acs.cpp:5174-5234,12375-12378`, `zt-bcc/src/builtin.c:164`,
`zt-bcc/lib/zcommon.bcs:143-189`). The `INPUT_*`/`MODINPUT_*` constant mapping and general button
semantics hold as described; the `player < 0`-with-no-activator branching and the complete absence
of `BT_RUN` in this fork are this doc's source-verified additions/corrections, not wiki-sourced.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
