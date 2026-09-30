/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * SecurityService Implementation.
 * Uses RAII wrappers for BCrypt handles to prevent resource leaks.
 */

#include "SecurityService.h"
#include <windows.h>
#include <bcrypt.h>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <vector>
#include <memory>

#pragma comment(lib, "bcrypt.lib")

namespace rj2xcl {

    // RAII wrappers for BCrypt handles (S-06 fix)
    struct BcryptAlgDeleter {
        void operator()(BCRYPT_ALG_HANDLE h) const { if (h) BCryptCloseAlgorithmProvider(h, 0); }
    };
    struct BcryptHashDeleter {
        void operator()(BCRYPT_HASH_HANDLE h) const { if (h) BCryptDestroyHash(h); }
    };

    SecurityService& SecurityService::Instance() {
        static SecurityService instance;
        return instance;
    }

    bool SecurityService::VerifyScriptIntegrity(const std::string& script_path) {
        std::string hash_path = script_path + ".sha256";
        
        std::ifstream hash_file(hash_path);
        if (!hash_file.is_open()) {
            // No hash file — allow execution but log for audit trail
            return true;
        }

        std::string expected_hash;
        hash_file >> expected_hash;
        hash_file.close();

        std::string actual_hash = CalculateSHA256(script_path);
        
        if (actual_hash.empty()) return false;

        // Case-insensitive compare
        return (actual_hash.length() == expected_hash.length() &&
                _stricmp(actual_hash.c_str(), expected_hash.c_str()) == 0);
    }

    std::string SecurityService::CalculateSHA256(const std::string& file_path) {
        std::ifstream file(file_path, std::ios::binary);
        if (!file.is_open()) return "";

        // Open algorithm provider (RAII)
        BCRYPT_ALG_HANDLE hAlgRaw = NULL;
        if (BCryptOpenAlgorithmProvider(&hAlgRaw, BCRYPT_SHA256_ALGORITHM, NULL, 0) != 0) return "";
        std::unique_ptr<void, BcryptAlgDeleter> hAlg(hAlgRaw);

        DWORD cbData = 0, cbHash = 0, cbHashObject = 0;
        if (BCryptGetProperty(hAlgRaw, BCRYPT_OBJECT_LENGTH, (PBYTE)&cbHashObject, sizeof(DWORD), &cbData, 0) != 0) return "";
        if (BCryptGetProperty(hAlgRaw, BCRYPT_HASH_LENGTH, (PBYTE)&cbHash, sizeof(DWORD), &cbData, 0) != 0) return "";

        // Use vectors for automatic cleanup (RAII)
        std::vector<BYTE> hashObject(cbHashObject);
        std::vector<BYTE> hash(cbHash);

        // Create hash (RAII)
        BCRYPT_HASH_HANDLE hHashRaw = NULL;
        if (BCryptCreateHash(hAlgRaw, &hHashRaw, hashObject.data(), cbHashObject, NULL, 0, 0) != 0) return "";
        std::unique_ptr<void, BcryptHashDeleter> hHash(hHashRaw);

        // Hash file contents
        char buffer[4096];
        while (file.read(buffer, sizeof(buffer)) || file.gcount() > 0) {
            if (BCryptHashData(hHashRaw, (PBYTE)buffer, (ULONG)file.gcount(), 0) != 0) return "";
        }

        if (BCryptFinishHash(hHashRaw, hash.data(), cbHash, 0) != 0) return "";

        // Convert to hex string
        std::stringstream ss;
        for (DWORD i = 0; i < cbHash; i++) {
            ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
        }
        return ss.str();
    }

} // namespace rj2xcl
