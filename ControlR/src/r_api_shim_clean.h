/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * r_api_shim_clean.h -- NEVEN v2.4 Dynamic Engine Loading
 *
 * Drop-in replacement for the R headers used across ControlR source files.
 * Include this INSTEAD of Rinternals.h, RStartup.h, Rembedded.h, graphapp.h.
 *
 * Strategy:
 *   1. Include Rinternals.h FIRST (before the loader) so cetype_t comes from
 *      the mock and is never redefined. Its dllimport globals are safe because
 *      all code uses the #define macros below which redirect to REngineLoader.
 *   2. Block the startup headers (RStartup, Rembedded, graphapp, Rinterface).
 *   3. Include r_engine_loader.h (defines SEXP, function pointer typedefs).
 *   4. Define #define macros that redirect R API calls to REngineLoader.
 */

#pragma once

// =============================================================================
// STEP 1: Include Rinternals.h BEFORE anything else.
//   - This defines cetype_t (CE_UTF8 etc.), Rboolean, NA_STRING etc.
//   - Must come before r_engine_loader.h so there is no redefinition.
//   - The dllimport globals (R_GlobalEnv etc.) are overridden by #defines below.
// =============================================================================
#include <Rinternals.h>

// =============================================================================
// STEP 2: Block startup headers (their function declarations conflict with
//         the dynamic loader we implement via LoadLibrary/GetProcAddress).
// =============================================================================
#ifndef REMBEDDED_H
#define REMBEDDED_H
#endif
#ifndef GRAPHAPP_H
#define GRAPHAPP_H
#endif
#ifndef R_EXT_RSTARTUP_H
#define R_EXT_RSTARTUP_H
#endif
#ifndef RINTERFACE_H
#define RINTERFACE_H
#endif
#ifndef RVERSION_H
#define RVERSION_H
#endif

// =============================================================================
// STEP 3: Include the engine loader (Windows.h + typedefs + REngineLoader class).
// =============================================================================
#include "r_engine_loader.h"

// ParseStatus -- from mock Include/R_ext/Parse.h
#include <R_ext/Parse.h>

// DL_FUNC
#ifndef DL_FUNC
typedef void *(*DL_FUNC)(void);
#endif

// R_CFinalizer_t
#ifndef R_CFINALIZER_T_DEFINED
#define R_CFINALIZER_T_DEFINED
typedef void (*R_CFinalizer_t)(SEXP);
#endif

// =============================================================================
// STEP 4: SEXP type constants (in case Rinternals.h mock doesn't define them)
// =============================================================================
#ifndef NILSXP
#define NILSXP      0
#define SYMSXP      1
#define LISTSXP     2
#define CLOSXP      3
#define ENVSXP      4
#define PROMSXP     5
#define LANGSXP     6
#define SPECIALSXP  7
#define BUILTINSXP  8
#define CHARSXP     9
#define LGLSXP     10
#define INTSXP     13
#define REALSXP    14
#define CPLXSXP    15
#define STRSXP     16
#define DOTSXP     17
#define ANYSXP     18
#define VECSXP     19
#define EXPRSXP    20
#define EXTPTRSXP  22
#define S4SXP      25
#endif

// =============================================================================
// STEP 5: Constants and simple macros
// =============================================================================
#ifndef R_NilValue
#define R_NilValue ((SEXP)0)
#endif

#ifndef R_CHAR
#define R_CHAR(x) ((const char*)(x))
#endif

#ifndef NA_INTEGER
#define NA_INTEGER  (-2147483648)
#endif
#ifndef NA_LOGICAL
#define NA_LOGICAL  (-2147483648)
#endif

#ifndef ISNA
static inline int _r_shim_IsNA(double v) {
    union { double d; int i[2]; } u;
    u.d = v;
    return (u.i[1] == 0x7ff00000 && u.i[0] == 1954);
}
#define ISNA(v) _r_shim_IsNA(v)
#endif

#ifndef LinkDLL
#define LinkDLL 2
#endif

#ifndef SA_NOSAVE
#define SA_NOSAVE    0
#define SA_SAVE      1
#define SA_SAVEASK   2
#define SA_SUICIDE   3
#define SA_NORESTORE 0x10
#endif

