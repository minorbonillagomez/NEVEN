# Addin Module: Packages all components into Dist/ for deployment
#
# The XLL format is a DLL with a renamed extension that Excel recognises
# as an add-in. RJ2XCL.dll already exports all required XLL entry-points
# (xlAutoOpen, xlAutoClose, xlAutoAdd, xlAutoRemove, xlAutoFree12).
#
# This target copies all compiled artifacts and config files to Dist/
# so that the installer packaging script can find them in a predictable location.

project(NEVEN_Addin)

# Ensure the distribution directory exists
set(NEVEN_DIST_DIR "${CMAKE_BINARY_DIR}/Dist")
file(MAKE_DIRECTORY ${NEVEN_DIST_DIR})
file(MAKE_DIRECTORY ${NEVEN_DIST_DIR}/startup)
file(MAKE_DIRECTORY ${NEVEN_DIST_DIR}/examples)

# Copy NEVEN64.xll to Dist/ after each build (already built as .xll)
add_custom_target(NEVEN_XLL ALL
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "$<TARGET_FILE:NEVEN_Core>"
        "${NEVEN_DIST_DIR}/NEVEN64.xll"
    DEPENDS NEVEN_Core
    COMMENT "Packaging: NEVEN64.xll -> Dist/NEVEN64.xll"
)

# Copy ControlR.exe to Dist/ (if it was built)
add_custom_command(TARGET NEVEN_XLL POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "$<TARGET_FILE:ControlR>"
        "${NEVEN_DIST_DIR}/ControlR.exe"
    COMMENT "Packaging: ControlR.exe -> Dist/"
)

# Copy ControlJulia.exe to Dist/ (if it was built)
add_custom_command(TARGET NEVEN_XLL POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "$<TARGET_FILE:ControlJulia>"
        "${NEVEN_DIST_DIR}/ControlJulia.exe"
    COMMENT "Packaging: ControlJulia.exe -> Dist/"
)

# Copy ControlPython.exe to Dist/ (if it was built)
if(NEVEN_ENABLE_PYTHON)
    add_custom_command(TARGET NEVEN_XLL POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "$<TARGET_FILE:ControlPython>"
            "${NEVEN_DIST_DIR}/ControlPython.exe"
        COMMENT "Packaging: ControlPython.exe -> Dist/"
    )
endif()

# Copy config templates to Dist/
add_custom_command(TARGET NEVEN_XLL POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_SOURCE_DIR}/Install/neven-config.json"
        "${NEVEN_DIST_DIR}/neven-config.json"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_SOURCE_DIR}/Install/neven-languages.json"
        "${NEVEN_DIST_DIR}/neven-languages.json"
    COMMENT "Packaging: copying config templates to Dist/"
)

# Copy startup scripts to Dist/startup/
add_custom_command(TARGET NEVEN_XLL POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_SOURCE_DIR}/startup/startup.r"
        "${NEVEN_DIST_DIR}/startup/startup.r"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_SOURCE_DIR}/startup/startup.jl"
        "${NEVEN_DIST_DIR}/startup/startup.jl"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_SOURCE_DIR}/startup/startup.py"
        "${NEVEN_DIST_DIR}/startup/startup.py"
    COMMENT "Packaging: copying startup scripts to Dist/startup/"
)

# Copy example files to Dist/examples/
add_custom_command(TARGET NEVEN_XLL POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_SOURCE_DIR}/Ejemplos"
        "${NEVEN_DIST_DIR}/examples"
    COMMENT "Packaging: copying examples to Dist/examples/"
)

message(STATUS "Addin: XLL packaging target configured -> ${NEVEN_DIST_DIR}/")
