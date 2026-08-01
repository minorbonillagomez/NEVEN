"""Property test for task 4.6: --languages CLI override.

**Property 10: ``--languages`` CLI argument exactly controls which engines start**
**Validates: Requirements 9.6**

Builds a config with a different ``languages`` set, calls
``resolve_languages(config, ','.join(cli_langs))``, and asserts the returned
set equals exactly ``cli_langs``.
"""

from __future__ import annotations

import os
import sys
import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TASKPANE not in sys.path:
    sys.path.insert(0, _TASKPANE)

from start_studio import resolve_languages  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config_with_different_langs(cli_langs: frozenset) -> dict:
    """Return a config whose Standalone.languages differs from cli_langs."""
    # Compute the complement — what's NOT in cli_langs
    all_langs = {"r", "python", "julia"}
    complement = list(all_langs - cli_langs)
    # Use the complement if non-empty; otherwise use all three to create a diff
    stored_langs = complement if complement else list(all_langs)
    return {
        "Standalone": {
            "languages": stored_langs,
        }
    }


# ---------------------------------------------------------------------------
# Property 10: --languages CLI override exact control
# ---------------------------------------------------------------------------

class TestCLILanguagesOverride(unittest.TestCase):
    """Property 10 — ``--languages`` exactly controls enabled engines (Req 9.6)."""

    @given(
        cli_langs=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=50)
    def test_cli_override_returns_exactly_cli_langs(
        self, cli_langs: frozenset
    ) -> None:
        """resolve_languages with CLI arg returns exactly those languages.

        **Property 10: ``--languages`` CLI argument exactly controls which engines start**
        **Validates: Requirements 9.6**
        """
        config = _config_with_different_langs(cli_langs)
        cli_arg = ",".join(sorted(cli_langs))
        result = resolve_languages(config, cli_arg)
        self.assertEqual(result, set(cli_langs))

    @given(
        cli_langs=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=50)
    def test_cli_override_ignores_config_languages(
        self, cli_langs: frozenset
    ) -> None:
        """When CLI arg is provided, config ``languages`` is ignored.

        **Validates: Requirements 9.6**
        """
        # Config deliberately has a different set of languages
        config = _config_with_different_langs(cli_langs)
        cli_arg = ",".join(sorted(cli_langs))

        result = resolve_languages(config, cli_arg)

        # The config languages (the complement) should NOT appear in the result
        all_langs = {"r", "python", "julia"}
        complement = all_langs - cli_langs
        for lang in complement:
            with self.subTest(unexpected_lang=lang):
                self.assertNotIn(lang, result)

    @given(
        cli_langs=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=30)
    def test_cli_with_spaces_and_uppercase_normalised(
        self, cli_langs: frozenset
    ) -> None:
        """CLI arg with extra spaces and mixed case is normalised correctly.

        **Validates: Requirements 9.6**
        """
        config = _config_with_different_langs(cli_langs)
        # Add spaces and uppercase
        cli_arg = " , ".join(lang.upper() for lang in sorted(cli_langs))
        result = resolve_languages(config, cli_arg)
        self.assertEqual(result, set(cli_langs))

    @given(
        cli_langs=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=30)
    def test_result_is_subset_of_valid_languages(self, cli_langs: frozenset) -> None:
        """Result is always a subset of valid language identifiers.

        **Validates: Requirements 9.6**
        """
        config = _config_with_different_langs(cli_langs)
        cli_arg = ",".join(sorted(cli_langs))
        result = resolve_languages(config, cli_arg)
        valid = {"r", "python", "julia"}
        self.assertTrue(result.issubset(valid))

    # ── Edge cases ──────────────────────────────────────────────────────────

    def test_none_arg_uses_config_languages(self) -> None:
        """When CLI arg is None, config languages are used."""
        config = {"Standalone": {"languages": ["r", "julia"]}}
        result = resolve_languages(config, None)
        self.assertEqual(result, {"r", "julia"})

    def test_all_three_via_cli(self) -> None:
        """All three languages can be specified via CLI."""
        config = {"Standalone": {"languages": ["r"]}}
        result = resolve_languages(config, "r,python,julia")
        self.assertEqual(result, {"r", "python", "julia"})

    def test_single_language_via_cli(self) -> None:
        """A single language via CLI returns a one-element set."""
        config = {"Standalone": {"languages": ["r", "python", "julia"]}}
        result = resolve_languages(config, "julia")
        self.assertEqual(result, {"julia"})

    def test_invalid_language_in_cli_is_skipped(self) -> None:
        """Invalid language identifiers in CLI arg are silently dropped."""
        config = {"Standalone": {"languages": []}}
        result = resolve_languages(config, "r,cobol,python")
        # 'cobol' is invalid — only r and python should be returned
        self.assertIn("r", result)
        self.assertIn("python", result)
        self.assertNotIn("cobol", result)


if __name__ == "__main__":
    unittest.main()
