# SOP: Manejo de Errores — Patrón Result 🛡️

Para asegurar un código determinista y evitar fallos silenciosos, el proyecto NEVEN adopta el patrón `Result`.

## 1. El Template Result

En lugar de lanzar excepciones o retornar códigos de error básicos, las funciones críticas retornan un objeto `Result<T, E>`. La implementación se encuentra en `Common/result.h`.

```cpp
namespace NEVEN {

template <typename T, typename E>
class Result {
    bool success_;
    T value_;
    E error_;
public:
    static Result Success(T value);
    static Result Failure(E error);

    bool is_success() const;
    bool is_failure() const;
    const T& value() const;
    const E& error() const;
};

// Specialization for void results (operations that don't return data)
template <typename E>
class Result<void, E> {
public:
    static Result Success();
    static Result Failure(E error);
    bool is_success() const;
    bool is_failure() const;
    const E& error() const;
};

} // namespace NEVEN
```

## 2. Reglas de Implementación

1.  **No usar `bool` para éxito**: Un `bool` no explica *por qué* falló algo.
2.  **Verificación obligatoria**: El llamador debe verificar `is_success()` antes de acceder a `value()`.
3.  **Logging**: Todo error debe ser registrado (vía `LogService`) antes de retornar `Result::Failure`.
4.  **Propagación**: Los errores se propagan hacia arriba, nunca se silencian.

## 3. Ejemplos de Uso Real en el Proyecto

### ConfigService — Lectura de archivos JSON
```cpp
Result<json11::Json, APIFunctions::FileError> ConfigService::ReadJsonFile(const std::string& path) {
    if (!file_exists(path)) {
        RJ2XCL_LOG_WARN("Config file not found: %s", path.c_str());
        return Result::Failure(APIFunctions::FileError::FileNotFound);
    }

    std::string parse_error;
    auto json = json11::Json::parse(contents, parse_error, json11::COMMENTS);
    if (!parse_error.empty()) {
        RJ2XCL_LOG_ERROR("JSON parse error in %s: %s", path.c_str(), parse_error.c_str());
        return Result::Failure(APIFunctions::FileError::ParseError);
    }

    return Result::Success(json);
}
```

### DiscoveryService — Detección de R/Julia
```cpp
Result<std::string, std::string> DiscoveryService::FindRHome() {
    // Try registry first
    auto reg_result = ScanRegistry("R");
    if (reg_result.is_success()) return reg_result;

    // Try common paths
    auto path_result = ScanPaths("R");
    if (path_result.is_success()) return path_result;

    return Result::Failure(std::string("R installation not found"));
}
```

### Void Results — Operaciones sin valor de retorno
```cpp
Result<void, int> SecurityService::VerifyAllScripts(const std::string& dir) {
    int failures = 0;
    for (const auto& script : scan_directory(dir)) {
        if (!VerifyScriptIntegrity(script)) failures++;
    }
    if (failures > 0) return Result<void, int>::Failure(failures);
    return Result<void, int>::Success();
}
```

## 4. Códigos de Error Estándar

```cpp
namespace APIFunctions {
    enum class FileError {
        Success    = 0,
        NotFound   = 1,
        AccessDenied = 2,
        ParseError = 3   // Added in v2.0.0
    };
}
```

## 5. Tests del Patrón

Los tests unitarios en `tests/common_tests.cc` verifican:
- `ResultTest::SuccessValue` — Acceso correcto al valor exitoso
- `ResultTest::FailureError` — Acceso correcto al error
- `ResultTest::VoidSuccess` — Resultado void sin datos

---
**Versión**: 2.0.0 | **Estado**: Vigente
