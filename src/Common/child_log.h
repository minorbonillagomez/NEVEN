/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * Lightweight logging macros for child processes (ControlR, ControlJulia).
 * These processes run with CREATE_NO_WINDOW so std::cout goes nowhere.
 * All output goes to the process-specific log file via g_logFile.
 *
 * Usage:
 *   extern FILE* g_logFile;  // declared in main .cc
 *   CHILD_LOG("message %s %d", str, num);
 *   CHILD_LOG_ERR("error: %d", err);
 */

#pragma once

#include <cstdio>

// Log to file if available, otherwise silently discard
#define CHILD_LOG(fmt, ...) \
    do { if (g_logFile) { fprintf(g_logFile, "[INFO] " fmt "\n", ##__VA_ARGS__); fflush(g_logFile); } } while(0)

#define CHILD_LOG_ERR(fmt, ...) \
    do { if (g_logFile) { fprintf(g_logFile, "[ERROR] " fmt "\n", ##__VA_ARGS__); fflush(g_logFile); } } while(0)

#define CHILD_LOG_WARN(fmt, ...) \
    do { if (g_logFile) { fprintf(g_logFile, "[WARN] " fmt "\n", ##__VA_ARGS__); fflush(g_logFile); } } while(0)

#define CHILD_LOG_DEBUG(fmt, ...) \
    do { if (g_logFile) { fprintf(g_logFile, "[DEBUG] " fmt "\n", ##__VA_ARGS__); fflush(g_logFile); } } while(0)
