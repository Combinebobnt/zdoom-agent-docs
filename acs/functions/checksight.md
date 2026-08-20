# CheckSight

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `CheckSight - ZDoom Wiki` (https://zdoom.org/w/index.php?title=CheckSight&oldid=52148), verified against Zandronum source 2026-07-29
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (`zcommon.bcs` index -35, dispatches to `case ACSF_CheckSight` in `p_acs.cpp:6290`)

**Syntax:** `bool CheckSight(int source, int dest, int flags)`

---

## Description

Performs a line-of-sight check between one or more source actors and one or more destination actors. Returns true if **any** actor with the source TID can see **any** actor with the destination TID. Useful for script logic gating visibility-based behavior (AI detection, event triggers, etc.).

### Parameters

- **`source`**: Thing ID of the actor(s) doing the seeing. Use `0` to refer to the script activator.
- **`dest`**: Thing ID of the actor(s) to search for. Use `0` to refer to the script activator.
- **`flags`**: Bit flags to modify sight-check behavior. Currently supported flags are:
  - **`CSF_NOFAKEFLOORS` (0x1)**: Ignores non-solid fake floors created by `Transfer_Heights` (e.g., water sectors). When set, sight checks pass through these visual boundaries.
  - **`CSF_NOBLOCKALL` (0x2)**: Ignores lines marked "Block Everything". Monsters can see through these lines if there's a chance that shooting them will make them unblock (like scripted breakable glass).

### Return value

`true` (1) if any actor matching the source TID has line of sight to any actor matching the destination TID, `false` (0) otherwise.

### Behavior details

- **Activator equivalence:** When `source == 0` and `dest == 0`, the function returns `true` (you can always see yourself). If `source == 0`, the activator is used as the seeing actor. If `dest == 0`, the activator is used as the target actor.

- **Inclusive multi-actor matching:** If either TID matches multiple actors, the function iterates through **all combinations** of source and destination actors and returns `true` as soon as **any pair** has line of sight. The iteration stops on the first successful pair (short-circuit evaluation), so it may not check all combinations.

- **Null activator:** If `source == 0` or `dest == 0` and the activator is `NULL` (e.g., in `OPEN` scripts that run without an activating actor), the function degrades to a silent `false` return.

- **Flag semantics:** The flags argument is a bitmask:
  - **Bit 0 (0x1):** Sets `SF_IGNOREWATERBOUNDARY` in the engine, allowing sight to pass through non-solid fake floors.
  - **Bit 1 (0x2):** Sets both `SF_SEEPASTBLOCKEVERYTHING` and `SF_SEEPASTSHOOTABLELINES` in the engine, allowing sight through "Block Everything" lines and shootable/damaging lines. These can be combined: `flags = CSF_NOFAKEFLOORS | CSF_NOBLOCKALL` (0x3) sets both.

- **Always ignores visibility:** Internally, the implementation always sets `SF_IGNOREVISIBILITY`, meaning the base sight check ignores whether actors are currently invisible. The line-of-sight trace is purely geometric (line-of-sight vs. obstruction), not appearance-dependent.

### Related functions

- **`A_CheckSight`** (action function): A DECORATE action function variant that performs a similar check on the calling actor. Not directly available from ACS, but demonstrates the same underlying engine logic.

---

## Wiki notes

The wiki page for ZDoom is accurate and complete for Zandronum. **No divergence found** — all described flags and behavior are present and work as documented in the fork's source code.

---

## Code references

- **Engine implementation:** the Zandronum source's `src/p_acs.cpp:6290-6315` (the case block with full flag handling and multi-actor iteration)
- **Declaration:** the zt-bcc source's `lib/zcommon.bcs:1663`
- **Flag enumeration (SF_*):** the Zandronum source's `src/p_local.h:100-104` (the `ESightFlags` enum)
- **Sight-check core logic:** the Zandronum source's `src/p_sight.cpp:900-950` (P_CheckSight implementation with fake-floor handling)
