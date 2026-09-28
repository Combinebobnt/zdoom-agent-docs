# Outbound traffic measurement (`sv_measureoutboundtraffic`)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `Measuring outbound traffic` (https://wiki.zandronum.com/w/index.php?title=Measuring_outbound_traffic&oldid=756, saved 2026-09-22) + verified against the Zandronum source's `src/network/nettraffic.cpp` (whole file), `src/networkshared.cpp:62-64, 149-181`, `src/network/netcommand.cpp:145-340`, `src/network/packetarchive.cpp:96-121, 214-239`, `src/sv_main.cpp:947-1031`, `src/p_mobj.cpp:3956-4593` (`AActor::Tick`), `src/p_acs.cpp:9146, 13048, 13266` (`DLevelScript::RunScript` and its immediate-run caller), `src/g_level.cpp:1138` (`G_DoLoadLevel`). Line numbers are from the 3.3-alpha checkout; `nettraffic.cpp` and `networkshared.cpp` are unchanged since 3.2.1, and the other files' changes since then don't touch the counting.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

A Zandronum server can attribute the bytes it queues for clients to the **actor class** or
**ACS script** that was running when they were queued. Three console entries drive it:
[`sv_measureoutboundtraffic`](../notes/sv_measureoutboundtraffic.md) turns recording on,
[`dumptrafficmeasure`](../notes/dumptrafficmeasure.md) prints the totals, and
[`cleartrafficmeasure`](../notes/cleartrafficmeasure.md) empties them. The numbers are useful for
ranking which classes and scripts generate the most network commands, but they are not wire bytes
and several code paths inflate, drop, or misattribute them. Read the caveats below before treating
a figure as a bandwidth cost.

## How recording works

- **One global byte counter, two measurement windows.** `NETWORK_StartTrafficMeasurement` zeroes a
  single static counter and turns counting on; `NETWORK_StopTrafficMeasurement` turns it off and
  returns the count (`networkshared.cpp:62-64, 169-181`). The only two windows in the engine are
  the body of `AActor::Tick` (start at `p_mobj.cpp:3959`, stop at `:4592`) and the body of
  `DLevelScript::RunScript` (start at `p_acs.cpp:9146`, stop at `:13048`).
- **Where bytes are counted.** Only the `BYTESTREAM_s` write helpers that go through
  `AdvancePointer(n, true)` count: `WriteByte`/`WriteShort`/`WriteLong`/`WriteBuffer` and everything
  built on them (`WriteFloat`, `WriteString`, and the bit-packing helpers via `EnsureBitSpace`).
  The counter is fed whenever counting is on, regardless of which buffer is being written.
- **Attribution key.** Actor traffic is summed per class name (`GetClass()->TypeName`), so every
  instance of a class shares one total. Script traffic is summed per script number; named scripts
  are keyed by their negative name index and print as `Script "name": N`
  (`FBehavior::RepresentScript`, `p_acs.cpp:1685`).
- **Server only.** Both `NETTRAFFIC_Add*` functions return unless `NETWORK_GetState()` is
  `NETSTATE_SERVER` and `sv_measureoutboundtraffic` is true (`nettraffic.cpp:80, 93`). A zero-byte
  window records nothing, so a class or script that never sent anything is absent from the dump
  rather than listed with 0.
- **Resets every map.** `G_DoLoadLevel` calls `NETTRAFFIC_Reset()` unconditionally
  (`g_level.cpp:1138`), so `map`, `changemap`, rotation advances and hub moves all clear the
  totals. Turning the cvar off and on again mid-map does **not** clear them; only
  `cleartrafficmeasure` or a map load does.

## What a number actually means

"Bytes" here are **pre-compression stream bytes** written into server-side buffers: before Huffman
(or, on 3.3-alpha, Zstandard) encoding, and before UDP/IP headers. On top of that:

- **Counted once per recipient.** A server command is assembled in its own `NetCommand` buffer by
  `addInteger`, which advances the pointer directly and is *not* counted
  (`netcommand.cpp:145-158`). The counted copy is the one made into each client's packet buffer:
  `sendCommandToClients` loops `sendCommandToOneClient`, which calls `writeCommandToStream`, which
  uses `WriteTo`/`WriteBuffer` (`netcommand.cpp:274-340`). A 10-byte command broadcast to 8 clients
  records 80. The total therefore scales with the player count, not just with what the mod does.
- **Some fields are counted one extra time.** `addBit`, `addVariable`, `addShortByte` and `addBuffer`
  go through the counted `BYTESTREAM_s` helpers while the command is assembled
  (`netcommand.cpp:196-256`), so those parts are counted at build time as well as per recipient.
  Small in practice, but it means the figure is not an exact multiple of the command size.
- **A mid-window packet flush charges the whole packet to whoever triggered it.** Before copying a
  command into a client's buffer, `SERVER_CheckClientBuffer` sends that buffer early if the command
  wouldn't fit (`sv_main.cpp:1006-1031`). Counting is still on, so the flush's own writes are
  counted too: for the reliable channel, `StorePacket` copies the packet into the resend archive and
  `SendPacket` copies it again behind a 5-byte header (`packetarchive.cpp:118, 228-231`); for the
  unreliable channel, `SERVER_SendClientPacket` copies it once behind a 1-byte header. The class or
  script whose command happened to overflow the buffer is charged one (unreliable) or roughly two
  (reliable) extra copies of everything else already queued for that client. The reliable-channel
  charge only lands when that client isn't already throttled: if `sv_maxpacketspertick` is used up
  or earlier packets are still waiting, `ScheduleUnsentPacket` just queues the packet (uncounted)
  and it is stored and sent later, outside any window. Expect occasional large spikes that aren't
  the charged actor's or script's fault.

