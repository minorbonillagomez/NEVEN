cmake_minimum_required(VERSION 3.15)
project(NEVEN VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Force Static Runtime (/MT) for total independence
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

if(MSVC)
    add_compile_definitions(_SILENCE_CXX17_OLD_ALLOCATOR_MEMBERS_DEPRECATION_WARNING _SILENCE_CXX17_HASH_IMPLEMENTATION_DEPRECATION_WARNING _SILENCE_STDEXT_HASH_DEPRECATION_WARNING _SILENCE_CXX17_CODECVT_HEADER_DEPRECATION_WARNING)
endif()

# Security compilation flags — applied globally to all targets
if(MSVC)
    # /GS: Buffer security check (stack canaries)
    # /guard:cf: Control Flow Guard
    add_compile_options(/GS /guard:cf)

    # /DYNAMICBASE: ASLR (Address Space Layout Randomization)
    # /NXCOMPAT: DEP (Data Execution Prevention)
    # /CETCOMPAT: Intel CET Shadow Stack (hardware-enforced control flow)
    add_link_options(/DYNAMICBASE /NXCOMPAT /CETCOMPAT)
endif()

# Directorio base para archivos comúnes e interfaces
include_directories(include)
include_directories(Common)
include_directories(OfficeTypes)

include(FetchContent)

# Protobuf (keep URL as it is a specific release artifact)
FetchContent_Declare(
  protobuf
  URL "https://github.com/protocolbuffers/protobuf/releases/download/v21.12/protobuf-cpp-3.21.12.zip"
)
set(protobuf_BUILD_TESTS OFF CACHE INTERNAL "")
set(protobuf_BUILD_EXAMPLES OFF CACHE INTERNAL "")
set(protobuf_MSVC_STATIC_RUNTIME ON CACHE INTERNAL "")

# GoogleTest (Switch to GIT_REPOSITORY for better stability)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.14.0
)
# For Windows: prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt OFF CACHE BOOL "" FORCE)

# rapidcheck — Property-based testing library
FetchContent_Declare(
  rapidcheck
  GIT_REPOSITORY https://github.com/emil-e/rapidcheck.git
  GIT_TAG        master
)
set(RC_ENABLE_GTEST ON CACHE BOOL "Enable rapidcheck GTest integration" FORCE)
set(RC_ENABLE_GMOCK OFF CACHE BOOL "" FORCE)

# Make them available (Separate calls help isolate failures)
FetchContent_MakeAvailable(protobuf)
FetchContent_MakeAvailable(googletest)
FetchContent_MakeAvailable(rapidcheck)

# WebView2 SDK (Microsoft NuGet package — downloaded and extracted)
# The .nupkg is a ZIP containing headers and static loader library.
# We use FetchContent to download it, then set include/lib paths manually.
FetchContent_Declare(
  webview2
  URL "https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/1.0.2903.40"
  DOWNLOAD_NO_EXTRACT FALSE
)
FetchContent_MakeAvailable(webview2)

# WebView2 SDK paths — headers and static loader for x64
set(WEBVIEW2_INCLUDE_DIR "${webview2_SOURCE_DIR}/build/native/include" CACHE PATH "WebView2 SDK include directory")
set(WEBVIEW2_LOADER_DIR "${webview2_SOURCE_DIR}/build/native/x64" CACHE PATH "WebView2 SDK x64 library directory")

include_directories(${protobuf_SOURCE_DIR}/src)

# Subdirectorios para la arquitectura multi-motor
add_subdirectory(PB)
add_subdirectory(Common)

# Language targets (ControlR, ControlJulia) require R/Julia SDKs
# Skip them in CI when only running unit tests
option(SKIP_LANGUAGE_TARGETS "Skip ControlR/ControlJulia (for CI without R/Julia)" OFF)
option(NEVEN_ENABLE_PYTHON "Build ControlPython.exe (optional, requires Python >= 3.10)" ON)

if(NOT SKIP_LANGUAGE_TARGETS)
    add_subdirectory(ControlR)
    add_subdirectory(ControlJulia)

    if(NEVEN_ENABLE_PYTHON)
        add_subdirectory(ControlPython)
    endif()
endif()

add_subdirectory(Core)
add_subdirectory(Ribbon)

if(NOT SKIP_LANGUAGE_TARGETS)
    add_subdirectory(Addin)
endif()

enable_testing()
add_subdirectory(tests)

# Console (Electron REPL) was removed in the security remediation.
# The WebView2-based REPL (REPLManager + REPLBridge) is the replacement.
# See: Common/REPLManager.cc, Common/IPC/REPLBridge.cc
