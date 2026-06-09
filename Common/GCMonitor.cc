/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#include "GCMonitor.h"
#include "ScriptEngine.h"

namespace rj2xcl {

GCMonitor& GCMonitor::GetInstance() {
    static GCMonitor instance;
    return instance;
}

void GCMonitor::RegisterEngine(IScriptEngine* engine) {
    std::lock_guard<std::mutex> lock(m_mutex);
    if(engine) {
        m_engines.push_back(engine);
    }
}

void GCMonitor::NotifyExcelCOMRelease() {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_excel_allocations_since_sweep++;
    
    // Threshold heuristic. After 100 COM array boundaries, force GC
    if(m_excel_allocations_since_sweep > 100) {
        ForceGlobalSweep();
        m_excel_allocations_since_sweep = 0;
    }
}

void GCMonitor::ForceGlobalSweep() {
    // Note: Mutex is assumed to be locked by the caller (NotifyExcelCOMRelease)
    // or called directly via specific UI button in the Ribbon
    for(auto* engine : m_engines) {
        engine->ForceGarbageCollection();
    }
}

} // namespace rj2xcl
