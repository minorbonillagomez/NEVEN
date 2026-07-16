/**
 * @file sim_bridge.cc
 * @brief SimBridge implementation — xlUDF relay to NEVEN base engines.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include "sim_bridge.h"
#include "json11/json11.hpp"
#include <windows.h>
#include <fstream>
#include <sstream>
#include <vector>

// xlUDF is the Excel SDK constant for calling a user-defined function
// In the full Excel SDK this is 255; define here if not already defined.
#ifndef xlUDF
#define xlUDF 255
#endif

namespace neven_sim {

SimBridge& SimBridge::Instance() {
    static SimBridge instance;
    return instance;
}

SimBridge::SimBridge() {}

bool SimBridge::Initialize() {
    std::lock_guard<std::mutex> lock(mutex_);

    // Resolve NEVEN home path from environment or standard location
    char buf[MAX_PATH] = {};
    DWORD len = GetEnvironmentVariableA("RJ2XCL_HOME", buf, MAX_PATH);
    if (len > 0) {
        home_path_ = std::string(buf, len);
    } else {
        // Fallback: check standard install location
        DWORD attrs = GetFileAttributesA("C:\\NEVEN\\neven-config.json");
        if (attrs != INVALID_FILE_ATTRIBUTES) {
            home_path_ = "C:\\NEVEN\\";
        }
    }

    if (home_path_.empty()) {
        base_available_ = false;
        return false;
    }

    // IMPORTANT: Do NOT call DetectNevenBase() here!
    // xlUDF is NOT allowed during xlAutoOpen — it will hang/crash Excel.
    // Detection is deferred to first actual use (EnsureAvailable).
    base_available_ = false;  // Will be detected lazily on first call
    return true;  // Home path found = initialization succeeded
}

bool SimBridge::EnsureAvailable() {
    // Lazy re-detection: if base was not available during init,
    // try again (NEVEN64.xll may have loaded after us).
    if (!base_available_) {
        base_available_ = DetectNevenBase();
    }
    return base_available_;
}

bool SimBridge::DetectNevenBase() {
    // Try calling NEVEN.status via xlUDF — if it returns a result, base is loaded
    XLOPER12 result;
    memset(&result, 0, sizeof(result));
    
    // Build the function name "NEVEN.status" as Pascal-style wide string
    static wchar_t func_name_buf[] = { 12, L'N', L'E', L'V', L'E', L'N', L'.', L's', L't', L'a', L't', L'u', L's', 0 };
    XLOPER12 xlFuncName;
    xlFuncName.xltype = xltypeStr;
    xlFuncName.val.str = func_name_buf;

    LPXLOPER12 args[1] = { &xlFuncName };

    // xlUDF calls another XLL's registered function by name
    int err = Excel12v(xlUDF, &result, 1, args);
    
    if (err == 0 && result.xltype != xltypeErr) {
        return true;
    }

    return false;
}

std::string SimBridge::CallR(const std::string& code) {
    if (!EnsureAvailable()) {
        return "[ERROR] SimBridge: NEVEN base not available or R not connected";
    }

    XLOPER12 result;
    memset(&result, 0, sizeof(result));

    if (!CallUDF("NEVEN.r", code, result)) {
        return "[ERROR] SimBridge: R call failed";
    }

    std::string output;
    if (result.xltype == xltypeStr && result.val.str) {
        int len = result.val.str[0]; // Pascal-style length prefix
        output.assign((const char*)(result.val.str + 1), len * sizeof(wchar_t));
        // Convert wide to narrow
        std::wstring ws(result.val.str + 1, len);
        output.resize(len);
        for (int i = 0; i < len; i++) output[i] = (char)ws[i];
    } else if (result.xltype == xltypeNum) {
        output = std::to_string(result.val.num);
    } else if (result.xltype == xltypeErr) {
        output = "[ERROR] R returned Excel error code " + std::to_string(result.val.err);
    } else {
        output = "[ERROR] Unexpected result type from R";
    }

    return output;
}

std::string SimBridge::CallJulia(const std::string& code) {
    if (!EnsureAvailable()) {
        return "[ERROR] SimBridge: NEVEN base not available or Julia not connected";
    }

    XLOPER12 result;
    memset(&result, 0, sizeof(result));

    if (!CallUDF("NEVEN.j", code, result)) {
        return "[ERROR] SimBridge: Julia call failed";
    }

    std::string output;
    if (result.xltype == xltypeStr && result.val.str) {
        int len = result.val.str[0];
        std::wstring ws(result.val.str + 1, len);
        output.resize(len);
        for (int i = 0; i < len; i++) output[i] = (char)ws[i];
    } else if (result.xltype == xltypeNum) {
        output = std::to_string(result.val.num);
    } else if (result.xltype == xltypeErr) {
        output = "[ERROR] Julia returned Excel error code " + std::to_string(result.val.err);
    } else {
        output = "[ERROR] Unexpected result type from Julia";
    }

    return output;
}

bool SimBridge::CallR_Raw(const std::string& code, XLOPER12& result) {
    return CallUDF("NEVEN.r", code, result);
}

bool SimBridge::CallJulia_Raw(const std::string& code, XLOPER12& result) {
    return CallUDF("NEVEN.j", code, result);
}

bool SimBridge::CallUDF_Public(const std::string& func_name, const std::string& arg, XLOPER12& result) {
    return CallUDF(func_name, arg, result);
}

bool SimBridge::CallUDF(const std::string& func_name, const std::string& code, XLOPER12& result) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!base_available_) {
        // One more lazy attempt
        base_available_ = DetectNevenBase();
        if (!base_available_) return false;
    }

    // Build function name as Pascal-style wide string
    std::wstring wfunc(func_name.begin(), func_name.end());
    std::vector<wchar_t> pascal_func(wfunc.length() + 2);
    pascal_func[0] = (wchar_t)wfunc.length();
    memcpy(&pascal_func[1], wfunc.c_str(), wfunc.length() * sizeof(wchar_t));

    XLOPER12 xlFuncName;
    xlFuncName.xltype = xltypeStr;
    xlFuncName.val.str = pascal_func.data();

    // Build code argument as Pascal-style wide string
    std::wstring wcode(code.begin(), code.end());
    std::vector<wchar_t> pascal_code(wcode.length() + 2);
    pascal_code[0] = (wchar_t)wcode.length();
    memcpy(&pascal_code[1], wcode.c_str(), wcode.length() * sizeof(wchar_t));

    XLOPER12 xlCode;
    xlCode.xltype = xltypeStr;
    xlCode.val.str = pascal_code.data();

    LPXLOPER12 args[2] = { &xlFuncName, &xlCode };

    memset(&result, 0, sizeof(result));
    int err = Excel12v(xlUDF, &result, 2, args);

    return (err == 0 && result.xltype != xltypeErr);
}

} // namespace neven_sim
