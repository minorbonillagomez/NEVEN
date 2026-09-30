add_executable(rj2xcl_tests 
    common_tests.cc
    raii_xloper_tests.cc
    callback_dispatcher_tests.cc
    discovery_tests.cc
    security_tests.cc
    sandbox_tests.cc
    python_sandbox_pbt.cc
    config_service_tests.cc
    type_conversion_tests.cc
    callback_behavior_tests.cc
    basic_functions_tests.cc
    com_object_map_tests.cc
    language_service_tests.cc
    integration_tests.cc
    reliability_tests.cc
    reliability_pbt.cc
    webview2_pbt.cc
    e2e_tests.cc
    new_functions_tests.cc
    viewer_professional_tests.cc
    build_verification_tests.cc
    repo_hygiene_tests.cc
    input_sanitizer_pbt.cc
    input_sanitizer_tests.cc
    sandbox_path_pbt.cc
    sandbox_blocklist_pbt.cc
    protobuf_ipc_pbt.cc
    pipe_lifecycle_tests.cc
    r_library_tests.cc
    env_lookup_pbt.cc
    python_reactivation_exploration_pbt.cc
    python_reactivation_preservation_pbt.cc
)

target_link_libraries(rj2xcl_tests 
    PRIVATE 
        GTest::gtest_main 
        $<TARGET_OBJECTS:NEVEN_Core_Objects>
        Common
        PB
        libprotobuf
        gmock
        rapidcheck
        "${WEBVIEW2_LOADER_DIR}/WebView2LoaderStatic.lib"
        winhttp
)

# Compilar Mock Engine Backend
add_executable(mock_engine_backend mock_engine_backend.cc)
target_link_libraries(mock_engine_backend PRIVATE Common PB libprotobuf)

# Asegurar que mock_engine_backend se copia junto a los tests
add_custom_command(TARGET rj2xcl_tests POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:mock_engine_backend> $<TARGET_FILE_DIR:rj2xcl_tests>
)

target_include_directories(rj2xcl_tests PRIVATE 
    ${CMAKE_SOURCE_DIR}/Common
    ${CMAKE_SOURCE_DIR}/Common/IPC
    ${CMAKE_SOURCE_DIR}/Common/Security
    ${CMAKE_SOURCE_DIR}/PB
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/Core/include
    ${CMAKE_SOURCE_DIR}/RJ2XCL/ExcelLib
    ${rapidcheck_SOURCE_DIR}/include
    ${rapidcheck_SOURCE_DIR}/extras/gtest/include
)

# Pass CMAKE_SOURCE_DIR as a compile definition for build verification tests
target_compile_definitions(rj2xcl_tests PRIVATE
    CMAKE_SOURCE_DIR="${CMAKE_SOURCE_DIR}"
)

include(GoogleTest)
gtest_discover_tests(rj2xcl_tests)
