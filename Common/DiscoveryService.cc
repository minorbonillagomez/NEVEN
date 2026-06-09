/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * DiscoveryService Implementation.
 */

#include "DiscoveryService.h"
#include <windows.h>
#include <algorithm>
#include <iostream>
#include <sstream>

namespace rj2xcl {

    DiscoveryService& DiscoveryService::Instance() {
        static DiscoveryService instance;
        return instance;
    }

    std::vector<LanguageInstallation> DiscoveryService::FindR() {
        std::vector<LanguageInstallation> results;
        HKEY hKey;
        
        // Potential keys for R
        const char* r_keys[] = {
            "SOFTWARE\\R-core\\R",
            "SOFTWARE\\R-core\\R64"
        };

        for (const char* key_path : r_keys) {
            if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, key_path, 0, KEY_READ | KEY_WOW64_64KEY, &hKey) == ERROR_SUCCESS) {
                char subkey_name[256];
                DWORD subkey_len = sizeof(subkey_name);
                DWORD index = 0;

                while (RegEnumKeyExA(hKey, index++, subkey_name, &subkey_len, NULL, NULL, NULL, NULL) == ERROR_SUCCESS) {
                    HKEY hSubKey;
                    if (RegOpenKeyExA(hKey, subkey_name, 0, KEY_READ | KEY_WOW64_64KEY, &hSubKey) == ERROR_SUCCESS) {
                        char path_buffer[MAX_PATH];
                        DWORD path_len = sizeof(path_buffer);
                        if (RegQueryValueExA(hSubKey, "InstallPath", NULL, NULL, (LPBYTE)path_buffer, &path_len) == ERROR_SUCCESS) {
                            LanguageInstallation inst;
                            inst.name = "R";
                            inst.version = subkey_name;
                            inst.home_path = path_buffer;
                            inst.is_64bit = (strstr(key_path, "R64") != nullptr || strstr(path_buffer, "x64") != nullptr);
                            inst.priority = 10; // Default priority
                            results.push_back(inst);
                        }
                        RegCloseKey(hSubKey);
                    }
                    subkey_len = sizeof(subkey_name);
                }
                RegCloseKey(hKey);
            }
        }
        return results;
    }

    std::vector<LanguageInstallation> DiscoveryService::FindJulia() {
        std::vector<LanguageInstallation> results;
        
        // 1. Check environment variable JULIA_HOME
        char env_path[MAX_PATH];
        if (GetEnvironmentVariableA("JULIA_HOME", env_path, MAX_PATH) > 0) {
            LanguageInstallation inst;
            inst.name = "Julia";
            inst.version = "Unknown (Env)";
            inst.home_path = env_path;
            inst.is_64bit = true; // Assume 64-bit for modern Julia
            inst.priority = 100; // High priority for explicit env var
            results.push_back(inst);
        }

        // 2. Heuristic: Check LocalAppData\Programs\Julia (common installer path)
        char local_app_data[MAX_PATH];
        if (GetEnvironmentVariableA("LOCALAPPDATA", local_app_data, MAX_PATH) > 0) {
            std::string julia_base = std::string(local_app_data) + "\\Programs\\Julia*";
            WIN32_FIND_DATAA find_data;
            HANDLE hFind = FindFirstFileA(julia_base.c_str(), &find_data);
            if (hFind != INVALID_HANDLE_VALUE) {
                do {
                    if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                        LanguageInstallation inst;
                        inst.name = "Julia";
                        inst.version = find_data.cFileName; // e.g., Julia-1.8.5
                        inst.home_path = std::string(local_app_data) + "\\Programs\\" + find_data.cFileName;
                        inst.is_64bit = true;
                        inst.priority = 10;
                        results.push_back(inst);
                    }
                } while (FindNextFileA(hFind, &find_data));
                FindClose(hFind);
            }
        }

        return results;
    }

    std::vector<LanguageInstallation> DiscoveryService::FindPython() {
        std::vector<LanguageInstallation> results;

        // Helper: validate a Python installation has python3.dll (or python3XX.dll) and include/Python.h
        auto ValidatePythonHome = [](const std::string& home) -> bool {
            // Check for stable ABI DLL: python3.dll
            std::string stable_dll = home + "\\python3.dll";
            if (GetFileAttributesA(stable_dll.c_str()) != INVALID_FILE_ATTRIBUTES) return true;
            // Check for versioned DLL pattern: python3XX.dll
            std::string dll_pattern = home + "\\python3*.dll";
            WIN32_FIND_DATAA fd;
            HANDLE hf = FindFirstFileA(dll_pattern.c_str(), &fd);
            if (hf != INVALID_HANDLE_VALUE) {
                FindClose(hf);
                return true;
            }
            // Check for include/Python.h as fallback
            std::string header = home + "\\include\\Python.h";
            if (GetFileAttributesA(header.c_str()) != INVALID_FILE_ATTRIBUTES) return true;
            return false;
        };

        // 1. Check environment variables PYTHON_HOME / PYTHONHOME
        const char* env_names[] = { "PYTHON_HOME", "PYTHONHOME" };
        for (const char* env_name : env_names) {
            char env_path[MAX_PATH];
            if (GetEnvironmentVariableA(env_name, env_path, MAX_PATH) > 0) {
                std::string home(env_path);
                if (ValidatePythonHome(home)) {
                    LanguageInstallation inst;
                    inst.name = "Python";
                    inst.version = "Unknown (Env)";
                    inst.home_path = home;
                    inst.is_64bit = true;
                    inst.priority = 100; // High priority for explicit env var
                    results.push_back(inst);
                }
            }
        }

        // 2. Windows Registry: HKLM\SOFTWARE\Python\PythonCore\<version>\InstallPath
        HKEY hKey;
        if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, "SOFTWARE\\Python\\PythonCore", 0, KEY_READ | KEY_WOW64_64KEY, &hKey) == ERROR_SUCCESS) {
            char subkey_name[256];
            DWORD subkey_len = sizeof(subkey_name);
            DWORD index = 0;

            while (RegEnumKeyExA(hKey, index++, subkey_name, &subkey_len, NULL, NULL, NULL, NULL) == ERROR_SUCCESS) {
                std::string install_path_key = std::string(subkey_name) + "\\InstallPath";
                HKEY hSubKey;
                if (RegOpenKeyExA(hKey, install_path_key.c_str(), 0, KEY_READ | KEY_WOW64_64KEY, &hSubKey) == ERROR_SUCCESS) {
                    char path_buffer[MAX_PATH];
                    DWORD path_len = sizeof(path_buffer);
                    // Default value contains the install path
                    if (RegQueryValueExA(hSubKey, NULL, NULL, NULL, (LPBYTE)path_buffer, &path_len) == ERROR_SUCCESS) {
                        // Remove trailing backslash if present
                        std::string home(path_buffer);
                        while (!home.empty() && (home.back() == '\\' || home.back() == '/')) home.pop_back();

                        if (ValidatePythonHome(home)) {
                            LanguageInstallation inst;
                            inst.name = "Python";
                            inst.version = subkey_name; // e.g., "3.12"
                            inst.home_path = home;
                            inst.is_64bit = true; // Modern Python on Windows is 64-bit
                            inst.priority = 10;
                            results.push_back(inst);
                        }
                    }
                    RegCloseKey(hSubKey);
                }
                subkey_len = sizeof(subkey_name);
            }
            RegCloseKey(hKey);
        }

        // 3. Filesystem heuristics: %LOCALAPPDATA%\Programs\Python\Python3*
        char local_app_data[MAX_PATH];
        if (GetEnvironmentVariableA("LOCALAPPDATA", local_app_data, MAX_PATH) > 0) {
            std::string python_base = std::string(local_app_data) + "\\Programs\\Python\\Python3*";
            WIN32_FIND_DATAA find_data;
            HANDLE hFind = FindFirstFileA(python_base.c_str(), &find_data);
            if (hFind != INVALID_HANDLE_VALUE) {
                do {
                    if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                        std::string home = std::string(local_app_data) + "\\Programs\\Python\\" + find_data.cFileName;
                        if (ValidatePythonHome(home)) {
                            LanguageInstallation inst;
                            inst.name = "Python";
                            inst.version = find_data.cFileName; // e.g., Python312
                            inst.home_path = home;
                            inst.is_64bit = true;
                            inst.priority = 10;
                            results.push_back(inst);
                        }
                    }
                } while (FindNextFileA(hFind, &find_data));
                FindClose(hFind);
            }
        }

        // 4. Filesystem heuristics: %PROGRAMFILES%\Python3*
        char program_files[MAX_PATH];
        if (GetEnvironmentVariableA("PROGRAMFILES", program_files, MAX_PATH) > 0) {
            std::string python_base = std::string(program_files) + "\\Python3*";
            WIN32_FIND_DATAA find_data;
            HANDLE hFind = FindFirstFileA(python_base.c_str(), &find_data);
            if (hFind != INVALID_HANDLE_VALUE) {
                do {
                    if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                        std::string home = std::string(program_files) + "\\" + find_data.cFileName;
                        if (ValidatePythonHome(home)) {
                            LanguageInstallation inst;
                            inst.name = "Python";
                            inst.version = find_data.cFileName;
                            inst.home_path = home;
                            inst.is_64bit = true;
                            inst.priority = 10;
                            results.push_back(inst);
                        }
                    }
                } while (FindNextFileA(hFind, &find_data));
                FindClose(hFind);
            }
        }

        return results;
    }

    LanguageInstallation DiscoveryService::GetBestVersion(const std::string& language_name, 
                                                         const std::string& preferred_tag,
                                                         const std::string& override_home) {
        
        // 1. If override provided, use it
        if (!override_home.empty()) {
            LanguageInstallation inst;
            inst.name = language_name;
            inst.version = "Override";
            inst.home_path = override_home;
            inst.is_64bit = true;
            inst.priority = 1000;
            return inst;
        }

        std::vector<LanguageInstallation> candidates;
        if (language_name == "R") candidates = FindR();
        else if (language_name == "Julia") candidates = FindJulia();
        else if (language_name == "Python") candidates = FindPython();

        if (candidates.empty()) return {};

        // 2. Filter by tag if provided
        if (!preferred_tag.empty()) {
            for (const auto& inst : candidates) {
                if (inst.version.find(preferred_tag) != std::string::npos) {
                    return inst;
                }
            }
        }

        // 3. Sort by version (naive descending sort for now)
        std::sort(candidates.begin(), candidates.end(), [](const LanguageInstallation& a, const LanguageInstallation& b) {
            if (a.priority != b.priority) return a.priority > b.priority;
            return a.version > b.version; // Simple string compare, good enough for R/Julia version strings usually
        });

        return candidates[0];
    }

} // namespace rj2xcl
