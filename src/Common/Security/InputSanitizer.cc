#include "InputSanitizer.h"

#include <algorithm>
#include <cctype>

namespace rj2xcl {
namespace security {

// Maximum path length (Windows MAX_PATH)
static constexpr size_t kMaxPathLength = 260;

// ---------------------------------------------------------------------------
// Private helpers — character allowlists
// ---------------------------------------------------------------------------

bool InputSanitizer::IsAllowedPathChar(char c) {
    // Alphanumeric
    if (std::isalnum(static_cast<unsigned char>(c))) return true;
    // Path separators
    if (c == '\\' || c == '/') return true;
    // Common path characters
    if (c == '.' || c == '-' || c == '_') return true;
    // Space (allowed in Windows paths)
    if (c == ' ') return true;
    // Colon for drive letters (e.g., C:)
    if (c == ':') return true;

    return false;
}

bool InputSanitizer::IsAllowedArgumentChar(char c) {
    // Alphanumeric
    if (std::isalnum(static_cast<unsigned char>(c))) return true;
    // Limited set of safe punctuation
    if (c == '.' || c == '-' || c == '_') return true;
    // Space (for multi-word arguments)
    if (c == ' ') return true;
    // Equals sign (for --key=value style arguments)
    if (c == '=') return true;
    // Path separators and colon (for arguments that contain file paths)
    if (c == '\\' || c == '/' || c == ':') return true;

    return false;
}

// ---------------------------------------------------------------------------
// Public interface — stub implementations
// ---------------------------------------------------------------------------

InputSanitizer::ValidationResult InputSanitizer::ValidatePath(const std::string& path) {
    ValidationResult result{};
    result.is_valid = false;
    result.first_invalid_char = 0;
    result.invalid_char_position = 0;

    // Check for empty path
    if (path.empty()) {
        result.error_message = "Path is empty";
        return result;
    }

    // Check for path exceeding MAX_PATH
    if (path.size() > kMaxPathLength) {
        result.error_message = "Path exceeds maximum length of 260 characters";
        return result;
    }

    // Validate each character against the allowlist
    for (size_t i = 0; i < path.size(); ++i) {
        if (!IsAllowedPathChar(path[i])) {
            result.error_message = "Path contains disallowed character";
            result.first_invalid_char = path[i];
            result.invalid_char_position = i;
            return result;
        }
    }

    result.is_valid = true;
    return result;
}

InputSanitizer::ValidationResult InputSanitizer::ValidateArgument(const std::string& argument) {
    ValidationResult result{};
    result.is_valid = false;
    result.first_invalid_char = 0;
    result.invalid_char_position = 0;

    // Check for empty argument
    if (argument.empty()) {
        result.error_message = "Argument is empty";
        return result;
    }

    // Validate each character against the argument allowlist
    for (size_t i = 0; i < argument.size(); ++i) {
        if (!IsAllowedArgumentChar(argument[i])) {
            result.error_message = "Argument contains disallowed character";
            result.first_invalid_char = argument[i];
            result.invalid_char_position = i;
            return result;
        }
    }

    result.is_valid = true;
    return result;
}

std::string InputSanitizer::SanitizePath(const std::string& path) {
    std::string sanitized;
    sanitized.reserve(path.size());

    for (char c : path) {
        if (IsAllowedPathChar(c)) {
            sanitized += c;
        }
    }

    return sanitized;
}

std::pair<std::string, std::string> InputSanitizer::BuildSafeCommandLine(
    const std::string& executable,
    const std::vector<std::string>& arguments) {

    // Validate the executable path through ValidatePath before construction
    ValidationResult path_result = ValidatePath(executable);
    if (!path_result.is_valid) {
        // Return empty pair on validation failure — caller must check
        return {"", ""};
    }

    // lpApplicationName: the validated executable path (unquoted for CreateProcess)
    // Since ValidatePath passed, the path contains only allowed characters
    std::string app_name = executable;

    // lpCommandLine: quoted executable followed by quoted arguments
    // Per Windows CreateProcess convention, lpCommandLine should include the
    // executable as argv[0] in quoted form, followed by quoted arguments
    std::string cmd_line = "\"" + app_name + "\"";

    for (const auto& arg : arguments) {
        // Validate each argument through ValidateArgument before construction
        ValidationResult arg_result = ValidateArgument(arg);
        if (!arg_result.is_valid) {
            // Return empty pair on any argument validation failure
            return {"", ""};
        }
        cmd_line += " \"" + arg + "\"";
    }

    return {app_name, cmd_line};
}

} // namespace security
} // namespace rj2xcl
