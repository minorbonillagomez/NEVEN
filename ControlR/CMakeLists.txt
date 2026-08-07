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

# Build as executable
add_executable(ControlR ${SRC_FILES})

target_include_directories(ControlR BEFORE PRIVATE
    include
    ${R_INCLUDE_DIR}
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
