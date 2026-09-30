# ControlJulia Submodule — Builds ControlJulia.exe (Julia language service process)
#
# This executable embeds Julia and communicates with RJ2XCL.dll via Named Pipes.
# It requires Julia to be installed on the build machine.
#
# Set JULIA_HOME to your Julia installation if auto-detection fails:
#   cmake .. -A x64 -DJULIA_HOME="C:/Users/.../Programs/Julia-1.12.6"

project(ControlJulia)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Find Julia installation ---
if(NOT JULIA_HOME)
    if(DEFINED ENV{JULIA_HOME})
        set(JULIA_HOME "$ENV{JULIA_HOME}")
    else()
        # Heuristic: Check LocalAppData\Programs\Julia*
        file(GLOB JULIA_CANDIDATES "$ENV{LOCALAPPDATA}/Programs/Julia*")
        if(JULIA_CANDIDATES)
            list(SORT JULIA_CANDIDATES)
            list(GET JULIA_CANDIDATES -1 JULIA_HOME)
        endif()
    endif()
endif()

if(JULIA_HOME)
    message(STATUS "ControlJulia: Using JULIA_HOME = ${JULIA_HOME}")
    set(JULIA_INCLUDE_DIR "${JULIA_HOME}/include/julia")
else()
    message(WARNING "ControlJulia: JULIA_HOME not found. Using mock headers.")
    set(JULIA_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/Include")
endif()

# Source files (exclude Julia_Environment.cpp which uses xloper12)
file(GLOB SRC_FILES 
    "src/control_julia.cc"
    "src/julia_interface.cc"
    "src/JuliaConversion.cpp"
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
add_executable(ControlJulia ${SRC_FILES})

# Julia headers FIRST, then project mocks
target_include_directories(ControlJulia BEFORE PRIVATE
    ${JULIA_INCLUDE_DIR}
)

target_include_directories(ControlJulia PRIVATE
    include
    ../Common
    ../Common/IPC
    ../Common/Security
    ../PB
)

# Compile definitions
target_compile_definitions(ControlJulia PRIVATE
    WIN32
    _WINDOWS
    _CRT_SECURE_NO_WARNINGS
)

# Link dependencies
target_link_libraries(ControlJulia
    PRIVATE
    PB
    libprotobuf
    kernel32
    user32
    advapi32
    "${CMAKE_CURRENT_SOURCE_DIR}/lib/libjulia.lib"
)

set_target_properties(ControlJulia PROPERTIES OUTPUT_NAME "ControlJulia")
