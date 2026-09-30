# SOP: Manejo de Errores - Patrón Result 🛡️

Para asegurar un código determinista y evitar fallos silenciosos, el proyecto NEVEN adopta el patrón `Result`.

## 1. El Template Result

La implementación final se encuentra en `Common/result.h` y utiliza `std::variant` para una seguridad de tipos completa.

```cpp
namespace NEVEN {
    template <typename T, typename E>
    class Result {
    public:
        static Result Success(T value);
        static Result Failure(E error);

        bool is_success() const;
        bool is_failure() const;

        const T& value() const; // Solo si is_success()
        const E& error() const; // Solo si is_failure()
    };
}
```

## 2. Reglas de Implementación

1.  **No usar `bool` para éxito**: Un `bool` no explica *por qué* falló algo.
2.  **Verificación obligatoria**: El llamador debe verificar `is_success()` antes de acceder a `value()`.
3.  **Logging**: Todo error debe ser registrado antes de retornar el `Result::Failure`.

## 3. Ejemplo Real (Refactorizado)

### API de Archivos
```cpp
auto result = APIFunctions::FileContents("config.json");
if (result.is_success()) {
    std::string contents = result.value();
} else {
    log_error(result.error());
}
```

### Motor de Configuración
```cpp
auto config_result = engine->ReadConfigFile("config.json");
if (config_result.is_failure()) {
    return handle_error(config_result.error());
}
// Procesar config_result.value()
```

---
**Versión**: 1.1.0 | **Estado**: Vigente (Implementado)
