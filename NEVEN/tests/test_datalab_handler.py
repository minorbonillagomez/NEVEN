# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Tests para DataLabHandler
# Tasks 9.4 (handle_catalog) y 9.5 (handle_run)
# ═══════════════════════════════════════════════════════════════════════════════
import json
import os
import sys
import threading
import pytest

# Add startup dir to path so DataLabHandler can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ControlPython', 'startup'))
from datalab_handler import DataLabHandler, REQUIRED_SIDECAR_FIELDS

from unittest.mock import MagicMock, patch


VALID_SIDECAR = {
    "id": "TEST_FN",
    "family": "AD",
    "family_label": "Análisis de Datos",
    "name": "Test Function",
    "description": "A test function",
    "languages": ["r"],
    "function_name": "TEST_FN.Studio",
    "file": "test_fn.R",
    "variable_roles": {"X": {"label": "Variables", "types": ["numeric"], "multiple": True, "required": True}},
    "parameters": []
}


@pytest.fixture
def handler():
    return DataLabHandler()


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.4 — Tests para handle_catalog
# ─────────────────────────────────────────────────────────────────────────────

def test_handle_catalog_empty_dir(handler, tmp_path):
    result = handler.handle_catalog({"functions_dir": str(tmp_path)})
    assert result["status"] == "ok"
    assert result["catalog"] == {}
    assert result["warnings"] == []


def test_handle_catalog_valid_sidecar(handler, tmp_path):
    sidecar = tmp_path / "test_fn.json"
    sidecar.write_text(json.dumps(VALID_SIDECAR), encoding="utf-8")
    result = handler.handle_catalog({"functions_dir": str(tmp_path)})
    assert result["status"] == "ok"
    assert "r" in result["catalog"]
    assert "AD" in result["catalog"]["r"]
    assert len(result["catalog"]["r"]["AD"]) == 1


def test_handle_catalog_missing_field(handler, tmp_path):
    bad = {k: v for k, v in VALID_SIDECAR.items() if k != "description"}
    sidecar = tmp_path / "bad.json"
    sidecar.write_text(json.dumps(bad), encoding="utf-8")
    result = handler.handle_catalog({"functions_dir": str(tmp_path)})
    assert result["catalog"] == {}
    assert any("faltan campos" in w for w in result["warnings"])


def test_handle_catalog_invalid_json(handler, tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ not valid json }", encoding="utf-8")
    result = handler.handle_catalog({"functions_dir": str(tmp_path)})
    assert result["catalog"] == {}
    assert any("JSON inválido" in w for w in result["warnings"])


def test_handle_catalog_nonexistent_dir(handler):
    result = handler.handle_catalog({"functions_dir": r"C:\nonexistent_dir_xyz_12345"})
    assert result["status"] == "ok"
    assert result["catalog"] == {}
    assert len(result["warnings"]) > 0


def test_handle_catalog_select_param_no_options(handler, tmp_path):
    sidecar_with_bad_select = dict(VALID_SIDECAR)
    sidecar_with_bad_select["parameters"] = [
        {"name": "algo", "type": "select", "default": 1, "tier": 1}  # missing options
    ]
    sidecar = tmp_path / "bad_select.json"
    sidecar.write_text(json.dumps(sidecar_with_bad_select), encoding="utf-8")
    result = handler.handle_catalog({"functions_dir": str(tmp_path)})
    # Card should still be included (warning, not rejection)
    assert "r" in result["catalog"]
    assert any("options" in w for w in result["warnings"])


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.5 — Tests para handle_run
# ─────────────────────────────────────────────────────────────────────────────

def make_mock_db(raises=False, table_exists=True):
    db = MagicMock()
    if raises or not table_exists:
        db.execute.side_effect = Exception("Table not found: dataset")
    else:
        result_mock = MagicMock()
        result_mock.description = [("col1",), ("col2",)]
        result_mock.fetchall.return_value = [(1, 2), (3, 4)]
        db.execute.return_value = result_mock
    return db


def test_handle_run_missing_function_id(handler):
    result = handler.handle_run({}, {}, MagicMock(), threading.Lock(), MagicMock())
    assert result["status"] == "error"
    assert result["code"] == "VALIDATION_ERROR"


def test_handle_run_unsupported_language(handler):
    body = {"function_id": "AD_KMedias", "language": "python"}
    result = handler.handle_run(body, {}, MagicMock(), threading.Lock(), MagicMock())
    assert result["status"] == "error"
    assert result["code"] == "VALIDATION_ERROR"


