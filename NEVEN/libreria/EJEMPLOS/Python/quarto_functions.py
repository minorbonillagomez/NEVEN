"""
RJ2XCL Quarto Integration — User function file
Place this file in Documents/RJ2XCL/functions/ to register quarto_render as =P.quarto_render()
"""
import os
import sys


def quarto_render(file_path, format="html"):
    """Render a Quarto .qmd document and return the output file path.

    Parameters
    ----------
    file_path : str
        Path to the .qmd file.
    format : str
        Output format: html, pdf, or docx (default html).

    Returns
    -------
    str
        Path to rendered output, or error message.
    """
    import subprocess
    import shutil

    fmt = str(format).lower().strip()
    if fmt not in ("html", "pdf", "docx"):
        return "ERROR: Unsupported format. Use html, pdf, or docx"

    fp = str(file_path).strip()
    if not os.path.isfile(fp):
        return "ERROR: File not found: " + fp

    if not fp.lower().endswith(".qmd"):
        return "ERROR: File must have .qmd extension"

    quarto_exe = shutil.which("quarto")
    if not quarto_exe:
        return "ERROR: Quarto CLI not found"

    env = os.environ.copy()
    env["QUARTO_PYTHON"] = sys.executable
    env["RJ2XCL_EXCEL"] = "true"

    try:
        result = subprocess.run(
            [quarto_exe, "render", fp, "--to", fmt],
            capture_output=True, text=True, timeout=300,
            cwd=os.path.dirname(fp), env=env
        )
    except subprocess.TimeoutExpired:
        return "ERROR: Timed out after 300 seconds"
    except Exception as e:
        return "ERROR: " + str(e)

    if result.returncode != 0:
        err = result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
        return "ERROR: exit " + str(result.returncode) + ": " + err

    stem = fp[:-4]
    ext_map = {"html": ".html", "pdf": ".pdf", "docx": ".docx"}
    output = stem + ext_map.get(fmt, "." + fmt)

    if not os.path.isfile(output):
        return "ERROR: Output not found at " + output

    try:
        os.startfile(output)
    except Exception:
        pass

    return output
