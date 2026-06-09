/**
 * Copyright (c) 2026 RJ2XCL Project
 */

#include "EnvService.h"
#include <vector>
#include <algorithm>
#include <array>

namespace rj2xcl {

    EnvService& EnvService::Instance() {
        static EnvService instance;
        return instance;
    }

    void EnvService::SetSystemMetadata(const std::wstring& version, const std::string& build_date) {
        SetEnvironmentVariableW(L"RJ2XCL_VERSION", version.c_str());
        SetEnvironmentVariableA("RJ2XCL_BUILD_DATE", build_date.c_str());
    }

    std::string EnvService::ExpandEnvStrings(const std::string& input) {
        DWORD required_size = ::ExpandEnvironmentStringsA(input.c_str(), nullptr, 0);
        if (required_size == 0) return input;

        std::vector<char> buffer(required_size);
        if (::ExpandEnvironmentStringsA(input.c_str(), buffer.data(), required_size)) {
            return std::string(buffer.data());
        }
        return input;
    }

    void EnvService::PrependToPath(const std::string& directory) {
        if (directory.empty()) return;

        char path_buffer[32767]; // Max environment variable size
        DWORD size = GetEnvironmentVariableA("PATH", path_buffer, sizeof(path_buffer));
        
        if (size > 0 && size < sizeof(path_buffer)) {
            std::string current_path(path_buffer);
            // Only prepend if not already there
            if (current_path.find(directory) == std::string::npos) {
                std::string new_path = directory + ";" + current_path;
                SetEnvironmentVariableA("PATH", new_path.c_str());
            }
        } else if (size == 0) {
            SetEnvironmentVariableA("PATH", directory.c_str());
        }
    }

    std::string GetNevenEnvVar(const std::string& base_name) {
        // Priority: NEVEN_ > RJ2XCL_ > BERT_ > empty string
        static constexpr std::array<const char*, 3> prefixes = {
            "NEVEN_", "RJ2XCL_", "BERT_"
        };

        for (const auto& prefix : prefixes) {
            std::string var_name = std::string(prefix) + base_name;
            // Use GetEnvironmentVariableA to check if the variable is set
            DWORD size = GetEnvironmentVariableA(var_name.c_str(), nullptr, 0);
            if (size > 0) {
                std::vector<char> buffer(size);
                DWORD result = GetEnvironmentVariableA(var_name.c_str(), buffer.data(), size);
                if (result > 0 && result < size) {
                    return std::string(buffer.data(), result);
                }
            }
        }

        return std::string();
    }

} // namespace rj2xcl