// =============================================================================
// STEP 6: Override the dllimport globals from Rinternals.h with our loader.
//         These #defines shadow the dllimport declarations so no linking needed.
// =============================================================================
#ifdef R_GlobalEnv
#undef R_GlobalEnv
#endif
#define R_GlobalEnv      (*REngineLoader::pR_GlobalEnv)

#ifdef R_NamesSymbol
#undef R_NamesSymbol
#endif
#define R_NamesSymbol    (*REngineLoader::pR_NamesSymbol)

#ifdef R_DimNamesSymbol
#undef R_DimNamesSymbol
#endif
#define R_DimNamesSymbol (*REngineLoader::pR_DimNamesSymbol)

#ifdef R_LevelsSymbol
#undef R_LevelsSymbol
#endif
#define R_LevelsSymbol   (*REngineLoader::pR_LevelsSymbol)

#ifdef R_RowNamesSymbol
#undef R_RowNamesSymbol
#endif
#define R_RowNamesSymbol (*REngineLoader::pR_RowNamesSymbol)

#ifdef NA_STRING
#undef NA_STRING
#endif
#define NA_STRING        (*REngineLoader::pR_NaString)

#ifdef NA_REAL
#undef NA_REAL
#endif
#define NA_REAL          (*REngineLoader::pR_NaReal)

#ifdef UserBreak
#undef UserBreak
#endif
#define UserBreak        (*REngineLoader::pUserBreak)

// =============================================================================
// STEP 7: Redirect R API calls to REngineLoader function pointers.
// =============================================================================

// -- Startup / Shutdown -------------------------------------------------------
#define R_setStartTime               REngineLoader::R_setStartTime
#define R_DefParams                  REngineLoader::R_DefParams
#define R_SetParams                  REngineLoader::R_SetParams
#define R_set_command_line_arguments REngineLoader::R_set_command_line_arguments
#define GA_initapp                   REngineLoader::GA_initapp
#define readconsolecfg               REngineLoader::readconsolecfg
#define setup_Rmainloop              REngineLoader::setup_Rmainloop
#define run_Rmainloop                REngineLoader::run_Rmainloop
#define Rf_endEmbeddedR              REngineLoader::Rf_endEmbeddedR
#define getDLLVersion                REngineLoader::getDLLVersion

// -- Events -------------------------------------------------------------------
#define R_ProcessEvents              REngineLoader::R_ProcessEvents

// -- Memory -------------------------------------------------------------------
#define Rf_allocVector               REngineLoader::Rf_allocVector
#define Rf_allocMatrix               REngineLoader::Rf_allocMatrix
#define Rf_protect                   REngineLoader::Rf_protect
#define Rf_unprotect                 REngineLoader::Rf_unprotect
#define PROTECT(x)                   REngineLoader::Rf_protect(x)
#define UNPROTECT(n)                 REngineLoader::Rf_unprotect(n)

// -- Scalar constructors ------------------------------------------------------
#define Rf_ScalarReal                REngineLoader::Rf_ScalarReal
#define Rf_ScalarInteger             REngineLoader::Rf_ScalarInteger
#define Rf_ScalarLogical             REngineLoader::Rf_ScalarLogical
#define Rf_ScalarComplex             REngineLoader::Rf_ScalarComplex
#define ScalarReal                   REngineLoader::Rf_ScalarReal
#define ScalarInteger                REngineLoader::Rf_ScalarInteger
#define ScalarLogical                REngineLoader::Rf_ScalarLogical
#define ScalarComplex                REngineLoader::Rf_ScalarComplex
#define Rf_mkString                  REngineLoader::Rf_mkString
#define Rf_mkChar                    REngineLoader::Rf_mkChar
#define Rf_mkCharCE                  REngineLoader::Rf_mkCharCE
#define mkCharCE                     REngineLoader::Rf_mkCharCE
#define Rf_install                   REngineLoader::Rf_install
#define install                      REngineLoader::Rf_install
#define Rf_list2                     REngineLoader::Rf_list2

