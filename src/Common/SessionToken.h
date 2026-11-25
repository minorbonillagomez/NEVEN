// SessionToken.h - reads the per-session secret that neven_http_server.py
// publishes in %LOCALAPPDATA%\NEVEN\session.token (SEC-01). Native clients
// send it in the X-NEVEN-Token header on every POST to the local server.
#pragma once
#include <windows.h>
#include <fstream>
#include <string>

namespace neven {

// Returns the full header line "X-NEVEN-Token: <secret>\r\n", or an empty string
// if the token file is missing (the server then rejects the POST with HTTP 401).
inline std::wstring SessionTokenHeader() {
    wchar_t base[MAX_PATH] = {0};
    DWORD n = GetEnvironmentVariableW(L"LOCALAPPDATA", base, MAX_PATH);
    if (n == 0 || n >= MAX_PATH) return L"";
    std::wstring path = std::wstring(base) + L"\\NEVEN\\session.token";
    std::ifstream f(path.c_str(), std::ios::binary);
    if (!f) return L"";
    std::string tok;
    std::getline(f, tok);
    while (!tok.empty() && (tok.back() == '\r' || tok.back() == '\n' || tok.back() == ' ')) tok.pop_back();
    if (tok.empty()) return L"";
    for (unsigned char c : tok) {
        bool ok = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-' || c == '_';
        if (!ok) return L"";
    }
    return L"X-NEVEN-Token: " + std::wstring(tok.begin(), tok.end()) + L"\r\n";
}

}  // namespace neven