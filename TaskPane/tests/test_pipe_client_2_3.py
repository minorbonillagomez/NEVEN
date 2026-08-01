"""Tests for task 2.3: variable_to_python — Variable → Python type conversion helper.

Requirements: 2.5, 3.5, 3.6, 3.7

Covers all Variable oneof branches:
  integer, real, str, boolean, nil, missing, arr, html_content, err,
  and the unset/unrecognised fallback.
"""

from __future__ import annotations

import sys
import os
import unittest

# Ensure variable_pb2 can be found from production path
sys.path.insert(0, r"C:\NEVEN\taskpane")

# Add TaskPane to path so pipe_client is importable
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _TASKPANE)

import variable_pb2  # type: ignore[import]
from pipe_client import (  # noqa: E402
    PipeClientError,
    variable_to_python,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_integer(value: int) -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.integer = value
    return v


def make_real(value: float) -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.real = value
    return v


def make_str(value: str) -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.str = value
    return v


def make_boolean(value: bool) -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.boolean = value
    return v


def make_nil() -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.nil = True
    return v


def make_missing() -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.missing = True
    return v


def make_err(message: str) -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.err.message = message
    return v


def make_html_content(html: str, title: str) -> variable_pb2.Variable:
    v = variable_pb2.Variable()
    v.html_content.html = html
    v.html_content.title = title
    return v


def make_arr(colnames: list[str], rows_data: list[list]) -> variable_pb2.Variable:
    """Build a Variable with an Array whose data is row-major.

    Parameters
    ----------
    colnames:
        Column names.
    rows_data:
        A list of rows; each row is a list of Python scalars.
        Scalars must be int, float, str, bool, or None.
    """
    v = variable_pb2.Variable()
    arr = v.arr
    num_rows = len(rows_data)
    num_cols = len(colnames)
    arr.rows = num_rows
    arr.cols = num_cols
    arr.colnames.extend(colnames)

    # Flatten row-major and convert each cell to a Variable
    for row in rows_data:
        for cell in row:
            cell_var = arr.data.add()
            if cell is None:
                cell_var.nil = True
            elif isinstance(cell, bool):
                cell_var.boolean = cell
            elif isinstance(cell, int):
                cell_var.integer = cell
            elif isinstance(cell, float):
                cell_var.real = cell
            elif isinstance(cell, str):
                cell_var.str = cell

    return v


# ---------------------------------------------------------------------------
# 1. Scalar types
# ---------------------------------------------------------------------------

class TestScalarConversions(unittest.TestCase):
    def test_integer_returns_int(self):
        result = variable_to_python(make_integer(42))
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)

    def test_integer_negative(self):
        result = variable_to_python(make_integer(-7))
        self.assertEqual(result, -7)

    def test_integer_zero(self):
        result = variable_to_python(make_integer(0))
        self.assertEqual(result, 0)

    def test_real_returns_float(self):
        result = variable_to_python(make_real(3.14))
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, 3.14, places=10)

    def test_real_negative(self):
        result = variable_to_python(make_real(-2.718))
        self.assertAlmostEqual(result, -2.718, places=10)

    def test_real_zero(self):
        result = variable_to_python(make_real(0.0))
        self.assertEqual(result, 0.0)

    def test_str_returns_str(self):
        result = variable_to_python(make_str("hello"))
        self.assertIsInstance(result, str)
        self.assertEqual(result, "hello")

    def test_str_empty(self):
        result = variable_to_python(make_str(""))
        self.assertEqual(result, "")

    def test_str_unicode(self):
        result = variable_to_python(make_str("héllo wörld"))
        self.assertEqual(result, "héllo wörld")

    def test_boolean_true(self):
        result = variable_to_python(make_boolean(True))
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

    def test_boolean_false(self):
        result = variable_to_python(make_boolean(False))
        self.assertIsInstance(result, bool)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# 2. Nil / Missing → None
# ---------------------------------------------------------------------------

class TestNilMissing(unittest.TestCase):
    def test_nil_returns_none(self):
        result = variable_to_python(make_nil())
        self.assertIsNone(result)

    def test_missing_returns_none(self):
        result = variable_to_python(make_missing())
        self.assertIsNone(result)

    def test_unset_oneof_returns_none(self):
        """A Variable with no oneof set has WhichOneof == None; should return None."""
        v = variable_pb2.Variable()
        result = variable_to_python(v)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 3. err → PipeClientError
# ---------------------------------------------------------------------------

