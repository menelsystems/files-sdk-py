"""Port of Effect.js's `Hash.string` and UploadThing's `shuffle` helper.

The UploadThing ingest server reconstructs the appId from the first ~12 chars
of the `fileKey` by SQId-decoding with a deterministically-shuffled alphabet,
where the shuffle seed is `Hash.string(appId)`. To produce a fileKey the
server will accept, we must compute `Hash.string` identically to Effect.js's
implementation — which uses JS int32 semantics throughout.

Source: https://github.com/Effect-TS/effect/blob/main/packages/effect/src/Hash.ts
"""

from __future__ import annotations

import math


def _to_int32(x: int) -> int:
    """Coerce a Python int into the int32 range, matching JS bitwise semantics."""
    x &= 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x


def _optimize(n: int) -> int:
    """Port of Effect's `optimize`: ``(n & 0xbfffffff) | ((n >>> 1) & 0x40000000)``."""
    u = n & 0xFFFFFFFF
    return _to_int32((n & 0xBFFFFFFF) | ((u >> 1) & 0x40000000))


def effect_hash_string(s: str) -> int:
    """JS-equivalent `Hash.string(s)`.

    DJB2 variant: ``h = 5381; while i: h = (h * 33) ^ charCodeAt(--i)``.
    The loop walks the string in reverse, matching upstream.
    """
    h = 5381
    i = len(s)
    while i > 0:
        i -= 1
        h = _to_int32(_to_int32(h * 33) ^ ord(s[i]))
    return _optimize(h)


def _js_mod(a: int, b: int) -> int:
    """JS `%` keeps the sign of the dividend; Python's keeps the sign of the divisor."""
    return int(math.fmod(a, b))


def shuffle(s: str, seed: str) -> str:
    """Port of UploadThing's deterministic Fisher-Yates-ish shuffle.

    Source: ``packages/uploadthing/src/sdk/utils.ts``::

        for (let i = 0; i < chars.length; i++) {
          j = ((seedNum % (i + 1)) + i) % chars.length;
          [chars[i], chars[j]] = [chars[j], chars[i]];
        }
    """
    chars = list(s)
    seed_num = effect_hash_string(seed)
    n = len(chars)
    for i in range(n):
        j = _js_mod(_js_mod(seed_num, i + 1) + i, n)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


__all__ = ["effect_hash_string", "shuffle"]