// -- Type predicates ----------------------------------------------------------
#define Rf_isLogical                 REngineLoader::Rf_isLogical
#define Rf_isInteger                 REngineLoader::Rf_isInteger
#define Rf_isReal                    REngineLoader::Rf_isReal
#define Rf_isNumber                  REngineLoader::Rf_isNumber
#define Rf_isString                  REngineLoader::Rf_isString
#define Rf_isComplex                 REngineLoader::Rf_isComplex
#define Rf_isNull                    REngineLoader::Rf_isNull
#define Rf_isEnvironment             REngineLoader::Rf_isEnvironment
#define Rf_isFrame                   REngineLoader::Rf_isFrame
#define Rf_isMatrix                  REngineLoader::Rf_isMatrix
#define Rf_isFactor                  REngineLoader::Rf_isFactor
#define Rf_inherits                  REngineLoader::Rf_inherits
#define Rf_nrows                     REngineLoader::Rf_nrows
#define Rf_ncols                     REngineLoader::Rf_ncols
#define Rf_length                    REngineLoader::Rf_length
#define isReal                       REngineLoader::Rf_isReal
#define isString                     REngineLoader::Rf_isString
#define TYPEOF                       REngineLoader::TYPEOF

// -- Data accessors -----------------------------------------------------------
#define INTEGER                      REngineLoader::INTEGER
#define REAL                         REngineLoader::REAL
#define LOGICAL                      REngineLoader::LOGICAL
#define COMPLEX                      REngineLoader::COMPLEX
#define STRING_ELT                   REngineLoader::STRING_ELT
#define SET_STRING_ELT               REngineLoader::SET_STRING_ELT
#define VECTOR_ELT                   REngineLoader::VECTOR_ELT
#define SET_VECTOR_ELT               REngineLoader::SET_VECTOR_ELT

// -- Attribute helpers --------------------------------------------------------
#define Rf_getAttrib                 REngineLoader::Rf_getAttrib
#define getAttrib                    REngineLoader::Rf_getAttrib
#define Rf_setAttrib                 REngineLoader::Rf_setAttrib
#define Rf_asChar                    REngineLoader::Rf_asChar
#define Rf_asInteger                 REngineLoader::Rf_asInteger
#define Rf_asReal                    REngineLoader::Rf_asReal
#define Rf_translateCharUTF8         REngineLoader::Rf_translateCharUTF8
#define translateCharUTF8            REngineLoader::Rf_translateCharUTF8
#define Rf_error                     REngineLoader::Rf_error

// -- Parse / Eval -------------------------------------------------------------
#define R_ParseVector                REngineLoader::R_ParseVector
#define R_tryEval                    REngineLoader::R_tryEval
#define R_tryEvalSilent              REngineLoader::R_tryEvalSilent
#define Rf_eval                      REngineLoader::Rf_eval
#define R_curErrorBuf                REngineLoader::R_curErrorBuf

// -- Language object constructors ---------------------------------------------
#define Rf_lang1                     REngineLoader::Rf_lang1
#define Rf_lang2                     REngineLoader::Rf_lang2
#define Rf_lang3                     REngineLoader::Rf_lang3
#define Rf_GetOption1                REngineLoader::Rf_GetOption1
#define GetOption1                   REngineLoader::Rf_GetOption1

// -- S4 / External pointer ----------------------------------------------------
#define R_do_new_object              REngineLoader::R_do_new_object
#define R_do_slot                    REngineLoader::R_do_slot
#define R_do_slot_assign             REngineLoader::R_do_slot_assign
#define R_getClassDef                REngineLoader::R_getClassDef
#define R_MakeExternalPtr            REngineLoader::R_MakeExternalPtr
#define R_RegisterCFinalizerEx       REngineLoader::R_RegisterCFinalizerEx
#define R_ExternalPtrAddr            REngineLoader::R_ExternalPtrAddr

// -- Routine registration -----------------------------------------------------
#define R_getEmbeddingDllInfo        REngineLoader::R_getEmbeddingDllInfo
#define R_registerRoutines           REngineLoader::R_registerRoutines
#define R_RegisterCCallable          REngineLoader::R_RegisterCCallable
