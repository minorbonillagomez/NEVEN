# NEVEN Python Library

Python functions for the NEVEN Excel add-in. These files are loaded by ControlPython.exe
when Python is enabled as a language service.

## Structure

- `ai_functions.py` — AI/LLM integration functions (P.ai_call, P.ai_setup, P.ai_list_prompts)
- `quarto_functions.py` — Quarto document rendering via Python

## Usage in Excel

Python functions are prefixed with `Py.` in Excel:

```
=NEVEN.py("1 + 1")           # Execute Python code
=Py.ai_call("explain this")  # Call registered function
=Py.check_package("numpy")   # Check package availability
```

## Requirements

- Python >= 3.10 (stable ABI)
- Optional: numpy, pandas, matplotlib, openai

## Configuration

Enable Python in `neven-config.json`:

```json
{
  "NEVEN": {
    "Python": {
      "home": "C:/Users/.../Python312",
      "enabled": true,
      "minMajor": 3,
      "minMinor": 10,
      "maxMajor": 99
    }
  }
}
```
