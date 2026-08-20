# GetChar

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=GetChar&oldid=35766, retrieved 2026-08-06), verified against Zandronum source (p_acs.cpp, case ACSF_GetChar)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (ACSF_GetChar, index -15)

**Signature:** `int GetChar(str string, int index)`

## Summary

Returns the character at a given index in a string as an integer (ASCII/Unicode codepoint), or 0 on error.

## Behavior

The function looks up the string by its handle (`string`) and returns the character at the zero-based `index` position. If any of these conditions hold, it silently returns `0`:
- The `string` handle is invalid (lookup fails, resolves to NULL)
- The `index` is negative
- The `index` is >= the string length

There is no way to distinguish between these error conditions and a legitimate character with codepoint `0` — a character at the given index is simply returned as-is, whether it's printable ASCII, a null byte, or a high Unicode codepoint.

## Examples

```acs
GetChar("hello", 0)  // returns 'h' (104)
GetChar("hello", 4)  // returns 'o' (111)
GetChar("hello", 5)  // returns 0 (out of bounds)
GetChar("hello", -1) // returns 0 (negative index)
```

The character can be cast to `c` in HudMessage context:
```acs
HudMessage(c:GetChar("abc", 0); HUDMSG_PLAIN, 0, CR_WHITE, 160, 100, 1.0);
```

## Related

- `StrLen` — get the length of a string
- `GetSubString` — extract a substring
- `MidPrint`/`HudMessage` with the `c:` cast — display a single character
