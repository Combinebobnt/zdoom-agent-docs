# AmbientSound

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `AmbientSound - ZDoom Wiki.html` (zdoom.org, https://zdoom.org/w/index.php?title=AmbientSound&oldid=35962), verified against the Zandronum source on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

```text
void AmbientSound(str sound, int volume);
```

Compiler builtin (`PCD_AMBIENTSOUND`, `p_acs.cpp:11360`, the Zandronum source's `src/p_acs.cpp`).

## Behavior

Plays `sound` as a non-positional "world" sound: `S_Sound` on `CHAN_AUTO` at `volume / 127` with
`ATTN_NONE`, and no sector/actor/point origin at all. `ATTN_NONE` means no distance falloff.
The wiki's "all players can hear it at the same volume, regardless of how close to the activator
they are" is accurate and confirmed by the attenuation constant, not just observed behavior.
On Zandronum, when the script runs on the server, the case also calls `SERVERCOMMANDS_Sound(...)`
with no target-player argument, so every client plays it: a true global broadcast. Offline, or
when a client runs it itself (e.g. from a `CLIENTSIDE` script), it only plays locally. Compare
`LocalAmbientSound` (same file, `PCD_LOCALAMBIENTSOUND`, immediately below this case), which
requires a non-NULL activator, checks `activator->CheckLocalView(consoleplayer)`, and (for a
player activator) replicates with `SVCF_ONLYTHISCLIENT` to just that one client. The two builtins are otherwise structurally
parallel but are genuinely separate cases with separate NULL-activator handling — `AmbientSound`
never touches `activator` at all, so unlike `LocalAmbientSound` it works fine from scripts with
no activator (e.g. `OPEN`).

## Parameters

- `sound` — string-table index, resolved via `FBehavior::StaticLookupString`. If resolution
  fails (`lookup == NULL` — e.g. an out-of-range/garbage string index), the whole call is a
  silent no-op: no sound plays, no error/log message, and no console warning. The stack is still
  popped normally (`sp -= 2`) either way, so this failure is not observable from ACS at all.
- `volume` — integer, divided by `127.f` to produce the `float` volume `S_Sound` expects. The
  wiki's stated `0..127` range (0 = muted, 127 = full) is correct. The case itself doesn't clamp,
  but the sound start path does: a volume of 0 or below plays nothing, and after scaling by the
  sound's SNDINFO volume the result is capped at 1.0 (Zandronum `src/s_sound.cpp:901`, `:954`;
  UZDoom's `S_StartSound` does the same). So a value above 127 plays at full volume. It only
  differs from 127 when it offsets a SNDINFO `$volume` below 1. On Zandronum, clients never get
  that boost: the server clamps the float to `0..2` before packing it into the `Byte` volume
  field (`src/sv_commands.cpp:3653`), and the client caps the received value at 127
  (`src/cl_main.cpp:7212-7215`).

## Notes

- Channel is always `CHAN_AUTO` (engine picks an available channel) — there's no way to target a
  specific channel or later stop this particular sound by channel.
- No fork-specific divergence from the wiki was found beyond the above (the wiki doesn't mention
  the invalid-string no-op or the out-of-range volume handling, but doesn't contradict anything
  either).
