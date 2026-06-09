# Testing Guide — NEVEN

## 1. Overview

NEVEN uses [Google Test (GTest)](https://github.com/google/googletest) v1.14.0 for unit testing. Tests are located in the `tests/` directory and compiled as a single executable `neven_tests`.

---

## 2. Running Tests

### Via build script
```powershell
.\build.ps1 -Test
```

### Via CTest directly
```powershell
cd Build
cmake --build . --config Release --target neven_tests
ctest --output-on-failure -C Release
```

### Running a specific test
```powershell
cd Build
.\tests\Release\neven_tests.exe --gtest_filter="RaiiXlOperTest.*"
```

---

## 3. Test Architecture

All tests run **without Excel, R, or Julia installed**. This is possible because:

- `MockExcelBridge` simulates Excel's C API (`Excel12`/`Excel12v`)
- Mock headers in `include/` provide type declarations without implementations
- Services are designed with dependency injection for testability

### Test --> Mock Dependency Flow
```
Test Code
  └── uses MockExcelBridge (simulates Excel12 calls)
  └── uses RJ2XCL_Engine::Instance() (singleton in test mode)
  └── calls service methods directly (ConfigService, SecurityService, etc.)
```

---

## 4. Existing Test Coverage Map

| Test File | Module Tested | Tests | Coverage Level |
|-----------|--------------|:-----:|:--------------:|
| `raii_xloper_tests.cc` | `RaiiXlOper` (Layer 3) | 4 | ✅ High |
| `common_tests.cc` | `Result<T,E>`, `ConfigService`, `LogService`, R version logic | 12 | ✅ High |
| `security_tests.cc` | `SecurityService` (SHA-256) | 4 | ✅ High |
| `discovery_tests.cc` | `DiscoveryService` (R/Julia detection) | 3 | ⚠️ Medium |
| `callback_dispatcher_tests.cc` | `CallbackDispatcher` (Layer 2) | 5 | ⚠️ Medium |
| `callback_behavior_tests.cc` | Callback routing behavior | 4 | ⚠️ Medium |
| `type_conversion_tests.cc` | XLOPER12 <--> Protobuf conversions | 5 | ⚠️ Medium |

### Modules WITHOUT tests (contribution opportunities)

| Module | File | Why it matters |
|--------|------|---------------|
| `LanguageManager` | `LanguageManager.cc` | Core orchestrator — can cause cascading failures |
| `basic_functions` | `basic_functions.cc` (32KB) | XLL entry points — largest file in the project |
| `language_service` | `language_service.cc` (23KB) | IPC and pipe management |
| `com_object_map` | `com_object_map.cc` (21KB) | COM automation layer |
| `AutoLoader` | `AutoLoader.cc` | Script sourcing — untested filesystem interaction |
| `WindowManager` | `WindowManager.cc` | Console window lifecycle |

---

## 5. How to Write a New Test

### Step 1: Create or edit a test file in `tests/`

```cpp
// tests/my_feature_tests.cc
#include <gtest/gtest.h>
#include "MyService.h"

namespace NEVEN {

TEST(MyServiceTest, BasicBehavior) {
    MyService svc;
    auto result = svc.DoSomething("input");
    EXPECT_TRUE(result.is_success());
    EXPECT_EQ(result.value(), "expected_output");
}

} // namespace NEVEN
```

### Step 2: Include the file in CMake

The `tests/CMakeLists.txt` uses `file(GLOB ...)`, so new `*_tests.cc` files are auto-discovered. If not, add manually.

### Step 3: Run and verify

```powershell
.\build.ps1 -Test
```

### Best Practices

- **Use `MockExcelBridge`** — Never depend on a running Excel instance
- **Use `Result<T,E>`** — Test both `.is_success()` and `.is_failure()` paths
- **Use `TEST_F`** — For tests that share setup/teardown via a fixture
- **Clean up** — Delete temporary files in `TearDown()` (see `security_tests.cc`)
- **Namespace** — All tests should be inside `namespace NEVEN { }`

---

## 6. Test Naming Conventions

```
TEST(ComponentTest, DescriptiveBehavior)
TEST_F(FixtureTest, WhenCondition_ExpectResult)
```

Examples:
- `TEST(ResultTest, SuccessValue)` — Tests the success path
- `TEST_F(RaiiXlOperTest, MoveConstructorTransfersOwnership)` — Fixture test with clear WHEN/EXPECT

---

## 7. Continuous Integration

Tests run automatically on every push and PR via GitHub Actions. See `.github/workflows/build-and-test.yml`.

---

*Version: 1.0.0 | Status: Active*