## What is not attributed, or attributed to the wrong entry

- **Early returns in `AActor::Tick` drop the tick's bytes.** `AActor::Tick` has many `return`
  statements before the stop call, including "freed itself" after a state change destroys the actor
  (`p_mobj.cpp:4530, 4554`), destruction during movement, time-freeze, spectators, player bodies
  with no movement command processed this tic (`:4015`), and non-respawning actors in an
  infinite-duration state. On those paths the counter is left running and zeroed by the next
  window's start, so the bytes are lost rather than misattributed. The final tick of an actor that
  removes itself is exactly the one most likely to broadcast something, so self-destroying
  projectiles and effects tend to be under-counted.
- **The window is the whole tick, not just code pointers.** The dump's header says "caused by actor
  code pointers", but the window also covers movement, collision, `Inventory` `DoEffect` calls and
  poison damage. Zandronum syncs non-player actor positions with event-driven `MoveThing` commands
  sent from movement code and action functions (e.g. a monster's walk step), not from a separate
  per-tic pass, so for moving monsters and projectiles those position updates are usually a large
  share of the class's total. Whatever a class's tick causes is charged to that class: a missile's `Tick` that
  kills a monster is charged the monster's death broadcasts, not the monster's class.
- **Player weapons are not attributed at all.** Weapon (psprite) states run from `P_PlayerThink`
  via `P_MovePsprites` (`p_user.cpp:4174`), which the server calls outside any actor's `Tick`. The
  same goes for everything else the server does outside the two windows: the regular per-client
  player position updates (`SERVERCOMMANDS_MovePlayer` from the server's client loop), full updates
  to joining clients, chat, scoreboard and game-mode messages.
- **A script started from inside an actor's tick corrupts both entries.** The counter is one global
  with no nesting. `ACS_ExecuteWithResult` (including from a DECORATE action) runs the script
  immediately via `RunScript` (`p_acs.cpp:13266`), inside the calling actor's window. The script's
  start zeroes the actor's bytes so far; the script's stop turns counting off, so the actor's bytes
  after the call are not counted; and the actor's own stop then returns the counter value the
  script left behind. Net effect: the script is credited correctly, and the actor's class is
  credited with the **script's** bytes instead of its own.

## Output

`dumptrafficmeasure` prints two blocks through `Printf`, which on a server also reaches connected
RCON clients:

```text
Network traffic (in bytes) caused by actor code pointers:
<ClassName> <bytes>
...

Network traffic (in bytes) caused by ACS scripts:
Script <number or "name">: <bytes>
...
```

Each block is sorted by byte count, ascending by default so the heaviest entries end up at the
bottom, nearest the console input line; `dumptrafficmeasure desc` (case-insensitive) sorts
descending. Any other argument is ignored.

## Wiki/engine divergence

- The wiki's sample output is listed alphabetically by class name. That predates the sort added in
  `da434a2ba` (2023, before 3.2.1): current output is ordered by byte count, as above.
- The wiki reads each figure as what that class "has sent". Per the caveats above, it is the sum of
  per-recipient buffer copies during that class's ticks, so it grows with the number of connected
  clients and includes flush spikes and nested-script bytes.

## Contrast: whole-packet totals

These are a different measurement: whole packets, per process, with no per-actor or per-script
breakdown.

- **Win32 server console window.** The server-side `SERVER_STATISTIC_*` counters are fed from the
  actual `sendto`/`recvfrom` byte counts, i.e. encoded wire bytes, and are displayed only by the
  Windows server GUI's traffic panel (`win32/serverconsole/serverconsole.cpp:2025-2032`). A
  headless server has no console command that prints them, which makes `dumptrafficmeasure` the
  only built-in traffic readout there.
- **`stat nettraffic` (client only).** Shows the client's own link: In, Out and Loss, each as
  this-tick/last-second/peak. Despite being whole-packet totals, these are not wire bytes either:
  on 3.2.1 "Out" is the packet size before Huffman encoding (`cl_main.cpp`,
  `CLIENT_SendServerPacket`) and "In" is the size after decoding (the return value of
  `NETWORK_GetPackets`). The 3.3-alpha checkout still counts the same sizes, but from inside
  `NETWORK_LaunchPacket` and `NETWORK_GetPackets` (`network.cpp:972, 1902`). **3.3-alpha only (post-3.2.1):** both directions add a compression
  percentage (`fbd2198a0`) and a Zstandard percentage (`62d2ad61e`), and the `cl_netgraph` cvar
  draws a graph under the stat (`f10bc56b5`). None of those three commits is an ancestor of the
  3.2.1 release commit.

## Engine-family divergence

UZDoom has no equivalent. There is no `sv_measureoutboundtraffic` cvar and no
`dumptrafficmeasure`/`cleartrafficmeasure` command in its source, and no per-actor or per-script
traffic accounting of any kind. Its networking is a peer-to-peer lockstep model with no dedicated
server, so there is no server-to-client command stream to attribute. The closest diagnostic,
UZDoom's `stat network` (`src/d_net.cpp`), reports per-player latency, tic sequencing and
acknowledgement state, but no byte counts.
