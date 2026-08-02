# GetChar

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki, verified against Zandronum 3.3-alpha source (p_acs.cpp, case ACSF_GetChar)
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

```c
GetChar("hello", 0)  // returns 'h' (104)
GetChar("hello", 4)  // returns 'o' (111)
GetChar("hello", 5)  // returns 0 (out of bounds)
GetChar("hello", -1) // returns 0 (negative index)
```

The character can be cast to `c` in HudMessage context:
```c
HudMessage(c:GetChar("abc", 0); HUDMSG_PLAIN, 0, CR_WHITE, 160, 100, 1.0);
```

## Related

- `StrLen` — get the length of a string
- `GetSubString` — extract a substring
- `MidPrint`/`HudMessage` with the `c:` cast — display a single character
