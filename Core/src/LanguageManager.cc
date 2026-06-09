/**
 * Copyright (c) 2026 RJ2XCL Project
 */

#include "LanguageManager.h"
#include "ConfigService.h"
#include <iostream>

namespace rj2xcl {

    LanguageManager& LanguageManager::Instance() {
        static LanguageManager instance;
        return instance;
    }

    void LanguageManager::ResetForTesting() {
        Shutdown();
    }

    void LanguageManager::ConfigureLanguages(DWORD dev_flags, const json11::Json& config, const std::string& home_directory, const json11::Json& language_config, CallbackInfo& callback_info, COMObjectMap& object_map) {
        if (language_config.is_array()) {
            for (const auto &item : language_config.array_items()) {
                auto service = std::make_shared<LanguageService>(callback_info, object_map, dev_flags, config, home_directory, item);
                if (service->configured()) {
                    language_services_.push_back(service);
                }
            }
        }
    }

    void LanguageManager::ConnectLanguages(HANDLE job_handle) {
        for (auto& service : language_services_) {
            if (!service->connected() && !service->lazy_load()) {
                service->Connect(job_handle);
            }
        }
    }

    void LanguageManager::InitializeConnectedLanguages() {
        for (auto& service : language_services_) {
            if (service->connected()) {
                service->Initialize();
            }
        }
    }

    void LanguageManager::Shutdown() {
        for (auto& service : language_services_) {
            service->Shutdown();
        }
        language_services_.clear();
    }

    std::shared_ptr<LanguageService> LanguageManager::GetLanguageService(uint32_t key) {
        if (key < language_services_.size()) {
            return language_services_[key];
        }
        return nullptr;
    }

    std::shared_ptr<LanguageService> LanguageManager::GetLanguageService(const std::string &name) {
        for (auto& service : language_services_) {
            if (service->name() == name) {
                return service;
            }
        }
        return nullptr;
    }

    void LanguageManager::CallLanguage(uint32_t language_key, RJ2XCLBuffers::CallResponse &response, RJ2XCLBuffers::CallResponse &call) {
        auto service = GetLanguageService(language_key);
        if (service) {
            // Task 10.1: Health-aware dispatch — skip unavailable services
            if (service->GetHealthStatus() == HealthStatus::Unavailable) {
                response.set_err(service->name() + " is currently unavailable.");
                return;
            }
            service->Call(response, call);
        } else {
            response.set_err("invalid language key");
        }
    }

    void LanguageManager::RegisterLanguageCalls() {
        // Implementation logic for registering calls
    }

} // namespace rj2xcl
