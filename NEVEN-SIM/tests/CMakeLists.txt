# NEVEN-SIM Tests
# Unit tests for the simulation module components.

project(NEVEN_SIM_Tests)

# Build test sources + the SIM source files (excluding sim_main.cc which has DllMain)
file(GLOB SIM_TEST_SOURCES *.cc)
file(GLOB SIM_LIB_SOURCES ../src/sim_engine.cc ../src/sim_bridge.cc ../src/fit_service.cc ../src/montecarlo_service.cc ../src/sensitivity_service.cc ../src/sim_viewer.cc ../src/sim_excel_helpers.cc)

add_executable(NEVEN_SIM_Tests 
    ${SIM_TEST_SOURCES} 
    ${SIM_LIB_SOURCES}
    "${CMAKE_SOURCE_DIR}/Core/src/xlcall_stubs.cc"
)

target_include_directories(NEVEN_SIM_Tests PRIVATE
    ../include
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/Common
    ${CMAKE_SOURCE_DIR}/Common/json11
    ${CMAKE_SOURCE_DIR}/PB
    ${CMAKE_SOURCE_DIR}/OfficeTypes
    ${WEBVIEW2_INCLUDE_DIR}
)

target_compile_definitions(NEVEN_SIM_Tests PRIVATE UNICODE _UNICODE)

if(MSVC)
    target_compile_options(NEVEN_SIM_Tests PRIVATE /wd4576)
endif()

target_link_libraries(NEVEN_SIM_Tests 
    PRIVATE 
        Common 
        PB
        libprotobuf
        gtest
        gtest_main
        "${WEBVIEW2_LOADER_DIR}/WebView2LoaderStatic.lib"
        comdlg32
        oleacc
)

add_test(NAME NEVEN_SIM_Tests COMMAND NEVEN_SIM_Tests)
