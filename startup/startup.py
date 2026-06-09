"""
NEVEN Python Startup Script

This script is executed by ControlPython.exe during initialization.
It defines the core functions required for the NEVEN-Python integration:
  - list_functions(): Returns registered Python functions for Excel
  - read_script_file(path): Reads and executes a Python source file
  - Graphics helpers for plot rendering
  - Package availability checks
  - AI integration setup (if API key configured)
"""

import sys
import os
import importlib
import traceback

# ─── Function Registry ────────────────────────────────────────────────────────

_registered_functions = []


def register_function(name, description="", category="Python", arguments=None):
    """Register a Python function for Excel integration.

    Args:
        name: Function name (will be prefixed with Py. in Excel)
        description: Help text shown in Excel
        category: Function category for grouping
        arguments: List of argument descriptors [{"name": "x", "description": "..."}]
    """
    if arguments is None:
        arguments = []

    entry = {
        "name": name,
        "description": description,
        "category": category,
        "arguments": arguments
    }
    _registered_functions.append(entry)


def list_functions():
    """Return the list of registered Python functions.

    Called by ControlPython when the XLL requests function discovery.
    Returns a list of function descriptors for Excel registration.
    """
    return _registered_functions


def read_script_file(path, notify=False):
    """Read and execute a Python source file.

    Args:
        path: Absolute path to the .py file
        notify: Whether to send a notification on completion

    Returns:
        True on success, False on failure
    """
    try:
        if not os.path.isfile(path):
            print(f"[NEVEN] File not found: {path}", file=sys.stderr)
            return False

        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        # Execute in __main__ namespace so functions are globally available
        exec(compile(code, path, "exec"), globals())
        return True

    except Exception as e:
        print(f"[NEVEN] Error loading {path}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False


# ─── Graphics Helpers ─────────────────────────────────────────────────────────

_graphics_backend = None


def setup_graphics():
    """Configure matplotlib for non-interactive rendering if available."""
    global _graphics_backend
    try:
        import matplotlib
        matplotlib.use("Agg")
        _graphics_backend = "matplotlib"
    except ImportError:
        _graphics_backend = None


def render_plot(fig=None, format="png"):
    """Render a matplotlib figure to bytes.

    Args:
        fig: matplotlib Figure object (uses current figure if None)
        format: Output format ('png', 'svg', 'pdf')

    Returns:
        Bytes of the rendered image, or None on failure
    """
    try:
        import matplotlib.pyplot as plt
        from io import BytesIO

        if fig is None:
            fig = plt.gcf()

        buf = BytesIO()
        fig.savefig(buf, format=format, bbox_inches="tight", dpi=150)
        buf.seek(0)
        data = buf.read()
        plt.close(fig)
        return data

    except Exception as e:
        print(f"[NEVEN] render_plot error: {e}", file=sys.stderr)
        return None


# ─── Package Availability ─────────────────────────────────────────────────────

def check_package(name):
    """Check if a Python package is available.

    Args:
        name: Package name to check

    Returns:
        True if the package can be imported, False otherwise
    """
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def get_available_packages():
    """Return a dict of commonly-used packages and their availability."""
    packages = [
        "numpy", "pandas", "matplotlib", "scipy", "sklearn",
        "statsmodels", "seaborn", "plotly", "openpyxl", "xlsxwriter",
        "requests", "json", "csv", "re", "datetime"
    ]
    return {pkg: check_package(pkg) for pkg in packages}


# ─── AI Integration ──────────────────────────────────────────────────────────

_ai_configured = False
_ai_api_key = None
_ai_model = "gpt-4"


def ai_setup(api_key=None, model=None):
    """Configure AI/LLM integration.

    Args:
        api_key: API key for the LLM service (or reads from NEVEN_AI_KEY env var)
        model: Model name to use (default: gpt-4)
    """
    global _ai_configured, _ai_api_key, _ai_model

    if api_key:
        _ai_api_key = api_key
    else:
        _ai_api_key = os.environ.get("NEVEN_AI_KEY", "")

    if model:
        _ai_model = model

    _ai_configured = bool(_ai_api_key)
    return _ai_configured


def ai_call(prompt, context=None):
    """Call the configured AI/LLM with a prompt.

    Args:
        prompt: The prompt text
        context: Optional context string

    Returns:
        Response text from the AI, or error message
    """
    if not _ai_configured:
        return "[AI not configured — call ai_setup() first]"

    try:
        # Attempt to use openai package if available
        import openai
        openai.api_key = _ai_api_key

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        response = openai.ChatCompletion.create(
            model=_ai_model,
            messages=messages
        )
        return response.choices[0].message.content

    except ImportError:
        return "[openai package not installed]"
    except Exception as e:
        return f"[AI error: {e}]"


def ai_list_prompts():
    """List available AI prompt templates."""
    return [
        {"name": "explain", "description": "Explain code or concept"},
        {"name": "generate", "description": "Generate code from description"},
        {"name": "review", "description": "Review code for issues"},
        {"name": "document", "description": "Generate documentation"},
    ]


# ─── Initialization ──────────────────────────────────────────────────────────

def _startup():
    """Run startup initialization."""
    # Setup graphics backend
    setup_graphics()

    # Try to configure AI if key is available
    ai_setup()

    # Register built-in functions
    register_function("ai_call", "Call AI/LLM with a prompt", "AI",
                      [{"name": "prompt", "description": "The prompt text"}])
    register_function("ai_setup", "Configure AI integration", "AI",
                      [{"name": "api_key", "description": "API key (optional)"}])
    register_function("ai_list_prompts", "List available AI prompts", "AI")
    register_function("check_package", "Check if a package is available", "System",
                      [{"name": "name", "description": "Package name"}])
    register_function("get_available_packages", "List available packages", "System")
    register_function("render_plot", "Render current matplotlib plot", "Graphics",
                      [{"name": "format", "description": "Output format (png/svg/pdf)"}])


# Execute startup
_startup()
