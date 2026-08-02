# Variable scope: script, map, world, global — plus BCS's own extensions

**Tier:** A (engine limits and reset call sites traced directly to source; BCS extensions traced to `zt-bcc`'s own wiki, not inferred).
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD, a `3.3-alpha` development snapshot ahead of the 3.2.1 target — these are core variable-storage/reset mechanics, stable across that gap).
**Provenance:** `_intake/Scope - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Scope&oldid=40398`), verified against the Zandronum source's `src/p_acs.h` (`NUM_MAPVARS`/`NUM_WORLDVARS`/`NUM_GLOBALVARS`), `p_acs.cpp` (`P_ClearACSVars`, `ACS_WorldVars`/`ACS_GlobalVars` storage), `g_level.cpp`/`g_game.cpp` (hub/new-game clear call sites, including the Zandronum client-mode carve-out), and the zt-bcc wiki's `Declarations.md` (`static` locals, `let` block scoping, in-script `world`/`global` declarations) on 2026-07-29.

The ZDoom wiki's "Scope" page describes base ACS's four variable scopes. All four are real and
verified against this fork's engine limits below, but the page is silent on BCS-specific scoping
(`zt-bcc` block scoping via `let`/`strict namespace`, `static` locals, namespaces), and it doesn't
mention a real Zandronum multiplayer netcode carve-out for
when world/global vars actually get cleared.

## The four base-ACS scopes, verified against the Zandronum source's `src/p_acs.h`

| Scope | Declared | Visible to | Size limit (`p_acs.h:50,58-59`) | Reset when |
|---|---|---|---|---|
| Script | inside a script/function body | that script/function only | n/a (stack-local) | every call |
| Map | outside any script, or `static` inside one | any script/function in the same `BEHAVIOR` or an imported library | `NUM_MAPVARS = 128` | new map load (per-`BEHAVIOR` storage, not persistent) |
| World | `world int <index>:<name>;` | any map in the same hub | `NUM_WORLDVARS = 256` | entering a new hub |
| Global | `global int <index>:<name>;` | any map/library in the whole game | `NUM_GLOBALVARS = 64` | new game / full game exit |

The wiki's index ranges ("1 through 256" for world, "64" for global) and the map-variable cap of
128 match this fork's constants exactly — confirmed by reading `p_acs.h:50` (`NUM_MAPVARS 128`)
and `p_acs.h:58-59` (`NUM_WORLDVARS = 256, NUM_GLOBALVARS = 64`), not just the wiki's word for it.
World and global storage are separate arrays (`ACS_WorldVars`/`ACS_GlobalVars`,
`p_acs.cpp:343-348`), so — as the wiki notes — a world var and a global var can reuse the same
index number without colliding.

## Reset behavior, verified against the Zandronum source's `src/g_level.cpp` and `g_game.cpp`

Both scopes are cleared through one function, `P_ClearACSVars(bool alsoglobal)`
(`p_acs.cpp:1023`), which unconditionally zeroes world vars/arrays and additionally zeroes
global vars/arrays only when `alsoglobal` is true. The call sites confirm the wiki's claims
exactly:

- `g_level.cpp:1034`, inside the `FINISH_NextHub` branch of level completion: `P_ClearACSVars(false)`
  — **world vars reset on a hub transition, global vars are untouched.**
- `g_level.cpp:583` (`G_InitNew`, a fresh game start) and `g_game.cpp:3271`: `P_ClearACSVars(true)`
  — **both world and global vars reset on a new game.**

**Zandronum-only divergence the wiki doesn't cover:** `g_level.cpp:579-583` gates the new-game
clear behind `(NETWORK_InClientMode() == false) || (CLIENT_GetConnectionState() != CTS_ACTIVE)`,
with the inline comment `// [AK] Don't reset world or global ACS variables for clients when they
are changing levels, unless they haven't received the full snapshot.` In multiplayer, a
fully-connected client does **not** independently clear its own world/global ACS vars on a level
change — it relies on receiving the server's replicated values instead. Only the server (or a
client that hasn't yet gotten a full snapshot) actually runs the clear. This has no equivalent in
single-player ZDoom and isn't mentioned on the wiki page at all; it matters if you're ever
reasoning about client-side script state immediately after a map change in a networked game (see
[Client-side scripting](clientside-scripting.md) for the broader client/server variable-state
split).

## BCS extensions not on the ZDoom page at all

Any project compiled with `zt-bcc` gets a richer scoping model layered on top of these four
storage classes (confirmed in the zt-bcc wiki's `Declarations.md`):

- **`static` locals genuinely are map-scope storage**, not a separate mechanism — a `static`
  variable inside a script/function is allocated as an anonymous map variable (subject to the
  same 128-variable cap), but the compiler only lets *that* script/function's code refer to it by
  name; other scripts can't reach it even though it physically lives in map-variable storage. This
  matches the wiki's framing ("map scope... alternatively declared as static") but the wiki
  doesn't explain *why* — it's a compile-time name-visibility restriction on top of ordinary map
  storage, not a fifth scope.
- **`world`/`global` variables can be declared inside a script or function** in `bcc` too (same
  storage, index, and cross-map semantics as a top-level declaration) — the only difference is
  that the name isn't visible outside that script/function, same visibility trick as `static`.
- **Block scoping via `let`** — a `let`-qualified declaration (or any declaration inside a
  `strict namespace`, where `let` is implied) is scoped to its enclosing block and can shadow an
  outer variable of the same name; this is *tighter* than the wiki's "script scope" (which treats
  the whole script body as one flat scope) and doesn't exist in base ACS/ACC at all.
- **Namespaces** can nest enums, structs, type aliases, and `static` state; none of this maps onto
  the wiki's four-scope model, which predates `bcc`'s namespace support entirely.

None of this contradicts the wiki's four-scope model for plain `int`/`global`/`world`
declarations — it's additive tooling on top, worth knowing so a `static` or `let` variable isn't
mistaken for behaving like one of the wiki's four named scopes when its actual storage/visibility
rules differ in the ways above.
