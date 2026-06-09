/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * NevenProgressiveRegistrar: Handles UI-thread-safe progressive registration
 * of functions after background initialization completes. Uses SetTimer to
 * schedule callbacks on the UI thread.
 */

#pragma once

#include <queue>
#include <set>
#include <mutex>
#include <cstdint>
#include <Windows.h>

namespace neven {

/**
 * @brief Manages progressive function registration on the UI thread.
 *
 * Background worker threads enqueue engine indices when initialization
 * completes. A SetTimer callback on the UI thread periodically checks
 * the queue and calls xlfRegister for pending engines.
 *
 * Thread safety:
 * - EnqueueRegistration() is called from background threads.
 * - ProcessPendingRegistrations() is called from the UI thread only.
 * - The pending queue is protected by queue_mutex_.
 * - The registered set is accessed only from the UI thread (no lock needed).
 */
class ProgressiveRegistrar {
public:
    /** @brief Returns the singleton instance. */
    static ProgressiveRegistrar& Instance();

    /**
     * @brief Enqueues an engine for registration (called from background thread).
     * @param engine_index Index of the engine whose functions are ready.
     */
    void EnqueueRegistration(uint32_t engine_index);

    /**
     * @brief Processes pending registrations (called on UI thread via SetTimer).
     *
     * Dequeues all pending engine indices and calls the registration path
     * for each one. Skips engines that are already registered.
     */
    void ProcessPendingRegistrations();

    /**
     * @brief Checks if an engine's functions are already registered.
     * @param engine_index Index of the engine to check.
     * @return true if already registered.
     */
    bool IsRegistered(uint32_t engine_index) const;

    /**
     * @brief Checks if there are pending registrations in the queue.
     * @return true if the queue is non-empty.
     */
    bool HasPending() const;

    /**
     * @brief Checks if all expected engines have been registered.
     * @return true if registered count equals expected count.
     */
    bool AllComplete() const;

    /**
     * @brief Sets the expected number of engines to register.
     * @param count Total number of engines expected.
     */
    void SetExpectedEngineCount(int count);

    /** @brief Returns the number of engines successfully registered. */
    int GetRegisteredCount() const;

    /** @brief Resets internal state (for testing). */
    void ResetForTesting();

private:
    ProgressiveRegistrar();
    ~ProgressiveRegistrar() = default;
    ProgressiveRegistrar(const ProgressiveRegistrar&) = delete;
    ProgressiveRegistrar& operator=(const ProgressiveRegistrar&) = delete;

    std::queue<uint32_t> pending_registrations_;
    mutable std::mutex queue_mutex_;
    std::set<uint32_t> registered_engines_;
    int expected_engine_count_ = 0;
};

} // namespace neven
