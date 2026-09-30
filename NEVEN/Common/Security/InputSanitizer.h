#pragma once

#ifndef INPUT_SANITIZER_H
#define INPUT_SANITIZER_H

#include <string>
#include <vector>
#include <utility>

/// @brief Error code: path contains a character not in the allowlist.
#define NEVEN_ERR_INVALID_PATH_CHAR  0x80040001
/// @brief Error code: path string is empty.
#define NEVEN_ERR_EMPTY_PATH         0x80040002
/// @brief Error code: path exceeds MAX_PATH (260 characters).
#define NEVEN_ERR_PATH_TOO_LONG      0x80040003
/// @brief Error code: null or invalid input pointer.
#define NEVEN_ERR_NULL_INPUT         0x80040004

namespace rj2xcl {
namespace security {

/**
 * @brief Centralized input sanitizer for command-line argument safety.
 *
 * Validates strings against a character allowlist before they are used
 * in CreateProcess calls or command-line construction. Prevents OS
 * command injection via metacharacters in file paths from Excel cells.
 */
class InputSanitizer {
public:
    /** @brief Validation result with error details. */
    struct ValidationResult {
        bool is_valid;                  ///< true if the input passed validation
        std::string error_message;      ///< Empty if valid
        char first_invalid_char;        ///< First offending character (0 if valid)
        size_t invalid_char_position;   ///< Position of first offending char
    };

    /**
     * @brief Validates a file path against the character allowlist.
     *
     * Allowed characters: [A-Za-z0-9], path separators (\ /), dot (.),
     * hyphen (-), underscore (_), space, colon (:) for drive letters.
     *
     * @param path The file path string to validate.
     * @return ValidationResult indicating pass/fail with details.
     */
    static ValidationResult ValidatePath(const std::string& path);

    /**
     * @brief Validates a generic argument string (stricter than path).
     *
     * Allowed characters: [A-Za-z0-9], dot (.), hyphen (-),
     * underscore (_), space, equals (=), path separators (\ /), colon (:).
     * Rejects: & | ; ` < > " \n \r % $ ! and all control characters.
     *
     * @param argument The argument string to validate.
     * @return ValidationResult indicating pass/fail with details.
     */
    static ValidationResult ValidateArgument(const std::string& argument);

    /**
     * @brief Sanitizes a path by removing disallowed characters.
     *
     * Idempotent: sanitize(sanitize(x)) == sanitize(x).
     *
     * @param path The file path to sanitize.
     * @return Sanitized path with only allowed characters.
     */
    static std::string SanitizePath(const std::string& path);

    /**
     * @brief Constructs a safe CreateProcess call with separated
     *        lpApplicationName and lpCommandLine.
     *
     * @param executable Validated path to the executable.
     * @param arguments Vector of validated argument strings.
     * @return Pair of (lpApplicationName, lpCommandLine) strings.
     */
    static std::pair<std::string, std::string> BuildSafeCommandLine(
        const std::string& executable,
        const std::vector<std::string>& arguments);

private:
    /**
     * @brief Checks whether a character is allowed in file paths.
     * @param c The character to check.
     * @return true if the character is in the path allowlist.
     */
    static bool IsAllowedPathChar(char c);

    /**
     * @brief Checks whether a character is allowed in command arguments.
     * @param c The character to check.
     * @return true if the character is in the argument allowlist.
     */
    static bool IsAllowedArgumentChar(char c);
};

} // namespace security
} // namespace rj2xcl

#endif // INPUT_SANITIZER_H
