"""Property-based tests for pipe_client.py.

Each test corresponds to a numbered Correctness Property in the design document.

**Validates: Requirements 2.5, 3.5, 3.6, 3.7**
"""

from __future__ import annotations

import sys
import os

# Ensure variable_pb2 can be found from production path
sys.path.insert(0, r"C:\NEVEN\taskpane")

# Add TaskPane to path so pipe_client is importable
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _TASKPANE)

import variable_pb2  # type: ignore[import]
from pipe_client import variable_to_python  # noqa: E402

import pytest
from hypothesis import given, settings, strategies as st


# ---------------------------------------------------------------------------
# Strategy helpers
# ---------------------------------------------------------------------------

@st.composite
def variable_strategy(draw: st.DrawFn) -> variable_pb2.Variable:
    """Build a Variable protobuf message for any scalar oneof.

    Draws uniformly from the five scalar oneofs:
      integer, real, str, boolean, nil
    """
    var = variable_pb2.Variable()
    oneof = draw(st.sampled_from(["integer", "real", "str", "boolean", "nil"]))

    if oneof == "integer":
        # Protobuf int32: −2^31 to 2^31 − 1
        var.integer = draw(st.integers(min_value=-(2**31), max_value=2**31 - 1))
    elif oneof == "real":
        var.real = draw(st.floats(
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=True,
        ))
    elif oneof == "str":
        var.str = draw(st.text(max_size=1000))
    elif oneof == "boolean":
        var.boolean = draw(st.booleans())
    else:  # nil
        var.nil = True

    return var


# ---------------------------------------------------------------------------
# Property 5: Variable-to-Python mapping is correct for all scalar types
#
# Validates: Requirements 2.5, 3.5, 3.6, 3.7
# ---------------------------------------------------------------------------

@given(var=variable_strategy())
@settings(max_examples=200)
def test_variable_to_python_mapping(var: variable_pb2.Variable) -> None:
    """**Validates: Requirements 2.5, 3.5, 3.6, 3.7**

    For any Variable whose oneof is one of the five scalar types, calling
    variable_to_python() must return the correct Python type and value:

    * integer  → isinstance(result, int)   and result == var.integer
    * real     → isinstance(result, float) and result == var.real
    * str      → isinstance(result, str)   and result == var.str
    * boolean  → isinstance(result, bool)  and result == var.boolean
    * nil      → result is None
    """
    which = var.WhichOneof("value")
    result = variable_to_python(var)

    if which == "integer":
        assert isinstance(result, int), (
            f"Expected int for integer oneof, got {type(result).__name__}"
        )
        assert result == var.integer, (
            f"Value mismatch: {result!r} != {var.integer!r}"
        )

    elif which == "real":
        assert isinstance(result, float), (
            f"Expected float for real oneof, got {type(result).__name__}"
        )
        assert result == var.real, (
            f"Value mismatch: {result!r} != {var.real!r}"
        )

    elif which == "str":
        assert isinstance(result, str), (
            f"Expected str for str oneof, got {type(result).__name__}"
        )
        assert result == var.str, (
            f"Value mismatch: {result!r} != {var.str!r}"
        )

    elif which == "boolean":
        assert isinstance(result, bool), (
            f"Expected bool for boolean oneof, got {type(result).__name__}"
        )
        assert result == var.boolean, (
            f"Value mismatch: {result!r} != {var.boolean!r}"
        )

    elif which == "nil":
        assert result is None, (
            f"Expected None for nil oneof, got {result!r}"
        )

    else:
        pytest.fail(f"variable_strategy() produced unexpected oneof: {which!r}")
