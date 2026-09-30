# SOP: Estándares de Codificación NEVEN 📄

Este documento define las reglas de nomenclatura y estilo para asegurar la consistencia en el proyecto NEVEN.

## 1. Nomenclatura

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| **Clases** | `PascalCase` | `class LanguageManager` |
| **Funciones** | `snake_case` | `void register_functions()` |
| **Variables Locales** | `snake_case` | `std::string file_path` |
| **Miembros de Clase** | `snake_case_` | `int next_id_` |
| **Constantes/Macros** | `SCREAMING_SNAKE_CASE` | `MAX_BUFFER_SIZE` |

## 2. Archivos

*   **Extensiones**: Usar `.cc` para archivos de implementación C++ y `.h` para encabezados. (Evitar `.cpp`).
*   **Nombres**: Los nombres de archivo deben ser descriptivos y en `snake_case`.
    *   ✅ `message_utilities.cc`
    *   ❌ `RJ2XCL_Main.cpp`

## 3. Comentarios

*   Usar comentarios estilo Doxygen para documentar el propósito de las funciones en los encabezados.
*   Documentar el "Por qué" en la implementación, no solo el "Qué".

---
**Versión**: 1.0.0 | **Estado**: Vigente
