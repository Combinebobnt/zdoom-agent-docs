# The state-machine model

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki "Actor states" (retrieved 2026-07-31, oldid=55033) + ZDoom Wiki
"DECORATE format specifications" (retrieved 2026-07-31, oldid=52163), both cross-checked against
the Zandronum source's state-table parser and runtime (`src/thingdef/thingdef_states.cpp`,
`src/p_states.cpp`, `src/info.h`, `src/info.cpp`, `src/p_mobj.cpp`, `src/p_pspr.cpp`,
`src/thingdef/thingdef_parse.cpp`, `src/namedef.h`, `src/sc_man_scanner.re`). The wiki pages
describe the modern GZDoom-family engine, which layers ZScript-derived features onto DECORATE
states that **do not exist in Zandronum's older DECORATE-only codebase** — every claim below has
been checked against this fork specifically, and every place the wiki's description doesn't hold
here is called out explicitly rather than silently inherited. Per `../../shared/AUTHORING.md`'s
engine-scope caveats, the local Zandronum checkout used to verify this is a `master` HEAD
reporting `3.3-alpha` in `version.h`, not a pristine 3.2.1 checkout — re-check against an actual
3.2.1 client if a claim here ever turns out not to hold (this page cites `p_mobj.cpp`/
`p_states.cpp`/`p_pspr.cpp`/`thingdef_states.cpp`, none of which the applied ZandronumMCP patch
touches, so that patch's line-shift risk doesn't apply here).

Every DECORATE actor's animation/behavior is one state machine: a flat array of frames
(`FState` records) with labels pointing into it, and a "next state" pointer baked into each frame
at compile time. This page covers the block's grammar and the compile-time/runtime rules that
decide what "next" means — not any individual action function's own behavior (see `../actions/`
and `../families/` for those), not the actor-definition syntax the `States{}` block sits inside
(see `actor-definition-syntax.md`), and not how a sprite *lump name* itself encodes rotation/
mirroring (see `../../sprites/concepts/sprite-naming.md`) — this page only covers how a DECORATE
frame *letter* maps to a frame index at the `FState` level.

## Block and label grammar

A `States { ... }` block is a property-like keyword recognized on an actor definition — the `{`
must follow immediately, and only one such block is allowed per actor (a second one is a hard
compile error). Inside it, a **label** is a bare identifier followed by `:`. Labels can stack
(multiple `Label:` lines in a row before any actual state line, all pointing at the same next
state) and can nest via dotted sub-labels, e.g. `Death.Extreme:` under a `Death:` block. The
`Class::Label` qualified form is **only valid as a `Goto` target**, never as a label declaration
itself — see "Label scoping and inheritance" below.

A **state** (one sprite, one frame, one duration, at most one action call) is not the same thing
as a **state sequence** (everything from one label down to the next `Goto`/`Stop`/`Wait`/`Fail`/
`Loop`). A dynamic jump — an `A_Jump`-family action function taking the jump, or simply falling
through from one physical line to the next with no flow-control keyword — does not end a sequence
the way those four keywords do.

## State line grammar

A state line is, in order: a 4-character sprite name, one or more frame characters in a single
token, a duration, zero or more flag keywords, and an optional trailing action-function call.

```
TROO AB 4 BRIGHT A_FaceTarget
```

- **Sprite name** must be exactly 4 characters — anything else is a compile error. Three sprite
  names are reserved at fixed indices instead of naming a real graphic — see "Special sprite-name
  tokens" below.
