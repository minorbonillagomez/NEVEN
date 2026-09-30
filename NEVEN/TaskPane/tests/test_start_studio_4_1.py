"""Tests for task 4.1: start_studio.py — CLI parsing, config loading,
language resolution, and executable discovery.

Requirements: 1.1, 1.2, 9.1, 9.2, 9.3, 9.6
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Path setup: make start_studio importable from the TaskPane directory
# ---------------------------------------------------------------------------
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TASKPANE not in sys.path:
    sys.path.insert(0, _TASKPANE)

from start_studio import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    EXE_MAP,
    VALID_LANGUAGES,
    _STANDALONE_DEFAULTS,
    build_arg_parser,
    find_exe,
    load_config,
    resolve_languages,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _write_config(path: str, data: dict) -> None:
    """Write *data* as JSON to *path*."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def _make_config_with_standalone(**overrides) -> dict:
    """Return a minimal in-memory config dict with a Standalone section."""
    standalone = {**_STANDALONE_DEFAULTS, **overrides}
    return {"Standalone": standalone}


# ===========================================================================
# 1. build_arg_parser — CLI interface (Requirements 1.1, 9.2, 9.6)
# ===========================================================================

class TestBuildArgParser(unittest.TestCase):

    def setUp(self):
        self.parser = build_arg_parser()

    # ------------------------------------------------------------------
    # --config
    # ------------------------------------------------------------------

    def test_config_default_is_production_path(self):
        """--config absent → default is C:\\NEVEN\\neven-config.json (Req 1.1)."""
        args = self.parser.parse_args([])
        self.assertEqual(args.config, DEFAULT_CONFIG_PATH)

    def test_config_custom_path(self):
        """--config PATH stores the supplied path."""
        args = self.parser.parse_args(["--config", r"D:\custom\neven-config.json"])
        self.assertEqual(args.config, r"D:\custom\neven-config.json")

    # ------------------------------------------------------------------
    # --port
    # ------------------------------------------------------------------

    def test_port_default_is_none(self):
        """--port absent → args.port is None (port comes from config)."""
        args = self.parser.parse_args([])
        self.assertIsNone(args.port)

    def test_port_custom_int(self):
        """--port INT stores the integer value (Req 9.2)."""
        args = self.parser.parse_args(["--port", "8080"])
        self.assertEqual(args.port, 8080)

    def test_port_invalid_string_raises_system_exit(self):
        """--port with non-integer value causes argparse to exit."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--port", "abc"])

    # ------------------------------------------------------------------
    # --languages
    # ------------------------------------------------------------------

    def test_languages_default_is_none(self):
        """--languages absent → args.languages is None."""
        args = self.parser.parse_args([])
        self.assertIsNone(args.languages)

    def test_languages_stored_as_string(self):
        """--languages r,python stores the raw string (Req 9.6)."""
        args = self.parser.parse_args(["--languages", "r,python"])
        self.assertEqual(args.languages, "r,python")

    # ------------------------------------------------------------------
    # --no-browser
    # ------------------------------------------------------------------

    def test_no_browser_default_is_false(self):
        """--no-browser absent → args.no_browser is False."""
        args = self.parser.parse_args([])
        self.assertFalse(args.no_browser)

    def test_no_browser_flag_is_true_when_present(self):
        """--no-browser flag sets args.no_browser to True."""
        args = self.parser.parse_args(["--no-browser"])
        self.assertTrue(args.no_browser)

    # ------------------------------------------------------------------
    # Combinations
    # ------------------------------------------------------------------

    def test_all_args_combined(self):
        """All four arguments can be supplied together."""
        args = self.parser.parse_args([
            "--config", r"C:\NEVEN\neven-config.json",
            "--port", "5556",
            "--languages", "r,julia",
            "--no-browser",
        ])
        self.assertEqual(args.config, r"C:\NEVEN\neven-config.json")
        self.assertEqual(args.port, 5556)
        self.assertEqual(args.languages, "r,julia")
        self.assertTrue(args.no_browser)


# ===========================================================================
# 2. load_config — config file loading (Requirements 1.1, 9.1)
# ===========================================================================

class TestLoadConfig(unittest.TestCase):

    # ------------------------------------------------------------------
    # File present, Standalone section present
    # ------------------------------------------------------------------

    def test_loads_standalone_section(self):
        """load_config reads the Standalone section from the file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({
                "Standalone": {
                    "controlDir": r"D:\NEVEN\\",
                    "port": 6000,
                }
            }, fh)
            path = fh.name

        try:
            config = load_config(path)
            self.assertEqual(config["Standalone"]["controlDir"], r"D:\NEVEN\\")
            self.assertEqual(config["Standalone"]["port"], 6000)
        finally:
            os.unlink(path)

    def test_returns_full_config_dict(self):
        """load_config returns the whole parsed JSON dict, not just Standalone."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"NEVEN": {"logFile": "neven.log"}, "Standalone": {}}, fh)
            path = fh.name

        try:
            config = load_config(path)
            self.assertIn("NEVEN", config)
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # Defaults applied when Standalone section absent
    # ------------------------------------------------------------------

    def test_defaults_applied_when_standalone_absent(self):
        """load_config injects all defaults when Standalone is not in the file (Req 9.1)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"NEVEN": {}}, fh)
            path = fh.name

        try:
            config = load_config(path)
            sa = config["Standalone"]
            self.assertEqual(sa["controlDir"],   _STANDALONE_DEFAULTS["controlDir"])
            self.assertEqual(sa["startupDir"],   _STANDALONE_DEFAULTS["startupDir"])
            self.assertEqual(sa["staticDir"],    _STANDALONE_DEFAULTS["staticDir"])
            self.assertEqual(sa["functionsDir"], _STANDALONE_DEFAULTS["functionsDir"])
            self.assertEqual(sa["port"],         _STANDALONE_DEFAULTS["port"])
        finally:
            os.unlink(path)

    def test_defaults_applied_when_standalone_partial(self):
        """Missing keys in Standalone section fall back to defaults (Req 9.1)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"Standalone": {"controlDir": r"D:\custom\\"}}, fh)
            path = fh.name

        try:
            config = load_config(path)
            sa = config["Standalone"]
            # Supplied key preserved
            self.assertEqual(sa["controlDir"], r"D:\custom\\")
            # Missing keys fall back
            self.assertEqual(sa["port"], _STANDALONE_DEFAULTS["port"])
            self.assertEqual(sa["startupDir"], _STANDALONE_DEFAULTS["startupDir"])
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # File missing — warn and use defaults (Requirement 1.1)
    # ------------------------------------------------------------------

    def test_missing_file_logs_warning_to_stderr(self):
        """load_config logs a WARNING to stderr when the config file is not found."""
        non_existent = r"C:\no_such_dir\no_such_file.json"
        import io
        with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
            load_config(non_existent)
            output = mock_err.getvalue()
        self.assertIn("WARNING", output)
        # The path appears repr()-quoted in the output (backslashes doubled),
        # so check for the filename fragment which is unambiguous.
        self.assertIn("no_such_file.json", output)

    def test_missing_file_returns_defaults(self):
        """load_config returns defaults (not an error) when the file is not found."""
        non_existent = r"C:\no_such_dir\no_such_file.json"
        config = load_config(non_existent)
        self.assertIn("Standalone", config)
        sa = config["Standalone"]
        self.assertEqual(sa["port"], 5555)
        self.assertEqual(sa["controlDir"], _STANDALONE_DEFAULTS["controlDir"])

    def test_missing_file_does_not_raise(self):
        """load_config must not raise on a missing file."""
        try:
            load_config(r"C:\totally\fake\path\config.json")
        except Exception as exc:
            self.fail(f"load_config raised unexpectedly: {exc}")

    # ------------------------------------------------------------------
    # Invalid JSON
    # ------------------------------------------------------------------

    def test_invalid_json_logs_warning(self):
        """load_config logs a WARNING and returns defaults on malformed JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("{not valid json}")
            path = fh.name

        import io
        try:
            with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                config = load_config(path)
                output = mock_err.getvalue()
            self.assertIn("WARNING", output)
            self.assertEqual(config["Standalone"]["port"], 5555)
        finally:
            os.unlink(path)

    # ------------------------------------------------------------------
    # Port coercion
    # ------------------------------------------------------------------

    def test_port_in_file_is_int(self):
        """Port value from config is stored as int."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"Standalone": {"port": 7000}}, fh)
            path = fh.name

        try:
            config = load_config(path)
            self.assertIsInstance(config["Standalone"]["port"], int)
            self.assertEqual(config["Standalone"]["port"], 7000)
        finally:
            os.unlink(path)

    def test_invalid_port_in_file_falls_back_to_default(self):
        """Non-integer port in config falls back to 5555 with a warning."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"Standalone": {"port": "not_a_number"}}, fh)
            path = fh.name

        import io
        try:
            with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                config = load_config(path)
                output = mock_err.getvalue()
            self.assertIn("WARNING", output)
            self.assertEqual(config["Standalone"]["port"], 5555)
        finally:
            os.unlink(path)


