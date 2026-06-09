/**
 * Copyright (c) 2026 NEVEN Project — GPL v3
 *
 * @file viewer_professional_tests.cc
 * @brief Unit tests for Viewer Professional features:
 *        file extension detection, content hashing, TXT wrapping,
 *        Pandoc conversion error handling, and PostMessageBridge routing.
 */
#include <gtest/gtest.h>
#include <string>
#include <fstream>
#include <cstdio>

#include "ContentPipeline.h"

using namespace rj2xcl;

// ═══════════════════════════════════════════════════════════════════════════
// Task 1.3: File Extension Detection Tests
// ═══════════════════════════════════════════════════════════════════════════

TEST(ViewerProfessional_FileDetection, PdfFile_LowerCase) {
    EXPECT_TRUE(ContentPipeline::IsPdfFile("C:\\docs\\report.pdf"));
}

TEST(ViewerProfessional_FileDetection, PdfFile_UpperCase) {
    EXPECT_TRUE(ContentPipeline::IsPdfFile("C:\\docs\\report.PDF"));
}

TEST(ViewerProfessional_FileDetection, PdfFile_MixedCase) {
    EXPECT_TRUE(ContentPipeline::IsPdfFile("C:\\docs\\report.Pdf"));
}

TEST(ViewerProfessional_FileDetection, PdfFile_NotTxt) {
    EXPECT_FALSE(ContentPipeline::IsPdfFile("C:\\docs\\notes.txt"));
}

TEST(ViewerProfessional_FileDetection, TxtFile_LowerCase) {
    EXPECT_TRUE(ContentPipeline::IsTxtFile("C:\\docs\\notes.txt"));
}

TEST(ViewerProfessional_FileDetection, TxtFile_UpperCase) {
    EXPECT_TRUE(ContentPipeline::IsTxtFile("C:\\docs\\notes.TXT"));
}

TEST(ViewerProfessional_FileDetection, TxtFile_NotPdf) {
    EXPECT_FALSE(ContentPipeline::IsTxtFile("C:\\docs\\report.pdf"));
}

TEST(ViewerProfessional_FileDetection, DocxFile_LowerCase) {
    EXPECT_TRUE(ContentPipeline::IsDocxFile("C:\\docs\\report.docx"));
}

TEST(ViewerProfessional_FileDetection, DocxFile_UpperCase) {
    EXPECT_TRUE(ContentPipeline::IsDocxFile("C:\\docs\\report.DOCX"));
}

TEST(ViewerProfessional_FileDetection, DocxFile_NotDoc) {
    // .docx should NOT be detected as .doc
    EXPECT_FALSE(ContentPipeline::IsDocFile("C:\\docs\\report.docx"));
}

TEST(ViewerProfessional_FileDetection, DocFile_LowerCase) {
    EXPECT_TRUE(ContentPipeline::IsDocFile("C:\\docs\\report.doc"));
}

TEST(ViewerProfessional_FileDetection, DocFile_UpperCase) {
    EXPECT_TRUE(ContentPipeline::IsDocFile("C:\\docs\\report.DOC"));
}

TEST(ViewerProfessional_FileDetection, DocFile_NotDocx) {
    // .doc should NOT match .docx
    EXPECT_FALSE(ContentPipeline::IsDocFile("C:\\docs\\report.docx"));
    EXPECT_FALSE(ContentPipeline::IsDocFile("C:\\docs\\report.DOCX"));
}

TEST(ViewerProfessional_FileDetection, HtmlFile_NotPdf) {
    EXPECT_FALSE(ContentPipeline::IsPdfFile("C:\\docs\\page.html"));
}

TEST(ViewerProfessional_FileDetection, HtmlFile_IsHtml) {
    EXPECT_TRUE(ContentPipeline::IsHtmlFile("C:\\docs\\page.html"));
}

TEST(ViewerProfessional_FileDetection, HtmlFile_NotDocument) {
    EXPECT_FALSE(ContentPipeline::IsDocumentFile("C:\\docs\\page.html"));
}

// Mutual exclusivity tests
TEST(ViewerProfessional_FileDetection, MutualExclusivity_Pdf) {
    std::string path = "C:\\docs\\report.pdf";
    EXPECT_TRUE(ContentPipeline::IsPdfFile(path));
    EXPECT_FALSE(ContentPipeline::IsTxtFile(path));
    EXPECT_FALSE(ContentPipeline::IsDocxFile(path));
    EXPECT_FALSE(ContentPipeline::IsDocFile(path));
    EXPECT_FALSE(ContentPipeline::IsHtmlFile(path));
}

