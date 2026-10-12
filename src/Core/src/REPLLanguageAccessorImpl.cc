/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file REPLLanguageAccessorImpl.cc
 * @brief Concrete implementation of REPLLanguageAccessor using LanguageManager.
 *
 * This bridges the Common library (REPLBridge) with the Core library
 * (LanguageManager) without creating a circular dependency.
 */

#include "REPLLanguageAccessor.h"
#include "LanguageManager.h"
#include "variable.pb.h"
#include "LogService.h"
#include <sstream>

namespace rj2xcl {

/**
 * @brief Concrete accessor that delegates to LanguageManager.
 */
class REPLLanguageAccessorImpl : public REPLLanguageAccessor {
public:
    bool IsLanguageRegistered(const std::string& name) const override {
        auto svc = LanguageManager::Instance().GetLanguageService(name);
        return svc != nullptr;
    }

    bool IsLanguageConnected(const std::string& name) const override {
        auto svc = LanguageManager::Instance().GetLanguageService(name);
        if (!svc) return false;
        return svc->connected();
    }

    std::string ExecuteShellCommand(const std::string& language,
                                    const std::string& code) const override {
        auto svc = LanguageManager::Instance().GetLanguageService(language);
        if (!svc) return "Unknown language: " + language;
        if (!svc->connected()) return "Language engine not connected";

        // Build a Code message — same pattern as RJ_Exec_Generic
        // This is how =NEVEN.R("1+1") sends code to the language engines
        RJ2XCLBuffers::CallResponse call, response;
        call.set_wait(true);

        auto code_msg = call.mutable_code();
        // Split by newlines and add each line (for R/Julia)
        // For single-line code, just add the whole thing
        std::string::size_type pos = 0, prev = 0;
        while ((pos = code.find('\n', prev)) != std::string::npos) {
            std::string line = code.substr(prev, pos - prev);
            if (!line.empty()) code_msg->add_line(line);
            prev = pos + 1;
        }
        std::string last_line = code.substr(prev);
        if (!last_line.empty()) code_msg->add_line(last_line);

        svc->Call(response, call);

        if (response.operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kResult) {
            const auto& result = response.result();
            switch (result.value_case()) {
                case RJ2XCLBuffers::Variable::kStr:
                    return result.str();
                case RJ2XCLBuffers::Variable::kReal: {
                    std::ostringstream oss;
                    oss << result.real();
                    return oss.str();
                }
                case RJ2XCLBuffers::Variable::kInteger:
                    return std::to_string(result.integer());
                case RJ2XCLBuffers::Variable::kBoolean:
                    return result.boolean() ? "TRUE" : "FALSE";
                case RJ2XCLBuffers::Variable::kNil:
                    return "";
                default:
                    return result.str();
            }
        } else if (response.operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kErr) {
            return response.err();
        }

        return "";
    }
};

// Static instance — lives for the duration of the process
static REPLLanguageAccessorImpl g_repl_accessor_impl;

/**
 * @brief Register the accessor at startup.
 * Called from RJ2XCL_Engine::Init() indirectly via this translation unit's
 * inclusion in the Core library.
 */
void RegisterREPLLanguageAccessor() {
    REPLLanguageAccessor::Register(&g_repl_accessor_impl);
}

} // namespace rj2xcl
