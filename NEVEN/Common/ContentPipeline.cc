/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file ContentPipeline.cc
 * @brief Implementation of HTML content routing to WebView2 or fallback.
 */

#include "ContentPipeline.h"
#include "ViewerManager.h"
#include "LogService.h"
#include "Security/InputSanitizer.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <functional>

namespace rj2xcl {

std::string ContentPipeline::RouteHtmlContent(
    const std::string& html_content,
    const std::string& language,
    const std::string& title,
    LPDISPATCH application_dispatch)
{
    if (html_content.empty()) {
        RJ2XCL_LOG_WARN("ContentPipeline: empty HTML content — skipping");
        return "";
    }

    // Auto-detect Markdown: if content is not HTML but looks like Markdown,
    // wrap it in an HTML page with marked.js for rendering
    std::string content_to_route = html_content;
    if (!IsInlineHtml(html_content) && IsMarkdown(html_content)) {
        RJ2XCL_LOG_INFO("ContentPipeline: detected Markdown content, wrapping with marked.js renderer");
        content_to_route = WrapMarkdownAsHtml(html_content);
    }

    auto& viewer = ViewerManager::Instance();

    if (viewer.IsAvailable()) {
        // Route to WebView2 viewer
        std::string viewer_id;

        if (content_to_route.size() < SIZE_THRESHOLD) {
            // Small content: NavigateToString
            viewer_id = viewer.CreateViewer(content_to_route, language, title);
        } else {
            // Large content: write to temp file, then navigate via file:// URI
            std::string temp_dir = "C:\\NEVEN\\webview2-data\\";
            CreateDirectoryA(temp_dir.c_str(), nullptr);

            // Generate unique filename
            FILETIME ft;
            GetSystemTimeAsFileTime(&ft);
            std::string temp_path = temp_dir + "content_" +
                std::to_string(ft.dwLowDateTime) + ".html";

            std::ofstream out(temp_path, std::ios::binary);
            if (out.is_open()) {
                out.write(content_to_route.data(), content_to_route.size());
                out.close();
                viewer_id = viewer.CreateViewerFromFile(temp_path, language, title);
                RJ2XCL_LOG_INFO("ContentPipeline: large content (%zu bytes) → temp file %s",
                                 content_to_route.size(), temp_path.c_str());
            } else {
                // Fallback to NavigateToString even for large content
                viewer_id = viewer.CreateViewer(content_to_route, language, title);
                RJ2XCL_LOG_WARN("ContentPipeline: could not write temp file, using NavigateToString for %zu bytes",
                                 content_to_route.size());
            }
        }

        if (viewer_id.find("Error") != std::string::npos ||
            viewer_id.find("WebView2") != std::string::npos) {
            // Viewer creation failed — fallback
            return FallbackHyperlink(html_content, application_dispatch);
        }

        // Return cell value in format: 📊 [Title] (viewer-N)
        std::string display_title = title.empty() ? "Visualization" : title;
        return "\xF0\x9F\x93\x8A " + display_title + " (" + viewer_id + ")";
    }

    // ViewerManager not available — fallback to HYPERLINK
    return FallbackHyperlink(html_content, application_dispatch);
}

bool ContentPipeline::IsHtmlFile(const std::string& file_path) {
    if (file_path.size() < 5) return false;

    std::string lower = file_path;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

    return (lower.size() >= 5 && lower.substr(lower.size() - 5) == ".html") ||
           (lower.size() >= 4 && lower.substr(lower.size() - 4) == ".htm");
}

bool ContentPipeline::IsInlineHtml(const std::string& content) {
    if (content.size() < 5) return false;

    // Skip leading whitespace
    size_t start = content.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return false;

    std::string prefix = content.substr(start, 15);
    std::transform(prefix.begin(), prefix.end(), prefix.begin(), ::tolower);

    return prefix.find("<!doctype") == 0 || prefix.find("<html") == 0;
}

bool ContentPipeline::IsMarkdown(const std::string& content) {
    if (content.size() < 3) return false;

    // Skip leading whitespace
    size_t start = content.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return false;

    // Check for common Markdown indicators
    // Headers: # ## ###
    if (content[start] == '#') return true;
    // Bold: **text**
    if (content.find("**") != std::string::npos) return true;
    // Lists: - item or * item
    if (content[start] == '-' || content[start] == '*') return true;
    // Tables: | col1 | col2 |
    if (content.find("| ") != std::string::npos && content.find(" |") != std::string::npos) return true;
    // Code blocks: ```
    if (content.find("```") != std::string::npos) return true;

    return false;
}

std::string ContentPipeline::WrapMarkdownAsHtml(const std::string& markdown) {
    // Wrap markdown in a self-contained HTML page with marked.js for rendering
    std::string html;
    html += "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"UTF-8\">\n";
    html += "<script src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>\n";
    html += "<style>\n";
    html += "body{font-family:'Segoe UI',sans-serif;padding:24px 32px;background:#1e1e1e;color:#e0e0e0;line-height:1.7;max-width:900px;margin:0 auto}\n";
    html += "h1,h2,h3{color:#a0e515;margin-top:24px}\n";
    html += "h1{font-size:24px;border-bottom:1px solid #333;padding-bottom:8px}\n";
    html += "h2{font-size:20px}\n";
    html += "h3{font-size:16px;color:#c8e86e}\n";
    html += "table{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}\n";
    html += "th{background:#2a2a2a;color:#a0e515;padding:8px 12px;text-align:left;border:1px solid #3a3a3a}\n";
    html += "td{padding:6px 12px;border:1px solid #333}\n";
    html += "tr:nth-child(even){background:#242424}\n";
    html += "code{background:#2a2a2a;color:#ce9178;padding:2px 5px;border-radius:3px;font-family:Consolas,monospace;font-size:13px}\n";
    html += "pre{background:#161616;border:1px solid #333;border-radius:6px;padding:14px;overflow-x:auto}\n";
    html += "pre code{color:#d4d4d4;background:none;padding:0}\n";
    html += "strong{color:#e0e0e0}\n";
    html += "ul,ol{margin:8px 0 12px 20px}\n";
    html += "li{margin-bottom:4px}\n";
    html += "blockquote{border-left:3px solid #a0e515;padding:6px 14px;margin:10px 0;background:#242424;color:#bbb}\n";
    html += "a{color:#a0e515}\n";
    html += "hr{border:none;border-top:1px solid #333;margin:20px 0}\n";
    html += "</style></head><body>\n";
    html += "<div id=\"content\"></div>\n";
    html += "<script>\n";
    html += "var md = decodeURIComponent(\"";

    // URL-encode the markdown to safely embed it in JavaScript
    for (char c : markdown) {
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
            c == '-' || c == '_' || c == '.' || c == '~' || c == ' ') {
            if (c == ' ') html += "%20";
            else html += c;
        } else {
            char hex[4];
            snprintf(hex, sizeof(hex), "%%%02X", (unsigned char)c);
            html += hex;
        }
    }

