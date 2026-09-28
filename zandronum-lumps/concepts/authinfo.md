# The `AUTHINFO` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `AUTHINFO` (https://wiki.zandronum.com/w/index.php?title=AUTHINFO&oldid=2278, retrieved 2026-09-09) + verified against the Zandronum source's `src/network.cpp` (`NETWORK_Construct`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

`AUTHINFO` extends the network lump-authentication set: a list of lump names, each paired with a
namespace and an authentication mode, that both a connecting client and the server independently
hash into one MD5 checksum at startup (`NETWORK_Construct` runs on both sides). The client sends
its checksum to the server on connect, and the server compares it against its own (gated by the
`sv_pure` cvar) to catch a client whose copy of these lumps, `PLAYPAL`, `COLORMAP`, `DECORATE`,
`MAPINFO`, and similar, doesn't match. `AUTHINFO` itself is a flat, unbracketed directive list, not
`{ }`-delimited blocks: five recognized directives, `clearlumps`, `addlump`, `removelump`,
`addsprites`, and `removesprites`. An unrecognized directive word is a fatal parse error
(`sc.ScriptError`), the same fail-hard behavior `bots/`'s `BOTINFO` uses for an unrecognized key,
not the tolerant handling this section's own `ANCRINFO` uses for one.

## Grammar

```text
addlump global MYCUSTOMLUMP last
addlump sprite MYSPRA0 all
removelump global SOMEOLDLUMP
addsprites TNT1 A all
removesprites TNT1 AB
clearlumps
```

- `addlump <namespace> <lump name> <last|all>` adds one lump to the authentication set. `<namespace>` is one of the keywords documented below; an unrecognized keyword prints a warning and falls back to `global` (see Namespaces section). `<last|all>` selects the authentication mode: `last` checks only the most recently loaded copy of the lump (client and server may load different earlier copies, but whichever is loaded last must match); `all` checks every copy across every loaded archive (client and server must have identical copies at every load point).
- `removelump <namespace> <lump name>` uses the same namespace token, with no mode argument, since
  removing a lump from the set doesn't need one.
- `addsprites <4-char sprite name> <frame letters|all> <last|all>` matches every currently loaded
  sprite-namespace lump whose name starts with the given 4 characters and whose frame letter (the
  position that carries the frame in an `XXXXA1` or `XXXXA1A5`-style sprite lump name) is one of
  the given letters, or every frame if the second token is literally `all`. The sprite name must be
  exactly 4 characters and each frame letter must be a valid sprite-frame character; both are fatal
  parse errors if violated.
- `removesprites <4-char sprite name> <frame letters|all>` does the same matching, with no mode
  argument.
- `clearlumps` takes no arguments and empties the custom additions accumulated so far, not the
  engine's own hardcoded set (see below). Because the parser processes every loaded `AUTHINFO` lump
  in one pass, a later lump's `clearlumps` also wipes out an earlier lump's `addlump` entries, not
  just its own.

## Namespaces

Each namespace in `addlump` and `removelump` corresponds to a region of the lump namespace where lumps are loaded from markers or dedicated directory structures in WAD/PK3 archives:

- `global` — lumps outside any `X_START`/`X_END` marker range in a WAD, or in a PK3's root
  directory (the default fallback for an unrecognized namespace keyword). A PK3 lump nested in any
  subdirectory other than the ones listed here gets no namespace at all and can't be matched.
- `sprite` — lumps between `S_` or `SS_` markers, or in a `Sprites` directory.
- `flat` — lumps between `F_` or `FF_` markers, or in a `Flats` directory.
- `texture` — lumps between `TX_` markers, or in a `Textures` directory (distinct from hires
  textures).
- `hires` — high-resolution lumps between `HI_` markers, or in a `HiRes` directory.
- `voxel` — lumps between `VX_` markers, or in a `Voxels` directory.
- `sound` — lumps in a `Sounds` directory.
- `patch` — lumps in a `Patches` directory.
- `graphics` — lumps in a `Graphics` directory.
- `music` — lumps in a `Music` directory.

An unrecognized namespace keyword is not fatal (unlike an invalid sprite name or frame letter) — it
prints a warning message and falls back to `global`.

## Cannot touch the hardcoded protected set

Before any `AUTHINFO` lump is parsed, `NETWORK_Construct` builds a base set of lumps that are
always authenticated (`src/network.cpp:431-447`): `COLORMAP`, `PLAYPAL`, `HTICDEFS`, `HEXNDEFS`,
`STRFDEFS`, `DOOMDEFS`, `GLDEFS`, `DECORATE`, `LOADACS`, `DEHACKED`, `GAMEMODE`, `MAPINFO`,
`AUTHINFO`, `VOTEINFO`, and `MEDALDEF`, plus every rotation of the `ALLY`/`ENEM` sprites' `A` frame
added separately. This set is what stops `AUTHINFO` from disarming its own gatekeeping: it names `AUTHINFO`,
`VOTEINFO`, and `MEDALDEF` themselves, so a loaded `AUTHINFO` lump cannot use `removelump` or
`removesprites` to drop the requirement that a connecting client has a matching copy of any of
these authenticated.

The mechanism is a set-membership check applied to every parsed directive, not a name blacklist
checked only for `removelump`. Whatever entry a directive produces, from `addlump`, `removelump`,
`addsprites`, or `removesprites`, is looked up against the hardcoded base set by lump name and
namespace only; the authentication mode is deliberately excluded from that comparison
(`AUTHENTICATELUMP_s::operator<` only orders by name, then namespace). A hit prints a non-fatal
message ("... is an engineside protected lump and cannot be modified/removed") and the directive's
effect is dropped; parsing continues with the next directive rather than aborting the whole lump.
So both `addlump global AUTHINFO last` and `removelump global MEDALDEF`, spelled that way, parse
without error and are silently no-ops against the actual authentication set; only the printed
message reveals it happened.

The name comparison is case-sensitive. The parser keeps an `addlump`/`removelump` name exactly as
written (only the sprite directives upper-case, via the real lump names), and the base set holds
upper-case names. A lower-case spelling such as `addlump global decorate last` therefore skips the
protected message and enters the custom set as its own entry. Lump lookup upper-cases the name, so
that entry hashes the same lump a second time into the checksum. It still can't remove anything
from the base set, since `removelump` only erases from the custom set.

## Loading is additive across lumps, in one shared accumulator

The engine finds every loaded `AUTHINFO` lump (a `Wads.FindLump` loop) and parses all of them into
one running `customLumpsToAuthenticate` set before merging it into the base set once, after the
loop finishes. There is no per-lump isolation: `addlump`, `removelump`, `addsprites`,
`removesprites`, and `clearlumps` all act on the same accumulator no matter which loaded `AUTHINFO`
lump they came from, so load order across archives matters for the final authentication set the
same way it would within a single file.

## Wiki/source divergence

The Zandronum Wiki's "Restricted lumps" section incompletely lists the hardcoded protected set.
It names COLORMAP, PLAYPAL, HTICDEFS, HEXNDEFS, STRFDEFS, DOOMDEFS, GLDEFS, DECORATE, LOADACS,
DEHACKED, GAMEMODE, MAPINFO, and AUTHINFO, but omits `VOTEINFO` and `MEDALDEF` — both of which
are confirmed protected and cannot be modified or removed by `AUTHINFO` directives (source:
`src/network.cpp:431-447`).

## Engine-family divergence

UZDoom/GZDoom-family engines have no lump-authentication subsystem of this shape and do not parse
`AUTHINFO` at all.