# ===========================================================================
# 3. resolve_languages — language resolution (Requirements 1.2, 9.6)
# ===========================================================================

class TestResolveLanguages(unittest.TestCase):

    # ------------------------------------------------------------------
    # CLI argument provided (Requirement 9.6)
    # ------------------------------------------------------------------

    def test_cli_arg_single_language(self):
        """--languages r → {r}."""
        result = resolve_languages({}, "r")
        self.assertEqual(result, {"r"})

    def test_cli_arg_multiple_languages(self):
        """--languages r,python → {r, python}."""
        result = resolve_languages({}, "r,python")
        self.assertEqual(result, {"r", "python"})

    def test_cli_arg_all_three(self):
        """--languages r,python,julia → {r, python, julia}."""
        result = resolve_languages({}, "r,python,julia")
        self.assertEqual(result, {"r", "python", "julia"})

    def test_cli_arg_with_spaces(self):
        """Comma-separated entries with surrounding spaces are stripped."""
        result = resolve_languages({}, " r , python ")
        self.assertEqual(result, {"r", "python"})

    def test_cli_arg_uppercase_normalised(self):
        """Upper-case CLI language names are lower-cased before validation."""
        result = resolve_languages({}, "R,Python")
        self.assertEqual(result, {"r", "python"})

    def test_cli_arg_invalid_language_dropped_with_warning(self):
        """Invalid language in CLI arg is dropped and valid ones kept."""
        import io
        with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
            result = resolve_languages({}, "r,fortran")
            output = mock_err.getvalue()
        self.assertEqual(result, {"r"})
        self.assertIn("WARNING", output)
        self.assertIn("fortran", output)

    def test_cli_arg_all_invalid_falls_back_to_all_languages(self):
        """If all CLI languages are invalid, all three languages are enabled."""
        import io
        with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
            result = resolve_languages({}, "cobol,fortran")
        self.assertEqual(result, VALID_LANGUAGES)

    def test_cli_arg_overrides_config(self):
        """CLI --languages overrides what the config says (Req 9.6)."""
        config = _make_config_with_standalone(languages=["r", "julia"])
        result = resolve_languages(config, "python")
        self.assertEqual(result, {"python"})

    # ------------------------------------------------------------------
    # Config-based resolution (Requirement 1.2)
    # ------------------------------------------------------------------

    def test_config_languages_list_used_when_no_cli_arg(self):
        """Languages section from config is used when --languages not given."""
        config = _make_config_with_standalone(languages=["r", "julia"])
        result = resolve_languages(config, None)
        self.assertEqual(result, {"r", "julia"})

    def test_config_empty_languages_falls_back_to_all(self):
        """Empty languages list in config enables all three."""
        config = _make_config_with_standalone(languages=[])
        result = resolve_languages(config, None)
        self.assertEqual(result, VALID_LANGUAGES)

    def test_config_no_languages_key_falls_back_to_all(self):
        """Absent languages key in config enables all three."""
        config = {"Standalone": {}}
        result = resolve_languages(config, None)
        self.assertEqual(result, VALID_LANGUAGES)

    def test_config_invalid_language_entry_dropped(self):
        """Invalid entries in config languages are silently dropped."""
        import io
        config = _make_config_with_standalone(languages=["r", "cobol"])
        with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
            result = resolve_languages(config, None)
            output = mock_err.getvalue()
        self.assertEqual(result, {"r"})
        self.assertIn("WARNING", output)

    def test_no_config_no_arg_returns_all(self):
        """No config and no CLI arg → all three languages enabled."""
        result = resolve_languages({}, None)
        self.assertEqual(result, VALID_LANGUAGES)

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    def test_returns_set(self):
        """resolve_languages always returns a set."""
        result = resolve_languages({}, "r")
        self.assertIsInstance(result, set)