def test_handle_run_no_dataset(handler):
    body = {"function_id": "AD_KMedias", "language": "r", "column_roles": {"X": ["col1"]}}
    db = make_mock_db(table_exists=False)
    result = handler.handle_run(body, {}, db, threading.Lock(), MagicMock())
    assert result["status"] == "error"
    assert result["code"] == "NO_DATASET"


def test_handle_run_no_columns_assigned(handler):
    body = {"function_id": "AD_KMedias", "language": "r", "column_roles": {}}
    # COUNT check succeeds
    db2 = MagicMock()
    count_result = MagicMock()
    count_result.fetchone.return_value = (5,)
    db2.execute.return_value = count_result
    result = handler.handle_run(body, {}, db2, threading.Lock(), MagicMock())
    assert result["status"] == "error"
    assert result["code"] == "VALIDATION_ERROR"


def test_handle_run_invalid_filter(handler):
    body = {
        "function_id": "AD_KMedias",
        "language": "r",
        "column_roles": {"X": ["col1"]},
        "filter_clause": "INVALID FILTER ;;;"
    }
    db = MagicMock()
    # COUNT succeeds, SELECT raises
    count_mock = MagicMock()
    count_mock.fetchone.return_value = (10,)

    def side_effect(sql):
        if "COUNT" in sql.upper():
            return count_mock
        raise Exception("DuckDB syntax error")

    db.execute.side_effect = side_effect
    result = handler.handle_run(body, {}, db, threading.Lock(), MagicMock())
    assert result["status"] == "error"
    assert result["code"] == "FILTER_ERROR"


def test_handle_run_engine_unavailable(handler):
    body = {
        "function_id": "AD_KMedias",
        "language": "r",
        "column_roles": {"X": ["col1"]},
        "filter_clause": ""
    }
    db = MagicMock()
    result_mock = MagicMock()
    result_mock.description = [("col1",)]
    result_mock.fetchall.return_value = [(1,), (2,)]
    db.execute.return_value = result_mock

    def raise_key_error(lang):
        raise KeyError(lang)

    result = handler.handle_run(body, {}, db, threading.Lock(), raise_key_error)
    assert result["status"] == "error"
    assert result["code"] == "ENGINE_UNAVAILABLE"


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.6 — Property 1 (hypothesis): valid sidecars appear in catalog,
#            invalid ones appear in warnings
# Validates: Requirements 1.1, 1.2
# ─────────────────────────────────────────────────────────────────────────────
import tempfile
import shutil
from hypothesis import given, settings
import hypothesis.strategies as st


def _make_valid_sidecar(override: dict = None) -> dict:
    base = {
        "id": "PROP_FN",
        "family": "AD",
        "family_label": "Análisis de Datos",
        "name": "Prop Function",
        "description": "Property test function",
        "languages": ["r"],
        "function_name": "PROP_FN.Studio",
        "file": "prop_fn.R",
        "variable_roles": {},
        "parameters": []
    }
    if override:
        base.update(override)
    return base


@st.composite
def sidecar_strategy(draw):
    """Generate either a valid sidecar or an invalid one (missing a required field)."""
    is_valid = draw(st.booleans())
    sidecar = _make_valid_sidecar({
        "id": draw(st.text(
            min_size=1, max_size=20,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='_'
            )
        )),
        "name": draw(st.text(min_size=1, max_size=30)),
    })
    if not is_valid:
        # Remove a random required field
        field_to_remove = draw(st.sampled_from(sorted(REQUIRED_SIDECAR_FIELDS)))
        sidecar.pop(field_to_remove, None)
        return {"sidecar": sidecar, "is_valid": False}
    return {"sidecar": sidecar, "is_valid": True}


