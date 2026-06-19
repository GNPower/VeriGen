"""Tests for values-config validation and normalization."""

import pytest

from verigen.core.definition import GeneratorDefinition
from verigen.core.errors import ValidationError
from verigen.core.values import default_values, normalize_values


def _defn(elements, outputs=None):
    return GeneratorDefinition.model_validate(
        {
            "id": "t",
            "name": "T",
            "pages": [{"title": "p", "elements": elements}],
            "outputs": outputs or [{"template": "t.j2", "destination": "x"}],
        }
    )


def test_required_value_missing():
    defn = _defn([{"type": "integer", "id": "w", "min": 1, "max": 8}])
    with pytest.raises(ValidationError):
        normalize_values(defn, {})


def test_integer_out_of_range():
    defn = _defn([{"type": "integer", "id": "w", "min": 1, "max": 8}])
    with pytest.raises(ValidationError):
        normalize_values(defn, {"w": 99})


def test_integer_in_range_and_coerced():
    defn = _defn([{"type": "integer", "id": "w", "min": 1, "max": 8}])
    assert normalize_values(defn, {"w": "4"}) == {"w": 4}


def test_choice_rejects_invalid():
    defn = _defn([{"type": "choice", "id": "m", "options": ["a", "b"]}])
    with pytest.raises(ValidationError):
        normalize_values(defn, {"m": "c"})


def test_choice_int_options_coerced():
    defn = _defn([{"type": "choice", "id": "m", "options": [0, 1], "default": 0}])
    assert normalize_values(defn, {"m": "1"}) == {"m": 1}


def test_boolean_coercion():
    defn = _defn([{"type": "boolean", "id": "b"}])
    assert normalize_values(defn, {"b": "true"})["b"] is True
    assert normalize_values(defn, {})["b"] is False  # default


def test_unknown_key_rejected():
    defn = _defn([{"type": "integer", "id": "w", "default": 1, "min": 1, "max": 8}])
    with pytest.raises(ValidationError):
        normalize_values(defn, {"w": 4, "bogus": 1})


def test_table_validation():
    defn = _defn(
        [
            {
                "type": "dynamic_table",
                "id": "rows",
                "sub_elements": [{"type": "string", "id": "name"}],
            }
        ]
    )
    out = normalize_values(defn, {"rows": [{"name": "a"}, {"name": "b"}]})
    assert out == {"rows": [{"name": "a"}, {"name": "b"}]}
    # Missing table -> empty list.
    assert normalize_values(defn, {}) == {"rows": []}
    # Unknown column -> error.
    with pytest.raises(ValidationError):
        normalize_values(defn, {"rows": [{"name": "a", "extra": 1}]})


def test_errors_are_aggregated():
    defn = _defn(
        [
            {"type": "integer", "id": "w", "min": 1, "max": 8},
            {"type": "choice", "id": "m", "options": ["a", "b"]},
        ]
    )
    with pytest.raises(ValidationError) as exc:
        normalize_values(defn, {"w": 99, "m": "c"})
    assert len(exc.value.errors) >= 2


def test_float_validation_and_coercion():
    defn = _defn([{"type": "float", "id": "f", "min": 0.0, "max": 10.0, "default": 1.0}])
    assert normalize_values(defn, {"f": "2.5"}) == {"f": 2.5}
    with pytest.raises(ValidationError):
        normalize_values(defn, {"f": 99.0})


def test_integer_accepts_integral_float():
    defn = _defn([{"type": "integer", "id": "w", "min": 1, "max": 100}])
    assert normalize_values(defn, {"w": 8.0}) == {"w": 8}
    with pytest.raises(ValidationError):
        normalize_values(defn, {"w": 8.5})


def test_text_passthrough():
    defn = _defn([{"type": "text", "id": "d", "default": ""}])
    assert normalize_values(defn, {"d": "multi\nline"}) == {"d": "multi\nline"}


def test_default_values():
    defn = _defn(
        [
            {"type": "integer", "id": "w", "default": 5, "min": 1, "max": 8},
            {"type": "boolean", "id": "b", "default": True},
        ]
    )
    assert default_values(defn) == {"w": 5, "b": True}