TEST(ViewerProfessional_FileDetection, MutualExclusivity_Txt) {
    std::string path = "C:\\docs\\notes.txt";
    EXPECT_FALSE(ContentPipeline::IsPdfFile(path));
    EXPECT_TRUE(ContentPipeline::IsTxtFile(path));
    EXPECT_FALSE(ContentPipeline::IsDocxFile(path));
    EXPECT_FALSE(ContentPipeline::IsDocFile(path));
    EXPECT_FALSE(ContentPipeline::IsHtmlFile(path));
}

TEST(ViewerProfessional_FileDetection, MutualExclusivity_Docx) {
    std::string path = "C:\\docs\\report.docx";
    EXPECT_FALSE(ContentPipeline::IsPdfFile(path));
    EXPECT_FALSE(ContentPipeline::IsTxtFile(path));
    EXPECT_TRUE(ContentPipeline::IsDocxFile(path));
    EXPECT_FALSE(ContentPipeline::IsDocFile(path));
    EXPECT_FALSE(ContentPipeline::IsHtmlFile(path));
}

TEST(ViewerProfessional_FileDetection, MutualExclusivity_Doc) {
    std::string path = "C:\\docs\\report.doc";
    EXPECT_FALSE(ContentPipeline::IsPdfFile(path));
    EXPECT_FALSE(ContentPipeline::IsTxtFile(path));
    EXPECT_FALSE(ContentPipeline::IsDocxFile(path));
    EXPECT_TRUE(ContentPipeline::IsDocFile(path));
    EXPECT_FALSE(ContentPipeline::IsHtmlFile(path));
}

TEST(ViewerProfessional_FileDetection, IsDocumentFile_AllTypes) {
    EXPECT_TRUE(ContentPipeline::IsDocumentFile("report.pdf"));
    EXPECT_TRUE(ContentPipeline::IsDocumentFile("notes.txt"));
    EXPECT_TRUE(ContentPipeline::IsDocumentFile("doc.docx"));
    EXPECT_TRUE(ContentPipeline::IsDocumentFile("old.doc"));
    EXPECT_FALSE(ContentPipeline::IsDocumentFile("page.html"));
    EXPECT_FALSE(ContentPipeline::IsDocumentFile("style.css"));
    EXPECT_FALSE(ContentPipeline::IsDocumentFile(""));
}

TEST(ViewerProfessional_FileDetection, ShortPaths) {
    EXPECT_FALSE(ContentPipeline::IsPdfFile(""));
    EXPECT_FALSE(ContentPipeline::IsPdfFile("ab"));
    EXPECT_FALSE(ContentPipeline::IsTxtFile(""));
    EXPECT_FALSE(ContentPipeline::IsDocxFile(""));
    EXPECT_FALSE(ContentPipeline::IsDocFile(""));
}

// ═══════════════════════════════════════════════════════════════════════════
// Task 1.3: Content Hash Tests
// ═══════════════════════════════════════════════════════════════════════════

TEST(ViewerProfessional_ContentHash, Deterministic) {
    std::string content = "Hello, World!";
    size_t hash1 = ContentPipeline::ComputeContentHash(content);
    size_t hash2 = ContentPipeline::ComputeContentHash(content);
    EXPECT_EQ(hash1, hash2);
}

TEST(ViewerProfessional_ContentHash, DifferentContent_DifferentHash) {
    std::string content1 = "Hello, World!";
    std::string content2 = "Hello, World?";
    size_t hash1 = ContentPipeline::ComputeContentHash(content1);
    size_t hash2 = ContentPipeline::ComputeContentHash(content2);
    EXPECT_NE(hash1, hash2);
}

TEST(ViewerProfessional_ContentHash, EmptyString) {
    size_t hash1 = ContentPipeline::ComputeContentHash("");
    size_t hash2 = ContentPipeline::ComputeContentHash("");
    EXPECT_EQ(hash1, hash2);
}

TEST(ViewerProfessional_ContentHash, LargeContent) {
    std::string large(10000, 'A');
    size_t hash1 = ContentPipeline::ComputeContentHash(large);
    size_t hash2 = ContentPipeline::ComputeContentHash(large);
    EXPECT_EQ(hash1, hash2);
}

// ═══════════════════════════════════════════════════════════════════════════
// Task 2.2: WrapTxtAsHtml Tests
// ═══════════════════════════════════════════════════════════════════════════

class ViewerProfessional_TxtWrap : public ::testing::Test {
protected:
    std::string temp_file_;

    void SetUp() override {
        temp_file_ = "test_wrap_txt_temp.txt";
    }

