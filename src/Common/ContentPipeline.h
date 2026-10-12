/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file ContentPipeline.h
 * @brief Routes HTML content to WebView2 viewer or fallback HYPERLINK.
 */

#pragma once

#include <string>
#include <windows.h>

namespace rj2xcl {

/**
 * @brief Routes HTML content from language engines to the WebView2 viewer.
 *
 * When ViewerManager is available, HTML content is displayed in a floating
 * WebView2 window. When unavailable, falls back to saving an HTML file
 * and returning a HYPERLINK formula.
 */
class ContentPipeline {
public:
    /**
     * @brief Route HTML content to viewer or fallback.
     * @param html_content Complete HTML string.
     * @param language Source language ("R", "Julia").
     * @param title Content title.
     * @param application_dispatch Excel COM dispatch pointer (for fallback).
     * @return Cell value: "📊 [Title] (viewer-N)" or HYPERLINK formula.
     */
    static std::string RouteHtmlContent(
        const std::string& html_content,
        const std::string& language,
        const std::string& title,
        LPDISPATCH application_dispatch);

    /**
     * @brief Check if a file path points to an HTML file.
     * @param file_path Path to check.
     * @return true if the path ends with .html or .htm (case-insensitive).
     */
    static bool IsHtmlFile(const std::string& file_path);

    /**
     * @brief Detect if a string is inline HTML content.
     * @param content String to check.
     * @return true if the string starts with <!DOCTYPE or <html.
     */
    static bool IsInlineHtml(const std::string& content);

    /**
     * @brief Detect if a string is Markdown content.
     * @param content String to check.
     * @return true if the string contains Markdown indicators (headers, bold, tables, code blocks).
     */
    static bool IsMarkdown(const std::string& content);

    /**
     * @brief Wrap Markdown content in a self-contained HTML page with marked.js renderer.
     * @param markdown Raw Markdown text.
     * @return Complete HTML string with dark theme and marked.js rendering.
     */
    static std::string WrapMarkdownAsHtml(const std::string& markdown);

    /**
     * @brief Read an HTML file into a string.
     * @param file_path Path to the HTML file.
     * @return File content, or empty string on failure.
     */
    static std::string ReadHtmlFile(const std::string& file_path);

    // ─── Document Type Detection ────────────────────────────────────────

    /** @brief Check if path ends with .pdf (case-insensitive). */
    static bool IsPdfFile(const std::string& file_path);

    /** @brief Check if path ends with .txt (case-insensitive). */
    static bool IsTxtFile(const std::string& file_path);

    /** @brief Check if path ends with .docx (case-insensitive). */
    static bool IsDocxFile(const std::string& file_path);

    /** @brief Check if path ends with .doc but NOT .docx (case-insensitive). */
    static bool IsDocFile(const std::string& file_path);

    /** @brief Check if path is any supported document type (.pdf/.txt/.docx/.doc). */
    static bool IsDocumentFile(const std::string& file_path);

    // ─── Document Conversion ─────────────────────────────────────────────

    /**
     * @brief Read a TXT file and wrap in dark-theme HTML with <pre>.
     * @param file_path Path to the .txt file.
     * @return Complete HTML string, or empty on failure.
     */
    static std::string WrapTxtAsHtml(const std::string& file_path);

    /**
     * @brief Convert DOCX/DOC to HTML via Pandoc.
     * @param file_path Path to the .docx or .doc file.
     * @param from_format "docx" or "doc".
     * @return HTML string on success, or error string prefixed with "Error:".
     */
    static std::string ConvertWithPandoc(const std::string& file_path,
                                          const std::string& from_format);

    /**
     * @brief Locate pandoc.exe: check PATH first, then C:\Quarto\bin\pandoc.exe.
     * @return Full path to pandoc.exe, or empty string if not found.
     */
    static std::string FindPandoc();

    // ─── Content Hashing ─────────────────────────────────────────────────

    /**
     * @brief Compute a fast hash of content string using std::hash<std::string>.
     * @param content The content to hash.
     * @return Hash value.
     */
    static size_t ComputeContentHash(const std::string& content);

    /** @brief Size threshold for NavigateToString vs temp file (2 MB). */
    static constexpr size_t SIZE_THRESHOLD = 2 * 1024 * 1024;

private:
    /**
     * @brief Fallback: save HTML to file and return HYPERLINK formula.
     */
    static std::string FallbackHyperlink(
        const std::string& html_content,
        LPDISPATCH application_dispatch);
};

} // namespace rj2xcl