- **Frame character(s)**: each character in the token becomes its own expanded state (see
  "Multiple frames on one line" below). A letter maps to a frame index case-insensitively
  (`'A'`→0, `'B'`→1, ... `'Z'`→25), followed by `'['`→26, `'\'`→27, `']'`→28; anything that
  resolves outside 0–28 is a compile error. `#` as a **frame character** (not to be confused with
  the unrelated `"####"` **sprite name**, see below) sets the per-state `SameFrame` flag — keep
  whatever frame was already showing, applied only to the frame, independent of the sprite name in
  the same line. Per the wiki, a frame sequence containing `[`, `\`, or `]` must be wrapped in
  quotes; that specific lexer requirement wasn't independently traced in this checkout (flagged
  below), but the 0–28 index range and the letter mapping are.
- **Duration**: a plain integer, or `RANDOM(min, max)` — see "Duration semantics" below.
- **Flags** (any combination, order-independent, each just `continue`s the parser's token loop):
  `BRIGHT`, `FAST`, `SLOW`, `NODELAY`, `CANRAISE`, `OFFSET(x, y)` (weapon sprite offset — per the
  wiki, `Offset(0, 0)` specifically means "keep the previous offset" rather than "reset to
  `(0,0)`", a deliberate Hexen-compatibility carve-out, not independently re-verified against
  source here), and `LIGHT("name"[, "name2", ...])` (dynamic-light attachment — **gated behind a
  `DYNLIGHT` build flag in this source tree; whether release Zandronum binaries actually build
  with it defined is unverified in this checkout**, flagged as an open question below). `NODELAY`
  is only meaningful immediately after a `Spawn:` label; using it elsewhere produces a non-fatal
  warning, not a compile error. In a multi-frame expansion (`TROO AB 4 NODELAY`), the flag is
  cleared on every expanded state after the first — it is never carried past the first frame of a
  multi-frame line. (The wiki additionally frames `NODELAY`'s purpose as "an actor's `Spawn:`
  sequence doesn't run its first frame's action on the tic it spawns unless told to" — consistent
  with, and a useful gloss on, the parser-level restriction above.)
- **Action function call**: optional and always trailing. If a token isn't a flag and isn't a
  resolvable action-function name, the parser just ungets it and the state gets no action —
  there's no explicit "no action" keyword needed, an omitted call is simply legal.

**Not available in Zandronum's DECORATE** (ZScript/GZDoom-only additions the wiki page documents
alongside DECORATE, since ZDoom-family wikis describe the union of both): anonymous
`{ statements; }` action blocks in place of a bare action-function call, `return`/
`FindState()`/`ResolveState()` used as a state-jump target, and reading/assigning `self.tics` or
`curstate.tics`. None of these appear anywhere in `thingdef_states.cpp`'s state-line grammar —
that file resolves the trailing token exclusively as either a line-special name or a
`PSymbolActionFunction` lookup, with no `{`-block alternative. See `../../shared/AUTHORING.md`'s
"Engine scope" — this generalizes the same "ZScript doesn't exist in Zandronum at all" rule
`zscript/concepts/zscript-engine-availability.md` documents, applied specifically to states.

## Special sprite-name tokens

Three sprite names are pre-registered by the engine at fixed indices (`FActorInfo::StaticInit`,
`src/info.cpp:112-132`) rather than naming an actual graphic lump, and are checked by index
(not by re-comparing the string) wherever they matter at runtime (`AActor::SetState`,
`src/p_mobj.cpp:530-556`; `src/info.h:56-61`):

- **`TNT1`** — sprite index 0, "the empty sprite." There is no special-cased "don't render"
  branch for index 0 anywhere in the runtime code read for this page; `TNT1` makes an actor
  invisible simply because no `TNT1A0`-style graphic lump is ever shipped for it, so the renderer
  has nothing to draw. `TNT1 A 0` (paired with a 0-tic duration to also cost no time) is the
  standard idiom for an invisible marker/spawner frame.
- **`----`** — sprite index 1, `SPR_FIXED`. When a state's sprite is `SPR_FIXED`, **neither the
  sprite nor the frame changes** on entering that state — the entire "okay to change sprite/frame"
  block in `AActor::SetState` is skipped outright (`p_mobj.cpp:544`: `if (newsprite != SPR_FIXED)
  { ...frame...; ...sprite... }`).
- **`####`** — sprite index 2, `SPR_NOCHANGE`. This is **not** the same as `----`: the frame can
  still change (governed independently by the state's own `SameFrame`/frame-character fields,
  which are checked regardless of sprite value), but the **sprite** specifically is left as
  whatever it already was (`p_mobj.cpp:550`: `if (newsprite != SPR_NOCHANGE) { ...sprite... }`,
  nested *inside* the block above, after the frame has already potentially been updated).

These three are ordinary sprite-name tokens as far as the parser is concerned — `state.sprite =
GetSpriteIndex(statestring)` (`thingdef_states.cpp:235`) resolves them through the same generic
sprite-name lookup as any real sprite, with no string-literal special-casing in the parser itself.
Their behavior comes entirely from being pre-registered at indices 0/1/2 and checked by index at
the two call sites above, plus the equivalent guard in `src/p_pspr.cpp:225-231` for weapon/overlay
`PSprite` layers.

**Do not confuse these three sprite-name tokens with the unrelated `#` frame character** described
above — `TROO # 4` (a `#` **frame**, on a real sprite name) means "keep the current frame, but
`TROO` is still a normal sprite that can still change"; `SPRT #### 4` (`####` as the **sprite
name**) means "keep the current sprite, but the frame given (`#### `is 4 characters here as a
sprite name, not frame characters) can still update." They read similarly but occupy different
grammar positions and control different things.

