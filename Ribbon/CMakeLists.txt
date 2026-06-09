# Ribbon COM Add-in for NEVEN
# Builds NEVENRibbon.dll — COM in-process server for Excel Ribbon integration
project(NEVENRibbon)

# MIDL compile the IDL to generate type library
set(IDL_FILE ${CMAKE_CURRENT_SOURCE_DIR}/RJ2XCLRibbon.idl)
set(TLB_FILE ${CMAKE_CURRENT_BINARY_DIR}/NEVENRibbon.tlb)
set(IDL_H ${CMAKE_CURRENT_BINARY_DIR}/NEVENRibbon_i.h)
set(IDL_C ${CMAKE_CURRENT_BINARY_DIR}/NEVENRibbon_i.c)

add_custom_command(
    OUTPUT ${TLB_FILE} ${IDL_H} ${IDL_C}
    COMMAND midl /nologo /W1 /char signed /env x64 /Oicf
            /out "${CMAKE_CURRENT_BINARY_DIR}"
            /h "NEVENRibbon_i.h"
            /iid "NEVENRibbon_i.c"
            /tlb "NEVENRibbon.tlb"
            "${IDL_FILE}"
    # Copy .tlb to source dir so the .rc file can find it
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${CMAKE_CURRENT_BINARY_DIR}/NEVENRibbon.tlb"
            "${CMAKE_CURRENT_SOURCE_DIR}/RJ2XCLRibbon.tlb"
    DEPENDS ${IDL_FILE}
    COMMENT "Compiling IDL: RJ2XCLRibbon.idl"
)

add_library(NEVENRibbon SHARED
    dllmain.cpp
    ribbon.cc
    ribbon_connect.cc
    stdafx.cpp
    ${IDL_C}
    RJ2XCLRibbon_utf8.rc
)

# Add generated files as dependencies
target_sources(NEVENRibbon PRIVATE ${TLB_FILE})

target_include_directories(NEVENRibbon PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
    ${CMAKE_SOURCE_DIR}/Common
    ${CMAKE_SOURCE_DIR}/OfficeTypes
)

target_compile_definitions(NEVENRibbon PRIVATE
    UNICODE _UNICODE _WINDLL _ATL_NO_AUTOMATIC_NAMESPACE
)

target_link_libraries(NEVENRibbon PRIVATE
    gdiplus
    shlwapi
    psapi
)

# Module definition file for COM exports
target_link_options(NEVENRibbon PRIVATE /DEF:${CMAKE_CURRENT_SOURCE_DIR}/Ribbon.def)

set_target_properties(NEVENRibbon PROPERTIES
    OUTPUT_NAME "NEVENRibbon"
    PREFIX ""
)

# Copy to Dist after build
add_custom_command(TARGET NEVENRibbon POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:NEVENRibbon> ${CMAKE_BINARY_DIR}/Dist/NEVENRibbon.dll
    COMMENT "Packaging: NEVENRibbon.dll → Dist/"
)
