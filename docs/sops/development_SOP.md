# NEVEN Development Standard Operating Procedures (SOP)

## 1. Arquitectura del Proyecto
NEVEN sigue un patrón de **Servicios Desacoplados**. El `RJ2XCL_Engine` actúa como orquestador central, delegando responsabilidades a servicios especializados:

- **RibbonService**: Gestión de la interfaz COM de Excel (Botones, Ribbon XML).
- **FileWatchService**: Vigilancia de directorios y recarga en caliente (Hot-Reload) de scripts.
- **LanguageManager**: Gestión del ciclo de vida de motores R y Julia.
- **CallbackDispatcher**: Enrutamiento de llamadas desde lenguajes externos hacia Excel.

## 2. Flujo de Desarrollo
### Añadir una nueva función de Excel
1. Definir la lógica en `basic_functions.h` (si es core) o en los servicios de lenguaje.
2. Asegurar que use `rj2xcl_integration_constants.h` para cualquier trigger de macro.

### Modificar la Comunicación (Pipes)
- La resiliencia está implementada en `LanguageService::Call`. Cualquier error de pipe dispara un reintento automático (`Connect` + `Initialize`).
- El tamaño del buffer es dinámico (8KB inicial, crece hasta 256KB si es necesario).

## 3. Pruebas y Validación
### Ejecutar Suite de Tests
```powershell
cd Build
cmake --build . --config Debug --target neven_tests
ctest -C Debug --output-on-failure
```

### Crear Nuevo Test
- Usar `MockExcelBridge` para simular la API de Excel sin necesidad de abrir la aplicación.
- Verificar conteos de llamadas con `mock_bridge->GetCallCount(xlfn)`.

## 4. Mejores Prácticas (Escuadrón BLAST)
- **RAII**: Usar siempre `std::unique_ptr` o `std::shared_ptr`. Evitar `new/delete` manual.
- **Strings**: No usar strings hardcodeados para integración. Usar `constants::k*`.
- **Thread Safety**: Las llamadas de retorno desde R/Julia deben ser marshalled a través de `HandleCallbackOnThread`.

---
*Documento generado tras el Sprint 5 de modernización.*
