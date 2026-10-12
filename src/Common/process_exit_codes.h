/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * @file process_exit_codes.h
 * @brief Exit codes for child processes (ControlR, ControlJulia, ControlPython).
 */
 
#ifndef __PROCESS_EXIT_CODES_H
#define __PROCESS_EXIT_CODES_H

/** @brief Child process exited due to unsupported runtime version. */
#define PROCESS_ERROR_UNSUPPORTED_VERSION 100

/** @brief Child process exited due to configuration error (missing config, bad paths). */
#define PROCESS_ERROR_CONFIGURATION_ERROR 101

#endif // #ifndef __PROCESS_EXIT_CODES_H


