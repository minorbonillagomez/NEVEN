# ControlR Submodule — Builds ControlR.exe (R language service process)
#
# This executable embeds R and communicates with RJ2XCL.dll via Named Pipes.
# It requires R to be installed on the build machine.
#
# Set R_HOME to your R installation if auto-detection fails:
#   cmake .. -A x64 -DR_HOME="C:/Program Files/R/R-4.4.1"

project(ControlR)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Find R installation ---
if(NOT R_HOME)
    # Try environment variable
    if(DEFINED ENV{R_HOME})
        set(R_HOME "$ENV{R_HOME}")
    else()
        # Try registry (Windows)
        execute_process(
            COMMAND reg query "HKLM\\SOFTWARE\\R-core\\R" /v InstallPath
            OUTPUT_VARIABLE R_REG_OUTPUT
            ERROR_QUIET
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        if(R_REG_OUTPUT)
            string(REGEX MATCH "[A-Z]:\\\\[^\r\n]+" R_HOME "${R_REG_OUTPUT}")
        endif()
        
        # Fallback: try common paths
        if(NOT R_HOME)
            file(GLOB R_CANDIDATES "C:/Program Files/R/R-*")
            if(R_CANDIDATES)
                list(SORT R_CANDIDATES)
                list(GET R_CANDIDATES -1 R_HOME)
            endif()
        endif()
    endif()
endif()

if(R_HOME)
    message(STATUS "ControlR: Using R_HOME = ${R_HOME}")
    set(R_INCLUDE_DIR "${R_HOME}/include")
    set(R_BIN_DIR "${R_HOME}/bin/x64")
else()
    message(WARNING "ControlR: R_HOME not found. Using mock headers from Include/. ControlR may not link correctly.")
    set(R_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/Include")
    set(R_BIN_DIR "")
endif()

# Source files (exclude R_Environment.cpp which uses xloper12 from Excel SDK)
file(GLOB SRC_FILES 
    "src/controlr.cc"
    "src/rinterface_common.cc"
    "src/rinterface_win.cc"
    "src/r_engine_loader.cc"
    "src/r_version_compat.cc"
    "src/rinterface_loop.cc"
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

list(APPEND SRC_FILES
    "${CMAKE_CURRENT_SOURCE_DIR}/../Common/LogService.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/../Common/IPC/MessageValidator.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/../Common/IPC/SafePipeHandle.cc"
)

# rcall_seh.cc: SEH wrapper compiled WITHOUT optimizations (/Od) and WITHOUT LTCG (/GL-)
# so the __except block is never eliminated by the optimizer or linker
list(APPEND SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/rcall_seh.cc")
set_source_files_properties(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/rcall_seh.cc"
    PROPERTIES COMPILE_FLAGS "/Od /GL-"
)

# v2.4 Dynamic Loading: r_engine_loader.cc, r_version_compat.cc, controlr.cc, rinterface_win.cc
# must NOT have R_INCLUDE_DIR in their include path — they define their own R types
# via r_engine_loader.h and would clash with the real R headers.
# We pass /I- (remove all includes) is not available in MSVC, so we use compile definitions
# to guard against the conflicting headers (NEVEN_DYNAMIC_LOAD is defined in the files themselves).
# The R_INCLUDE_DIR is kept for rinterface_common.cc which still uses real R headers directly.

# Build as executable
add_executable(ControlR ${SRC_FILES})

# v2.4: Separate include paths by TU role:
# - Loader TUs (r_engine_loader.cc, r_version_compat.cc, controlr.cc, rinterface_win.cc)
#   must NOT see R_INCLUDE_DIR — they define their own R typedefs and clash with real headers.
# - R-direct TUs (rinterface_common.cc, console/gdi/spreadsheet graphics, convert.cc)
#   need the real R headers from R_INCLUDE_DIR.

# Files that must NOT have R_INCLUDE_DIR:
set(LOADER_TUS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/r_engine_loader.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/r_version_compat.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/rinterface_loop.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/controlr.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/rinterface_win.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/rcall_seh.cc"
)

# Files that still need real R headers:
set(R_DIRECT_TUS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/rinterface_common.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/convert.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/console_graphics_device.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/gdi_graphics_device.cc"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/spreadsheet_graphics_device.cc"
)

# Apply R_INCLUDE_DIR only to R-direct TUs via per-file include property
# NOTE: set_source_files_properties INCLUDE_DIRECTORIES overrides target-level includes,
# so we must list ALL needed include paths explicitly.
set(COMMON_INCLUDES
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${CMAKE_SOURCE_DIR}/Common"
    "${CMAKE_SOURCE_DIR}/Common/IPC"
    "${CMAKE_SOURCE_DIR}/Common/Security"
    "${CMAKE_SOURCE_DIR}/PB"
)

# Loader TUs also need the loader/ subdirectory
set(LOADER_INCLUDES
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${CMAKE_CURRENT_SOURCE_DIR}/include/loader"
    "${CMAKE_SOURCE_DIR}/Common"
    "${CMAKE_SOURCE_DIR}/Common/IPC"
    "${CMAKE_SOURCE_DIR}/Common/Security"
    "${CMAKE_SOURCE_DIR}/PB"
)

# Convert list to semicolon-separated string for set_source_files_properties
list(JOIN COMMON_INCLUDES ";" COMMON_INCLUDES_STR)
list(JOIN LOADER_INCLUDES ";" LOADER_INCLUDES_STR)

foreach(tu IN LISTS R_DIRECT_TUS)
    set_source_files_properties(${tu} PROPERTIES
        INCLUDE_DIRECTORIES "${COMMON_INCLUDES_STR};${R_INCLUDE_DIR}"
    )
endforeach()

# Loader TUs: common + loader paths, no R headers
foreach(tu IN LISTS LOADER_TUS)
    set_source_files_properties(${tu} PROPERTIES
        INCLUDE_DIRECTORIES "${LOADER_INCLUDES_STR}"
    )
endforeach()

target_include_directories(ControlR BEFORE PRIVATE
    include
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
# Note: R64.lib still needed for graphics device APIs (GE functions, Rf_* in graphics TUs)
# The startup API (R_DefParams, setup_Rmainloop etc.) is loaded dynamically via REngineLoader.
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
    "${CMAKE_CURRENT_SOURCE_DIR}/lib/R64.lib"
    "${CMAKE_CURRENT_SOURCE_DIR}/lib/RGraphApp64.lib"
)

set_target_properties(ControlR PROPERTIES OUTPUT_NAME "ControlR")
