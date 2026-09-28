# Thing_Destroy

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `Thing_Destroy` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=Thing_Destroy&oldid=33504) + verified against the Zandronum source's `src/p_lnspec.cpp:1335-1371`, `src/p_enemy.cpp:3801-3827` (`P_Massacre`), `src/p_mobj.cpp:1511-1528` (`AActor::Massacre`) and `src/p_interaction.cpp:1212,1261,1266,1313,1339,1533` (`P_DamageMobj` telefrag gates).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special (index 133)

**Signature:** `int Thing_Destroy(int tid, [int extreme, int tag])`

Destroys one or more actors by damaging them. Which actors are hit, and how hard, depends on the parameters:

- `tid`: Thing ID of the actors to destroy. Zero selects by sector tag instead: with `tag` nonzero, every `MF_SHOOTABLE` actor (players included, not just monsters) standing in a sector tagged `tag`; with `tag` also zero, every monster on the map through the massacre routine (see below).
- `extreme`: If nonzero, the damage is `TELEFRAG_DAMAGE` (1,000,000), which drives health far below the gib threshold, so the actor uses its extreme death (`XDeath`) state if it has one. If zero, the damage equals the actor's current `health`. Ignored by the massacre path.
- `tag`: Sector tag filter. With a nonzero `tid`, zero means no filter. With `tid == 0` it is the selector described above. Zandronum sectors carry a single tag; UZDoom matches any of a sector's tags.

The activator is passed as the damage source (kill credit). With a nonzero `tid` or `tag`, only actors with `MF_SHOOTABLE` are hit.

**Massacre path (`tid == 0 && tag == 0`):** every monster (`ISMONSTER`) that isn't `DORMANT` is made shootable, has `INVULNERABLE` cleared, and is hit repeatedly with telefrag-magnitude damage (damage type `Massacre`, no source) until it dies or stops taking damage. Since this always uses telefrag damage, `Thing_Destroy(0)` gibs exactly like `Thing_Destroy(0, 1)`. On Zandronum the massacre does nothing on a client (`NETWORK_InClientMode()`); it runs offline or on the server.

**Return:** Always `true`.

**Limitations:**

- `extreme = 0` deals only the target's current health, so anything that reduces damage leaves the target alive: player armor, a `DamageFactor` below 1, protection powerups. Players with armor commonly survive it.
- How much protection telefrag damage (`extreme` nonzero, and the massacre path) bypasses differs by engine:
  - UZDoom: it is not reduced by skill or damage factors, protection powerups or armor unless the target has `LAXTELEFRAGDMG`. `DORMANT` still blocks it.
  - Zandronum: it skips `INVULNERABLE`, god mode and the player skill damage factor, but the actor's own `DamageFactor`, protection powerups, armor absorption and `DORMANT` still apply. Armor can't absorb more than its point total, so armored players still die. For example an actor with `DamageFactor 0` survives both modes (the massacre loop gives up once the actor stops taking damage).
- For finer control, apply explicit damage with `Thing_Damage`.

**Examples:**

- `Thing_Destroy(0)` - kill all monsters (gibbing those with an `XDeath` state; `extreme` makes no difference here).
- `Thing_Destroy(0, 1, 5)` - gib every shootable actor, players included, in sectors tagged 5.
- `Thing_Destroy(123)` - destroy the actor with TID 123.
- `Thing_Destroy(123, 1, 5)` - destroy the actor with TID 123 if it's in a sector with tag 5, gibbing it.
