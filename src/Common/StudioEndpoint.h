// StudioEndpoint.h - how native clients reach the NEVEN Studio server (port 5555).
//
// neven_http_server.py serves HTTPS when TaskPane.certPath/keyPath point to
// existing files and plain HTTP otherwise. The clients (Ribbon, Core, WebView2
// panel) must use the same scheme. The scheme is detected by probing the live
// server (https first, then http); when nothing answers, it is derived from
// neven-config.json the same way the server does. Certificate validation is
// never disabled: the localhost certificate is trusted by the user store.
#pragma once
#include <windows.h>
#include <winhttp.h>
#include <fstream>
#include <iterator>
#include <string>

namespace neven {

// ---- Pure logic (no I/O) ---------------------------------------------------

// Returns the string value of the first "key": "value" found at or after `from`,
// or an empty string. Handles the \\ and \" escapes used in Windows paths.
inline std::string StudioJsonString(const std::string& json, const std::string& key,
                                    size_t from = 0, size_t* end_pos = nullptr) {
    const std::string needle = "\"" + key + "\"";
    size_t p = json.find(needle, from);
    if (p == std::string::npos) return "";
    p = json.find(':', p + needle.size());
    if (p == std::string::npos) return "";
    p = json.find_first_not_of(" \t\r\n", p + 1);
    if (p == std::string::npos || json[p] != '"') return "";
    std::string out;
    for (size_t i = p + 1; i < json.size(); ++i) {
        char c = json[i];
        if (c == '\\' && i + 1 < json.size()) { out += json[++i]; continue; }
        if (c == '"') { if (end_pos) *end_pos = i; return out; }
        out += c;
    }
    return "";
}

// Mirrors the server: HTTPS only when certPath and keyPath are both set and the
// files exist. `*_exists` are supplied by the caller so this stays testable.
inline bool StudioHttpsFromPaths(const std::string& cert_path, const std::string& key_path,
                                 bool cert_exists, bool key_exists) {
    return !cert_path.empty() && !key_path.empty() && cert_exists && key_exists;
}

// Extracts TaskPane.certPath / keyPath from the text of neven-config.json.
inline void StudioCertPathsFromConfig(const std::string& config_json,
                                      std::string& cert_path, std::string& key_path) {
    size_t sec = config_json.find("\"TaskPane\"");
    if (sec == std::string::npos) { cert_path.clear(); key_path.clear(); return; }
    cert_path = StudioJsonString(config_json, "certPath", sec);
    key_path  = StudioJsonString(config_json, "keyPath", sec);
}

inline std::string StudioScheme(bool https) { return https ? "https" : "http"; }

// "https://localhost:5555" or "http://localhost:5555"
inline std::string StudioBaseUrl(bool https, int port, const std::string& host = "localhost") {
    return StudioScheme(https) + "://" + host + ":" + std::to_string(port);
}

inline std::string StudioUrl(bool https, int port, const std::string& path) {
    return StudioBaseUrl(https, port) + path;
}

inline std::wstring StudioUrlW(bool https, int port, const std::wstring& path) {
    std::string b = StudioBaseUrl(https, port);
    return std::wstring(b.begin(), b.end()) + path;
}

// dwFlags for WinHttpOpenRequest.
inline DWORD StudioOpenFlags(bool https) { return https ? WINHTTP_FLAG_SECURE : 0; }

// True if `url` points at localhost/127.0.0.1:<port> over http or https.
inline bool StudioIsLocalUrl(const std::wstring& url, int port) {
    const std::wstring p = std::to_wstring(port);
    const wchar_t* schemes[] = {L"http://", L"https://"};
    const wchar_t* hosts[] = {L"localhost:", L"127.0.0.1:"};
    for (auto s : schemes)
        for (auto h : hosts)
            if (url.find(std::wstring(s) + h + p) == 0) return true;
    return false;
}

// ---- I/O --------------------------------------------------------------------

// HTTPS expected by neven-config.json (used only when no server answers).
inline bool StudioHttpsFromConfigFile() {
    wchar_t home[MAX_PATH] = {0};
    DWORD n = GetEnvironmentVariableW(L"NEVEN_HOME", home, MAX_PATH);
    std::wstring dir = (n > 0 && n < MAX_PATH) ? std::wstring(home) : L"C:\\NEVEN";
    std::ifstream f((dir + L"\\neven-config.json").c_str(), std::ios::binary);
    if (!f) return false;
    std::string text((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    std::string cert, key;
    StudioCertPathsFromConfig(text, cert, key);
    auto exists = [](const std::string& p) {
        if (p.empty()) return false;
        return GetFileAttributesA(p.c_str()) != INVALID_FILE_ATTRIBUTES;
    };
    return StudioHttpsFromPaths(cert, key, exists(cert), exists(key));
}

// One GET with the given scheme. True if the server produced an HTTP response.
inline bool StudioProbe(int port, bool https, const wchar_t* path = L"/api/engines",
                        DWORD timeout_ms = 1500) {
    HINTERNET hT = WinHttpOpen(L"NEVEN-Studio-Probe/1.0", WINHTTP_ACCESS_TYPE_NO_PROXY,
                               WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hT) return false;
    WinHttpSetOption(hT, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout_ms, sizeof(timeout_ms));
    WinHttpSetOption(hT, WINHTTP_OPTION_SEND_TIMEOUT, &timeout_ms, sizeof(timeout_ms));
    WinHttpSetOption(hT, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout_ms, sizeof(timeout_ms));
    bool ok = false;
    if (HINTERNET hC = WinHttpConnect(hT, L"localhost", (INTERNET_PORT)port, 0)) {
        if (HINTERNET hR = WinHttpOpenRequest(hC, L"GET", path, nullptr, WINHTTP_NO_REFERER,
                                              WINHTTP_DEFAULT_ACCEPT_TYPES, StudioOpenFlags(https))) {
            ok = WinHttpSendRequest(hR, WINHTTP_NO_ADDITIONAL_HEADERS, 0, nullptr, 0, 0, 0) &&
                 WinHttpReceiveResponse(hR, nullptr);
            WinHttpCloseHandle(hR);
        }
        WinHttpCloseHandle(hC);
    }
    WinHttpCloseHandle(hT);
    return ok;
}

// Server alive over either scheme. `*https` receives the scheme that answered.
inline bool StudioIsAlive(int port, bool* https = nullptr, const wchar_t* path = L"/api/engines") {
    if (StudioProbe(port, true, path))  { if (https) *https = true;  return true; }
    if (StudioProbe(port, false, path)) { if (https) *https = false; return true; }
    return false;
}

// Scheme to use for the next request: the live server's, else the configured one.
inline bool StudioResolveHttps(int port) {
    bool https = false;
    if (StudioIsAlive(port, &https)) return https;
    return StudioHttpsFromConfigFile();
}

}  // namespace neven
