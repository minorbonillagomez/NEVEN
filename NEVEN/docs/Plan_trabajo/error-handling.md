# SOP: Manejo de Errores - Patrón Result 🛡️

Para asegurar un código determinista y evitar fallos silenciosos, el proyecto NEVEN adopta el patrón `Result`.

## 1. El Template Result

En lugar de lanzar excepciones o retornar códigos de error básicos, las funciones críticas deben retornar un objeto `Result<T, E>`.

```cpp
template <typename T, typename E>
struct Result {
    bool success;
    T data;
    E error;

    static Result Success(T val) { return {true, val, {}}; }
    static Result Failure(E err) { return {false, {}, err}; }
};
```

## 2. Reglas de Implementación

1.  **No usar `bool` para éxito**: Un `bool` no explica *por qué* falló algo.
2.  **Verificación obligatoria**: El llamador debe verificar `success` antes de acceder a `data`.
3.  **Logging**: Todo error debe ser registrado antes de retornar el `Result::Failure`.

## 3. Ejemplo Práctico

```cpp
Result<std::string, FileError> read_file(const std::string& path) {
    if (!file_exists(path)) {
        return Result::Failure(FileNotFound);
    }
    // ... lógica de lectura
    return Result::Success(contents);
}
```

---
**Versión**: 1.0.0 | **Estado**: Propuesto
