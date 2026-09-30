project(NEVEN_Core)

file(GLOB RJ2XCL_SOURCES src/*.cc src/*.cpp)

add_library(NEVEN_Core_Objects OBJECT ${RJ2XCL_SOURCES})

add_library(NEVEN_Core SHARED $<TARGET_OBJECTS:NEVEN_Core_Objects> RJ2XCL.rc)

target_include_directories(NEVEN_Core_Objects PUBLIC 
    include
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/Common
    ${CMAKE_SOURCE_DIR}/Common/Security
    ${CMAKE_SOURCE_DIR}/Common/IPC
    ${CMAKE_SOURCE_DIR}/Common/json11
    ${CMAKE_SOURCE_DIR}/ControlR/include
    ${CMAKE_SOURCE_DIR}/ControlJulia/include
    ${CMAKE_SOURCE_DIR}/PB
    ${CMAKE_SOURCE_DIR}/OfficeTypes
    ${WEBVIEW2_INCLUDE_DIR}
)

target_compile_definitions(NEVEN_Core_Objects PUBLIC UNICODE _UNICODE)

target_link_libraries(NEVEN_Core 
    PRIVATE 
        Common 
        PB
        libprotobuf
        "${WEBVIEW2_LOADER_DIR}/WebView2LoaderStatic.lib"
        comdlg32
        oleacc
)

set_target_properties(NEVEN_Core PROPERTIES 
    OUTPUT_NAME "NEVEN64"
    PREFIX ""
)

if(MSVC)
    target_link_options(NEVEN_Core PRIVATE /DEF:${CMAKE_CURRENT_SOURCE_DIR}/src/rj2xcl.def)
endif()

# Copy pre-generated Office Type Libraries to build folder
file(COPY "${CMAKE_SOURCE_DIR}/OfficeTypes/excel.tlh" "${CMAKE_SOURCE_DIR}/OfficeTypes/excel.tli" DESTINATION "${CMAKE_CURRENT_BINARY_DIR}")
file(COPY "${CMAKE_SOURCE_DIR}/OfficeTypes/mso.tlh" "${CMAKE_SOURCE_DIR}/OfficeTypes/mso.tli" DESTINATION "${CMAKE_CURRENT_BINARY_DIR}")
