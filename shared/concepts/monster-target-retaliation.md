# Damage retaliation: what writes a monster's `target` during gameplay

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @0d6263ac5f (2026-08-31); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/p_interaction.cpp` (`P_DamageMobj`'s
retaliation block and `AActor::Die`'s `target = source` overwrite, both cited by symbol — that
file carries local drift relative to `28f736fb3`, confirmed by diff not to touch either region),
`src/p_interaction.cpp:1935-1992` (`AActor::OkayToSwitchTarget`, cited by line — that function is
byte-identical at `28f736fb3`), `src/p_enemy.cpp:330-356` (`P_CheckMissileRange`, also
byte-identical at `28f736fb3`), `src/p_lnspec.cpp:1394-1562` (`Thing_Hate`), and
`src/p_mobj.cpp`/`src/g_game.cpp` (`AActor::CopyFriendliness`, `GAME_ResetMap`, the
`respawnactors` console command), with `src/p_mobj.cpp:1177-1204` (`CopyFriendliness`) and its
DECORATE-reachable callers at `src/thingdef/thingdef_codeptr.cpp:319-329`/`:2453`/`:3682` and
`src/g_doom/a_painelemental.cpp:152`. Every claim was then read again directly on the UZDoom source:
`src/playsim/p_interaction.cpp` (`ReactToDamage`, `CallReactToDamage`,
`AActor::CallOkayToSwitchTarget`/`OkayToSwitchTarget`, `AActor::Die`),
`src/playsim/p_enemy.cpp` (`P_CheckMissileRange`), and
`wadsrc/static/zscript/actors/actor.zs:804`/`:913` (the `native virtual` declarations), plus `src/scripting/thingdef_data.cpp:80` (`NOHATEPLAYERS`
in the internal flag table) and `src/playsim/p_actionfunctions.cpp:653-669`
(`A_CopyFriendliness`). No wiki
page covers this.

An actor's `target` field is read all over this tree — [GetActorProperty](../../acs/functions/getactorproperty.md)'s
`APROP_TargetTID`, `AAPTR_TARGET` pointer selectors, DECORATE action functions that branch on it —
but nothing here documents what sets it during ordinary play. This page covers exactly one write
path: **damage retaliation**, the mechanism where getting shot flips who a monster is chasing. It
does not attempt to inventory every place `target` is written — projectile ownership, puff owners,
goal-actor handling, and `A_RearrangePointers` all write it too, for unrelated reasons, and are out
of scope here. Sight/sound-based target acquisition (`P_LookForPlayers`, `A_Look`, sound alerting)
is also out of scope — that path is already documented in
[A_Look](../../decorate/actions/a_look.md), [A_LookEx](../../decorate/actions/a_lookex.md), and
[A_AlertMonsters](../../decorate/actions/a_alertmonsters.md).

## The write itself: getting hit flips your target

When a damaged actor wakes up and the damage has a `source` (the actor credited with dealing it):
if `source` is already the actor's `target`, only its `threshold` is refreshed and, if it was still
in its spawn state, it's pushed into `SeeState`. Otherwise the actor's target-switch gate (below)
runs, and if it allows the switch: the actor's *previous* target is saved as `lastenemy` (but only
if there wasn't one already, or the existing one is dead, or it is a non-player and the damaged
actor itself has no `Thing_Hate` target, i.e. `TIDtoHate` is 0), `target` is reassigned to `source`, `threshold` is reset, and — again, only from the
spawn state — the actor is pushed into `SeeState`.

This runs from the tail end of the damage-application pipeline: Zandronum inlines it directly in
`P_DamageMobj`; UZDoom does the same work in a separate `ReactToDamage` function, called through a
`CallReactToDamage` dispatcher every damage event goes through (see "Engine-family divergence"
below for why that split exists and what it enables).

## The gate: `OkayToSwitchTarget`, in order

Whether the switch above is even allowed to happen is decided entirely by one function,
`OkayToSwitchTarget`, called on the *candidate new target* (`other`) from the actor considering the
switch. On Zandronum it is twelve ordered checks, each an unconditional `return false` — order
matters, since an earlier refusal means a later flag is never consulted:

1. **Self.** Never target yourself (can happen when shooting your own barrels/projectiles).
2. **`+NEVERTARGET`** on the candidate — refuses unconditionally, before anything else about the
   candidate is even inspected.
3. **Not `+SHOOTABLE`.** Can't attack something that can't be hurt.
4. **`+NOTARGETSWITCH`**, but only if the actor already has *some* target — an actor with no target
   yet can still acquire its first one even with the flag set.
5. **Master/minion protection.** Refuses a candidate of your master's class (your master
   included), or one whose master is of your class (your own minions included). Three things
   lift the refusal: the candidate reads as hostile (`IsHostile`), its TID is the one this actor
   hates (a non-zero `TIDtoHate`), or the two sides carry different `TIDtoHate` values.
6. **`+NOTARGET`** on the candidate, unless it reads as hostile or its TID is the one this actor
   hates (a non-zero `TIDtoHate`).
7. **`threshold != 0`, unless `+QUICKTORETALIATE`.** `threshold` is the "stay locked onto my
   current target for a bit" cooldown set on every successful switch (`BASETHRESHOLD` on
   Zandronum, a per-actor `DefThreshold` on UZDoom — see below); this is what makes
   `+QUICKTORETALIATE` mean "ignore that cooldown and retaliate anyway."
8. **`IsFriend(other)`.** Friendlies don't target other friendlies.
9. **Infighting resolution.** `+NOINFIGHTING` on the actor, the map's `LEVEL2_TOTALINFIGHTING`/
   `LEVEL2_NOINFIGHTING` flags, or the `infighting` cvar decide whether non-friendly monsters fight
   each other at all; if infighting is off, a non-player, non-hostile candidate is refused. (On
   Zandronum specifically, this check has an extra clause — see "Zandronum-specific" below.)
10. **Matching `TIDtoHate`.** Two actors both tagged to hate the same TID (via `Thing_Hate`) are
    "teammates" and won't target each other.
11. **`+NOHATEPLAYERS`**, checked against the candidate being a player — see "A gate flag DECORATE
    can't set" below.
12. **Don't give up too easily.** If the actor already has a *living* target it's specifically
    tagged to hate (`TIDtoHate` matches that target's TID) and can currently see it
    (`P_CheckSight`), there's a roughly 50% chance (`pr_switcher() < 128`) it refuses the switch
    anyway and keeps chasing what it was already hunting.

Only if every one of these passes does the function return `true` and the switch above proceed.

## `MF_JUSTHIT`: set after the target write, not as part of it

Some pain reactions (electric damage under one branch, ordinary pain-state resolution under
another) set a local `justhit` flag *before* the target-write logic above runs at all. Once that
logic has finished, a separate, later check decides whether to actually raise the persistent
`MF_JUSTHIT` flag on the actor: only if `justhit` was set, **and** the actor's target is now the
damage `source`, or it has no target, or its target isn't a friend. So `MF_JUSTHIT` does not track
"did the retaliation write happen" — it can be set even when the switch above was refused (the
actor keeps its old target but still remembers it was just hit), and it is explicitly suppressed
when the actor would otherwise fight back against a friend that hit it.

The flag is consumed, and cleared, by `P_CheckMissileRange` — reached every tic `A_Chase`/`A_DoChase`
considers whether to attack — as a fast-path "attack right back" that skips the normal
missile-range roll entirely (with an extra defect-chance check for friendly fire specifically). See
[A_Chase](../../decorate/actions/a_chase.md) for the surrounding attack-decision logic this flag
short-circuits.

What it skips, in both engines (`P_CheckMissileRange` in `src/p_enemy.cpp` on Zandronum,
`src/playsim/p_enemy.cpp` on UZDoom): only the sight check comes before it. `reactiontime`, the
`MaxTargetRange` cap and the random range roll all come after the early `return true`. So a monster
with `MaxTargetRange` that is hit from any distance while its target is visible enters its
`Missile` state regardless of the cap. A missile state that must stay short-range needs its own
distance check (see the `JLOSF_CLOSENOJUMP` pitfall in
[A_JumpIfTargetInLOS](../../decorate/actions/a_jumpiftargetinlos.md)).

The non-retaliation path doesn't compare `MaxTargetRange` against the raw distance either. It uses
the 2D distance minus 64, and minus a further 128 when the actor has no `Melee` state. A monster
with `MaxTargetRange 160` and a `Melee` state can therefore start a missile attack at up to 224
units.

## `AActor::Die` overwrites `target` unconditionally

Independent of all of the above: when a non-missile actor dies with a `source`, `Die` sets
`target = source` regardless of the death gate's outcome or what the actor's `target` held a
moment earlier. So a corpse's `target` is always its killer, never whatever it was chasing when it
died — the same overwrite [Holding a handle on an actor that has no unique
TID](../../acs/concepts/actor-handles.md) already covers from the pointer-lifetime side. Code
reading `APROP_TargetTID` (see [GetActorProperty](../../acs/functions/getactorproperty.md)) or an
`AAPTR_TARGET` selector on something that may already be dead should not assume the value it gets
back has anything to do with pre-death behavior.

## A gate flag DECORATE can't set: `+NOHATEPLAYERS`

`MF4_NOHATEPLAYERS` (gate 11 above) is real on both engines but is deliberately absent from
`decorate/inventory/actor-flags.md`. An actor definition cannot write `+NOHATEPLAYERS`: Zandronum
has no flag-table entry for it at all, and UZDoom lists it only among its internal flags, which
actor definitions can't use. What sets it from scratch is
[Thing_Hate](../../acs/functions/thing_hate.md) (types 5/6, from ACS/BCS). On UZDoom, ZScript code
can also write the `bNOHATEPLAYERS` member directly.

It is also *copied* from one actor to another, without ever being re-derived.
`AActor::CopyFriendliness` copies it along with the rest of the source actor's hate data. That
function has many callers, and several are reachable from DECORATE on both engines, via action
functions or a `RandomSpawner` subclass: `A_CopyFriendliness`, `A_SpawnItem`/`A_SpawnItemEx` when
the spawner is a monster, `A_Burst`'s chunks, the Pain Elemental skull spawns, and
`RandomSpawner`'s spawned actor. Engine-internal callers include Arch-Vile
resurrection ("the resurrector's minion now, so hate what it hates"), nightmare-difficulty
respawn, and morphing. On UZDoom, ZScript can also call `CopyFriendliness` directly. Zandronum
has two more respawn paths that copy the raw bit without going through `CopyFriendliness`: a
level reset (`GAME_ResetMap`) and the `respawnactors` console command. UZDoom has neither. So
DECORATE can't give an actor the bit, but it can pass one on from an actor that already has it.

## Engine-family divergence

| | Zandronum 3.2.1 | UZDoom 5.0.0-pre |
|---|---|---|
| Retaliation block | inline in `P_DamageMobj` | its own `ReactToDamage`, dispatched through `CallReactToDamage` |
| `OkayToSwitchTarget` override | not overridable — C++ only | `native virtual` (`actor.zs:804`) — a ZScript mod can replace the entire gate |
| `ReactToDamage` override | doesn't exist as a separate function to override | `native virtual` (`actor.zs:913`) — a ZScript mod can replace the whole retaliation write |
| Threshold reset value | fixed `BASETHRESHOLD` constant (100) | per-actor `DefThreshold` field, settable per class |
| Gate name at the call site | `OkayToSwitchTarget` | `CallOkayToSwitchTarget` (resolves to the virtual override if one exists, else the native default) |
| `SeeState` transition | broadcasts `SERVERCOMMANDS_SetThingState` to clients when hosting | no broadcast — no such system exists |
| Default gate's own extra checks | none of the below | adds an explicit null-candidate check, an MBF21 `infighting_group` mutual-exclusion check, and a `+NOINFIGHTSPECIES` species check; its infighting resolution also recognizes `+FORCEINFIGHTING` and, in place of the `infighting` cvar, falls back to a per-skill `SKILLP_Infight` property via `FLevelLocals::GetInfighting()` — which still checks `LEVEL2_TOTALINFIGHTING`/`LEVEL2_NOINFIGHTING` first, so those two map flags resolve the same way on both engines |

That last row matters beyond a line-count curiosity: it means the twelve-gate list above is
Zandronum's gate set specifically. UZDoom's *native default* implements the same twelve *decisions*
in the same order — same nine untouched gates, plus the map-flag pair folded into
`GetInfighting()` rather than inlined — plus three more gates with no Zandronum counterpart at
all, and swaps the cvar fallback for a skill property. Because the function is `native virtual`,
a ZScript-based mod can also replace the gate set entirely, so no fixed gate count can be asserted
as UZDoom's behavior in general the way it can for Zandronum.

## Zandronum-specific: infighting during invasion mode

Zandronum's infighting resolution (gate 9 above) carries one extra disjunct UZDoom's does not:
non-friendly monsters also refuse to infight with each other while an Invasion-mode round is
active (`|| invasion`), on top of the ordinary `+NOINFIGHTING`/map-flag/cvar reasons. UZDoom has no
Invasion game mode and no equivalent clause.
