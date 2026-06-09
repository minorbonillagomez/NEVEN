# ControlPython Submodule — Builds ControlPython.exe (Python language service process)
#
# This executable embeds CPython and communicates with NEVEN.dll via Named Pipes.
# It requires Python >= 3.10 to be installed on the build machine.
#
# Set PYTHON_HOME to your Python installation if auto-detection fails:
#   cmake .. -A x64 -DPYTHON_HOME="C:/Users/.../Programs/Python/Python312"

project(ControlPython)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Find Python installation ---
if(NOT PYTHON_HOME)
    # Try environment variable
    if(DEFINED ENV{PYTHON_HOME})
        set(PYTHON_HOME "$ENV{PYTHON_HOME}")
    else()
        # Heuristic: Check LocalAppData\Programs\Python\Python3*
        file(GLOB PYTHON_CANDIDATES "$ENV{LOCALAPPDATA}/Programs/Python/Python3*")
        if(NOT PYTHON_CANDIDATES)
            # Fallback: Check Program Files
            file(GLOB PYTHON_CANDIDATES "$ENV{PROGRAMFILES}/Python3*")
        endif()
        if(PYTHON_CANDIDATES)
            list(SORT PYTHON_CANDIDATES)
            list(GET PYTHON_CANDIDATES -1 PYTHON_HOME)
        endif()
    endif()
endif()

if(PYTHON_HOME)
    message(STATUS "ControlPython: Using PYTHON_HOME = ${PYTHON_HOME}")
    set(PYTHON_INCLUDE_DIR "${PYTHON_HOME}/include")
    set(PYTHON_LIB_DIR "${PYTHON_HOME}/libs")
else()
    message(WARNING "ControlPython: PYTHON_HOME not found. Using mock headers. ControlPython may not link correctly.")
    set(PYTHON_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/Include")
    set(PYTHON_LIB_DIR "")
endif()

# Source files
set(SRC_FILES
    "src/control_python.cc"
    "src/python_interface.cc"
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
add_executable(ControlPython ${SRC_FILES})

# Python headers FIRST, then project headers
target_include_directories(ControlPython BEFORE PRIVATE
    ${PYTHON_INCLUDE_DIR}
)

target_include_directories(ControlPython PRIVATE
    include
    ../Common
    ../Common/IPC
    ../PB
)

# Compile definitions
target_compile_definitions(ControlPython PRIVATE
    WIN32
    _WINDOWS
    _CRT_SECURE_NO_WARNINGS
)

# Link directories for Python stable ABI library
if(PYTHON_LIB_DIR)
    target_link_directories(ControlPython PRIVATE "${PYTHON_LIB_DIR}")
endif()

# Link dependencies
target_link_libraries(ControlPython
    PRIVATE
    PB
    libprotobuf
    kernel32
    user32
    advapi32
    python3
)

# Stack guard fix: 2MB stack to provide headroom for CPython initialization
target_link_options(ControlPython PRIVATE /STACK:2097152)

set_target_properties(ControlPython PROPERTIES OUTPUT_NAME "ControlPython")
