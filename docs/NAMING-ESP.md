# NEVEN — Guía de Nomenclatura e Identidad

Este documento explica la relación entre los tres nombres utilizados en el proyecto: **NEVEN**, **RJ2XCL** y **BERT**. Comprender esta historia es esencial para navegar el código fuente sin confusión.

## Contexto Histórico

El proyecto ha pasado por tres fases de nomenclatura:

1. **BERT** (Basic Excel R Toolkit) — el nombre original del proyecto cuando solo soportaba la integración de R con Excel. Este nombre aparece en variables de entorno legacy y en documentación temprana.

2. **RJ2XCL** (R Julia 2 Excel) — el namespace interno de C++ y prefijo adoptado cuando se agregó el soporte para Julia. Se convirtió en el identificador canónico del código compilado: namespaces, prefijos de clase, exports de DLL y símbolos ABI usan este prefijo.

3. **NEVEN** — el nombre público actual utilizado en todas las superficies visibles al usuario. Es el nombre que los usuarios ven en la cinta de Excel, la documentación, los archivos de configuración y las llamadas a funciones.

## Cuándo Usar Cada Nombre

### NEVEN — Contextos Visibles al Usuario

Use **NEVEN** en todo lo que un usuario ve o con lo que interactúa:

- Pestaña del Ribbon y elementos de interfaz en Excel
- Documentación de usuario y texto de ayuda
- Nombres de archivos de configuración (`neven-config.json`)
- Funciones de hoja de cálculo (`=NEVEN.r()`, `=NEVEN.j()`)
- Directorio de instalación (`C:\NEVEN\`)
- Nuevas variables de entorno (usar prefijo `NEVEN_`)
- Mensajes de error mostrados al usuario
- README, CHANGELOG y documentación pública

### RJ2XCL — Código Interno C++

Use **RJ2XCL** en la capa compilada de C++ por compatibilidad ABI:

- Namespaces de C++ (`namespace rj2xcl { }`)
- Prefijos de nombres de clase donde están históricamente establecidos
- Símbolos de exportación de DLL (cambiarlos rompería la compatibilidad binaria)
- Nombre del paquete Protocol Buffers (`RJ2XCLBuffers`)
- Guards de headers internos y macros
- Nombres de targets de build en CMake (ej: `rj2xcl_tests`)
- Instancias singleton (`RJ2XCL_Engine`)

> **¿Por qué no renombrar?** Renombrar símbolos C++ rompería la compatibilidad ABI con add-ins compilados existentes, requeriría actualizaciones coordinadas en todas las fronteras de DLL, e invalidaría cualquier herramienta externa que haga referencia a símbolos exportados por nombre.

### BERT — Solo Variables de Entorno Legacy

Use **BERT** únicamente para mantener compatibilidad con despliegues existentes:

- Variables de entorno legacy (`BERT_HOME`, `BERT_FUNCTIONS_DIRECTORY`, etc.)
- Estas se leen como último recurso de fallback por `GetNevenEnvVar()`
- **No cree nuevas variables con el prefijo BERT_**

## Convención de Variables de Entorno

Las nuevas variables de entorno **deben** usar el prefijo `NEVEN_`. La función `GetNevenEnvVar()` (declarada en `Common/EnvService.h`) implementa un fallback basado en prioridad:

```
Prioridad: NEVEN_{nombre}  >  RJ2XCL_{nombre}  >  BERT_{nombre}  >  (cadena vacía)
```

Por ejemplo, llamar a `GetNevenEnvVar("HOME")` verifica en orden:
1. `NEVEN_HOME` — retorna su valor si está definida
2. `RJ2XCL_HOME` — retorna su valor si está definida
3. `BERT_HOME` — retorna su valor si está definida
4. Retorna cadena vacía

Esto asegura que las nuevas instalaciones usen el prefijo moderno mientras que los despliegues existentes continúen funcionando sin reconfiguración.

## Tabla de Referencia Rápida

| Contexto | Nombre a Usar | Ejemplo |
|----------|---------------|---------|
| Funciones Excel | NEVEN | `=NEVEN.r("summary(x)")` |
| Archivos de config | NEVEN | `neven-config.json` |
| UI / Ribbon | NEVEN | Pestaña "NEVEN" en Excel |
| Documentación | NEVEN | Este archivo |
| Namespaces C++ | rj2xcl | `namespace rj2xcl { }` |
| Exports de DLL | RJ2XCL | Singleton `RJ2XCL_Engine` |
| Paquete Protobuf | RJ2XCL | `RJ2XCLBuffers::Variable` |
| Targets de test | rj2xcl | `rj2xcl_tests` |
| Nuevas variables de entorno | NEVEN_ | `NEVEN_HOME` |
| Variables legacy | BERT_ / RJ2XCL_ | `BERT_HOME` (solo fallback) |
