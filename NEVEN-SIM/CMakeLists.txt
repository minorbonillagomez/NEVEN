# NEVEN-SIM: Modular Simulation Add-in for Excel
#
# Builds NEVEN-SIM.xll — a separate XLL that loads alongside NEVEN64.xll
# and provides Monte Carlo simulation, distribution fitting, and sensitivity analysis.
#
# Requires: Common.lib, PB.lib, WebView2 SDK, Excel SDK headers

project(NEVEN_SIM)

file(GLOB SIM_SOURCES src/*.cc)

# Include xlcall_stubs.cc for Excel12/Excel12v/SetExcel12EntryPt implementation
set(SIM_SOURCES ${SIM_SOURCES} "${CMAKE_SOURCE_DIR}/Core/src/xlcall_stubs.cc")

add_library(NEVEN_SIM SHARED ${SIM_SOURCES} NEVEN-SIM.rc)

target_include_directories(NEVEN_SIM PUBLIC 
    include
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/Common
    ${CMAKE_SOURCE_DIR}/Common/json11
    ${CMAKE_SOURCE_DIR}/PB
    ${CMAKE_SOURCE_DIR}/OfficeTypes
    ${WEBVIEW2_INCLUDE_DIR}
)

target_compile_definitions(NEVEN_SIM PUBLIC UNICODE _UNICODE)

# Disable C4576: compound literal is a non-standard extension (used in xlAddInManagerInfo12)
if(MSVC)
    target_compile_options(NEVEN_SIM PRIVATE /wd4576)
endif()

target_link_libraries(NEVEN_SIM 
    PRIVATE 
        Common 
        PB
        libprotobuf
        "${WEBVIEW2_LOADER_DIR}/WebView2LoaderStatic.lib"
        comdlg32
        oleacc
)

# Output as NEVEN-SIM.dll (renamed to .xll during packaging)
set_target_properties(NEVEN_SIM PROPERTIES 
    OUTPUT_NAME "NEVEN-SIM"
    PREFIX ""
    SUFFIX ".xll"
)

# Module definition file for XLL exports
if(MSVC)
    target_link_options(NEVEN_SIM PRIVATE /DEF:${CMAKE_CURRENT_SOURCE_DIR}/src/neven_sim.def)
endif()

message(STATUS "NEVEN-SIM: Simulation module configured")

# Tests
add_subdirectory(tests)
