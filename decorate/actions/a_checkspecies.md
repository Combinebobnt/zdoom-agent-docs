# `action state A_CheckSpecies(statelabel label, name species = 'none', int ptr = AAPTR_DEFAULT)`

**Tier:** A
**Engine:** UZDoom 4.15pre / GZDoom-family — does not exist in Zandronum
**Provenance:** ZDoom Wiki `A_CheckSpecies` (retrieved 2026-08-01, oldid=44308) + verified against UZDoom source's `wadsrc/static/zscript/actors/checks.zs:195-199`.

Checks whether a target actor has a specified species and jumps to a given state if the check passes.

## Availability note

**This action does not exist in Zandronum** — it is part of the ZScript standard library in UZDoom/GZDoom-family engines only. A Zandronum equivalent would require conditional logic using ACS function calls or DECORATE expressions to check the `Species` property, since Zandronum's DECORATE action functions do not include species-checking built-ins.

## Parameters

- `statelabel label` — The state to jump to if the species check succeeds.
- `name species` — The species name to check for. Default is `'none'`. When not specified or set to `'none'`, the function checks whether the target actor has no explicit species (or an empty species). Species matching is case-insensitive.
- `int ptr` — The actor pointer to check, specified as an `AAPTR_*` constant (e.g., `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`, `AAPTR_DEFAULT`). Default is `AAPTR_DEFAULT` (the calling actor). If the pointer is null, the function returns without jumping.

## Return value

Returns to the next state in sequence (null / implicit `Loop`) if the species check fails or the actor pointer is null. Returns the resolved state label if the check passes.

## Behavior

The function retrieves the actor referenced by the `ptr` parameter and compares its species against the requested species value. If they match, execution jumps to the provided `label`; otherwise, the action returns without jumping and the state machine proceeds normally.

**Species resolution:** An actor's species (`GetSpecies()`, `src/playsim/p_mobj.cpp`) is determined either by explicit declaration via the `Species` property in DECORATE, or — if unset — by walking the class's ancestry: for a monster actor (`MF3_ISMONSTER`), it climbs to the **highest ancestor class that is still a monster** and uses that class's name, not the actor's own leaf class name; for a non-monster actor, it falls back to the actor's own class name directly (see [Inheritance](../concepts/inheritance.md) for the automatic species-resolution rules).

## Examples

Jumping to a different state if a target has a specific species:

```decorate
ACTOR MonsterChecker : Actor
{
    States
    {
        Spawn:
            PLYR A 0 A_CheckSpecies("SpecialMonster", "DemonSpecies", AAPTR_TARGET)
            goto Idle
        SpecialMonster:
            PLYR B 10 A_AlertMonsters
            loop
        Idle:
            PLYR A 10 A_Look
            loop
    }
}
```

## Cross-engine note

The wiki's `A_CheckSpecies` page is documented for ZDoom-family engines in general. Wiki parameter descriptions listed "cannot be `AAPTR_NULL`," but the actual implementation gracefully handles null pointers by returning without jumping — no error or crash occurs. Additionally, the wiki's parameter documentation for the first parameter was incorrectly labeled and described; the actual ZScript signature uses `statelabel label` as the first parameter.

## Related actions

- [A_JumpIf](a_jumpif.md) — generic conditional jump on a DECORATE expression
- [A_CheckFlag](a_checkflag.md) — checks an actor flag and jumps if set (deprecated in UZDoom/GZDoom, present in Zandronum)
- [A_CheckRange](a_checkrange.md) — jumps if a target is within/beyond a distance threshold
- [A_CheckLOF](a_checklof.md) — jumps if a target is in line of fire

## See also

- [Inheritance](../concepts/inheritance.md) — covers automatic species determination by walking class ancestry and the `MF3_ISMONSTER` flag
