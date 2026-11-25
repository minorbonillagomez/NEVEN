#!/usr/bin/env python
"""Recuento del estado de las especificaciones de .kiro/specs (B-21).

Uso:  python src/scripts/count_spec_status.py [--json]

Cuenta por script las casillas de cada .kiro/specs/*/tasks.md y las agrupa por
situacion segun la tabla STATUS (la clasificacion de 04-notas-mejoras.md de la
auditoria). Una especificacion que exista en disco y no este en la tabla se
informa como SIN CLASIFICAR y hace fallar el script (codigo 1), igual que si la
deuda real no coincide con EXPECTED_DEUDA_REAL, para que el recuento no se
quede desactualizado sin que nadie lo vea.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPECS = os.path.join(ROOT, ".kiro", "specs")
EXPECTED_DEUDA_REAL = 207

DEUDA = "deuda real (vigente)"
ALCANCE = "decision de alcance pendiente"
AJENA = "ajena a NEVEN"
IMPL = "implementada sin cerrar"
SUPERADA = "superada por la implementacion"
INCOMPLETA = "sin tasks.md"

STATUS = {
    "maintainability-improvements": DEUDA, "quarto-integration": DEUDA,
    "webview2-repl-console": DEUDA, "console-diagnostic-stream": DEUDA,
    "startup-optimization": DEUDA, "webview2-viewer": DEUDA,
    "neven-datalab-gr-family": DEUDA, "neven-installer": DEUDA,
    "ontologia-v2": DEUDA, "neven-package-manager": DEUDA,
    "neven-data-lab": DEUDA, "reliability-improvements": DEUDA,
    "viewer-professional": DEUDA,
    "neven-sim": ALCANCE, "neven-enterprise": ALCANCE,
    "ontology-engine-framework": AJENA,
    "nevenx-dispatcher": IMPL, "neven-v3-taskpane": IMPL,
    "ai-integration": SUPERADA,
    "ai-interpreter": INCOMPLETA,
    # Cerradas (0 casillas abiertas)
    "code-audit": DEUDA, "function-dictionary": DEUDA,
    "neven-studio-standalone": DEUDA, "python-integration": DEUDA,
    "python-reactivation": DEUDA, "rj2xcl-to-ponto-rename": DEUDA,
    "security-remediation": DEUDA,
}

OPEN = re.compile(r"^\s*- \[ \]")
DONE = re.compile(r"^\s*- \[[xX]\]")
PROG = re.compile(r"^\s*- \[-\]")


def main():
    rows, unknown = [], []
    for name in sorted(os.listdir(SPECS)):
        d = os.path.join(SPECS, name)
        if not os.path.isdir(d) or name.startswith("_"):
            continue
        f = os.path.join(d, "tasks.md")
        o = x = p = 0
        if os.path.isfile(f):
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    o += bool(OPEN.match(line))
                    x += bool(DONE.match(line))
                    p += bool(PROG.match(line))
        st = STATUS.get(name)
        if st is None:
            unknown.append(name)
            st = "SIN CLASIFICAR"
        if o == 0 and os.path.isfile(f) and st != "SIN CLASIFICAR":
            st = "cerrada (0 casillas abiertas)"
        rows.append({"spec": name, "abiertas": o, "hechas": x, "en_curso": p,
                     "tiene_tasks": os.path.isfile(f), "estado": st})

    groups = {}
    for r in rows:
        groups[r["estado"]] = groups.get(r["estado"], 0) + r["abiertas"]
    total = sum(r["abiertas"] for r in rows)
    deuda = groups.get(DEUDA, 0)

    if "--json" in sys.argv:
        print(json.dumps({"specs": rows, "por_estado": groups, "total_abiertas": total}, indent=2))
    else:
        print(f"Especificaciones: {len(rows)}  (con tasks.md: {sum(r['tiene_tasks'] for r in rows)})")
        print(f"{'spec':34}{'abiertas':>9}{'hechas':>8}  estado")
        for r in rows:
            print(f"{r['spec']:34}{r['abiertas']:>9}{r['hechas']:>8}  {r['estado']}")
        print("-" * 70)
        print(f"Casillas abiertas: {total}")
        for k, v in sorted(groups.items(), key=lambda kv: -kv[1]):
            print(f"  {v:>4}  {k}")
        print(f"Deuda real: {deuda}  (esperado {EXPECTED_DEUDA_REAL})")
    rc = 0
    if unknown:
        print("SIN CLASIFICAR: " + ", ".join(unknown), file=sys.stderr)
        rc = 1
    if deuda != EXPECTED_DEUDA_REAL:
        print(f"La deuda real {deuda} difiere de {EXPECTED_DEUDA_REAL}", file=sys.stderr)
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
