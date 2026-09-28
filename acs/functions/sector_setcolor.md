# Sector_SetColor

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Sector_SetColor - ZDoom Wiki (https://zdoom.org/w/index.php?title=Sector_SetColor&oldid=36901), verified against Zandronum 3.2.1 source (p_lnspec.cpp line 2497, p_sectors.cpp line 696); netcode wire format and client handler re-read at Zandronum bdd0f7beb (protocolspec/spec.sectors.txt lines 38-44, cl_main.cpp lines 6818-6824).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**Signature:** `Sector_SetColor(tag, r, g, b[, desat]):int` (action special 212)

Sets the color tint of light in all sectors matching `tag`. Returns 1 unconditionally — the return value is not a success/failure signal and does not indicate how many sectors were affected (the loop inside `LS_Sector_SetColor` calls `SetColor` on each match, but the function returns true regardless of the count).

## Parameters

- **`tag`** — Sector tag. Resolves via `P_FindSectorFromTag` (Zandronum, `src/p_spec.cpp:270`), which uses modular arithmetic and can match multiple sectors. Passing `tag=0` behaves like any other tag value (matches sectors with numeric tag 0, if any exist), not a wildcard. Confirmed identical on UZDoom: `LS_Sector_SetColor` calls the single-argument `Level->GetSectorTagIterator(tag)` overload, whose `Init(int tag)` also treats `tag=0` as a literal tag lookup (`src/playsim/p_tags.cpp:127`) — the "tag 0 means back of the activating line" semantics live in a *different*, two-argument `FSectorTagIterator` constructor (`p_tags.cpp:130-143`) that this special doesn't use.
- **`r`, `g`, `b`** — Red, green, blue intensity values, each an int in range 0–255. White light (255, 255, 255) is the default. **Correction: values outside this range are not clamped, they wrap (silently truncate modulo 256).** `GetSpecialLights` itself does no range-checking at all — it just stores the `PalEntry` it's handed (Zandronum `src/r_data/colormaps.cpp:186-210`). The actual narrowing happens one call earlier, in `sector_t::SetColor`'s `PalEntry color = PalEntry(r, g, b)` (Zandronum `src/p_sectors.cpp:696-704`): `PalEntry`'s 3-argument constructor takes `BYTE` (`unsigned char`) parameters (Zandronum `src/doomtype.h:190`), so an `int` argument like `300` becomes `300 & 0xFF == 44`, and `-1` becomes `255` — a wraparound, not a clamp to the nearest in-range value. UZDoom behaves identically: `LS_Sector_SetColor` constructs a `PalEntry` directly from the three raw arguments (`src/playsim/p_lnspec.cpp:2427`), and UZDoom's `PalEntry` constructor also takes `uint8_t` (`src/common/utility/palentry.h:101`), so the same modulo-256 wraparound applies there too. This corrects the previous version of this doc, which claimed `GetSpecialLights` performs a 0–255 clamp; it doesn't receive raw `r`/`g`/`b` at all, and the actual conversion it's fed doesn't clamp anything.
- **`desat`** — **Optional** (trailing parameter). Desaturation level, 0–255, where 0 = normal colors and 255 = grayscale. If omitted, defaults to 0 (no desaturation). The name varies by engine. On Zandronum, `sector_t::SetColor` calls it `desat`, while the `LS_Sector_SetColor` comment (`src/p_lnspec.cpp:2498`), `GetSpecialLights` and the network command all use the wiki's `desaturate`. UZDoom's free `SetColor(sector_t*, int color, int desat)` at `src/playsim/p_sectors.cpp:757` uses `desat`. Unlike `r`/`g`/`b`, `desat` reaches `GetSpecialLights`/`FDynamicColormap::Desaturate` as a plain, unclamped `int` on Zandronum when run offline or on the server — an out-of-[0,255] value isn't rejected here, it just produces an unusual result once `FDynamicColormap::BuildLights` scales it (`ld = Desaturate*256/255`, negated if negative — `colormaps.cpp:260-265`); this doc doesn't claim a clamp for `desat` and none was found. A networked Zandronum client sees a different value when the server relays the call: the network command carries `desaturate` as one unsigned byte (`protocolspec/spec.sectors.txt:38-44`), so a client applies `desat & 0xFF`. For example `-1` renders as full grayscale (255) on clients but as near-zero desaturation offline.

## Return value

Always `1` (`true`). No distinction between "no sectors matched the tag" and "sectors updated successfully" — a zero-match tag still returns 1. Confirmed identical on UZDoom: `LS_Sector_SetColor` there also returns true unconditionally regardless of how many sectors the tag iterator matched.

## Netcode (Zandronum)

Offline and on a server, every matching sector's color is always set locally. A server then sends one `SERVERCOMMANDS_SetSectorColorByTag(tag, r, g, b, desat)` to all clients rather than one command per sector (`src/p_lnspec.cpp:2509-2511`). Clients run the same tag loop on receipt (`src/cl_main.cpp:6818-6824`). The command carries `tag` as a signed 16-bit short and `r`/`g`/`b`/`desat` as unsigned bytes (`protocolspec/spec.sectors.txt:38-44`); see the `desat` note above for the one place that truncation changes the result.

On a client (and during client-demo playback, which `NETWORK_InClientMode()` also covers), `sector_t::SetColor` returns without doing anything unless its `bExecuteOnClient` argument is true (`src/p_sectors.cpp:700-701`). `LS_Sector_SetColor` passes `ACS_IsCalledFromScript()` for that argument (`src/p_lnspec.cpp:2507`) — **correction: that gate is not CLIENTSIDE-specific.** `ACS_IsCalledFromScript()` just checks `g_pCurrentScript != NULL` (`src/p_acs.cpp:13655-13658`), i.e. "was this special reached through the ACS interpreter at all" (as opposed to a direct linedef walkover/switch/gun activation or a DECORATE `A_CallSpecial`, which share the same `LineSpecials[]` dispatch table but leave `g_pCurrentScript` null). It does not check whether the running script is flagged `CLIENTSIDE`. The code comment directly above the call says the intent is to allow clients to set the color, since it is purely a visual effect, only from a `CLIENTSIDE` ACS script. The guard doesn't enforce that narrower condition. In practice the scripts a client runs are mostly `CLIENTSIDE` ones, because the server only tells clients to start scripts flagged `CLIENTSIDE` (see [Client-side scripting](../concepts/clientside-scripting.md)). But nothing on the client refuses a non-`CLIENTSIDE` script the client starts locally (for example through `ACS_Execute` from a `CLIENTSIDE` script), and a `Sector_SetColor` call from such a script also takes effect on that client. Either way, **client-side changes do not broadcast back to the server or to other clients.** The broadcast only happens when the network state is server.

## Engine-family divergence: no client/server replication step on UZDoom

The entire "Netcode (Zandronum)" section above is specific to Zandronum's authoritative-server
network architecture and does not carry over to UZDoom. UZDoom's `LS_Sector_SetColor` does the
sector-tag lookup and calls `sector_t::SetColor` directly and unconditionally for every match
(`src/playsim/p_lnspec.cpp:2421-2432`) — there is no `bInformClients`/`bExecuteOnClient`-style
parameter, no `ACS_IsCalledFromScript()`-equivalent gate, and no `SERVERCOMMANDS_*`-style network
command (that whole mechanism — `SERVERCOMMANDS_*`, `NETSTATE_SERVER`, `NETWORK_InClientMode()` —
doesn't exist anywhere in the UZDoom tree; grepped absent). UZDoom, a GZDoom-family engine, doesn't
split ACS execution between an authoritative server and replicated clients the way Zandronum's
netcode does, so there's no separate "did this run on the client" question for this special to
answer: wherever the owning script runs, the color is set there, full stop. The `CLIENTSIDE`
script flag still exists as a concept on UZDoom, but per
[Zandronum-vs-UZDoom ACS bytecode compatibility](../concepts/zandronum-uzdoom-compat.md) it
decodes to `SCRIPTF_Ignored` there and has no bearing on how this special behaves.

## UDMF equivalent

**Correction:** the previous version of this doc hedged that the ZDoom Wiki's UDMF `lightcolor`/
`desaturation` sector properties were "not verified as behavior in Zandronum itself." They are:
Zandronum's UDMF sector parser reads a `lightcolor` key (`src/p_udmf.cpp:1410`, `NAME_Lightcolor`)
and a `desaturation` key (`src/p_udmf.cpp:1418`, `NAME_Desaturation`, stored as `int(255 *
CheckFloat(key))`) and feeds them into the exact same `GetSpecialLights(lightcolor, fadecolor,
desaturation)` call this action special ultimately reaches (`src/p_udmf.cpp:1497`) — a static,
map-load-time equivalent of calling `Sector_SetColor` once at level start, not a ZDoom-only
feature. UZDoom's UDMF sector parser is the same shape: `NAME_Lightcolor`/`NAME_Desaturation` keys
(`src/maploader/udmf.cpp:1831,1886`) feeding `sec->Colormap.LightColor`/`Desaturation`
(`:2303,2312`) — the same runtime fields `sector_t::SetColor` writes. One UZDoom-side detail with
no Zandronum equivalent: UZDoom's UDMF loader clamps the parsed `desaturation` value to `[0,255]`
before storing it (`src/maploader/udmf.cpp:2312`), whereas the *action special*'s own
`desat` argument, on both engines, is not clamped anywhere in the code paths checked (see the
`desat` parameter note above) — a UDMF-authored desaturation value is range-checked at map load,
a script-set one currently isn't.

## See also

- [Sector_SetFade](sector_setfade.md) — companion function setting the fade (background) color instead of light color.
- [GetSectorFloorZ](getsectorfloorz.md) — uses the same `P_FindSectorFromTag` resolution logic for tag matching.
