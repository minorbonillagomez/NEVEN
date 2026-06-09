/**
 * Copyright (c) 2026 NEVEN Project
 */

#include "ConfigService.h"
#include "module_functions.h"
#include "LogService.h"
#include <iostream>
#include <ctime>
#include <Lmcons.h>

namespace rj2xcl {

    ConfigService::ConfigService() 
        : dev_flags_(0), config_(json11::Json()) {
    }

    ConfigService& ConfigService::Instance() {
        static ConfigService instance;
        return instance;
    }

    rj2xcl::Result<void, APIFunctions::FileError> ConfigService::Initialize() {
        
        // 1. Get dev flags from registry
        APIFunctions::GetRegistryDWORD(dev_flags_, "NEVEN.DevOptions");

        // 2. Resolve home directory
        home_directory_ = ModuleFunctions::ModulePath();
        if (home_directory_.empty()) {
            RJ2XCL_LOG_WARN("NEVEN home directory not found");
        }

        // 3. Set environment variable
        SetEnvironmentVariableA("NEVEN_HOME", home_directory_.c_str());

        // 4. Load main config
        auto result = ReadJsonFile("neven-config.json");
        if (result.is_success()) {
            config_ = result.value();
            ValidateConfig();
            return rj2xcl::Result<void, APIFunctions::FileError>::Success();
        }

        return rj2xcl::Result<void, APIFunctions::FileError>::Failure(result.error());
    }

    Result<json11::Json, APIFunctions::FileError> ConfigService::ReadJsonFile(const std::string &filename) {
        std::string path = home_directory_ + filename;
        auto result = APIFunctions::FileContents(path);
        
        if (result.is_failure()) {
            return Result<json11::Json, APIFunctions::FileError>::Failure(result.error());
        }

        std::string parse_error;
        auto json = json11::Json::parse(result.value(), parse_error, json11::COMMENTS);
        // RESOLVED: C-06 — validate parse_error before returning Success
        if (!parse_error.empty()) {
            RJ2XCL_LOG_ERR("JSON parse error in '%s': %s", filename.c_str(), parse_error.c_str());
            return Result<json11::Json, APIFunctions::FileError>::Failure(APIFunctions::FileError::ParseError);
        }
        return Result<json11::Json, APIFunctions::FileError>::Success(json);
    }

    void ConfigService::ValidateConfig() {
        auto rj2xcl = config_["NEVEN"];
        
        // Validate callTimeoutMs: must be positive, max 30 minutes
        int timeout = rj2xcl["callTimeoutMs"].int_value();
        if (timeout < 0 || timeout > 1800000) {
            RJ2XCL_LOG_WARN("callTimeoutMs out of range (0-1800000), using default 600000");
        }

        // Validate maxRetries: must be 0-10
        int retries = rj2xcl["maxRetries"].int_value();
        if (retries < 0 || retries > 10) {
            RJ2XCL_LOG_WARN("maxRetries out of range (0-10), using default 2");
        }

        // Validate paths: no ".." traversal, no pipe characters, no command separators
        auto validate_path = [](const std::string& path, const std::string& name) -> bool {
            if (path.empty()) return true; // empty = use default
            // Block path traversal
            if (path.find("..") != std::string::npos) {
                RJ2XCL_LOG_WARN("SECURITY: %s contains '..' path traversal — blocked", name.c_str());
                return false;
            }
            // Block command injection characters
            for (char c : {'|', '&', ';', '`', '$', '>', '<'}) {
                if (path.find(c) != std::string::npos) {
                    RJ2XCL_LOG_WARN("SECURITY: %s contains suspicious character '%c' — blocked", name.c_str(), c);
                    return false;
                }
            }
            return true;
        };

        validate_path(rj2xcl["functionsDirectory"].string_value(), "functionsDirectory");
        validate_path(rj2xcl["graphicsDirectory"].string_value(), "graphicsDirectory");
        validate_path(rj2xcl["R"]["home"].string_value(), "R.home");
        validate_path(rj2xcl["Julia"]["home"].string_value(), "Julia.home");

        // Validate Quarto paths
        auto quarto = config_["Quarto"];
        validate_path(quarto["path"].string_value(), "Quarto.path");
        validate_path(quarto["outputDirectory"].string_value(), "Quarto.outputDirectory");
    }

    bool ConfigService::RequestSandboxDisable() {
        // Show confirmation dialog via MessageBox (Excel parent window)
        HWND excel_hwnd = FindWindowA("XLMAIN", nullptr);
        int result = MessageBoxA(
            excel_hwnd,
            "WARNING: You are about to disable the code execution sandbox.\n\n"
            "This will allow ALL code (including potentially dangerous operations "
            "like system(), file.remove(), etc.) to execute without restriction.\n\n"
            "Only disable the sandbox in trusted development environments.\n\n"
            "Do you want to disable the sandbox?",
            "NEVEN \xC2\xB7 Security",
            MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2
        );

        if (result != IDYES) {
            // User cancelled — keep sandbox enabled
            RJ2XCL_LOG_INFO("[Security] Sandbox disable request cancelled by user");
            return false;
        }

        // User confirmed — disable sandbox in config
        // Rebuild config with sandboxEnabled = false
        auto neven_obj = config_["NEVEN"].object_items();
        neven_obj["sandboxEnabled"] = json11::Json(false);
        auto root_obj = config_.object_items();
        root_obj["NEVEN"] = json11::Json(neven_obj);
        config_ = json11::Json(root_obj);

        // Get Windows username
        char username[UNLEN + 1] = {};
        DWORD username_len = UNLEN + 1;
        if (!GetUserNameA(username, &username_len)) {
            strcpy_s(username, "UNKNOWN");
        }

        // Get current timestamp
        time_t now = time(nullptr);
        struct tm tm_buf;
        localtime_s(&tm_buf, &now);
        char timestamp[32];
        strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", &tm_buf);

        // Log the disable event with username and timestamp
        RJ2XCL_LOG_WARN("[Security] Sandbox disabled by %s at %s", username, timestamp);

        return true;
    }

} // namespace rj2xcl
