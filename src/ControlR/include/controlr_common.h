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

#include <Rversion.h>
#include <Rinternals.h>

#ifndef NEVEN_DYNAMIC_LOAD
// In dynamic-load mode (v2.4), REngineLoader provides its own structRstart
// definition and manages R startup. Including Rembedded.h / R_ext\RStartup.h
// here would cause redefinition conflicts with r_engine_loader.h.
#include <Rembedded.h>
#endif

#ifdef WIN32

	#include <graphapp.h>
#ifndef NEVEN_DYNAMIC_LOAD
	#include <R_ext\RStartup.h>
#endif

#else // #ifdef WIN32

	#include <signal.h>
	#include <unistd.h>
	#include <Rinterface.h>

#endif // #ifdef WIN32

#include <R_ext/Parse.h>
#include <R_ext/Rdynload.h>

// try to store fuel now, you jerks
#undef clear
#undef length

#define error_return(msg) { Rf_error(msg); return R_NilValue; }

SEXP RCallback(SEXP, SEXP);
SEXP COMCallback(SEXP, SEXP, SEXP, SEXP, SEXP);

extern "C" {

  // loop functions
  extern void setup_Rmainloop();
  extern void run_Rmainloop();

  // Programmatic save/restore — available for future use
  extern void R_RestoreGlobalEnvFromFile(const char *, Rboolean);
  extern void R_SaveGlobalEnvToFile(const char *);

  // for win32
  extern void R_ProcessEvents(void);

  extern void Rf_PrintWarnings();
  extern Rboolean R_Visible;

};

#endif // #ifndef __CONTROLR_COMMON_H


