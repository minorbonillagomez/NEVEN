/**
 * Copyright (c) 2026 RJ2XCL Project
 */

#include "QuartoService.h"
#include "ConfigService.h"
#include "DiscoveryService.h"
#include "EnvService.h"
#include "LogService.h"
#include "UniqueHandle.h"
#include "Security/InputSanitizer.h"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace rj2xcl {

    QuartoService::QuartoService()
        : initialized_(false), enabled_(true), available_(false),
          auto_open_(true), timeout_ms_(300000) {
    }

    QuartoService& QuartoService::Instance() {
        static QuartoService instance;
        return instance;
    }

    // -----------------------------------------------------------------------
    // Input validation
    // -----------------------------------------------------------------------

    bool QuartoService::ValidateInputSecurity(const std::string& input, std::string& error_msg) {
        if (input.empty()) {
            return true;
        }

        // Block path traversal
        if (input.find("..") != std::string::npos) {
            error_msg = "Input contains '..' path traversal";
            return false;
        }

        // Block command injection characters (original + new: " \n \r %)
        const char blocked_chars[] = { '|', '&', ';', '`', '<', '>', '"', '\n', '\r', '%' };
        for (char c : blocked_chars) {
            if (input.find(c) != std::string::npos) {
                error_msg = std::string("Input contains suspicious character '") + c + "'";
                return false;
            }
        }

        // Use InputSanitizer::ValidateArgument for stricter argument validation
        auto result = security::InputSanitizer::ValidateArgument(input);
        if (!result.is_valid) {
            error_msg = "InputSanitizer rejected input: " + result.error_message;
            return false;
        }

        return true;
    }

    bool QuartoService::ValidateExtension(const std::string& resolved_path) {
        if (resolved_path.size() < 4) return false;

        std::string ext = resolved_path.substr(resolved_path.size() - 4);
        std::transform(ext.begin(), ext.end(), ext.begin(),
                       [](unsigned char c) { return (char)std::tolower(c); });
        return ext == ".qmd";
    }

    bool QuartoService::ValidateFormat(const std::string& format, std::string& error_msg) {
        std::string lower = format;
        std::transform(lower.begin(), lower.end(), lower.begin(),
                       [](unsigned char c) { return (char)std::tolower(c); });

        if (lower == "html" || lower == "pdf" || lower == "docx") {
            return true;
        }

        error_msg = "Unsupported format '" + format + "'. Use html, pdf, or docx";
        return false;
    }

    std::string QuartoService::ResolveFilePath(const std::string& file_path) {
        if (file_path.empty()) return file_path;

        // Absolute path: drive letter (e.g., C:\) or UNC path (\\server)
        if (file_path.size() >= 2) {
            if (file_path[1] == ':') return file_path;           // Drive letter
            if (file_path[0] == '\\' && file_path[1] == '\\') return file_path; // UNC
        }

        // Relative path: resolve against output directory
        std::string base = output_directory_;
        if (!base.empty() && base.back() != '\\' && base.back() != '/') {
            base += '\\';
        }
        return base + file_path;
    }

    std::string QuartoService::ConstructOutputPath(const std::string& qmd_path,
                                                    const std::string& format) {
        // Find the last '.' that starts the .qmd extension
        // We need to replace only the final .qmd (case-insensitive)
        if (qmd_path.size() < 4) return qmd_path;

        std::string stem = qmd_path.substr(0, qmd_path.size() - 4);

        std::string ext;
        if (format == "html") ext = ".html";
        else if (format == "pdf") ext = ".pdf";
        else if (format == "docx") ext = ".docx";
        else ext = "." + format;

        return stem + ext;
    }

    // -----------------------------------------------------------------------
    // Initialization and CLI discovery
    // -----------------------------------------------------------------------

    void QuartoService::Initialize() {
        if (initialized_) return;
        initialized_ = true;

        auto& config = ConfigService::Instance();

        // Read config
        enabled_ = config.IsQuartoEnabled();
        if (!enabled_) {
            RJ2XCL_LOG_INFO("Quarto integration is disabled in configuration");
            available_ = false;
            return;
        }

        auto& env = EnvService::Instance();

        // Expand environment variables in paths
        output_directory_ = env.ExpandEnvStrings(config.GetQuartoOutputDirectory());
        default_format_ = config.GetQuartoDefaultFormat();
        auto_open_ = config.IsQuartoAutoOpen();
        timeout_ms_ = config.GetQuartoTimeoutMs();

        std::string configured_path = config.GetQuartoPath();
        if (!configured_path.empty()) {
            quarto_path_ = env.ExpandEnvStrings(configured_path);
        }

        // Discover CLI
        quarto_path_ = DiscoverQuartoCLI();
        if (quarto_path_.empty()) {
            RJ2XCL_LOG_WARN("Quarto CLI not found — integration unavailable");
            available_ = false;
        } else {
            available_ = true;
            RJ2XCL_LOG_INFO("Quarto CLI found: %s", quarto_path_.c_str());
        }

        // Create output directory
        std::string dir_error;
        if (!EnsureOutputDirectory(dir_error)) {
            RJ2XCL_LOG_WARN("Could not create Quarto output directory: %s", dir_error.c_str());
        }
    }

    std::string QuartoService::DiscoverQuartoCLI() {
        auto& config = ConfigService::Instance();
        auto& env = EnvService::Instance();

        // If a custom path is configured, use it
        std::string configured_path = config.GetQuartoPath();
        if (!configured_path.empty()) {
            std::string expanded = env.ExpandEnvStrings(configured_path);
            if (ValidateExecutable(expanded)) {
                return expanded;
            }
            RJ2XCL_LOG_ERR("Configured Quarto path is not a valid executable: %s", expanded.c_str());
            return "";
        }

        // Search PATH via SearchPathA
        char found_path[MAX_PATH];
        DWORD result = SearchPathA(NULL, "quarto.exe", NULL, MAX_PATH, found_path, NULL);
        if (result > 0 && result < MAX_PATH) {
            std::string path(found_path);
            if (ValidateExecutable(path)) {
                return path;
            }
        }

        // Also try just "quarto" (some installations use .cmd wrapper)
        result = SearchPathA(NULL, "quarto.cmd", NULL, MAX_PATH, found_path, NULL);
        if (result > 0 && result < MAX_PATH) {
            return std::string(found_path);
        }

        return "";
    }

    bool QuartoService::ValidateExecutable(const std::string& path) {
        DWORD attrs = GetFileAttributesA(path.c_str());
        if (attrs == INVALID_FILE_ATTRIBUTES) return false;
        if (attrs & FILE_ATTRIBUTE_DIRECTORY) return false;
        return true;
    }

    bool QuartoService::EnsureOutputDirectory(std::string& error_msg) {
        if (output_directory_.empty()) return true;

        DWORD attrs = GetFileAttributesA(output_directory_.c_str());
        if (attrs != INVALID_FILE_ATTRIBUTES) {
            return true; // Already exists
        }

        // Create directory recursively (consistent with existing pattern in rj2xcl.cc)
        std::string parent = output_directory_;
        std::vector<std::string> dirs_to_create;
        while (!parent.empty() && GetFileAttributesA(parent.c_str()) == INVALID_FILE_ATTRIBUTES) {
            dirs_to_create.push_back(parent);
            size_t pos = parent.find_last_of("\\/");
            if (pos == std::string::npos) break;
            parent = parent.substr(0, pos);
        }
        for (auto it = dirs_to_create.rbegin(); it != dirs_to_create.rend(); ++it) {
            if (!CreateDirectoryA(it->c_str(), NULL)) {
                DWORD err = GetLastError();
                if (err != ERROR_ALREADY_EXISTS) {
                    error_msg = *it;
                    return false;
                }
            }
        }
        return true;
    }

    // -----------------------------------------------------------------------
    // CSV serialization
    // -----------------------------------------------------------------------

    std::string QuartoService::SerializeToCSV(LPXLOPER12 data_range,
                                               const std::string& qmd_stem) {
        if (!data_range) return "";

        // Only handle xltypeMulti (array)
        if (!(data_range->xltype & xltypeMulti)) return "";

        int rows = data_range->val.array.rows;
        int cols = data_range->val.array.columns;
        if (rows <= 0 || cols <= 0) return "";

        // Build CSV path
        std::string csv_path = output_directory_;
        if (!csv_path.empty() && csv_path.back() != '\\' && csv_path.back() != '/') {
            csv_path += '\\';
        }
        csv_path += qmd_stem + "_data.csv";

        std::ofstream file(csv_path, std::ios::binary);
        if (!file.is_open()) {
            RJ2XCL_LOG_ERR("Failed to create CSV file: %s", csv_path.c_str());
            return "";
        }

        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (c > 0) file << ',';

                XLOPER12& cell = data_range->val.array.lparray[r * cols + c];
                int cell_type = cell.xltype & ~(xlbitDLLFree | xlbitXLFree);

                switch (cell_type) {
                case xltypeNum:
                {
                    std::ostringstream oss;
                    oss << cell.val.num;
                    file << oss.str();
                    break;
                }
                case xltypeStr:
                {
                    // Convert wide string to UTF-8
                    int len = cell.val.str[0];
                    int u8_len = WideCharToMultiByte(CP_UTF8, 0, cell.val.str + 1, len, NULL, 0, NULL, NULL);
                    std::string utf8(u8_len, '\0');
                    WideCharToMultiByte(CP_UTF8, 0, cell.val.str + 1, len, &utf8[0], u8_len, NULL, NULL);

                    // CSV quoting: wrap in double quotes, escape internal quotes
                    file << '"';
                    for (char ch : utf8) {
                        if (ch == '"') file << '"';
                        file << ch;
                    }
                    file << '"';
                    break;
                }
                case xltypeBool:
                    file << (cell.val.xbool ? "TRUE" : "FALSE");
                    break;
                case xltypeInt:
                    file << cell.val.w;
                    break;
                case xltypeErr:
                    file << "#ERROR";
                    break;
                case xltypeNil:
                case xltypeMissing:
                default:
                    // Empty field
                    break;
                }
            }
            file << "\r\n";
        }

        file.close();
        return csv_path;
    }

    // -----------------------------------------------------------------------
    // Process spawning
    // -----------------------------------------------------------------------

    std::string QuartoService::SpawnRender(const std::string& resolved_path,
                                            const std::string& format,
                                            const std::string& csv_path) {
        // Build command line
        std::string cmd = "\"" + quarto_path_ + "\" render \"" + resolved_path + "\" --to " + format;

        // Create stderr pipe
        SECURITY_ATTRIBUTES sa;
        sa.nLength = sizeof(sa);
        sa.bInheritHandle = TRUE;
        sa.lpSecurityDescriptor = NULL;

        HANDLE hReadPipe = INVALID_HANDLE_VALUE;
        HANDLE hWritePipe = INVALID_HANDLE_VALUE;
        if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
            DWORD err = GetLastError();
            return "ERROR: Failed to create pipe (Windows error " + std::to_string(err) + ")";
        }

        UniqueHandle read_pipe(hReadPipe);
        UniqueHandle write_pipe(hWritePipe);

        // Ensure read end is not inherited
        SetHandleInformation(read_pipe.get(), HANDLE_FLAG_INHERIT, 0);

        // Set environment variables for child process
        if (!csv_path.empty()) {
            SetEnvironmentVariableA("RJ2XCL_DATA", csv_path.c_str());
        }
        SetEnvironmentVariableA("RJ2XCL_EXCEL", "true");

        // Tell Quarto which Python to use (must match where jupyter is installed)
        // Read Python home from config — same path used by ControlPython
        auto& cfg = ConfigService::Instance();
        std::string python_home = cfg.GetConfig()["RJ2XCL"]["Python"]["home"].string_value();
        if (!python_home.empty()) {
            std::string python_exe = python_home + "\\python.exe";
            SetEnvironmentVariableA("QUARTO_PYTHON", python_exe.c_str());
            RJ2XCL_LOG_INFO("Set QUARTO_PYTHON=%s", python_exe.c_str());
        } else {
            // Try DiscoveryService as fallback
            auto python_install = rj2xcl::DiscoveryService::Instance().GetBestVersion("Python");
            if (!python_install.home_path.empty()) {
                std::string python_exe = python_install.home_path + "\\python.exe";
                SetEnvironmentVariableA("QUARTO_PYTHON", python_exe.c_str());
                RJ2XCL_LOG_INFO("Set QUARTO_PYTHON=%s (via discovery)", python_exe.c_str());
            }
        }

        // Set writable cache directory for Quarto (Sass cache needs write access)
        SetEnvironmentVariableA("XDG_CACHE_HOME", output_directory_.c_str());

        // Determine working directory (parent of the QMD file)
        std::string working_dir;
        size_t last_sep = resolved_path.find_last_of("\\/");
        if (last_sep != std::string::npos) {
            working_dir = resolved_path.substr(0, last_sep);
        }

        // Setup process
        STARTUPINFOA si;
        memset(&si, 0, sizeof(si));
        si.cb = sizeof(si);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdError = write_pipe.get();
        si.hStdOutput = write_pipe.get();
        si.hStdInput = NULL;

        PROCESS_INFORMATION pi;
        memset(&pi, 0, sizeof(pi));

        // Need mutable buffer for CreateProcessA
        std::vector<char> cmd_buf(cmd.begin(), cmd.end());
        cmd_buf.push_back('\0');

        BOOL created = CreateProcessA(
            NULL,
            cmd_buf.data(),
            NULL, NULL,
            TRUE,  // Inherit handles
            CREATE_NO_WINDOW,
            NULL,  // Use parent environment (with RJ2XCL_DATA/RJ2XCL_EXCEL set)
            working_dir.empty() ? NULL : working_dir.c_str(),
            &si,
            &pi
        );

        // Clean up environment variables
        if (!csv_path.empty()) {
            SetEnvironmentVariableA("RJ2XCL_DATA", NULL);
        }
        SetEnvironmentVariableA("RJ2XCL_EXCEL", NULL);
        SetEnvironmentVariableA("QUARTO_PYTHON", NULL);
        SetEnvironmentVariableA("XDG_CACHE_HOME", NULL);

        if (!created) {
            DWORD err = GetLastError();
            return "ERROR: Failed to start Quarto process (Windows error " + std::to_string(err) + ")";
        }

        UniqueHandle process_handle(pi.hProcess);
        UniqueHandle thread_handle(pi.hThread);

        // Close write end of pipe in parent BEFORE reading — prevents deadlock
        write_pipe.reset();

        // Wait for process
        DWORD start_tick = GetTickCount();
        DWORD wait_result = WaitForSingleObject(process_handle.get(), timeout_ms_);
        DWORD elapsed = GetTickCount() - start_tick;

        if (wait_result == WAIT_TIMEOUT) {
            TerminateProcess(process_handle.get(), 1);
            DWORD seconds = timeout_ms_ / 1000;
            RJ2XCL_LOG_WARN("Quarto render timed out after %lu seconds: %s", seconds, resolved_path.c_str());
            return "ERROR: Quarto render timed out after " + std::to_string(seconds) + " seconds";
        }

        DWORD exit_code = 0;
        GetExitCodeProcess(process_handle.get(), &exit_code);

        if (exit_code != 0) {
            // Read stderr (last 500 chars)
            std::string stderr_output;
            char buffer[512];
            DWORD bytes_read = 0;
            while (ReadFile(read_pipe.get(), buffer, sizeof(buffer) - 1, &bytes_read, NULL) && bytes_read > 0) {
                buffer[bytes_read] = '\0';
                stderr_output += buffer;
            }

            // Truncate to last 500 chars
            if (stderr_output.size() > 500) {
                stderr_output = stderr_output.substr(stderr_output.size() - 500);
            }

            RJ2XCL_LOG_ERR("Quarto render failed (exit %lu, %lu ms): %s — %s",
                           exit_code, elapsed, resolved_path.c_str(), stderr_output.c_str());
            return "ERROR: Quarto render failed (exit " + std::to_string(exit_code) + "): " + stderr_output;
        }

        RJ2XCL_LOG_INFO("Quarto render completed in %lu ms: %s", elapsed, resolved_path.c_str());
        return ""; // Success — empty string means no error
    }

    // -----------------------------------------------------------------------
    // Render orchestration
    // -----------------------------------------------------------------------

    std::string QuartoService::Render(const std::string& file_path,
                                       const std::string& format,
                                       LPXLOPER12 data_range) {
        // Lazy initialization — only runs once, on first Render() call
        if (!initialized_) {
            Initialize();
        }

        // 1. Validate input security — file path
        std::string security_error;
        if (!ValidateInputSecurity(file_path, security_error)) {
            RJ2XCL_LOG_WARN("BLOCKED path: %s", security_error.c_str());
            return "BLOCKED: Path contains invalid characters";
        }

        // 2. Validate input security — format
        if (!format.empty()) {
            std::string fmt_security_error;
            if (!ValidateInputSecurity(format, fmt_security_error)) {
                RJ2XCL_LOG_WARN("BLOCKED format: %s", fmt_security_error.c_str());
                return "BLOCKED: Format contains invalid characters";
            }
        }

        // 3. Resolve file path
        std::string resolved = ResolveFilePath(file_path);

        // 4. Check file exists
        DWORD attrs = GetFileAttributesA(resolved.c_str());
        if (attrs == INVALID_FILE_ATTRIBUTES) {
            return "ERROR: File not found: " + resolved;
        }

        // 5. Validate extension
        if (!ValidateExtension(resolved)) {
            return "ERROR: File must have .qmd extension";
        }

        // 6. Validate and normalize format
        std::string effective_format = format.empty() ? default_format_ : format;
        std::string format_error;
        if (!ValidateFormat(effective_format, format_error)) {
            return "ERROR: " + format_error;
        }
        // Normalize to lowercase
        std::transform(effective_format.begin(), effective_format.end(),
                       effective_format.begin(),
                       [](unsigned char c) { return (char)std::tolower(c); });

        RJ2XCL_LOG_INFO("Quarto render: file=%s, format=%s, timeout=%lu ms",
                        resolved.c_str(), effective_format.c_str(), timeout_ms_);

        // 7. Serialize data range to CSV (if provided)
        std::string csv_path;
        if (data_range) {
            // Extract stem from QMD filename
            std::string filename = resolved;
            size_t last_sep = filename.find_last_of("\\/");
            if (last_sep != std::string::npos) {
                filename = filename.substr(last_sep + 1);
            }
            // Remove .qmd extension
            std::string stem = filename.substr(0, filename.size() - 4);
            csv_path = SerializeToCSV(data_range, stem);
        }

        // 8. Ensure output directory exists
        std::string dir_error;
        if (!EnsureOutputDirectory(dir_error)) {
            return "ERROR: Cannot create output directory: " + dir_error;
        }

        // 9. Spawn render process
        std::string spawn_result = SpawnRender(resolved, effective_format, csv_path);

        // 10. Cleanup temp CSV regardless of result
        if (!csv_path.empty()) {
            DeleteFileA(csv_path.c_str());
        }

        // 11. Check spawn result
        if (!spawn_result.empty()) {
            return spawn_result; // Error string from SpawnRender
        }

        // 12. Construct and verify output path
        std::string output_path = ConstructOutputPath(resolved, effective_format);
        DWORD out_attrs = GetFileAttributesA(output_path.c_str());
        if (out_attrs == INVALID_FILE_ATTRIBUTES) {
            return "ERROR: Render completed but output file not found at " + output_path;
        }

        // 13. Auto-open if enabled
        if (auto_open_) {
            HINSTANCE shell_result = ShellExecuteA(NULL, "open", output_path.c_str(),
                                                    NULL, NULL, SW_SHOWNORMAL);
            if ((INT_PTR)shell_result <= 32) {
                RJ2XCL_LOG_WARN("ShellExecuteA failed for: %s (result=%d)",
                               output_path.c_str(), (int)(INT_PTR)shell_result);
                // Non-fatal — still return the path
            }
        }

        return output_path;
    }

} // namespace rj2xcl
