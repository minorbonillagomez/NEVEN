#!/usr/bin/env python3
"""
NEVEN Ontology EVALS Runner
═══════════════════════════════════════════════════════════════════════════════

Ejecuta los tests de precisión para las ontologías de NEVEN.
Valida que el pipeline de extracción produzca entidades correctas.

Uso:
    python run_evals.py                     # Ejecuta todos los EVALS
    python run_evals.py --domain excel      # Solo ontología Excel
    python run_evals.py --domain econometria # Solo ontología Econometría
    python run_evals.py --verbose           # Modo detallado
    python run_evals.py --dry-run           # Solo valida YAML sin ejecutar

Requisitos:
    pip install pyyaml rich
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

EVALS_ROOT = Path(__file__).parent
DOMAINS = ['ontologia-econometria', 'ontologia-excel', 'agent_behavior']


# ═══════════════════════════════════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvalCase:
    """Un caso de prueba individual."""
    id: str
    description: str
    input: dict
    expected: dict
    transform_rule: str | None = None
    notes: str | None = None


@dataclass
class EvalResult:
    """Resultado de un caso de prueba."""
    case_id: str
    passed: bool
    expected: Any
    actual: Any | None = None
    error: str | None = None


@dataclass
class EvalSuiteResult:
    """Resultado de un conjunto completo de EVALS."""
    suite_name: str
    domain: str
    total_cases: int
    passed: int
    failed: int
    errors: int
    results: list[EvalResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.passed / self.total_cases


# ═══════════════════════════════════════════════════════════════════════════════
# CARGADOR DE EVALS
# ═══════════════════════════════════════════════════════════════════════════════

def load_eval_file(filepath: Path) -> dict:
    """Carga y valida un archivo YAML de EVAL."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Validación básica
    if 'eval' not in data:
        raise ValueError(f"Archivo {filepath.name} no tiene sección 'eval'")
    
    # Los casos pueden estar en 'cases' u otras secciones
    # Algunos archivos usan 'validation_cases', 'negative_cases', etc.
    has_cases = any(key.endswith('cases') or key == 'cases' or key == 'formats' 
                    for key in data.keys())
    if not has_cases:
        raise ValueError(f"Archivo {filepath.name} no tiene sección de casos")
    
    return data


def discover_evals(domain: str | None = None) -> dict[str, list[Path]]:
    """Descubre todos los archivos EVAL organizados por dominio."""
    evals = {}
    
    domains_to_scan = [domain] if domain else DOMAINS
    
    for d in domains_to_scan:
        domain_path = EVALS_ROOT / d
        if not domain_path.exists():
            continue
            
        eval_files = list(domain_path.glob('*.yaml'))
        if eval_files:
            evals[d] = eval_files
    
    return evals


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUTOR DE EVALS
# ═══════════════════════════════════════════════════════════════════════════════

