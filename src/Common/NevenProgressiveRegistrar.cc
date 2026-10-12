/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#include "NevenProgressiveRegistrar.h"
#include "LanguageManager.h"
#include "rj2xcl.h"
#include "excel_api_functions.h"
#include "LogService.h"

namespace neven {

ProgressiveRegistrar& ProgressiveRegistrar::Instance() {
    static ProgressiveRegistrar instance;
    return instance;
}

ProgressiveRegistrar::ProgressiveRegistrar()
    : expected_engine_count_(0) {
}

void ProgressiveRegistrar::EnqueueRegistration(uint32_t engine_index) {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    pending_registrations_.push(engine_index);
    RJ2XCL_LOG_INFO("ProgressiveRegistrar: engine %u enqueued for registration", engine_index);
}

void ProgressiveRegistrar::ProcessPendingRegistrations() {
    // Drain the queue under lock, then process without lock
    std::vector<uint32_t> to_register;
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        while (!pending_registrations_.empty()) {
            to_register.push_back(pending_registrations_.front());
            pending_registrations_.pop();
        }
    }

    for (uint32_t engine_index : to_register) {
        // Skip if already registered (no duplicate registrations)
        if (registered_engines_.count(engine_index) > 0) {
            RJ2XCL_LOG_INFO("ProgressiveRegistrar: engine %u already registered, skipping", engine_index);
            continue;
        }

        // ═══════════════════════════════════════════════════════════════════
        // ACTUAL REGISTRATION: Call MapLanguageFunctions + xlfRegister
        // This runs on the UI thread (via SetTimer callback), which is the
        // only safe context for xlfRegister.
        // ═══════════════════════════════════════════════════════════════════
        auto& lm = rj2xcl::LanguageManager::Instance();
        auto services = lm.GetServices();

        if (engine_index < services.size()) {
            auto service = services[engine_index];

            if (service->connected() && service->GetHealthStatus() != ::HealthStatus::Unavailable) {
                // Send application pointer to the newly-connected engine
                // (SetPointers may have been called before this engine connected)
                auto engine = RJ2XCL_Engine::Instance();
                LPDISPATCH app_dispatch = engine->GetApplicationDispatch();
                if (app_dispatch) {
                    service->SetApplicationPointer(app_dispatch);
                }

                RJ2XCL_LOG_INFO("ProgressiveRegistrar: mapping functions for engine %u (%s)",
                                engine_index, service->name().c_str());

                // Get function list from the engine via pipe
                FUNCTION_LIST functions = service->MapLanguageFunctions(engine_index, service);

                if (!functions.empty()) {
                    // Remove any existing functions for this engine (in case of re-registration)
                    std::string engine_name = service->name();
                    FUNCTION_LIST filtered;
                    for (auto& fp : engine->function_list_) {
                        if (fp->language_name_ != engine_name) {
                            filtered.push_back(fp);
                        }
                    }
                    // Add the new functions
                    filtered.insert(filtered.end(), functions.begin(), functions.end());
                    engine->function_list_ = filtered;

                    // Unregister all and re-register with the updated list
                    // This is safe because we're on the UI thread
                    UnregisterFunctions();
                    RegisterFunctions();

                    RJ2XCL_LOG_INFO("ProgressiveRegistrar: engine %u (%s) — %d functions registered",
                                    engine_index, service->name().c_str(),
                                    static_cast<int>(functions.size()));
                } else {
                    RJ2XCL_LOG_WARN("ProgressiveRegistrar: engine %u (%s) returned empty function list",
                                    engine_index, service->name().c_str());
                }
            } else {
                RJ2XCL_LOG_WARN("ProgressiveRegistrar: engine %u not connected or unavailable, skipping registration",
                                engine_index);
            }
        }

        // Mark as registered (even if it failed — prevent infinite retries)
        registered_engines_.insert(engine_index);
        RJ2XCL_LOG_INFO("ProgressiveRegistrar: registered engine %u (%d/%d complete)",
                        engine_index,
                        static_cast<int>(registered_engines_.size()),
                        expected_engine_count_);
    }
}

bool ProgressiveRegistrar::IsRegistered(uint32_t engine_index) const {
    return registered_engines_.count(engine_index) > 0;
}

bool ProgressiveRegistrar::HasPending() const {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    return !pending_registrations_.empty();
}

bool ProgressiveRegistrar::AllComplete() const {
    return expected_engine_count_ > 0 &&
           static_cast<int>(registered_engines_.size()) >= expected_engine_count_;
}

void ProgressiveRegistrar::SetExpectedEngineCount(int count) {
    expected_engine_count_ = count;
}

int ProgressiveRegistrar::GetRegisteredCount() const {
    return static_cast<int>(registered_engines_.size());
}

void ProgressiveRegistrar::ResetForTesting() {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    while (!pending_registrations_.empty()) {
        pending_registrations_.pop();
    }
    registered_engines_.clear();
    expected_engine_count_ = 0;
}

} // namespace neven
