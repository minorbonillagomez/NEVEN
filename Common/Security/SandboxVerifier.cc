/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * SandboxVerifier — Code execution safety layer
 * 
 * Validates code before sending to R/Julia to prevent:
 * - Shell command execution (system(), shell(), os.execute)
 * - File system manipulation (unlink, file.remove, rmdir)
 * - Network access from untrusted sources
 * - Process spawning
 * - Dynamic code construction that bypasses pattern matching
 * - Native code execution via ccall/dlopen
 *
 * SECURITY MODEL:
 * This is a defense-in-depth layer for =RJ2XCL.R("...") and =RJ2XCL.J("...")
 * which accept arbitrary code from Excel cells. Registered functions (=R.Func())
 * bypass this check because they execute known, pre-loaded code.
 *
 * LIMITATIONS:
 * Pattern-based blocking can be bypassed by sufficiently motivated attackers.
 * This layer raises the bar against casual/accidental misuse and malicious
 * workbooks, but is NOT a full sandbox. For production hardening, consider
 * OS-level sandboxing (AppContainer, restricted tokens).
 */

#include "SandboxVerifier.h"
#include "LogService.h"
#include <algorithm>
#include <cctype>
#include <regex>

namespace rj2xcl {
namespace security {

SandboxVerifier& SandboxVerifier::GetInstance() {
    static SandboxVerifier instance;
    return instance;
}

void SandboxVerifier::AddTrustedSignature(const std::string& signature) {
    if(std::find(m_trusted_signatures.begin(), m_trusted_signatures.end(), signature) == m_trusted_signatures.end()) {
        m_trusted_signatures.push_back(signature);
    }
}

ExecutionTrustLevel SandboxVerifier::EvaluateScript(const std::string& scriptContext) {
    if (ContainsRestrictedCommands(scriptContext)) {
        return ExecutionTrustLevel::Blocked; 
    }
    return ExecutionTrustLevel::PromptUser; 
}

/**
 * @brief Strips all whitespace from a string for normalized pattern matching.
 * Prevents bypass via "sys tem()" or "system \n (" tricks.
 */
static std::string StripWhitespace(const std::string& s) {
    std::string result;
    result.reserve(s.size());
    for (char c : s) {
        if (!std::isspace(static_cast<unsigned char>(c))) {
            result += c;
        }
    }
    return result;
}

bool SandboxVerifier::ValidateCodeForExecution(const std::string& code, std::string& rejection_reason) const {
    // IDEMPOTENCE GUARANTEE (Requirement 3.8):
    // This method is const — no member state is modified.
    // All blocklists are static const — initialized once, never mutated.
    // All intermediate processing uses local variables only.
    // Repeated calls with the same input always produce the same result.

    // Convert to lowercase for case-insensitive matching
    std::string lower_code = code;
    std::transform(lower_code.begin(), lower_code.end(), lower_code.begin(), ::tolower);

    // Also create a whitespace-stripped version to catch "sys tem()" tricks
    std::string stripped_code = StripWhitespace(lower_code);

    // Trim leading/trailing whitespace from original (Excel may add spaces)
    while (!lower_code.empty() && std::isspace(static_cast<unsigned char>(lower_code.front()))) lower_code.erase(lower_code.begin());
    while (!lower_code.empty() && std::isspace(static_cast<unsigned char>(lower_code.back()))) lower_code.pop_back();

    // ── R dangerous patterns ──────────────────────────────────────────
    static const std::vector<std::pair<std::string, std::string>> r_blocked = {
        // Shell execution
        {"system(", "system() — shell command execution blocked"},
        {"system2(", "system2() — shell command execution blocked"},
        {"shell(", "shell() — shell command execution blocked"},
        {"shell.exec(", "shell.exec() — shell command execution blocked"},
        {"pipe(", "pipe() — shell command execution blocked"},
        // File manipulation
        {"file.remove(", "file.remove() — file deletion blocked"},
        {"unlink(", "unlink() — file deletion blocked"},
        {"file.rename(", "file.rename() — file manipulation blocked"},
        {"file.copy(", "file.copy() — file manipulation blocked"},
        {"file.create(", "file.create() — file creation blocked"},
        // Network
        {"download.file(", "download.file() — network download blocked"},
        {"url(", "url() — network access blocked"},
        {"socketconnection(", "socketConnection() — network access blocked"},
        // Dynamic code construction (bypass prevention)
        {"eval(parse(", "eval(parse()) — dynamic code construction blocked"},
        {"do.call(", "do.call() — dynamic function dispatch blocked"},
        {"match.fun(", "match.fun() — dynamic function lookup blocked"},
        // File/script execution
        {"source(", "source() — script file execution blocked"},
        // Package loading (can load native code / arbitrary packages)
        {"library(", "library() — unrestricted package loading blocked"},
        // Connection opening
        {"open(", "open() — connection opening blocked"},
        // Process/environment manipulation
        {"sys.getenv(", "Sys.getenv() — environment variable access blocked"},
        {"sys.setenv(", "Sys.setenv() — environment manipulation blocked"},
        {"setwd(", "setwd() — working directory change blocked"},
        // Internal R function access (bypass R-level protections)
        {".internal(", ".Internal() — internal R function access blocked"},
        // Library loading (can load native code)
        {"dyn.load(", "dyn.load() — native code loading blocked"},
        {".c(", ".C() — native code execution blocked"},
        {".call(", ".Call() — native code execution blocked"},
        {".call (", ".Call() — native code execution blocked"},
        {".fortran(", ".Fortran() — native code execution blocked"},
        {".external(", ".External() — native code execution blocked"},
        // Allowed exceptions (empty reason = skip blocking)
        {"proc.time", ""}, // proc.time() is safe — only returns elapsed time
    };

    // ── Julia dangerous patterns ──────────────────────────────────────
    static const std::vector<std::pair<std::string, std::string>> julia_blocked = {
        // Shell execution
        {"run(", "run() — shell command execution blocked"},
        {"run(`", "run() — shell command execution blocked"},
        {"pipeline(", "pipeline() — shell command execution blocked"},
        // Backtick command literals (Julia-specific)
        {"`", "backtick command literal — shell execution blocked"},
        // File manipulation
        {"rm(\"", "rm() — file deletion blocked"},
        {"rm( \"", "rm() — file deletion blocked"},
        {"base.filesystem.rm(", "rm() — file deletion blocked"},
        {"mv(\"", "mv() — file manipulation blocked"},
        {"cp(\"", "cp() — file copy blocked"},
        {"mkpath(", "mkpath() — directory creation blocked"},
        // Network
        {"download(", "download() — network download blocked"},
        {"sockets.connect(", "Sockets.connect() — network access blocked"},
        // Native code execution
        {"ccall(", "ccall() — native code execution blocked"},
        {"@ccall", "@ccall — native code execution blocked"},
        {"cglobal(", "cglobal() — native symbol access blocked"},
        // Dynamic code construction
        {"eval(", "eval() — dynamic code evaluation blocked"},
        {"meta.parse(", "Meta.parse() — dynamic code construction blocked"},
        {"include(", "include() — file inclusion blocked"},
        // Unsafe operations
        {"unsafe_load(", "unsafe_load() — unsafe memory access blocked"},
        {"unsafe_store!", "unsafe_store! — unsafe memory access blocked"},
        {"unsafe_pointer_to_objref(", "unsafe_pointer_to_objref() — unsafe memory access blocked"},
        {"unsafe_wrap(", "unsafe_wrap() — unsafe array wrapping blocked"},
        {"unsafe_pointer", "unsafe_pointer*() — unsafe memory operations blocked"},
        // Environment variable access
        {"env[", "ENV[] — environment variable access blocked"},
    };

    // ── Python dangerous patterns ─────────────────────────────────────
    static const std::vector<std::pair<std::string, std::string>> python_blocked = {
        // Shell execution
        {"os.system(", "os.system() — shell command execution blocked"},
        {"os.popen(", "os.popen() — shell command execution blocked"},
        {"subprocess.call(", "subprocess — shell command execution blocked"},
        {"subprocess.run(", "subprocess — shell command execution blocked"},
        {"subprocess.popen(", "subprocess — shell command execution blocked"},
        {"subprocess.check_output(", "subprocess — shell command execution blocked"},
        {"subprocess.check_call(", "subprocess — shell command execution blocked"},
        // File manipulation
        {"os.remove(", "os.remove() — file deletion blocked"},
        {"os.unlink(", "os.unlink() — file deletion blocked"},
        {"os.rmdir(", "os.rmdir() — directory removal blocked"},
        {"os.rename(", "os.rename() — file manipulation blocked"},
        {"shutil.rmtree(", "shutil.rmtree() — recursive deletion blocked"},
        {"shutil.move(", "shutil.move() — file manipulation blocked"},
        {"shutil.copy(", "shutil.copy() — file copy blocked"},
        // Dynamic code execution
        {"exec(", "exec() — dynamic code execution blocked"},
        {"eval(", "eval() — dynamic code evaluation blocked"},
        {"compile(", "compile() — code compilation blocked"},
        {"__import__(", "__import__() — dynamic import blocked"},
        {"importlib.import_module(", "importlib — dynamic import blocked"},
        // Native/unsafe
        {"ctypes.cdll", "ctypes — native code access blocked"},
        {"ctypes.windll", "ctypes — native code access blocked"},
        {"ctypes.cdll(", "ctypes — native code loading blocked"},
        {"ctypes.windll(", "ctypes — native code loading blocked"},
        // Network
        {"urllib.request.urlopen(", "urllib — network access blocked"},
        {"socket.socket(", "socket — network access blocked"},
        {"http.client.httpconnection(", "http.client — network access blocked"},
        // Environment manipulation
        {"os.environ[", "os.environ — environment manipulation blocked"},
        {"os.putenv(", "os.putenv() — environment manipulation blocked"},
        {"os.chdir(", "os.chdir() — working directory change blocked"},
    };

    // Check R patterns against both original and stripped code
    for (const auto& pattern : r_blocked) {
        if (pattern.second.empty()) continue;
        if (lower_code.find(pattern.first) != std::string::npos ||
            stripped_code.find(pattern.first) != std::string::npos) {
            rejection_reason = pattern.second;
            return false;
        }
    }

    // Check Julia patterns
    for (const auto& pattern : julia_blocked) {
        if (pattern.second.empty()) continue;
        if (lower_code.find(pattern.first) != std::string::npos ||
            stripped_code.find(pattern.first) != std::string::npos) {
            rejection_reason = pattern.second;
            return false;
        }
    }

    // Check Python patterns
    for (const auto& pattern : python_blocked) {
        if (pattern.second.empty()) continue;
        if (lower_code.find(pattern.first) != std::string::npos ||
            stripped_code.find(pattern.first) != std::string::npos) {
            rejection_reason = pattern.second;
            return false;
        }
    }

    // ── Context-aware R pattern detection ─────────────────────────────

    // R get() — dynamic symbol lookup. Only block when it appears as a standalone
    // function call, not as part of another word (e.g., "widget(", "target(", "budget(")
    {
        size_t pos = 0;
        while ((pos = lower_code.find("get(", pos)) != std::string::npos) {
            // Check that 'get(' is not part of a larger word
            bool is_standalone = (pos == 0) ||
                (!std::isalnum(static_cast<unsigned char>(lower_code[pos - 1])) &&
                 lower_code[pos - 1] != '.' && lower_code[pos - 1] != '_');
            if (is_standalone) {
                rejection_reason = "get() \xe2\x80\x94 dynamic symbol lookup blocked";
                return false;
            }
            pos += 4;
        }
        // Also check stripped code
        pos = 0;
        while ((pos = stripped_code.find("get(", pos)) != std::string::npos) {
            bool is_standalone = (pos == 0) ||
                (!std::isalnum(static_cast<unsigned char>(stripped_code[pos - 1])) &&
                 stripped_code[pos - 1] != '.' && stripped_code[pos - 1] != '_');
            if (is_standalone) {
                rejection_reason = "get() \xe2\x80\x94 dynamic symbol lookup blocked";
                return false;
            }
            pos += 4;
        }
    }

    // readLines is only dangerous when used with pipe() or connection arguments
    // that enable shell command execution or network access.
    // Safe usage: readLines("file.txt") — reads a local file (allowed)
    // Dangerous: readLines(pipe("cmd")), readLines(url("http://...")),
    //            readLines(con) where con could be a pipe/url connection
    if (stripped_code.find("readlines") != std::string::npos ||
        lower_code.find("readlines") != std::string::npos) {
        // Check for readLines(pipe(...)) pattern
        if (stripped_code.find("readlines(pipe(") != std::string::npos ||
            lower_code.find("readlines(pipe(") != std::string::npos ||
            lower_code.find("readlines( pipe(") != std::string::npos ||
            lower_code.find("readlines (pipe(") != std::string::npos) {
            rejection_reason = "readLines(pipe()) \xe2\x80\x94 shell command execution via pipe blocked";
            return false;
        }
        // Check for readLines(url(...)) pattern
        if (stripped_code.find("readlines(url(") != std::string::npos ||
            lower_code.find("readlines(url(") != std::string::npos ||
            lower_code.find("readlines( url(") != std::string::npos ||
            lower_code.find("readlines (url(") != std::string::npos) {
            rejection_reason = "readLines(url()) \xe2\x80\x94 network access via readLines blocked";
            return false;
        }
        // Check for readLines(socketConnection(...)) pattern
        if (stripped_code.find("readlines(socketconnection(") != std::string::npos ||
            lower_code.find("readlines(socketconnection(") != std::string::npos) {
            rejection_reason = "readLines(socketConnection()) \xe2\x80\x94 network access via readLines blocked";
            return false;
        }
    }

    // ── Advanced bypass detection ─────────────────────────────────────

    // Detect R string concatenation to build blocked commands:
    // paste0("sys","tem(...)") or paste("sys","tem",sep="")
    if (lower_code.find("paste") != std::string::npos &&
        (lower_code.find("sys") != std::string::npos || 
         lower_code.find("shell") != std::string::npos ||
         lower_code.find("unlink") != std::string::npos)) {
        rejection_reason = "paste() with suspicious fragments — potential sandbox bypass blocked";
        return false;
    }

    // Detect R assign + environment manipulation
    if (lower_code.find("assign(") != std::string::npos &&
        lower_code.find("envir") != std::string::npos) {
        rejection_reason = "assign() with envir — environment manipulation blocked";
        return false;
    }

    // Detect Julia string interpolation to build commands
    if (lower_code.find("$(") != std::string::npos &&
        (lower_code.find("run") != std::string::npos ||
         lower_code.find("ccall") != std::string::npos)) {
        rejection_reason = "$() string interpolation with command execution — shell command execution blocked";
        return false;
    }

    // Detect Julia open() with process/Cmd patterns:
    // open(`cmd`), open(Cmd(...)), open(`...`)
    if (lower_code.find("open(") != std::string::npos || 
        stripped_code.find("open(") != std::string::npos) {
        // Check for backtick pattern: open(`...) 
        if (lower_code.find("open(`") != std::string::npos ||
            stripped_code.find("open(`") != std::string::npos) {
            rejection_reason = "open() with command literal — process execution blocked";
            return false;
        }
        // Check for Cmd pattern: open(Cmd(...)
        if (lower_code.find("open(cmd(") != std::string::npos ||
            stripped_code.find("open(cmd(") != std::string::npos) {
            rejection_reason = "open(Cmd()) — process execution blocked";
            return false;
        }
    }

    // Detect Julia standalone ENV access (not just ENV[ which is caught above)
    // Match "ENV" as a standalone token — not part of another word like "ENVIRON"
    {
        size_t pos = 0;
        while ((pos = lower_code.find("env", pos)) != std::string::npos) {
            // Check it's uppercase ENV in original code context (already lowered)
            // Verify it's a standalone token: not preceded/followed by alphanumeric or underscore
            bool preceded_by_word = (pos > 0 && (std::isalnum(static_cast<unsigned char>(lower_code[pos - 1])) || lower_code[pos - 1] == '_' || lower_code[pos - 1] == '.'));
            bool followed_by_word = (pos + 3 < lower_code.size() && (std::isalnum(static_cast<unsigned char>(lower_code[pos + 3])) || lower_code[pos + 3] == '_'));
            
            if (!preceded_by_word && !followed_by_word) {
                // It's standalone ENV — block it (environment variable access)
                rejection_reason = "ENV — environment variable access blocked";
                return false;
            }
            pos += 3;
        }
    }

    // Python getattr bypass: getattr(__import__('os'), 'system')
    if (lower_code.find("getattr(") != std::string::npos &&
        (lower_code.find("os") != std::string::npos ||
         lower_code.find("subprocess") != std::string::npos ||
         lower_code.find("shutil") != std::string::npos)) {
        rejection_reason = "getattr() with suspicious module — potential sandbox bypass blocked";
        return false;
    }

    // Python string concatenation: "os" + ".system"
    if (lower_code.find("\"os\"") != std::string::npos &&
        lower_code.find("+") != std::string::npos &&
        lower_code.find("system") != std::string::npos) {
        rejection_reason = "string concatenation with os.system — potential sandbox bypass blocked";
        return false;
    }

    return true;
}

bool SandboxVerifier::ContainsRestrictedCommands(const std::string& code) const {
    std::string reason;
    return !ValidateCodeForExecution(code, reason);
}

const char* SandboxVerifier::ExecutionSourceToString(ExecutionSource source) {
    switch (source) {
        case ExecutionSource::ExcelCell:      return "ExcelCell";
        case ExecutionSource::REPL:           return "REPL";
        case ExecutionSource::AutoLoader:     return "AutoLoader";
        case ExecutionSource::RegisteredFunc: return "RegisteredFunc";
        default:                              return "Unknown";
    }
}

bool SandboxVerifier::ValidateFromAnySource(const std::string& code,
                                            ExecutionSource source,
                                            std::string& rejection_reason) const {
    // Delegate to the single validation implementation — all sources get
    // identical checks. The source parameter is for audit logging only.
    bool result = ValidateCodeForExecution(code, rejection_reason);

    // Audit log: record the validation attempt with source context
    if (!result) {
        std::string log_msg = std::string("[SandboxVerifier] Blocked code from ") +
                              ExecutionSourceToString(source) + ": " + rejection_reason;
        LogService::Instance().Log(LogLevel::WARNING_LVL, log_msg);
    }

    return result;
}

} // namespace security
} // namespace rj2xcl
