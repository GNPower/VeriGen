"""Tests for the built-in generic filter library."""

import pytest

from verigen.filters import hdl, text


@pytest.mark.parametrize(
    "value,expected",
    [("Some Value", "some_value"), ("someValue", "some_value"), ("HTTPServer", "http_server")],
)
def test_snake_case(value, expected):
    assert text.snake_case(value) == expected


def test_case_conversions():
    assert text.camel_case("some value") == "someValue"
    assert text.pascal_case("some value") == "SomeValue"
    assert text.upper_case("some value") == "SOME_VALUE"
    assert text.kebab_case("Some Value") == "some-value"


def test_comment_block():
    assert text.comment_block("a\nb", "// ") == "// a\n// b"


@pytest.mark.parametrize("n,expected", [(1, 0), (2, 1), (4, 2), (5, 3), (8, 3), (64, 6)])
def test_clog2(n, expected):
    assert hdl.clog2(n) == expected


def test_number_filters():
    assert hdl.mask(8) == 0xFF
    assert hdl.to_hex(255, 4) == "00FF"
    assert hdl.to_bin(5, 4) == "0101"
    assert hdl.sv_hex(15, 8) == "8'h0F"
    assert hdl.bits(7, 0) == "[7:0]"
    assert hdl.bits(3) == "[3]"


def test_hdl_accepts_hex_strings():
    assert hdl.clog2("0x10") == 4
    assert hdl.to_hex("0xff") == "FF"
