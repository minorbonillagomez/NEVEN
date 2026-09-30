/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file PresentationBuilder.h
 * @brief Composes self-contained reveal.js HTML presentations.
 */

#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <mutex>

namespace rj2xcl {

/**
 * @brief Builds self-contained HTML presentations using reveal.js.
 *
 * Slides can be text (Markdown), HTML, or captured viewer content.
 * The output is a single .html file with reveal.js CSS+JS embedded inline.
 */
class PresentationBuilder {
public:
    PresentationBuilder(const std::string& title);

    // ─── Slide Management ────────────────────────────────────────────────

    /** @brief Add a text slide (Markdown content). */
    void AddTextSlide(const std::string& markdown_content);

    /** @brief Add a slide from a viewer's current HTML content. */
    void AddViewerSlide(const std::string& viewer_id);

    /** @brief Add a raw HTML slide. */
    void AddHtmlSlide(const std::string& html_content);

    // ─── Build ───────────────────────────────────────────────────────────

    /**
     * @brief Build the presentation as a self-contained HTML file.
     * @param output_path Output file path. If empty, auto-generates in User_Data_Folder.
     * @return Absolute file path of the generated HTML, or error string.
     */
    std::string Build(const std::string& output_path = "");

    // ─── Accessors ───────────────────────────────────────────────────────

    std::string GetId() const;
    int GetSlideCount() const;
    std::string GetTitle() const;

    // ─── Global Registry ─────────────────────────────────────────────────

    /** @brief Create a new presentation and register it globally. */
    static std::string CreatePresentation(const std::string& title);

    /** @brief Find a presentation by ID. Returns nullptr if not found. */
    static PresentationBuilder* FindPresentation(const std::string& id);

    /** @brief Add a slide to a registered presentation. */
    static std::string AddSlideToPresentation(const std::string& pres_id,
                                               const std::string& content,
                                               const std::string& slide_type);

    /** @brief Build a registered presentation. */
    static std::string BuildPresentation(const std::string& pres_id,
                                          const std::string& output_path);

private:
    struct Slide {
        enum Type { TEXT, VIEWER, HTML };
        Type type;
        std::string content;
    };

    std::string id_;
    std::string title_;
    std::vector<Slide> slides_;

    std::string GenerateRevealHtml() const;
    static std::string SanitizeTitle(const std::string& title);
    static std::string GenerateTimestamp();

    // ─── Global Registry ─────────────────────────────────────────────────

    static std::vector<PresentationBuilder> registry_;
    static std::mutex registry_mutex_;
    static uint32_t next_id_;
};

} // namespace rj2xcl
