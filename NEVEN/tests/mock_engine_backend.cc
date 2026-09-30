#include <iostream>
#include <string>
#include <vector>
#include <windows.h>
#include "variable.pb.h"
#include "message_utilities.h"
#include "IPC/MessageValidator.h"

// Dummy backend to simulate R or Julia via Named Pipes for Integration Tests
int main(int argc, char* argv[]) {
    std::string pipe_name;
    
    // Parse arguments (-p pipe_name)
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "-p" && i + 1 < argc) {
            pipe_name = argv[i + 1];
            break;
        }
    }

    if (pipe_name.empty()) {
        std::cerr << "Mock Engine Error: No pipe name provided (-p)" << std::endl;
        return 1;
    }

    std::string full_pipe_name = "\\\\.\\pipe\\" + pipe_name;
    HANDLE pipe_handle = INVALID_HANDLE_VALUE;

    // The mockup must act as the SERVER. LanguageService uses CreateFileA (Client)
    pipe_handle = CreateNamedPipeA(
        full_pipe_name.c_str(),
        PIPE_ACCESS_DUPLEX,
        PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
        1,       // Max instances
        8192,    // Out buffer
        8192,    // In buffer
        0,       // Default timeout
        NULL);   // Security attributes

    if (pipe_handle == INVALID_HANDLE_VALUE) {
        std::cerr << "Mock Engine Error: Failed to create pipe: " << full_pipe_name << " err: " << GetLastError() << std::endl;
        return 2;
    }

    std::cout << "MockEngine waiting for LanguageService to connect..." << std::endl;
    bool connected = ConnectNamedPipe(pipe_handle, NULL) ? true : (GetLastError() == ERROR_PIPE_CONNECTED);

    if (!connected) {
        std::cerr << "Mock Engine Error: LanguageService failed to connect." << std::endl;
        CloseHandle(pipe_handle);
        return 3;
    }

    // Communication loop
    bool running = true;
    char buffer[8192];
    DWORD bytes_read, bytes_written;

    while (running) {
        if (ReadFile(pipe_handle, buffer, sizeof(buffer), &bytes_read, NULL)) {
            RJ2XCLBuffers::CallResponse request, response;
            if (rj2xcl::ipc::MessageValidator::SafeUnframe(request, buffer, bytes_read)) {
                
                // Set the identical ID so LanguageService maps it correctly
                response.set_id(request.id());

                if (request.has_function_call()) {
                    if (request.function_call().function() == "shutdown") {
                        running = false;
                        response.mutable_result()->set_boolean(true);
                    } else if (request.function_call().function() == "list-functions") {
                        // Dummy list
                        auto list = response.mutable_function_list();
                        auto func = list->add_functions();
                        func->mutable_function()->set_name("mock_func");
                    } else {
                        // Echo success
                        response.mutable_result()->set_boolean(true);
                    }
                } else if (request.has_code()) {
                    response.mutable_result()->set_str("MOCK_OK");
                }

                std::string framed = MessageUtilities::Frame(response);
                WriteFile(pipe_handle, framed.c_str(), framed.size(), &bytes_written, NULL);
            }
        } else {
            DWORD err = GetLastError();
            if (err == ERROR_BROKEN_PIPE) break;
        }
    }

    CloseHandle(pipe_handle);
    return 0;
}
