/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef __CONTROLR_COMMON_H
#define __CONTROLR_COMMON_H

#ifdef WIN32

	#define Win32
	#include <windows.h>

#else // #ifdef WIN32

	#define R_INTERFACE_PTRS

#endif // #ifdef WIN32

#include <stdio.h>
#include <string.h>

#include <string>
#include <vector>
#include <iostream>

// v2.4 — Dynamic Engine Loading: include the shim instead of real R headers.
// All R API calls go through REngineLoader function pointers.
// The shim provides identical macro/type names so no other source changes needed.
#include "r_api_shim_clean.h"

// try to store fuel now, you jerks
#undef clear
#undef length

#define error_return(msg) { Rf_error(msg); return R_NilValue; }

SEXP RCallback(SEXP, SEXP);
SEXP COMCallback(SEXP, SEXP, SEXP, SEXP, SEXP);

// v2.4: setup_Rmainloop, run_Rmainloop and R_ProcessEvents are now resolved
// dynamically through REngineLoader (via r_api_shim.h macros).
// Rf_PrintWarnings and R_Visible are optional helpers; guarded at call sites.
// No static extern "C" declarations needed — all resolved via REngineLoader.

#endif // #ifndef __CONTROLR_COMMON_H


