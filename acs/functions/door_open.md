# `int Door_Open(int tag, int speed [, int lighttag])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Door_Open - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=Door_Open&oldid=46912`, ZDoom upstream) + source-verified against Zandronum fork
(`p_lnspec.cpp:228-232`, `p_doors.cpp:579-698`, `p_doors.cpp:463-530`). The wiki page accurately
describes the ceiling-height behavior ("four units below the lowest surrounding ceiling") and the
parametric meaning (`tag`, `speed`, `lighttag`), and its Doom-linedef conversion table anchors the
speed values (16 for normal, 64 for fast). The wiki page does **not** document the manual-trigger
behavior, the `*usefail` side effect, the `tag != 0` partial-success conflation, the `tag == 0`
behavior when the ceiling is already moving, the `SPEED()` `/8` scaling of the `speed` parameter,
the `COMPATF_NODOORLIGHT` compat-flag gate, or the Zandronum-specific netcode replication — those
are this doc's source-verified additions.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Raises the ceiling of sector(s) to a position four map units below the lowest surrounding ceiling,
opening a door effect. Action special (positive index 11 in `zcommon.bcs`'s `special` table),
semantics in the Zandronum source's `src/p_lnspec.cpp`, `FUNC(LS_Door_Open)` (line 228), which forwards
into `EV_DoDoor` (`p_doors.cpp:579`).

- `tag` — sector(s) to affect, or `0` for a manual trigger convention:
  - **`tag != 0`** (remote door): the special affects all sectors matching the tag. Sectors whose
    ceiling is already moving are skipped (`continue` in the loop at `p_doors.cpp:680-694`).
    Returns `1` if **at least one** sector was found and started moving; a partial success (e.g.
    one sector already had a ceiling in motion) is indistinguishable from full success.
  - **`tag == 0`** (manual trigger, back-sector convention): the special affects only the sector on
    the *back side of the triggering line*. Returns `0` (false) if there is no triggering line
    (`!line`, line is NULL) or if the line has no back sidedef (`line->sidedef[1] == NULL`). When
    the line exists but has no back sidedef, the function also **plays the `*usefail` sound at the
    activator** (`p_doors.cpp:598`) before returning. If the target sector's ceiling is already
    moving (even for a `doorRaise` type), returns `0` — reopen-a-closing-door logic is **not**
    available for `Door_Open` (that is gated on `door->m_Type == DDoor::doorRaise`, a check not
    passed for the `doorOpen` type at `p_doors.cpp:626-627`).

- `speed` — **not map-units-per-tic directly.** Passed through the `SPEED(a)` macro
  (`p_lnspec.cpp:76`: `#define SPEED(a) ((a)*(FRACUNIT/8))`), i.e. the raw integer you pass is
  divided by 8 to get map-units-per-tic in fixed point. Pass `16` for 2.0 units/tic (standard Doom
  normal-door speed), `64` for 8.0 units/tic (standard Doom fast-door speed).

- `lighttag` *(optional, defaults to 0)* — if non-zero, a gradual lighting effect is applied to
  sectors matching `lighttag`. The light is gradually changed between the darkest neighboring
  sector when the door is fully closed and the brightest when fully open. **This effect is
  silently disabled if the `COMPATF_NODOORLIGHT` compatibility flag is set** — the flag is checked
  in the `DDoor` constructor (`p_doors.cpp:470-473`) and zeros `m_LightTag` before any lighting
  work is done. The ZDoom wiki page does not document this engine-fork compat-flag gate (present in
  both Zandronum and UZDoom, source-verified against each).

**Example — open all sectors tagged 10 at normal speed:**

```text
Door_Open(10, 16);
```

**Example — open the manually-triggered door on the activating line's back sector at fast speed
with a lighting effect applied to sector tag 11:**

```text
Door_Open(0, 64, 11);
```

This pattern matches the `Door_Open(0, 16, tag)` conversion shown in the wiki's Doom-linedef
conversion table for D1 doors that use a different sector for the lighting effect than the door
itself.

**Returns:** `int`, per the declared signature — `1` for success, `0` for failure. For `tag != 0`
(remote), success means at least one sector was affected. For `tag == 0` (manual), success means
a valid line with a back sector was found and that sector did not already have a moving ceiling.

**Zandronum-specific netcode:** The manual-trigger case (`tag == 0`) replicates the `*usefail`
sound to clients via `SERVERCOMMANDS_SoundActor` when the activator pushes a one-sided line
(`p_doors.cpp:601-607`). The remote-trigger case (`tag != 0`) replicates the door motion to
clients via `SERVERCOMMANDS_DoDoor` for each sector (`p_doors.cpp:689-691`). The ZDoom wiki page
does not document this netcode behavior.