## Duration semantics

Tic counts are clamped to `[-1, SHRT_MAX]` at parse time — **`-1` is the practical floor**, not
just an unusual value:

- **`-1`**: the runtime tic countdown is skipped entirely (guarded by `if (tics != -1)`) — the
  actor never automatically advances out of this state on its own (matches the wiki's own
  "infinite duration" description). This is different from `Wait`/`Fail`, which self-loops every
  tic instead of freezing the countdown — see "Control-flow keywords".
- **`0`**: the engine chains straight through to the next state (running its action, checking its
  duration, etc.) within the same tic, with no frame actually rendered at 0 duration. This is the
  documented way to cascade several states instantly in one tic.
- **positive `n`**: counts down normally and advances once it reaches `<= 0` (deliberately `<=`
  rather than `==`, specifically so a `Spawn:` state given `0` tics still behaves as the case
  above rather than skipping a frame of countdown).
- **`RANDOM(min, max)`**: stores `min` and a range; at runtime the actual duration is `min` plus a
  uniformly-random pick across the range (inclusive of both endpoints), re-rolled every time the
  state is (re-)entered. `min`/`max` are independently clamped the same way as a plain integer and
  swapped if given in the wrong order.

**The duration field itself only accepts a literal integer or `RANDOM(<int>, <int>)` in this
fork** — `thingdef_states.cpp`'s duration parsing calls `sc.MustGetNumber()` directly, a raw
numeric-token read, not the general expression parser. The current ZDoom Wiki page shows duration
examples like `POSS A 100/5;` (arithmetic) and `POSS A TICRATE;` (a named constant) that **do not
compile in Zandronum** — those require the newer, expression-capable duration field added to
later GZDoom-family DECORATE, which this fork's parser doesn't have. **What Zandronum does support
instead**, confirmed at `thingdef_states.cpp:340-430`, is a full expression (including arithmetic
and named constants) as an **action function's argument** — e.g. `A_SetTics((waterlevel + 10) -
(accuracy / 10))` (a real function, `thingdef_codeptr.cpp:6007-6011`) compiles and works in
Zandronum, because action-function arguments go through the generic `ParseParameter`/
`FxExpression` path regardless of engine version; only the bare duration slot is restricted to a
literal.

## Control-flow keywords

Four keywords can appear where a state line normally would, each acting on the *preceding* state
(or, for `Goto`/`Stop`, on a dangling label with no state defined yet):

- **`Goto <label>[+<offset>]`** — retargets to a label instead of falling through to the next
  physical line. The label may be dotted (`Death.Extreme`) and/or class-qualified
  (`SomeAncestor::Label`, or `Super::Label` meaning "this class's immediate parent"). A qualifying
  class name **must be an actual ancestor of the class being defined** — the engine rejects both a
  nonexistent class and a class that isn't an ancestor with a hard compile error. `+offset` adds a
  fixed number of states past the resolved target; negative offsets are rejected, and combining
  `+offset` with a multi-frame state line (`TROO AB 4 Goto Foo+2` — ambiguous which of A/B it
  applies from) is also a compile error. Using `Goto` before any state in the block exists yet is
  a compile error ("GOTO before first state"). Per the wiki: because `Goto` is a static jump
  resolved at compile time against the target class, jumping into a label that only exists on a
  parent class moves execution into the *parent's* states permanently — there's no implicit
  "return" back into the subclass. A dynamic jump (`A_Jump`, or in ZScript `FindState`/
  `ResolveState` — not available here, see above) resolves against the actual runtime class
  instead, per the wiki, though that distinction wasn't independently re-traced against this
  fork's `A_Jump` implementation for this page.
- **`Stop`** — the state's `NextState` resolves to `NULL`. Reaching a null state pointer calls
  `AActor::HideOrDestroyIfSafe()` (`p_mobj.cpp:513-521, 619-648`), which **normally destroys the
  actor** — but on a server, for a level-spawned actor, in a game mode whose flags include
  `GMF_MAPRESETS` (Zandronum's own map-reset-capable modes, e.g. Invasion), the actor is hidden
  instead (unlinked, marked `MF2_DORMANT`, `STFL_HIDDEN_INSTEAD_OF_DESTROYED` set, moved to a
  built-in `HideIndefinitely` state) so it can reappear when the map resets, rather than being
  permanently gone. This full hide-vs-destroy branch is Zandronum-specific multiplayer behavior,
  not something the wiki (written for single-player-oriented GZDoom) describes. Same "before first
  state" guard as `Goto`.
- **`Wait` / `Fail`** — exact synonyms in DECORATE. Makes the preceding state's `NextState` point
  **at itself**, so the state re-enters itself indefinitely instead of ever advancing — distinct
  from `-1` duration, which instead skips the tic-countdown check altogether. Only legal after a
  real preceding state (unlike `Goto`/`Stop`, there's no "retarget a dangling label" form). Per the
  wiki, `Fail` has exactly one meaningful use: ending a `CustomInventory`'s `Use:` sequence with
  `Fail` instead of `Stop` prevents the item from being consumed on use — this is a convention
  read by the inventory-use code path, not a distinct parser behavior from `Wait`.
- **`Loop`** — points `NextState` back at the first state *of the current label's run*, not
  necessarily the first state in the whole block — i.e. it loops the most recently declared label,
  not the whole actor. Also requires a preceding state.

## Label scoping and inheritance

When a subclass is compiled, its state-label table starts out **seeded by copying every label
from its parent class** (recursively, including dotted sub-labels) — by raw pointer into the
parent's already-compiled `FState` array, not by name lookup performed later. Two consequences
follow directly from that:

- **A subclass's unqualified `Goto SomeLabel` can reach a label the subclass itself never
  redeclares**, because that label is already sitting in the subclass's own (inherited) table from
  the copy step — this needs no `Super::`/class qualifier.
- **If the subclass's own `States { }` block does redeclare a label** (e.g. its own `Death:`),
  only that label (and its own dotted children) gets overwritten in place; every sibling label the
  subclass doesn't touch keeps pointing at the ancestor's original states.
- **The reverse direction does not exist**: an ancestor class's states can never `Goto` into a
  label defined only on a descendant — both because the qualifying class in `Class::Label` must
  already be an ancestor of the class being compiled (checked and enforced at compile time), and
  structurally because when the ancestor's own `States` block is compiled, no descendant class has
  been parsed yet.

**Legacy flat names are silently rewritten to dotted sub-labels** when looked up: `Burn` →
`Death.Fire`, `Ice` → `Death.Ice`, `Disintegrate` → `Death.Disintegrate`, `XDeath` →
`Death.Extreme`. Writing the old flat name and the new dotted name are equivalent as lookup
targets, not two different states.

### Dotted sub-labels resolve with generic partial-match fallback

`FActorInfo::FindState`'s multi-name form (`p_states.cpp:261-305`) walks a dotted name
(`Death`, `Fire`) one component at a time, remembering the deepest label it successfully matched
so far (`best`) and only requiring an exact full match when the caller explicitly asks for one
(`exact=true`). In non-exact lookups — which is how the engine resolves a death/pain/crash/bounce
event's damage-type-qualified label — **a request for `Death.SomeUndefinedType` transparently
falls back to plain `Death`** if the more specific sub-label was never defined. This is a single
generic mechanism, not something special-cased per family: it's why "partial matches work just
like Pain sequences" (the wiki's phrasing) applies equally to `Death.*`, `Pain.*`, `Crash.*`, and
`Bounce.*` alike — any dotted label family gets the same fallback behavior for free.

## Reserved / automatically-looked-up label names

Confirmed by direct `FindState(NAME_...)` or literal-string `FindState("...")` call sites in this
Zandronum checkout (not from general DECORATE convention, since some commonly-cited names turned
out not to apply to this fork — see below):

- **Core monster/actor cycle**: `Spawn`, `See`, `Melee`, `Missile`, `Pain`, `Death` (plus its
  legacy-aliased dotted children `Death.Extreme`/`XDeath`, `Death.Fire`/`Burn`,
  `Death.Ice`/`Ice`, `Death.Disintegrate`/`Disintegrate`), `Raise`, `Heal`, `Crash`, `Idle`
  (`NAME_Idle`, falls back to the `Spawn` state if undefined — `AActor::SetIdle`,
  `p_mobj.cpp:7823-7827`), `Active`/`Inactive` (Hexen-style switchable decorations), `Wound`
  (`NAME_Wound`).
- **Damage-type-qualified dotted families**, resolved via the generic fallback above rather than
  being separate reserved names in their own right: `Death.<mod>`, `Pain.<mod>`, `Crash.<mod>` for
  any means-of-death name (`Crush`/`NAME_Crush` is one built-in example, used as a `mod` value
  passed into the standard damage path, not a standalone top-level label), and `Bounce`/
  `Bounce.Floor`/`Bounce.Ceiling`/`Bounce.Wall`/`Bounce.Actor`/`Bounce.Actor.Creature`
  (`NAME_Bounce` + sibling `NAME_` constants, `p_map.cpp:3522-3571`, `p_mobj.cpp:1837`).
- **Strife dialog**: `Greetings` (`NAME_Greetings`), `Yes` (`NAME_Yes`), `No` (`NAME_No`) —
  `p_mobj.cpp:1334-1340`.
- **Inventory/weapon-specific**: `Ready`, `Select`, `Deselect`, `Fire`, `AltFire`, `Hold`,
  `AltHold`, `Flash`, `AltFlash`, `Reload`, `Zoom`, `Drop`, `Use`, `Pickup`, `Held` (literal
  `FindState("Held")`, `a_pickups.cpp:872`), `HoldAndDestroy` (literal
  `FindState("HoldAndDestroy")`, `a_pickups.cpp:171`).

**Listed by the wiki but not found anywhere in this checkout** (checked both as a `NAME_`
constant in `src/namedef.h` and as a literal-string `FindState()` argument) — treat these as
absent in Zandronum rather than assuming wiki parity:

- **`Slam`** — exists only as an unrelated C++ virtual method, `AActor::Slam()`
  (`actor.h:796`, `p_mobj.cpp:3748`), a collision hook for `SKULLFLY`-type actors. It never calls
  `FindState`/looks up a `"Slam"` label; there is no engine-recognized `Slam:` state sequence in
  this fork.
- **`LightDone`** — `A_Light0`/`A_Light1`/`A_Light2` action functions exist
  (`p_pspr.cpp:1353-1385`), but no automatic `FindState("LightDone")`/`NAME_LightDone` lookup was
  found anywhere — the wiki's "all weapons have this built in" claim does not appear to hold here.
- **`Death.Sky`** — no `NAME_DeathSky`/literal lookup found.

A label outside the confirmed set above is only ever reached via an explicit `Goto`/action-function
jump, never automatically by the engine.

## Multiple frames on one line

`TROO AB 4` is a compile-time expansion, not a single state with two frames: the parser emits one
`FState` per character in the frame token, all sharing the given duration/flags/action, and only
the **last** expanded frame becomes the anchor a following label or `Goto`/`Loop` target actually
lands on. This is also why a `+offset` `Goto` can't be combined with a multi-frame line — which of
the expanded frames the offset should count from is ambiguous, so the compiler rejects it outright
rather than picking one.

## Other parsing quirks worth knowing

- **Comments**: `//` and `/* */` are confirmed to work inside a `States { }` block (shared lexer,
  not state-block-specific), matching the wiki's "DECORATE format specifications" page. Whether a
  bare `;` also works as a line comment inside a state block specifically is **not confirmed** in
  this checkout — flagged as an open question below.
