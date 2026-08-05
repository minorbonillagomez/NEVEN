# ControlR Submodule — Builds ControlR.exe (R language service process)
#
# NEVEN v2.4: ControlR uses dynamic engine loading (LoadLibrary/GetProcAddress)
# and no longer links against R64.lib or RGraphApp64.lib.
# R can be updated to any compatible version without recompiling.
#
# The only requirement at build time is that R is NOT needed as a dependency.
# At runtime, ControlR loads R.dll from the path in neven-config.json (NEVEN.R.home).

project(ControlR)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ─── R Graphics Engine headers (only for type definitions) ───────────────────
# console_graphics_device.cc and spreadsheet_graphics_device.cc need DevDesc,
# GEDevDesc, pGEcontext etc. (complex structs from R_ext/GraphicsEngine.h).
# We provide the R include path ONLY for these two files.  We do NOT link against
# R64.lib — the GE functions are loaded dynamically via REngineLoader.
#
# Strategy: compile these two files with R headers in path, but guard them so
# the shim's include-guards still block Rinternals.h/RStartup.h etc.
# The graphics-engine header R_ext/GraphicsEngine.h does not conflict with the shim.

# Find R installation for GE headers (optional — falls back to mock path)
if(NOT R_GE_INCLUDE_DIR)
    if(DEFINED ENV{R_HOME})
        set(R_GE_INCLUDE_DIR "$ENV{R_HOME}/include")
    else()
        execute_process(
            COMMAND reg query "HKLM\\SOFTWARE\\R-core\\R" /v InstallPath
            OUTPUT_VARIABLE R_REG_OUTPUT
            ERROR_QUIET
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        if(R_REG_OUTPUT)
            string(REGEX MATCH "[A-Z]:\\\\[^\r\n]+" R_GE_HOME "${R_REG_OUTPUT}")
            if(R_GE_HOME)
                set(R_GE_INCLUDE_DIR "${R_GE_HOME}/include")
            endif()
        endif()
        if(NOT R_GE_INCLUDE_DIR)
            file(GLOB R_CANDIDATES "C:/Program Files/R/R-*")
            if(R_CANDIDATES)
                list(SORT R_CANDIDATES)
                list(GET R_CANDIDATES -1 R_LATEST)
                set(R_GE_INCLUDE_DIR "${R_LATEST}/include")
            endif()
        endif()
    endif()
endif()

if(R_GE_INCLUDE_DIR AND EXISTS "${R_GE_INCLUDE_DIR}/R_ext/GraphicsEngine.h")
    message(STATUS "ControlR: R GE headers found at ${R_GE_INCLUDE_DIR}")
    # r_ge_loader.cc uses forward declarations only — no special include needed.
    # console and spreadsheet graphics devices use the mock headers (Include/)
    # which are already compatible with MSVC C++ mode.
else()
    message(STATUS "ControlR: R GE headers not found — using mock headers")
endif()

# Mock R headers path for graphics device files (compatible with MSVC C++)
set(R_MOCK_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/Include")
set_source_files_properties(
    src/console_graphics_device.cc
    src/spreadsheet_graphics_device.cc
    src/r_ge_loader.cc
    PROPERTIES INCLUDE_DIRECTORIES "${R_MOCK_INCLUDE_DIR}"
)

# Source files (exclude R_Environment.cpp which uses xloper12 from Excel SDK)
file(GLOB SRC_FILES 
    "src/controlr.cc"
    "src/rinterface_common.cc"
    "src/rinterface_win.cc"
    "src/r_engine_loader.cc"
    "src/r_version_compat.cc"
    "src/convert.cc"
    "src/console_graphics_device.cc"
    "src/gdi_graphics_device.cc"
    "src/spreadsheet_graphics_device.cc"
    "../PB/variable.pb.cc"
    "../Common/windows_api_functions.cc"
    "../Common/IPC/pipe.cc"
    "../Common/IPC/message_utilities.cc"
    "../Common/child_process_log.cc"
    "../Common/json11/json11.cpp"
)

# GE stubs — C-linkage wrappers for R Graphics Engine functions
# /TC overrides the global /TP so this file compiles as C, not C++,
# guaranteeing undecorated (C-linkage) symbol names.
list(APPEND SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/r_ge_stubs.cc")
set_source_files_properties(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/r_ge_stubs.cc"
    PROPERTIES COMPILE_FLAGS "/TC"
)

list(APPEND SRC_FILES
    "${CMAKE_CURRENT_SOURCE_DIR}/../Common/LogService.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/../Common/IPC/MessageValidator.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/../Common/IPC/SafePipeHandle.cc"
)

# Build as executable
add_executable(ControlR ${SRC_FILES})

target_include_directories(ControlR BEFORE PRIVATE
    include
    src
)

target_include_directories(ControlR PRIVATE
    ../Common
    ../Common/IPC
    ../Common/Security
    ../PB
)

# Compile definitions
target_compile_definitions(ControlR PRIVATE
    WIN32
    _WINDOWS
    UNICODE
    _UNICODE
    _CRT_SECURE_NO_WARNINGS
)

# Link dependencies
# v2.4: R64.lib and RGraphApp64.lib REMOVED — R is loaded dynamically at runtime
target_link_libraries(ControlR
    PRIVATE
    libprotobuf
    gdiplus
    kernel32
    user32
    gdi32
    winspool
    comdlg32
    advapi32
    shell32
    ole32
    oleaut32
    uuid
    odbc32
    odbccp32
)

set_target_properties(ControlR PROPERTIES OUTPUT_NAME "ControlR")
