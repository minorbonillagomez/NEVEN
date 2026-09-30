/**
 * @file bridge_poller.h
 * @brief BridgePoller — polls PostMessage bridge queue and writes cells.
 *
 * Enables the WebView2 viewer to write values to Excel cells reactively.
 * Uses a Windows timer to periodically check for queued commands from JS.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <string>
#include <windows.h>

namespace neven_sim {

/**
 * @brief Polls the bridge command queue file and executes write-cell commands.
 *
 * The WebView2 PostMessage bridge writes commands to C:\NEVEN\data\bridge_queue.json.
 * This poller reads that file on Excel's main thread (where Excel12 is safe)
 * and writes values to the specified cells.
 *
 * Usage:
 *   - JS: window.neven.writeCell("Sheet1", "B2", 0.75)
 *   - PostMessageBridge → writes bridge_queue.json
 *   - BridgePoller → reads file → Excel12(xlSet) → cell updated → recalculates
 */
class BridgePoller {
public:
    /** @brief Start the polling timer (call from xlAutoOpen). */
    static void Start();

    /** @brief Stop the polling timer (call from xlAutoClose). */
    static void Stop();

    /** @brief Process any pending bridge commands (called by timer or manually). */
    static void ProcessQueue();

private:
    static void CALLBACK TimerCallback(HWND hwnd, UINT uMsg, UINT_PTR idEvent, DWORD dwTime);

    /** @brief Write a value to an Excel cell using Excel12. */
    static bool WriteCellValue(const std::string& sheet, const std::string& cell, const std::string& value);

    static UINT_PTR timer_id_;
    static bool running_;
};

} // namespace neven_sim