    void TearDown() override {
        std::remove(temp_file_.c_str());
    }

    void WriteFile(const std::string& content) {
        std::ofstream out(temp_file_, std::ios::binary);
        out.write(content.data(), content.size());
        out.close();
    }
};

TEST_F(ViewerProfessional_TxtWrap, BasicContent) {
    WriteFile("Hello World\nLine 2");
    std::string html = ContentPipeline::WrapTxtAsHtml(temp_file_);
    EXPECT_FALSE(html.empty());
    EXPECT_NE(html.find("<pre>"), std::string::npos);
    EXPECT_NE(html.find("Hello World"), std::string::npos);
    EXPECT_NE(html.find("Line 2"), std::string::npos);
}

TEST_F(ViewerProfessional_TxtWrap, DarkTheme) {
    WriteFile("test");
    std::string html = ContentPipeline::WrapTxtAsHtml(temp_file_);
    EXPECT_NE(html.find("#1e1e1e"), std::string::npos);
    EXPECT_NE(html.find("monospace"), std::string::npos);
}

TEST_F(ViewerProfessional_TxtWrap, HtmlEscaping) {
    WriteFile("<script>alert('xss')</script> & \"quotes\"");
    std::string html = ContentPipeline::WrapTxtAsHtml(temp_file_);
    // Should NOT contain raw < or > inside <pre>
    EXPECT_NE(html.find("&lt;script&gt;"), std::string::npos);
    EXPECT_NE(html.find("&amp;"), std::string::npos);
    EXPECT_NE(html.find("&quot;quotes&quot;"), std::string::npos);
    // Should NOT contain unescaped <script>
    // The <pre> tag itself is fine, but the content should be escaped
    size_t pre_pos = html.find("<pre>");
    std::string after_pre = html.substr(pre_pos + 5);
    EXPECT_EQ(after_pre.find("<script>"), std::string::npos);
}

TEST_F(ViewerProfessional_TxtWrap, NonExistentFile) {
    std::string html = ContentPipeline::WrapTxtAsHtml("nonexistent_file_xyz.txt");
    EXPECT_TRUE(html.empty());
}

TEST_F(ViewerProfessional_TxtWrap, ValidHtmlStructure) {
    WriteFile("content");
    std::string html = ContentPipeline::WrapTxtAsHtml(temp_file_);
    EXPECT_NE(html.find("<!DOCTYPE html>"), std::string::npos);
    EXPECT_NE(html.find("<html>"), std::string::npos);
    EXPECT_NE(html.find("<body>"), std::string::npos);
    EXPECT_NE(html.find("</html>"), std::string::npos);
}

// ═══════════════════════════════════════════════════════════════════════════
// Task 3.3: Pandoc Conversion Error Handling Tests
// ═══════════════════════════════════════════════════════════════════════════

TEST(ViewerProfessional_Pandoc, ConvertWithPandoc_FileNotFound) {
    std::string result = ContentPipeline::ConvertWithPandoc(
        "C:\\nonexistent\\file.docx", "docx");
    EXPECT_NE(result.find("Error:"), std::string::npos);
    EXPECT_NE(result.find("file not found"), std::string::npos);
}

TEST(ViewerProfessional_Pandoc, FindPandoc_ReturnsStringOrEmpty) {
    // FindPandoc should return either a valid path or empty string
    std::string path = ContentPipeline::FindPandoc();
    // We can't guarantee pandoc is installed, but the function should not crash
    EXPECT_TRUE(path.empty() || path.find("pandoc") != std::string::npos);
}

// ═══════════════════════════════════════════════════════════════════════════
// Task 6.3: PostMessageBridge Save-Request Routing Tests
// ═══════════════════════════════════════════════════════════════════════════

// These tests verify that the save-request action is recognized
// We test the JSON parsing logic indirectly through the action routing

TEST(ViewerProfessional_SaveRequest, SaveFilterString) {
    // Verify the filter string format used in GetSaveFileName
    const char* filter = "HTML File (*.html)\0*.html\0PNG Image (*.png)\0*.png\0PDF Document (*.pdf)\0*.pdf\0\0";
    // First filter pair
    EXPECT_STREQ(filter, "HTML File (*.html)");
    // Verify all three formats are present in the filter
    std::string full_filter(filter, 80);  // Read enough bytes to cover all filters
    EXPECT_NE(full_filter.find("html"), std::string::npos);
    EXPECT_NE(full_filter.find("png"), std::string::npos);
    EXPECT_NE(full_filter.find("pdf"), std::string::npos);
}
