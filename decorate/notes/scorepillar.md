# `+SCOREPILLAR` (actor flag)

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. Zandronum, read at the 3.3-alpha checkout @bdd0f7beb: `src/actor.h:404`, `src/thingdef/thingdef_data.cpp:263`, `src/p_map.cpp:1358-1383` (`PIT_CheckThing`), `wadsrc/static/actors/Skulltag/skulltagscorepillars.txt`. UZDoom: `src/scripting/thingdef_data.cpp:448`, `src/scripting/decorate/thingdef_parse.cpp:460-462`, `src/scripting/thingdef_properties.cpp:343`.
**Bucket:** `DEFINE_FLAG(STFL, SCOREPILLAR, AActor, STFlags)` in Zandronum (`STFL_SCOREPILLAR` = `0x2000`).

Marks an actor as a Skulltag score pillar: a player carrying an enemy team item scores by bumping
it. The full scoring rules (the `args[0]` team and `args[1]` points convention, the
`Tag<TeamName>Skull` state jump, simple vs. scripted mode) are in
[Team items](../families/team-items.md#scoring-in-skulltag-mode-scorepillar-and-hellscorepillar).
That page is the reference; this note covers what the flag itself does and doesn't do.

## Zandronum

- **It does nothing alone.** The only reader is the sideways-bump block of `PIT_CheckThing`, which
  only runs for a `+SOLID` actor with [`+BUMPSPECIAL`](bumpspecial.md), bumped by a solid actor.
  A pillar needs all three flags, as the stock `HellScorePillar` (5020) has.
- **It doesn't replace the special.** After the score check, the pillar's `special` still runs
  with the same `args`, and it runs through Zandronum's older bump form: no cooldown, so about once
  per tic while a player pushes against it. A pillar normally has no special, since `args[0]` and
  `args[1]` are already taken by the team and point values.
- **Standing on top doesn't score.** The standing-on-top bump path never checks this flag.

## Engine-family divergence

UZDoom declares the name as `DEFINE_DUMMY_FLAG(SCOREPILLAR, false)` only so Skulltag-era DECORATE
still parses. A dummy flag has no storage, so the parser passes it to the deprecated-flag handler,
whose default case does nothing. The flag is accepted silently and has no effect. The generated
inventory's `UZD: yes` for this row is a name match only. UZDoom also has no team-item scoring
and no `HellScorePillar` class, so a pillar is just an actor with `+BUMPSPECIAL`, running its
special through UZDoom's own bump rules.

## See also

- [Team items](../families/team-items.md): the scoring mechanics and `HellScorePillar`.
- [`+BUMPSPECIAL`](bumpspecial.md): the two engines' bump trigger paths.
