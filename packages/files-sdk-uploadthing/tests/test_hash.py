"""Tests for the Effect.js Hash.string + shuffle ports."""

from __future__ import annotations

import pytest
from files_sdk_uploadthing._hash import effect_hash_string, shuffle


# ---- Hash.string --------------------------------------------------------
# Reference values were computed by running the actual Effect.js Hash.string
# in Node — these lock the port byte-for-byte.


def test_effect_hash_string_empty_returns_optimized_seed() -> None:
    # Empty string never enters the loop → h stays 5381 → optimize(5381) = 5381.
    assert effect_hash_string("") == 5381


def test_effect_hash_string_single_char() -> None:
    # h = 5381; i=0: h = (5381*33) ^ 97 = 177573 ^ 97 = 177604.
    # optimize(177604) = 177604 (positive, no bit 30/31 set).
    assert effect_hash_string("a") == 177604


def test_effect_hash_string_is_deterministic() -> None:
    assert effect_hash_string("hello") == effect_hash_string("hello")


def test_effect_hash_string_differs_for_permutations() -> None:
    # DJB2 is permutation-sensitive
    assert effect_hash_string("abc") != effect_hash_string("cba")


def test_effect_hash_string_returns_int32_signed() -> None:
    # `optimize` returns int32; some inputs hash to negative numbers
    out = effect_hash_string("uploadthing")
    assert -(2**31) <= out < 2**31


# ---- shuffle ------------------------------------------------------------


def test_shuffle_preserves_chars() -> None:
    src = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    shuffled = shuffle(src, "seed")
    assert sorted(shuffled) == sorted(src)
    assert len(shuffled) == len(src)


def test_shuffle_is_deterministic() -> None:
    src = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    assert shuffle(src, "myapp") == shuffle(src, "myapp")


def test_shuffle_varies_by_seed() -> None:
    src = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    assert shuffle(src, "app1") != shuffle(src, "app2")