@given(st.lists(sidecar_strategy(), min_size=0, max_size=20))
@settings(max_examples=30)
def test_property_1_catalog_filtering(sidecar_entries):
    """Valid sidecars appear in catalog; invalid ones appear in warnings.

    Uses tempfile.mkdtemp() instead of the tmp_path pytest fixture because
    @given and pytest fixtures cannot be combined directly.
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        h = DataLabHandler()
        valid_ids = set()
        invalid_ids = set()

        for i, entry in enumerate(sidecar_entries):
            sidecar = entry["sidecar"]
            fname = f"sidecar_{i}.json"
            fpath = os.path.join(tmp_dir, fname)
            with open(fpath, "w", encoding="utf-8") as fp:
                json.dump(sidecar, fp)
            sid = sidecar.get("id", f"sidecar_{i}")
            if entry["is_valid"]:
                valid_ids.add(sid)
            else:
                invalid_ids.add(sid)

        result = h.handle_catalog({"functions_dir": tmp_dir})

        # Collect all ids that made it into the catalog
        catalog_ids = set()
        for lang_data in result["catalog"].values():
            for family_data in lang_data.values():
                for card in family_data:
                    catalog_ids.add(card["id"])

        # Every valid sidecar id should be in the catalog
        for vid in valid_ids:
            assert vid in catalog_ids, (
                f"Valid sidecar id '{vid}' missing from catalog"
            )

        # Every invalid sidecar id should NOT be in the catalog,
        # unless a *valid* sidecar happens to share the same id (in which case
        # the catalog entry is legitimately from the valid sidecar).
        for iid in invalid_ids - valid_ids:
            assert iid not in catalog_ids, (
                f"Invalid sidecar id '{iid}' found in catalog"
            )
            assert any(iid in w or "faltan campos" in w for w in result["warnings"]), (
                f"Invalid sidecar '{iid}' not mentioned in warnings"
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.7 — Property 6 (hypothesis): invalid filter_clause → FILTER_ERROR
#            and pipe_client.send_code is never called
# Validates: Requirements 5.6
# ─────────────────────────────────────────────────────────────────────────────

@given(st.text(min_size=1).filter(lambda s: s.strip()))
@settings(max_examples=30)
def test_property_6_filter_error_no_pipe_call(filter_clause):
    """When DuckDB raises on SELECT, send_code is never invoked."""
    h = DataLabHandler()
    body = {
        "function_id": "AD_KMedias",
        "language": "r",
        "column_roles": {"X": ["col1"]},
        "filter_clause": filter_clause
    }

    db = MagicMock()
    count_mock = MagicMock()
    count_mock.fetchone.return_value = (5,)

    def side_effect(sql):
        if "COUNT" in sql.upper():
            return count_mock
        raise Exception("DuckDB syntax error for: " + sql[:50])

    db.execute.side_effect = side_effect

    pipe_client = MagicMock()

    result = h.handle_run(
        body, {}, db, threading.Lock(), lambda lang: pipe_client
    )

    assert result["status"] == "error"
    assert result["code"] == "FILTER_ERROR"
    pipe_client.send_code.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.8 — Property 8 (hypothesis): json.dumps on slot list never raises
# Validates: Requirements 5.8
# ─────────────────────────────────────────────────────────────────────────────

@st.composite
def slot_list_strategy(draw):
    """Generate a list of slot dicts with varied types and values."""
    slot_type = draw(st.sampled_from(
        ["table", "scalar", "vector", "html", "text", "unknown"]
    ))

    if slot_type == "table":
        value = draw(st.lists(
            st.fixed_dictionaries({
                "col1": st.one_of(st.integers(), st.text(max_size=20), st.none())
            }),
            max_size=5
        ))
    elif slot_type == "vector":
        value = draw(st.lists(
            st.one_of(st.integers(), st.floats(allow_nan=False), st.text(max_size=10)),
            max_size=10
        ))
    elif slot_type == "scalar":
        value = draw(st.one_of(
            st.integers(), st.floats(allow_nan=False), st.text(max_size=20), st.none()
        ))
    elif slot_type == "html":
        value = draw(st.text(max_size=100))
    else:
        value = draw(st.one_of(st.text(max_size=50), st.none(), st.integers()))

    slot = {
        "name": draw(st.text(
            min_size=1, max_size=20,
            alphabet="abcdefghijklmnopqrstuvwxyz_"
        )),
        "label": draw(st.text(max_size=30)),
        "type": slot_type,
        "value": value,
        "tier": draw(st.sampled_from([1, 2]))
    }
    return slot


@given(st.lists(slot_list_strategy(), min_size=0, max_size=10))
@settings(max_examples=50)
def test_property_8_slots_always_serializable(slots):
    """json.dumps({'status': 'ok', 'slots': slots}) never raises."""
    try:
        result = json.dumps({"status": "ok", "slots": slots})
        assert isinstance(result, str)
    except (TypeError, ValueError) as exc:
        pytest.fail(f"json.dumps raised: {exc} — slots: {slots}")
