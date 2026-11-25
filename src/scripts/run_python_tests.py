#!/usr/bin/env python
"""Runner unico de los tests de Python de NEVEN (B-02).

Uso (desde la raiz del repositorio o desde src/):
    python src/scripts/run_python_tests.py [--strict] [--list]

Ejecuta pytest con la configuracion de src/pytest.ini y src/conftest.py y
da un recuento de pasados, fallados, con error, saltados, xfail y xpass.
Los fallos se separan en dos grupos:
  - conocidos en la base: listados en src/tests/python_baseline_failures.txt
  - nuevos: cualquier otro fallo o error
Nada se oculta: los conocidos se cuentan y se imprimen. Los saltados y los
xfail tambien se listan con su motivo.

Codigo de salida: 0 si no hay fallos nuevos; 1 si los hay, o con --strict si
hay cualquier fallo; 2 si pytest no pudo ejecutarse.
"""
import argparse
import os
import sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(SRC, "tests", "python_baseline_failures.txt")


class Collector:
    def __init__(self):
        self.outcomes = {}   # nodeid -> (categoria, detalle)

    def _set(self, nodeid, cat, detail=""):
        self.outcomes[nodeid] = (cat, detail)

    def pytest_collectreport(self, report):
        if report.failed:
            self._set(report.nodeid, "error", "fallo de coleccion")

    def pytest_runtest_logreport(self, report):
        nid = report.nodeid
        wasxfail = getattr(report, "wasxfail", None)
        if report.when == "call":
            if wasxfail is not None:
                self._set(nid, "xfailed" if report.skipped else "xpassed", wasxfail)
            elif report.skipped:
                reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else str(report.longrepr)
                self._set(nid, "skipped", reason)
            elif report.passed:
                self.outcomes.setdefault(nid, ("passed", ""))
            elif report.failed:
                self._set(nid, "failed")
        elif report.when == "setup":
            if report.failed:
                self._set(nid, "error", "error en setup")
            elif report.skipped:
                reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else str(report.longrepr)
                self._set(nid, "xfailed" if wasxfail is not None else "skipped", wasxfail or reason)
        elif report.when == "teardown" and report.failed:
            self._set(nid, "error", "error en teardown")


def load_baseline():
    ids = set()
    if os.path.isfile(BASELINE):
        with open(BASELINE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ids.add(line)
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="salir con 1 ante cualquier fallo, conocido o no")
    ap.add_argument("--list", action="store_true", help="imprimir los ids de fallos en formato de baseline")
    args = ap.parse_args()

    try:
        import pytest
    except ImportError:
        print("pytest no esta instalado: pip install pytest", file=sys.stderr)
        return 2

    for s in (sys.stdout, sys.stderr):
        s.reconfigure(errors='replace')
    os.chdir(SRC)
    col = Collector()
    rc = pytest.main(["-q", "--tb=short", "--continue-on-collection-errors"], plugins=[col])
    if rc in (3, 4):
        print(f"pytest fallo internamente (codigo {rc})", file=sys.stderr)
        return 2

    cats = {}
    for nid, (cat, det) in col.outcomes.items():
        cats.setdefault(cat, []).append((nid, det))
    n = lambda c: len(cats.get(c, []))
    bad = sorted(nid for c in ("failed", "error") for nid, _ in cats.get(c, []))
    baseline = load_baseline()
    known = [b for b in bad if b in baseline]
    new = [b for b in bad if b not in baseline]
    stale = sorted(baseline - set(bad))

    if args.list:
        for b in bad:
            print("ID: " + b)
        return 0

    total = len(col.outcomes)
    print("=" * 70)
    print(f"Tests de Python: {total} recogidos")
    print(f"  pasados : {n('passed')}")
    print(f"  fallados: {n('failed')}  (incluye los esperado-fallo)")
    print(f"  errores : {n('error')}")
    print(f"  saltados: {n('skipped')}")
    print(f"  xfail   : {n('xfailed')}   xpass: {n('xpassed')}")
    print(f"  esperado-fallo (deuda de la base): {len(known)}")
    print(f"  fallos nuevos: {len(new)}")
    print(f"Fallos+errores: {len(bad)}  =  {len(known)} esperado-fallo + {len(new)} nuevos")
    for c in ("skipped", "xfailed", "xpassed"):
        for nid, det in sorted(cats.get(c, [])):
            print(f"  [{c}] {nid}  {det}")
    if known:
        print("Esperado-fallo (deuda de la base, lista en tests/python_baseline_failures.txt):")
        for b in known:
            print(f"  [esperado-fallo] {b}")
    if new:
        print("NUEVOS:")
        for b in new:
            print(f"  [NUEVO] {b}")
    if stale:
        print("En la lista base pero que ya no fallan (retirar de la lista):")
        for b in stale:
            print(f"  [obsoleto] {b}")
    print("=" * 70)
    if new or (args.strict and bad):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
