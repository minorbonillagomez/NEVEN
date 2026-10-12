"""
NEVEN Python Quarto Functions

Quarto document rendering via Python for the NEVEN Excel add-in.
Provides functions to render .qmd files and manage Quarto output.
"""

import os
import subprocess
import tempfile
import json


def quarto_render(input_path, output_format="html", output_dir=None):
    """Render a Quarto document.

    Args:
        input_path: Path to the .qmd file
        output_format: Output format (html, pdf, docx, revealjs)
        output_dir: Output directory (defaults to same as input)

    Returns:
        Path to the rendered output file, or error message
    """
    if not os.path.isfile(input_path):
        return f"[File not found: {input_path}]"

    cmd = ["quarto", "render", input_path, "--to", output_format]

    if output_dir:
        cmd.extend(["--output-dir", output_dir])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            # Determine output path
            base = os.path.splitext(input_path)[0]
            ext_map = {"html": ".html", "pdf": ".pdf", "docx": ".docx", "revealjs": ".html"}
            ext = ext_map.get(output_format, f".{output_format}")
            output_path = base + ext
            if output_dir:
                output_path = os.path.join(output_dir, os.path.basename(base) + ext)
            return output_path
        else:
            return f"[Quarto error: {result.stderr.strip()}]"

    except FileNotFoundError:
        return "[Quarto not found — install from https://quarto.org]"
    except subprocess.TimeoutExpired:
        return "[Quarto render timed out (120s)]"
    except Exception as e:
        return f"[Quarto error: {e}]"


def quarto_check():
    """Check if Quarto is installed and return version info.

    Returns:
        Dict with installed status, version, and path
    """
    try:
        result = subprocess.run(
            ["quarto", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return {"installed": True, "version": version}
        else:
            return {"installed": False, "version": None}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"installed": False, "version": None}


def quarto_preview(input_path, port=4200):
    """Start a Quarto preview server (non-blocking).

    Args:
        input_path: Path to the .qmd file
        port: Port for the preview server

    Returns:
        URL of the preview server, or error message
    """
    if not os.path.isfile(input_path):
        return f"[File not found: {input_path}]"

    try:
        subprocess.Popen(
            ["quarto", "preview", input_path, "--port", str(port), "--no-browser"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f"http://localhost:{port}"
    except FileNotFoundError:
        return "[Quarto not found]"
    except Exception as e:
        return f"[Preview error: {e}]"


def quarto_render_inline(code, output_format="html", engine="python"):
    """Render inline Quarto content from a string.

    Args:
        code: Quarto markdown content
        output_format: Output format
        engine: Computation engine (python, jupyter)

    Returns:
        Path to rendered output, or error message
    """
    try:
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".qmd", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        result = quarto_render(temp_path, output_format)

        # Clean up temp .qmd (keep output)
        try:
            os.unlink(temp_path)
        except OSError:
            pass

        return result

    except Exception as e:
        return f"[Inline render error: {e}]"


# ─── Registration ─────────────────────────────────────────────────────────────

def _register_quarto_functions():
    """Register Quarto functions with the NEVEN function registry."""
    register_function("quarto_render", "Render a Quarto document", "Quarto",
                      [{"name": "input_path", "description": "Path to .qmd file"},
                       {"name": "output_format", "description": "Output format (html/pdf/docx)"}])
    register_function("quarto_check", "Check Quarto installation", "Quarto")
    register_function("quarto_preview", "Start Quarto preview server", "Quarto",
                      [{"name": "input_path", "description": "Path to .qmd file"}])
    register_function("quarto_render_inline", "Render inline Quarto content", "Quarto",
                      [{"name": "code", "description": "Quarto markdown content"}])


_register_quarto_functions()
