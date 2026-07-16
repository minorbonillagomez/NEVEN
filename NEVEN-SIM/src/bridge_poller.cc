/**
 * @file bridge_poller.cc
 * @brief BridgePoller implementation — reads bridge queue, writes Excel cells.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <windows.h>
#undef ERROR

#include "bridge_poller.h"
#include "XLCALL.H"
#include "json11/json11.hpp"
#include <fstream>
#include <sstream>
#include <string>

#ifndef xlUDF
#define xlUDF 255
#endif

// Excel12 — from xlcall_stubs.cc
extern "C" int pascal Excel12(int xlfn, LPXLOPER12 operRes, int count, ...);

namespace neven_sim {

UINT_PTR BridgePoller::timer_id_ = 0;
bool BridgePoller::running_ = false;

static const char* QUEUE_PATH = "C:\\NEVEN\\data\\bridge_queue.json";

void BridgePoller::Start() {
    if (running_) return;
    // DISABLED: Excel12 is not safe from timer callbacks.
    // Using file-based approach with =SIM.ReadBridge() instead.
    // timer_id_ = SetTimer(NULL, 0, 250, TimerCallback);
    running_ = true;
}

void BridgePoller::Stop() {
    if (timer_id_) {
        KillTimer(NULL, timer_id_);
        timer_id_ = 0;
    }
    running_ = false;
}

void CALLBACK BridgePoller::TimerCallback(HWND hwnd, UINT uMsg, UINT_PTR idEvent, DWORD dwTime) {
    ProcessQueue();
}

void BridgePoller::ProcessQueue() {
    // Check if queue file exists and has content
    DWORD attrs = GetFileAttributesA(QUEUE_PATH);
    if (attrs == INVALID_FILE_ATTRIBUTES) return;

    // Read the file
    std::ifstream file(QUEUE_PATH);
    if (!file.is_open()) return;

    std::string content;
    std::getline(file, content, '\0');  // Read entire file
    file.close();

    if (content.empty()) return;

    // Delete the file immediately to prevent re-processing
    DeleteFileA(QUEUE_PATH);

    // Parse JSON command
    std::string err;
    json11::Json cmd = json11::Json::parse(content, err);
    if (!err.empty() || !cmd.is_object()) return;

    std::string action = cmd["action"].string_value();

    if (action == "write-cell") {
        std::string sheet = cmd["sheet"].string_value();
        std::string cell = cmd["cell"].string_value();
        std::string value;
        if (cmd["value"].is_number()) {
            value = std::to_string(cmd["value"].number_value());
        } else {
            value = cmd["value"].string_value();
        }

        if (!sheet.empty() && !cell.empty()) {
            WriteCellValue(sheet, cell, value);
        }
    }
    else if (action == "sim-command") {
        // Future: handle simulation commands from the viewer
        // For now, just consume the message
    }
}

bool BridgePoller::WriteCellValue(const std::string& sheet, const std::string& cell, const std::string& value) {
    // Strategy: Use NEVEN.r() via xlUDF to write the cell via R's Excel callback
    // R can call RJ2XCL$.Excel() which routes through the safe callback path
    //
    // Alternative: Build an xlSet command directly with Excel12
    // xlSet requires a reference (xlRef) which is complex to construct.
    //
    // Simplest reliable approach: Call NEVEN.r() with R code that uses
    // the Excel callback to set the cell value.
    
    // Build R code: RJ2XCL$.Excel(0x4000 + 1, ref, value)
    // Actually, the safest approach is to use xlcSet (= 0x4001) but we
    // need to build the reference properly.
    
    // Even simpler: use NEVEN.r() with the .Excel function
    // RJ2XCL$.Excel(1, reference, value) where 1 = xlSet
    
    // The most reliable approach for Phase 1:
    // Call NEVEN.r("invisible(0)") which triggers a recalculation context,
    // then on the SAME thread write via direct Excel12.
    
    // Actually — we ARE on the Excel main thread (timer callback runs on Excel's thread!)
    // So we can use Excel12 directly here.
    
    // Build the cell reference string like "Sheet1!B2"
    std::string full_ref = sheet + "!" + cell;
    
    // Convert cell reference to XLOPER12 using xlCoerce
    // The simplest way: use xlfEvaluate to evaluate the reference string
    XLOPER12 xlRef, xlValue, xlResult;
    
    // Build reference formula: ="Sheet1!B2"
    std::wstring wref(full_ref.begin(), full_ref.end());
    int rlen = (int)wref.length();
    wchar_t* rbuf = new wchar_t[rlen + 2];
    rbuf[0] = (wchar_t)rlen;
    memcpy(rbuf + 1, wref.c_str(), rlen * sizeof(wchar_t));
    rbuf[rlen + 1] = 0;

    xlRef.xltype = xltypeStr;
    xlRef.val.str = rbuf;

    // Evaluate the reference string to get an xlRef type
    XLOPER12 xlEvalResult;
    memset(&xlEvalResult, 0, sizeof(xlEvalResult));
    // xlfEvaluate = 257 — evaluates a string as if typed in a cell
    #ifndef xlfEvaluate
    #define xlfEvaluate 257
    #endif
    
    int err = Excel12(xlfEvaluate, &xlEvalResult, 1, &xlRef);
    delete[] rbuf;

    if (err != 0) return false;

    // Now set the value
    // Try to parse as number
    double numVal = 0;
    bool isNumber = false;
    try {
        numVal = std::stod(value);
        isNumber = true;
    } catch (...) {}

    if (isNumber) {
        xlValue.xltype = xltypeNum;
        xlValue.val.num = numVal;
    } else {
        std::wstring wval(value.begin(), value.end());
        int vlen = (int)wval.length();
        wchar_t* vbuf = new wchar_t[vlen + 2];
        vbuf[0] = (wchar_t)vlen;
        memcpy(vbuf + 1, wval.c_str(), vlen * sizeof(wchar_t));
        vbuf[vlen + 1] = 0;
        xlValue.xltype = xltypeStr;
        xlValue.val.str = vbuf;
    }

    // xlSet = 0x4001 (xlCommand + 1) — sets the value of a cell reference
    #ifndef xlSet
    #define xlSet (1 | 0x4000)
    #endif

    memset(&xlResult, 0, sizeof(xlResult));
    err = Excel12(xlSet, &xlResult, 2, &xlEvalResult, &xlValue);

    // Cleanup
    if (!isNumber && xlValue.xltype == xltypeStr) {
        delete[] xlValue.val.str;
    }

    return (err == 0);
}

} // namespace neven_sim
