# AmbientSound

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `AmbientSound - ZDoom Wiki.html` (zdoom.org, https://zdoom.org/w/index.php?title=AmbientSound&oldid=35962), verified against the Zandronum source on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

```text
void AmbientSound(str sound, int volume);
```

Compiler builtin (`PCD_AMBIENTSOUND`, `p_acs.cpp:11360`, the Zandronum source's `src/p_acs.cpp`).

## Behavior

Plays `sound` as a non-positional "world" sound: `S_Sound(CHAN_AUTO, lookup, volume/127.f,
ATTN_NONE)` with no sector/actor/point origin at all. `ATTN_NONE` means no distance falloff —
the wiki's "all players can hear it at the same volume, regardless of how close to the activator
they are" is accurate and confirmed by the attenuation constant, not just observed behavior.
Server-side, the sound is broadcast to every client via a plain `SERVERCOMMANDS_Sound(...)` call
with no target-player argument — this is a true global broadcast, unlike `LocalAmbientSound`
(same file, `PCD_LOCALAMBIENTSOUND`, immediately below this case), which requires a non-NULL
activator, checks `activator->CheckLocalView(consoleplayer)`, and replicates with
`SVCF_ONLYTHISCLIENT` to just that one client. The two builtins are otherwise structurally
parallel but are genuinely separate cases with separate NULL-activator handling — `AmbientSound`
never touches `activator` at all, so unlike `LocalAmbientSound` it works fine from scripts with
no activator (e.g. `OPEN`).

## Parameters

- `sound` — string-table index, resolved via `FBehavior::StaticLookupString`. If resolution
  fails (`lookup == NULL` — e.g. an out-of-range/garbage string index), the whole call is a
  silent no-op: no sound plays, no error/log message, and no console warning. The stack is still
  popped normally (`sp -= 2`) either way, so this failure is not observable from ACS at all.
- `volume` — integer, divided by `127.f` to produce the `float` volume `S_Sound` expects. The
  wiki's stated `0..127` range (0 = muted, 127 = full) is correct for the intended use, but
  **nothing in this case clamps the input** — passing `>127` yields a volume `>1.0`, and a
  negative value passes a negative float straight into `S_Sound`; behavior in that out-of-range
  case is whatever the underlying sound mixer does with it, not something this function guards
  against.

## Notes

- Channel is always `CHAN_AUTO` (engine picks an available channel) — there's no way to target a
  specific channel or later stop this particular sound by channel.
- No fork-specific divergence from the wiki was found beyond the above (the wiki doesn't mention
  the invalid-string no-op or the missing volume clamp, but doesn't contradict anything either).