- **`#include "path/to/lump"`** can appear anywhere outside an actor definition (not inside a
  `States{}` block, and not inside the surrounding actor's braces at all) to split DECORATE
  content across multiple lumps — per the "DECORATE format specifications" wiki page, not
  independently re-verified against this fork's include-handling code for this page.
- **String escapes are turned off while parsing a state block** (re-enabled immediately after) —
  a backslash inside a `LIGHT("...")` argument is literal, not a C-style escape, unlike string
  literals elsewhere in DECORATE.
- **A zero-argument action function must be called with no parentheses at all** — `A_Fall`, not
  `A_Fall()` — the parser hard-errors ("You cannot pass parameters to '...'") if it sees `(` right
  after a function whose declared signature takes no arguments. A function whose parameters are
  all optional may be called either bare or with parens.
- **Any line special can be called as if it were an action function** inside a state (e.g. a
  special normally used in a linedef can appear as `Door_Open(1, 16)` on a state line) — the
  parser transparently rewrites this into an internal call carrying the special's number and up to
  five numeric arguments.

## Open questions (unverified in this checkout — don't guess past these)

- Whether the `LIGHT(...)` state keyword has any actual runtime effect in a real Zandronum release
  build, or is parsed and silently discarded because `DYNLIGHT` isn't defined for that build.
- Whether `;` is usable as a state-block line comment (a separate lexer mode appears to support it
  elsewhere in the source, but its activation during actor/state parsing specifically wasn't
  traced).
- Whether a frame sequence containing `[`, `\`, or `]` genuinely requires quoting in this fork's
  lexer, as the wiki states — plausible given those characters' other syntactic roles, but not
  traced against `sc_man`/`thingdef_states.cpp`'s tokenizing of the frame-character field
  specifically.
- Whether `Offset(0, 0)`'s "keep previous offset" special case (as opposed to resetting to
  `(0,0)`) holds in this fork's `OFFSET(x,y)` handling — the wiki states this as Hexen-compat
  behavior; this page's own source read of `thingdef_states.cpp`'s `OFFSET` branch didn't check
  for a `(0,0)` special case one way or the other.
- Whether `A_Jump`'s dynamic-jump target resolution actually differs from `Goto`'s static,
  compile-time-class-bound resolution the way the wiki describes (i.e., whether `A_Jump` jumping
  into an inherited label lands in the *runtime* class's override rather than the *defining*
  class's version) — not independently re-traced against this fork's `A_Jump` implementation.

If wiki material resolves any of these, fold the answer into this file directly and drop the
matching bullet here rather than leaving it stale.
