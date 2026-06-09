# Common Module static library for RJ2XCL framework - Core Utilities
project(Common)

set(COMMON_SOURCES
    module_functions.cc
    windows_api_functions.cc
    AutoLoader.cc
    GCMonitor.cc
    RuntimeLoader.cc
    ConfigService.cc
    WindowManager.cc
    debug_functions.cc
    LogService.cc
    DiscoveryService.cc
    EnvService.cc
    QuartoService.cc
    child_process_log.cc
    json11/json11.cpp
    # Security module
    Security/InputSanitizer.cc
    Security/SandboxVerifier.cc
    Security/SecurityService.cc
    # IPC module
    IPC/MessageValidator.cc
    IPC/SafePipeHandle.cc
    IPC/pipe.cc
    IPC/message_utilities.cc
    IPC/REPLBridge.cc
    # WebView2 Viewer components
    ViewerManager.cc
    ViewerWindow.cc
    PlutoManager.cc
    ContentPipeline.cc
    PostMessageBridge.cc
    NotebookLibrary.cc
    NotebookExporter.cc
    PresentationBuilder.cc
    MenuService.cc
    CrashHandler.cc
    # REPL Console components
    REPLManager.cc
    REPLLanguageAccessor.cc
    # Diagnostic Stream
    DiagnosticRouter.cc
    # Startup Optimization
    NevenStartupConfig.cc
    NevenStatusBarReporter.cc
    NevenWatchdogTimer.cc
    NevenProgressiveRegistrar.cc
    NevenProgressiveRegisterExport.cc
    NevenBackgroundConnector.cc
    NevenInitOrchestrator.cc
)

add_library(Common STATIC ${COMMON_SOURCES})

target_include_directories(Common PUBLIC 
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/json11
    ${CMAKE_CURRENT_SOURCE_DIR}/Security
    ${CMAKE_CURRENT_SOURCE_DIR}/IPC
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/PB
    ${CMAKE_SOURCE_DIR}/Core/include
    ${WEBVIEW2_INCLUDE_DIR}
)

target_link_libraries(Common PRIVATE libprotobuf shlwapi bcrypt winhttp)
