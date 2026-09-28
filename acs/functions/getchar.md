# GetChar

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-24)
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=GetChar&oldid=35766, retrieved 2026-08-06), verified against Zandronum source (p_acs.cpp, case ACSF_GetChar)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (ACSF_GetChar, index -15)

**Signature:** `int GetChar(str string, int index)`

## Summary

Returns the byte at a given index in a string, promoted from `char` to `int`, or 0 on error.

## Behavior

The function looks up the string by its handle (`string`) and returns the byte at the zero-based `index` position. If any of these conditions hold, it silently returns `0`:
- The `string` handle is invalid (lookup fails, resolves to NULL)
- The `index` is negative
- The `index` is >= the string length

The three error conditions above are indistinguishable from each other. They are not indistinguishable from a valid character, though. Since `index` is bounded by the string's length as measured by `strlen`, an in-range index can never land on a null byte. So `0` unambiguously signals one of the three error conditions. There is no Unicode decoding involved: the value returned for a valid index is the raw `char` at that position, promoted to `int`, not a decoded codepoint. A multibyte UTF-8 character yields one raw byte per index. On platforms where `char` is signed, which is true of the compilers Zandronum ships on, byte values `0x80`-`0xFF` come back as negative integers.

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