class TestErrRaisesPipeClientError(unittest.TestCase):
    def test_err_raises_pipe_client_error(self):
        with self.assertRaises(PipeClientError):
            variable_to_python(make_err("something went wrong"))

    def test_err_message_propagated(self):
        msg = "division by zero in R"
        with self.assertRaises(PipeClientError) as ctx:
            variable_to_python(make_err(msg))
        self.assertIn(msg, str(ctx.exception))

    def test_err_empty_message(self):
        with self.assertRaises(PipeClientError):
            variable_to_python(make_err(""))


# ---------------------------------------------------------------------------
# 4. arr → dict(columns, rows)
# ---------------------------------------------------------------------------

class TestArrConversion(unittest.TestCase):
    def test_arr_returns_dict_with_correct_keys(self):
        result = variable_to_python(make_arr(["a", "b"], [[1, 2], [3, 4]]))
        self.assertIsInstance(result, dict)
        self.assertIn("columns", result)
        self.assertIn("rows", result)

    def test_arr_columns_list(self):
        result = variable_to_python(make_arr(["x", "y", "z"], [[1, 2, 3]]))
        self.assertEqual(result["columns"], ["x", "y", "z"])

    def test_arr_rows_structure(self):
        result = variable_to_python(make_arr(["a", "b"], [[1, 2], [3, 4]]))
        self.assertEqual(result["rows"], [[1, 2], [3, 4]])

    def test_arr_single_row(self):
        result = variable_to_python(make_arr(["col1"], [[42]]))
        self.assertEqual(result["columns"], ["col1"])
        self.assertEqual(result["rows"], [[42]])

    def test_arr_mixed_types(self):
        """Array with int, float, str, bool cells."""
        result = variable_to_python(
            make_arr(["int_col", "float_col", "str_col", "bool_col"],
                     [[1, 2.5, "text", True]])
        )
        self.assertEqual(result["rows"][0][0], 1)
        self.assertAlmostEqual(result["rows"][0][1], 2.5)
        self.assertEqual(result["rows"][0][2], "text")
        self.assertEqual(result["rows"][0][3], True)

    def test_arr_empty_data(self):
        """Array with 0 rows should produce empty rows list."""
        v = variable_pb2.Variable()
        v.arr.rows = 0
        v.arr.cols = 0
        result = variable_to_python(v)
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["columns"], [])

    def test_arr_row_major_order(self):
        """Flat data is stored row-major: first all cells of row 0, then row 1, ..."""
        result = variable_to_python(
            make_arr(["A", "B", "C"], [[10, 20, 30], [40, 50, 60]])
        )
        self.assertEqual(result["rows"][0], [10, 20, 30])
        self.assertEqual(result["rows"][1], [40, 50, 60])


# ---------------------------------------------------------------------------
# 5. html_content → dict(html, title)
# ---------------------------------------------------------------------------

class TestHtmlContentConversion(unittest.TestCase):
    def test_html_content_returns_dict_with_correct_keys(self):
        result = variable_to_python(make_html_content("<html/>", "My Title"))
        self.assertIsInstance(result, dict)
        self.assertIn("html", result)
        self.assertIn("title", result)

    def test_html_content_html_field(self):
        html = "<html><body><p>Hello</p></body></html>"
        result = variable_to_python(make_html_content(html, "Test"))
        self.assertEqual(result["html"], html)

    def test_html_content_title_field(self):
        result = variable_to_python(make_html_content("<div/>", "RPivot Chart"))
        self.assertEqual(result["title"], "RPivot Chart")

    def test_html_content_empty_strings(self):
        result = variable_to_python(make_html_content("", ""))
        self.assertEqual(result["html"], "")
        self.assertEqual(result["title"], "")

    def test_html_content_does_not_include_extra_keys(self):
        """The dict should only contain 'html' and 'title' from the Variable payload."""
        result = variable_to_python(make_html_content("<b>bold</b>", "bold"))
        # source_language and mime_type from HtmlContent are intentionally excluded
        self.assertEqual(set(result.keys()), {"html", "title"})


# ---------------------------------------------------------------------------
# 6. Return type consistency
# ---------------------------------------------------------------------------

class TestReturnTypeConsistency(unittest.TestCase):
    def test_integer_type_is_int_not_float(self):
        result = variable_to_python(make_integer(5))
        self.assertNotIsInstance(result, float)
        self.assertIsInstance(result, int)

    def test_real_type_is_float(self):
        result = variable_to_python(make_real(5.0))
        self.assertIsInstance(result, float)

    def test_boolean_type_is_bool(self):
        result = variable_to_python(make_boolean(True))
        self.assertIsInstance(result, bool)

    def test_arr_type_is_dict(self):
        result = variable_to_python(make_arr(["c"], [[1]]))
        self.assertIsInstance(result, dict)

    def test_html_content_type_is_dict(self):
        result = variable_to_python(make_html_content("<p/>", "t"))
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