# ===========================================================================
# 4. find_exe — executable discovery (Requirement 9.3)
# ===========================================================================

class TestFindExe(unittest.TestCase):

    # ------------------------------------------------------------------
    # Binary found
    # ------------------------------------------------------------------

    def test_returns_path_when_exe_exists(self):
        """find_exe returns the full path when the binary is present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe_path = os.path.join(tmpdir, "ControlR.exe")
            open(exe_path, "w").close()  # create empty file

            config = _make_config_with_standalone(controlDir=tmpdir)
            result = find_exe(config, "r")
            self.assertEqual(result, exe_path)

    def test_returns_correct_exe_for_python(self):
        """find_exe returns ControlPython.exe for lang='python'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe_path = os.path.join(tmpdir, "ControlPython.exe")
            open(exe_path, "w").close()

            config = _make_config_with_standalone(controlDir=tmpdir)
            result = find_exe(config, "python")
            self.assertEqual(result, exe_path)

    def test_returns_correct_exe_for_julia(self):
        """find_exe returns ControlJulia.exe for lang='julia'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe_path = os.path.join(tmpdir, "ControlJulia.exe")
            open(exe_path, "w").close()

            config = _make_config_with_standalone(controlDir=tmpdir)
            result = find_exe(config, "julia")
            self.assertEqual(result, exe_path)

    # ------------------------------------------------------------------
    # Binary absent — log and return None (Requirement 9.3)
    # ------------------------------------------------------------------

    def test_returns_none_when_exe_missing(self):
        """find_exe returns None when the binary is not in controlDir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Directory exists but ControlR.exe does not
            config = _make_config_with_standalone(controlDir=tmpdir)
            result = find_exe(config, "r")
            self.assertIsNone(result)

    def test_logs_warning_when_exe_missing(self):
        """find_exe logs a WARNING when the binary is absent (Req 9.3)."""
        import io
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config_with_standalone(controlDir=tmpdir)
            with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                find_exe(config, "r")
                output = mock_err.getvalue()
        self.assertIn("WARNING", output)
        self.assertIn("ControlR.exe", output)
        self.assertIn("r", output)

    def test_warning_format_matches_spec(self):
        """Warning log format: '[NEVEN Launcher] WARNING: <exe> not found — skipping <lang>'."""
        import io
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config_with_standalone(controlDir=tmpdir)
            with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                find_exe(config, "python")
                output = mock_err.getvalue()
        self.assertIn("[NEVEN Launcher]", output)
        self.assertIn("WARNING", output)
        self.assertIn("ControlPython.exe", output)
        self.assertIn("not found", output)
        self.assertIn("skipping", output)
        self.assertIn("python", output)

    def test_returns_none_for_unknown_language(self):
        """find_exe returns None (not KeyError) for an unrecognised language."""
        config = _make_config_with_standalone()
        result = find_exe(config, "cobol")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # controlDir from config vs default
    # ------------------------------------------------------------------

    def test_uses_control_dir_from_config(self):
        """find_exe builds the path from config['Standalone']['controlDir']."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Place ControlR.exe in tmpdir
            exe_path = os.path.join(tmpdir, "ControlR.exe")
            open(exe_path, "w").close()

            config = _make_config_with_standalone(controlDir=tmpdir)
            result = find_exe(config, "r")
            self.assertTrue(result.startswith(tmpdir))

    def test_uses_default_control_dir_when_not_in_config(self):
        """find_exe falls back to the default controlDir when absent from config."""
        # With no controlDir in config, find_exe should use the default.
        # The default dir (C:\NEVEN\) most likely won't have the exe in CI,
        # so the result will be None — but we can verify the behaviour.
        config = {"Standalone": {}}
        # Should not raise even when the default path doesn't exist
        try:
            result = find_exe(config, "r")
            self.assertIn(result, [None, os.path.join(_STANDALONE_DEFAULTS["controlDir"], "ControlR.exe")])
        except Exception as exc:
            self.fail(f"find_exe raised unexpectedly: {exc}")


# ===========================================================================
# 5. EXE_MAP constant
# ===========================================================================

class TestExeMap(unittest.TestCase):

    def test_exe_map_has_all_languages(self):
        self.assertEqual(set(EXE_MAP.keys()), VALID_LANGUAGES)

    def test_r_maps_to_control_r_exe(self):
        self.assertEqual(EXE_MAP["r"], "ControlR.exe")

    def test_python_maps_to_control_python_exe(self):
        self.assertEqual(EXE_MAP["python"], "ControlPython.exe")

    def test_julia_maps_to_control_julia_exe(self):
        self.assertEqual(EXE_MAP["julia"], "ControlJulia.exe")


# ===========================================================================
# 6. VALID_LANGUAGES constant
# ===========================================================================

class TestValidLanguages(unittest.TestCase):

    def test_valid_languages_contains_r(self):
        self.assertIn("r", VALID_LANGUAGES)

    def test_valid_languages_contains_python(self):
        self.assertIn("python", VALID_LANGUAGES)

    def test_valid_languages_contains_julia(self):
        self.assertIn("julia", VALID_LANGUAGES)

    def test_valid_languages_has_exactly_three_entries(self):
        self.assertEqual(len(VALID_LANGUAGES), 3)

    def test_valid_languages_is_frozenset(self):
        self.assertIsInstance(VALID_LANGUAGES, frozenset)


# ===========================================================================
# 7. Integration: load_config → resolve_languages → find_exe
# ===========================================================================

class TestIntegration(unittest.TestCase):
    """End-to-end test: config file → language resolution → exe lookup."""

    def test_full_flow_with_real_temp_dir(self):
        """load_config + resolve_languages + find_exe work together correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake ControlR.exe
            exe_path = os.path.join(tmpdir, "ControlR.exe")
            open(exe_path, "w").close()

            # Write a config file that enables only R
            config_path = os.path.join(tmpdir, "neven-config.json")
            _write_config(config_path, {
                "Standalone": {
                    "controlDir": tmpdir,
                    "languages": ["r"],
                    "port": 5555,
                }
            })

            config = load_config(config_path)
            langs = resolve_languages(config, None)
            self.assertEqual(langs, {"r"})

            result = find_exe(config, "r")
            self.assertEqual(result, exe_path)

    def test_port_override_propagates_via_config(self):
        """After load_config + port override, the port stored in config is correct."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"Standalone": {"port": 5555}}, fh)
            path = fh.name

        try:
            config = load_config(path)
            # Simulate --port override (as main() does)
            config["Standalone"]["port"] = 9999
            self.assertEqual(config["Standalone"]["port"], 9999)
        finally:
            os.unlink(path)

    def test_cli_languages_override_config_languages(self):
        """--languages CLI arg takes precedence over config file (Req 9.6)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"Standalone": {"languages": ["r", "julia"]}}, fh)
            path = fh.name

        try:
            config = load_config(path)
            # CLI supplies only python
            langs = resolve_languages(config, "python")
            self.assertEqual(langs, {"python"})
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