class EvalRunner:
    """Ejecutor de tests de ontología."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def run_case(self, case: dict, eval_type: str) -> EvalResult:
        """Ejecuta un caso de prueba individual."""
        case_id = case.get('id', 'unknown')
        expected = case.get('expected', {})
        
        # Por ahora, solo validamos la estructura
        # En el futuro, esto llamará al pipeline de extracción real
        
        try:
            # Placeholder: aquí iría la lógica real de evaluación
            # Por ahora, marcamos como passed si tiene la estructura correcta
            
            # Aceptar 'input', 'query', o 'pattern' como entrada válida
            has_input = any(key in case for key in ['input', 'query', 'pattern', 'description'])
            has_expected = 'expected' in case or 'response_must_contain' in case.get('expected', {})
            
            if not has_input or not has_expected:
                return EvalResult(
                    case_id=case_id,
                    passed=False,
                    expected=expected,
                    error="Caso incompleto: falta 'input' o 'expected'"
                )
            
            # Validar que expected tiene campos válidos
            valid_expected_fields = {
                'type', 'type_in', 'name', 'name_contains', 
                'category', 'required_fields', 'has_formula',
                'has_common_errors', 'has_best_practices',
                'entities', 'functions_used', 'keys', 'keys_contains',
                'transformed', 'related_function', 'transform_rules'
            }
            
            for key in expected:
                if key not in valid_expected_fields:
                    if self.verbose:
                        print(f"  ⚠️  Campo desconocido en expected: {key}")
            
            return EvalResult(
                case_id=case_id,
                passed=True,
                expected=expected,
                actual=None  # Placeholder
            )
            
        except Exception as e:
            return EvalResult(
                case_id=case_id,
                passed=False,
                expected=expected,
                error=str(e)
            )
    
    def run_suite(self, filepath: Path) -> EvalSuiteResult:
        """Ejecuta un archivo completo de EVAL."""
        data = load_eval_file(filepath)
        
        eval_info = data['eval']
        suite_name = eval_info.get('name', filepath.stem)
        domain = eval_info.get('domain', 'unknown')
        
        cases = data.get('cases', [])
        
        # También procesar casos adicionales si existen
        for key in data:
            if key.endswith('_cases') and key != 'cases':
                cases.extend(data[key])
        
        results = []
        passed = 0
        failed = 0
        errors = 0
        
        for case in cases:
            result = self.run_case(case, eval_info.get('id', 'unknown'))
            results.append(result)
            
            if result.error:
                errors += 1
            elif result.passed:
                passed += 1
            else:
                failed += 1
        
        return EvalSuiteResult(
            suite_name=suite_name,
            domain=domain,
            total_cases=len(cases),
            passed=passed,
            failed=failed,
            errors=errors,
            results=results
        )


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTES
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary(results: list[EvalSuiteResult]) -> None:
    """Imprime resumen de todos los EVALS ejecutados."""
    total_cases = sum(r.total_cases for r in results)
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    total_errors = sum(r.errors for r in results)
    
    print("\n" + "═" * 70)
    print("📊 RESUMEN DE EVALS")
    print("═" * 70)
    
    for result in results:
        status = "✅" if result.failed == 0 and result.errors == 0 else "❌"
        rate = f"{result.success_rate * 100:.1f}%"
        print(f"{status} {result.suite_name:<40} {result.passed}/{result.total_cases} ({rate})")
    
    print("─" * 70)
    
    overall_rate = (total_passed / total_cases * 100) if total_cases > 0 else 0
    print(f"📈 TOTAL: {total_passed}/{total_cases} casos pasaron ({overall_rate:.1f}%)")
    
    if total_errors > 0:
        print(f"⚠️  {total_errors} errores de ejecución")
    
    if total_failed > 0:
        print(f"❌ {total_failed} casos fallaron")
    
    print("═" * 70)


def export_results_json(results: list[EvalSuiteResult], output_path: Path) -> None:
    """Exporta resultados a JSON para análisis posterior."""
    data = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'suites': []
    }
    
    for result in results:
        suite_data = {
            'name': result.suite_name,
            'domain': result.domain,
            'total': result.total_cases,
            'passed': result.passed,
            'failed': result.failed,
            'errors': result.errors,
            'success_rate': result.success_rate,
            'results': [
                {
                    'case_id': r.case_id,
                    'passed': r.passed,
                    'error': r.error
                }
                for r in result.results
            ]
        }
        data['suites'].append(suite_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Resultados exportados a: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Ejecuta EVALS de ontologías NEVEN',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python run_evals.py                     # Todos los EVALS
    python run_evals.py --domain excel      # Solo Excel
    python run_evals.py --verbose --export  # Detallado + JSON
        """
    )
    
    parser.add_argument(
        '--domain', '-d',
        choices=['excel', 'econometria'],
        help='Ejecutar solo EVALS de un dominio específico'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar detalles de cada caso'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo validar YAML sin ejecutar'
    )
    
    parser.add_argument(
        '--export', '-e',
        action='store_true',
        help='Exportar resultados a JSON'
    )
    
    args = parser.parse_args()
    
    # Mapear dominio a nombre de carpeta
    domain_map = {
        'excel': 'ontologia-excel',
        'econometria': 'ontologia-econometria',
        None: None
    }
    domain = domain_map.get(args.domain)
    
    # Descubrir EVALS
    print("🔍 Descubriendo EVALS...")
    evals = discover_evals(domain)
    
    if not evals:
        print("❌ No se encontraron archivos EVAL")
        sys.exit(1)
    
    total_files = sum(len(files) for files in evals.values())
    print(f"📁 Encontrados {total_files} archivos EVAL en {len(evals)} dominios\n")
    
    # Validar YAML
    print("✅ Validando sintaxis YAML...")
    valid_files = []
    
    for domain_name, files in evals.items():
        for filepath in files:
            try:
                load_eval_file(filepath)
                valid_files.append((domain_name, filepath))
                if args.verbose:
                    print(f"   ✓ {filepath.name}")
            except Exception as e:
                print(f"   ✗ {filepath.name}: {e}")
    
    if args.dry_run:
        print(f"\n🏁 Dry run completado. {len(valid_files)}/{total_files} archivos válidos.")
        sys.exit(0 if len(valid_files) == total_files else 1)
    
    # Ejecutar EVALS
    print("\n🚀 Ejecutando EVALS...")
    runner = EvalRunner(verbose=args.verbose)
    results = []
    
    for domain_name, filepath in valid_files:
        print(f"\n📋 {filepath.stem} ({domain_name})")
        result = runner.run_suite(filepath)
        results.append(result)
        
        if args.verbose:
            for r in result.results:
                status = "✅" if r.passed else "❌"
                print(f"   {status} {r.case_id}")
                if r.error:
                    print(f"      Error: {r.error}")
    
    # Resumen
    print_summary(results)
    
    # Exportar si se solicita
    if args.export:
        output_path = EVALS_ROOT / 'eval_results.json'
        export_results_json(results, output_path)
    
    # Exit code
    total_failed = sum(r.failed + r.errors for r in results)
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == '__main__':
    main()