    html += "\");\n";
    html += "document.getElementById('content').innerHTML = marked.parse(md);\n";
    html += "</script></body></html>";

    return html;
}

std::string ContentPipeline::ReadHtmlFile(const std::string& file_path) {
    std::ifstream file(file_path, std::ios::binary);
    if (!file.is_open()) {
        RJ2XCL_LOG_WARN("ContentPipeline: cannot read file %s", file_path.c_str());
        return "";
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

std::string ContentPipeline::FallbackHyperlink(
    const std::string& html_content,
    LPDISPATCH application_dispatch)
{
    // Save HTML to temp file when WebView2 is not available
    std::string temp_dir = "C:\\NEVEN\\webview2-data\\";
    CreateDirectoryA(temp_dir.c_str(), nullptr);

    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    std::string temp_path = temp_dir + "fallback_" +
        std::to_string(ft.dwLowDateTime) + ".html";

    std::ofstream out(temp_path, std::ios::binary);
    if (out.is_open()) {
        out.write(html_content.data(), html_content.size());
        out.close();
        RJ2XCL_LOG_INFO("ContentPipeline: fallback saved to %s", temp_path.c_str());
        return temp_path;
    }

    RJ2XCL_LOG_WARN("ContentPipeline: fallback could not save file");
    return "Error: could not save HTML content";
}

// ─── Document Type Detection ────────────────────────────────────────────

bool ContentPipeline::IsPdfFile(const std::string& file_path) {
    if (file_path.size() < 4) return false;
    std::string ext = file_path.substr(file_path.size() - 4);
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    return ext == ".pdf";
}

bool ContentPipeline::IsTxtFile(const std::string& file_path) {
    if (file_path.size() < 4) return false;
    std::string ext = file_path.substr(file_path.size() - 4);
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    return ext == ".txt";
}

bool ContentPipeline::IsDocxFile(const std::string& file_path) {
    if (file_path.size() < 5) return false;
    std::string ext = file_path.substr(file_path.size() - 5);
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    return ext == ".docx";
}

bool ContentPipeline::IsDocFile(const std::string& file_path) {
    if (file_path.size() < 4) return false;
    // Must end with .doc but NOT .docx
    std::string ext4 = file_path.substr(file_path.size() - 4);
    std::transform(ext4.begin(), ext4.end(), ext4.begin(), ::tolower);
    if (ext4 != ".doc") return false;
    // Ensure it's not .docx (check that there's no 'x' after .doc)
    if (file_path.size() >= 5) {
        std::string ext5 = file_path.substr(file_path.size() - 5);
        std::transform(ext5.begin(), ext5.end(), ext5.begin(), ::tolower);
        if (ext5 == ".docx") return false;
    }
    return true;
}

bool ContentPipeline::IsDocumentFile(const std::string& file_path) {
    return IsPdfFile(file_path) || IsTxtFile(file_path) ||
           IsDocxFile(file_path) || IsDocFile(file_path);
}

// ─── Content Hashing ────────────────────────────────────────────────────

size_t ContentPipeline::ComputeContentHash(const std::string& content) {
    return std::hash<std::string>{}(content);
}

// ─── TXT Document Viewing ───────────────────────────────────────────────

std::string ContentPipeline::WrapTxtAsHtml(const std::string& file_path) {
    std::ifstream file(file_path, std::ios::binary);
    if (!file.is_open()) {
        RJ2XCL_LOG_WARN("ContentPipeline: cannot read TXT file %s", file_path.c_str());
        return "";
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();

    // HTML-escape special characters
    std::string escaped;
    escaped.reserve(content.size() + content.size() / 10);
    for (char c : content) {
        switch (c) {
            case '<': escaped += "&lt;"; break;
            case '>': escaped += "&gt;"; break;
            case '&': escaped += "&amp;"; break;
            case '"': escaped += "&quot;"; break;
            default: escaped += c; break;
        }
    }

    // Wrap in dark-theme HTML with <pre> and monospace font
    std::string html;
    html += "<!DOCTYPE html><html><head><meta charset=\"UTF-8\">\n";
    html += "<style>\n";
    html += "body{margin:0;padding:24px;background:#1e1e1e;color:#d4d4d4;font-family:Consolas,'Courier New',monospace;font-size:14px;line-height:1.6}\n";
    html += "pre{white-space:pre-wrap;word-wrap:break-word;margin:0}\n";
    html += "</style></head><body>\n";
    html += "<pre>" + escaped + "</pre>\n";
    html += "</body></html>";

    return html;
}

// ─── Pandoc Conversion ──────────────────────────────────────────────────

std::string ContentPipeline::FindPandoc() {
    // Search system PATH first using SearchPathA
    char path_buffer[MAX_PATH] = {};
    DWORD result = SearchPathA(NULL, "pandoc.exe", NULL, MAX_PATH, path_buffer, NULL);
    if (result > 0 && result < MAX_PATH) {
        return std::string(path_buffer);
    }

    // Fallback to Quarto installation
    const char* quarto_pandoc = "C:\\Quarto\\bin\\pandoc.exe";
    DWORD attrs = GetFileAttributesA(quarto_pandoc);
    if (attrs != INVALID_FILE_ATTRIBUTES) {
        return std::string(quarto_pandoc);
    }

    return "";
}

std::string ContentPipeline::ConvertWithPandoc(const std::string& file_path,
                                                const std::string& from_format) {
    // Validate file path against allowlist before process creation
    auto path_validation = rj2xcl::security::InputSanitizer::ValidatePath(file_path);
    if (!path_validation.is_valid) {
        return "Error: invalid file path - " + path_validation.error_message;
    }

    // Validate from_format argument
    auto format_validation = rj2xcl::security::InputSanitizer::ValidateArgument(from_format);
    if (!format_validation.is_valid) {
        return "Error: invalid format argument - " + format_validation.error_message;
    }

    // Find pandoc
    std::string pandoc_path = FindPandoc();
    if (pandoc_path.empty()) {
        return "Error: Pandoc not found — install Quarto or add pandoc to PATH";
    }

    // Check file exists
    DWORD attrs = GetFileAttributesA(file_path.c_str());
    if (attrs == INVALID_FILE_ATTRIBUTES) {
        return "Error: file not found — " + file_path;
    }

    // Create pipes for stdout and stderr
    SECURITY_ATTRIBUTES sa = {};
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;

    HANDLE stdout_read = NULL, stdout_write = NULL;
    HANDLE stderr_read = NULL, stderr_write = NULL;

    if (!CreatePipe(&stdout_read, &stdout_write, &sa, 0)) {
        return "Error: Pandoc conversion failed — could not create stdout pipe";
    }
    if (!CreatePipe(&stderr_read, &stderr_write, &sa, 0)) {
        CloseHandle(stdout_read);
        CloseHandle(stdout_write);
        return "Error: Pandoc conversion failed — could not create stderr pipe";
    }

    // Ensure read handles are not inherited
    SetHandleInformation(stdout_read, HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(stderr_read, HANDLE_FLAG_INHERIT, 0);

    // Build safe command line with separated executable and arguments
    auto safe_cmd = rj2xcl::security::InputSanitizer::BuildSafeCommandLine(
        pandoc_path, {"--from=" + from_format, "--to=html", "--standalone", file_path});

    if (safe_cmd.first.empty()) {
        CloseHandle(stdout_read);
        CloseHandle(stdout_write);
        CloseHandle(stderr_read);
        CloseHandle(stderr_write);
        return "Error: Pandoc command line validation failed";
    }

    STARTUPINFOA si = {};
    si.cb = sizeof(STARTUPINFOA);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdOutput = stdout_write;
    si.hStdError = stderr_write;
    si.hStdInput = NULL;

    PROCESS_INFORMATION pi = {};

    std::string cmd_line = safe_cmd.second;
    std::vector<char> cmd_buf(cmd_line.begin(), cmd_line.end());
    cmd_buf.push_back('\0');

    BOOL created = CreateProcessA(
        safe_cmd.first.c_str(),
        cmd_buf.data(),
        NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL,
        &si, &pi);

    // Close write ends in parent process
    CloseHandle(stdout_write);
    CloseHandle(stderr_write);

    if (!created) {
        CloseHandle(stdout_read);
        CloseHandle(stderr_read);
        return "Error: Pandoc conversion failed — could not start process";
    }

    // Wait for process with 30s timeout
    DWORD wait_result = WaitForSingleObject(pi.hProcess, 30000);

    if (wait_result == WAIT_TIMEOUT) {
        TerminateProcess(pi.hProcess, 1);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        CloseHandle(stdout_read);
        CloseHandle(stderr_read);
        return "Error: Pandoc timed out (30s)";
    }

    // Read stdout
    std::string stdout_content;
    char read_buffer[4096];
    DWORD bytes_read;
    while (ReadFile(stdout_read, read_buffer, sizeof(read_buffer), &bytes_read, NULL) && bytes_read > 0) {
        stdout_content.append(read_buffer, bytes_read);
    }

    // Read stderr
    std::string stderr_content;
    while (ReadFile(stderr_read, read_buffer, sizeof(read_buffer), &bytes_read, NULL) && bytes_read > 0) {
        stderr_content.append(read_buffer, bytes_read);
    }

    // Check exit code
    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(stdout_read);
    CloseHandle(stderr_read);

    if (exit_code != 0) {
        return "Error: Pandoc conversion failed — " + stderr_content;
    }

    return stdout_content;
}

} // namespace rj2xcl
