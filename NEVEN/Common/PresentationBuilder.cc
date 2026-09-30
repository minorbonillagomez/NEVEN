/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file PresentationBuilder.cc
 * @brief Implementation of reveal.js presentation builder.
 */

#include "PresentationBuilder.h"
#include "ViewerManager.h"
#include "LogService.h"
#include "ConfigService.h"

#include <fstream>
#include <sstream>
#include <algorithm>
#include <ctime>

namespace rj2xcl {

// ─── Static Members ─────────────────────────────────────────────────────

std::vector<PresentationBuilder> PresentationBuilder::registry_;
std::mutex PresentationBuilder::registry_mutex_;
uint32_t PresentationBuilder::next_id_ = 1;

// ─── Constructor ────────────────────────────────────────────────────────

PresentationBuilder::PresentationBuilder(const std::string& title)
    : title_(title)
{
    std::stringstream ss;
    ss << "presentation-" << next_id_++;
    id_ = ss.str();
}

// ─── Slide Management ───────────────────────────────────────────────────

void PresentationBuilder::AddTextSlide(const std::string& markdown_content) {
    slides_.push_back({Slide::TEXT, markdown_content});
}

void PresentationBuilder::AddViewerSlide(const std::string& viewer_id) {
    std::string html = ViewerManager::Instance().CaptureViewerContent(viewer_id);
    if (html.empty()) {
        RJ2XCL_LOG_WARN("PresentationBuilder: viewer %s not found or empty — skipping slide", viewer_id.c_str());
        return;
    }
    slides_.push_back({Slide::VIEWER, html});
}

void PresentationBuilder::AddHtmlSlide(const std::string& html_content) {
    slides_.push_back({Slide::HTML, html_content});
}

// ─── Build ──────────────────────────────────────────────────────────────

std::string PresentationBuilder::Build(const std::string& output_path) {
    std::string html = GenerateRevealHtml();

    // Determine output path
    std::string path = output_path;
    if (path.empty()) {
        std::string dir = ConfigService::Instance().GetWebView2UserDataFolder();
        CreateDirectoryA(dir.c_str(), nullptr);
        path = dir + "\\" + "presentation_" + SanitizeTitle(title_) + "_" + GenerateTimestamp() + ".html";
    }

    // Write file
    std::ofstream file(path, std::ios::binary);
    if (!file.is_open()) {
        RJ2XCL_LOG_ERR("PresentationBuilder: cannot write to %s", path.c_str());
        return "Error: cannot write presentation file";
    }

    file << html;
    file.close();

    RJ2XCL_LOG_INFO("Presentation built: %s (%d slides)", path.c_str(), (int)slides_.size());

    // Open in viewer for preview
    ViewerManager::Instance().CreateViewerFromFile(path, "Presentation", title_);

    return path;
}

// ─── Accessors ──────────────────────────────────────────────────────────

std::string PresentationBuilder::GetId() const { return id_; }
int PresentationBuilder::GetSlideCount() const { return (int)slides_.size(); }
std::string PresentationBuilder::GetTitle() const { return title_; }

// ─── HTML Generation ────────────────────────────────────────────────────

std::string PresentationBuilder::GenerateRevealHtml() const {
    std::stringstream ss;

    // HTML header with embedded reveal.js CSS
    ss << "<!DOCTYPE html>\n<html>\n<head>\n";
    ss << "<meta charset=\"utf-8\">\n";
    ss << "<title>" << title_ << "</title>\n";
    ss << "<style>\n";
    // Minimal reveal.js CSS (embedded inline for portability)
    ss << "html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; font-family: 'Segoe UI', sans-serif; }\n";
    ss << ".reveal { position: relative; width: 100%; height: 100%; }\n";
    ss << ".slides { position: absolute; width: 100%; height: 100%; }\n";
    ss << ".slides > section { position: absolute; width: 90%; height: 85%; left: 5%; top: 5%; display: none; box-sizing: border-box; padding: 40px; overflow: auto; }\n";
    ss << ".slides > section.active { display: block; }\n";
    ss << ".slides > section h1 { font-size: 2.5em; color: #2c3e50; margin-bottom: 20px; }\n";
    ss << ".slides > section h2 { font-size: 1.8em; color: #34495e; margin-bottom: 15px; }\n";
    ss << ".slides > section p { font-size: 1.2em; line-height: 1.6; color: #555; }\n";
    ss << ".nav-btn { position: fixed; bottom: 20px; padding: 10px 20px; font-size: 16px; cursor: pointer; background: #3498db; color: white; border: none; border-radius: 5px; z-index: 100; }\n";
    ss << ".nav-btn:hover { background: #2980b9; }\n";
    ss << ".viewer-content { width: 100%; height: 80%; border: none; }\n";
    ss << ".viewer-content iframe { width: 100%; height: 100%; border: none; }\n";
    ss << ".slide-counter { position: fixed; bottom: 25px; left: 50%; transform: translateX(-50%); font-size: 14px; color: #888; z-index: 100; }\n";
    ss << "</style>\n</head>\n<body>\n";

    // Slides container
    ss << "<div class=\"reveal\">\n<div class=\"slides\">\n";

    // Title slide
    ss << "<section class=\"active\">\n";
    ss << "<h1>" << title_ << "</h1>\n";
    ss << "<p>Generado por RJ2XCL — Universidad de Costa Rica</p>\n";
    ss << "<p style=\"color:#888;font-size:0.8em;\">" << GenerateTimestamp() << "</p>\n";
    ss << "</section>\n";

    // Content slides
    for (const auto& slide : slides_) {
        ss << "<section>\n";
        switch (slide.type) {
        case Slide::TEXT:
            // Simple Markdown-to-HTML (headers, paragraphs)
            {
                std::istringstream lines(slide.content);
                std::string line;
                while (std::getline(lines, line)) {
                    if (line.find("# ") == 0) {
                        ss << "<h1>" << line.substr(2) << "</h1>\n";
                    } else if (line.find("## ") == 0) {
                        ss << "<h2>" << line.substr(3) << "</h2>\n";
                    } else if (!line.empty()) {
                        ss << "<p>" << line << "</p>\n";
                    }
                }
            }
            break;

        case Slide::VIEWER:
        case Slide::HTML:
            ss << "<div class=\"viewer-content\">\n";
            ss << slide.content << "\n";
            ss << "</div>\n";
            break;
        }
        ss << "</section>\n";
    }

    ss << "</div>\n</div>\n";

    // Navigation JavaScript
    ss << "<button class=\"nav-btn\" id=\"prev-btn\" onclick=\"navigate(-1)\">&#9664; Anterior</button>\n";
    ss << "<span class=\"slide-counter\" id=\"counter\"></span>\n";
    ss << "<button class=\"nav-btn\" id=\"next-btn\" onclick=\"navigate(1)\">Siguiente &#9654;</button>\n";
    ss << "<script>\n";
    ss << "let current = 0;\n";
    ss << "const slides = document.querySelectorAll('.slides > section');\n";
    ss << "function navigate(dir) {\n";
    ss << "  slides[current].classList.remove('active');\n";
    ss << "  current = Math.max(0, Math.min(slides.length - 1, current + dir));\n";
    ss << "  slides[current].classList.add('active');\n";
    ss << "  document.getElementById('counter').textContent = (current + 1) + ' / ' + slides.length;\n";
    ss << "}\n";
    ss << "document.addEventListener('keydown', function(e) {\n";
    ss << "  if (e.key === 'ArrowRight' || e.key === ' ') navigate(1);\n";
    ss << "  if (e.key === 'ArrowLeft') navigate(-1);\n";
    ss << "});\n";
    ss << "navigate(0);\n";
    ss << "</script>\n";

    ss << "</body>\n</html>\n";
    return ss.str();
}

// ─── Utilities ──────────────────────────────────────────────────────────

std::string PresentationBuilder::SanitizeTitle(const std::string& title) {
    if (title.empty()) return "untitled";
    std::string result;
    for (char c : title) {
        result += std::isalnum(static_cast<unsigned char>(c)) ? c : '_';
    }
    // Collapse multiple underscores
    std::string clean;
    bool last_underscore = false;
    for (char c : result) {
        if (c == '_') { if (!last_underscore) clean += c; last_underscore = true; }
        else { clean += c; last_underscore = false; }
    }
    while (!clean.empty() && clean.back() == '_') clean.pop_back();
    return clean.empty() ? "untitled" : clean;
}

std::string PresentationBuilder::GenerateTimestamp() {
    time_t now = time(nullptr);
    struct tm tm_buf;
    localtime_s(&tm_buf, &now);
    char buf[20];
    strftime(buf, sizeof(buf), "%Y%m%d_%H%M%S", &tm_buf);
    return std::string(buf);
}

// ─── Global Registry ────────────────────────────────────────────────────

std::string PresentationBuilder::CreatePresentation(const std::string& title) {
    std::lock_guard<std::mutex> lock(registry_mutex_);
    registry_.emplace_back(title);
    return registry_.back().GetId();
}

PresentationBuilder* PresentationBuilder::FindPresentation(const std::string& id) {
    std::lock_guard<std::mutex> lock(registry_mutex_);
    for (auto& pres : registry_) {
        if (pres.GetId() == id) return &pres;
    }
    return nullptr;
}

std::string PresentationBuilder::AddSlideToPresentation(
    const std::string& pres_id, const std::string& content, const std::string& slide_type) {
    auto* pres = FindPresentation(pres_id);
    if (!pres) return "Error: presentation not found — " + pres_id;

    if (slide_type == "text") {
        pres->AddTextSlide(content);
    } else if (slide_type == "viewer") {
        pres->AddViewerSlide(content);
    } else if (slide_type == "html") {
        pres->AddHtmlSlide(content);
    } else {
        return "Error: invalid slide type — use text, viewer, or html";
    }
    return "OK";
}

std::string PresentationBuilder::BuildPresentation(
    const std::string& pres_id, const std::string& output_path) {
    auto* pres = FindPresentation(pres_id);
    if (!pres) return "Error: presentation not found — " + pres_id;
    return pres->Build(output_path);
}

} // namespace rj2xcl
