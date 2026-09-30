/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * r_engine_loader.h — NEVEN v2.4 Dynamic Engine Loading
 *
 * Defines typedefs for every R C API function used by NEVEN, and the
 * REngineLoader class that resolves them at runtime via LoadLibrary /
 * GetProcAddress.  Zero dependencies on R64.lib or R headers — the
 * binary becomes version-agnostic.
 *
 * Usage:
 *   REngineLoader::Load("C:/Program Files/R/R-4.6.1");
 *   REngineLoader::Rf_mkString("hello");   // call like a normal function
 *   ...
 *   REngineLoader::Unload();
 */

#pragma once

// ─── Block original R startup/config headers ─────────────────────────────────
// Rinternals.h and Boolean.h are NOT blocked — they provide type definitions
// (cetype_t, Rboolean, ParseStatus etc.) that ControlR source files use.
// Their dllimport globals (R_GlobalEnv etc.) are unused because the shim macros
// redirect all references to REngineLoader pointers, so the linker never resolves them.
// We only block the startup headers (RStartup.h, Rinterface.h etc.) which declare
// functions we now provide through the loader.
#ifndef REMBEDDED_H
#define REMBEDDED_H
#endif
#ifndef REMBEDDED_H_
#define REMBEDDED_H_
#endif
#ifndef GRAPHAPP_H
#define GRAPHAPP_H
#endif
#ifndef _GRAPHAPP_H
#define _GRAPHAPP_H
#endif
#ifndef R_EXT_RSTARTUP_H
#define R_EXT_RSTARTUP_H
#endif
#ifndef R_EXT_RSTARTUP_H_
#define R_EXT_RSTARTUP_H_
#endif
#ifndef RINTERFACE_H
#define RINTERFACE_H
#endif
#ifndef RVERSION_H
#define RVERSION_H
#endif
#ifndef R_VERSION_H
#define R_VERSION_H
#endif

#include <Windows.h>
#include <stdint.h>
#include <string>

// ─── Forward declarations of R opaque types ──────────────────────────────────
// These replicate the minimum needed from Rinternals.h / RStartup.h so that
// this header can be included WITHOUT the real R headers.

#ifndef SEXP_DEFINED
#define SEXP_DEFINED
typedef struct _SEXP *SEXP;
#endif

#ifndef R_COMPLEX_DEFINED
#define R_COMPLEX_DEFINED
typedef struct { double r, i; } Rcomplex;
#endif

typedef int    SA_TYPE;
typedef int    Rboolean;

// SA_TYPE enum values — match R's SA_TYPE in R_ext/RStartup.h exactly
// These values are stable across R versions.
#ifndef SA_NORESTORE
#define SA_NORESTORE 0
#define SA_RESTORE   1
#define SA_DEFAULT   2
#define SA_NOSAVE    3
#define SA_SAVE      4
#define SA_SAVEASK   5
#define SA_SUICIDE   6
#endif

// DL_FUNC — generic function pointer, matches R's canonical definition
// typedef void *(*DL_FUNC)(void) — function returning void*
#ifndef DL_FUNC
typedef void *(*DL_FUNC)(void);
#endif

// UImode enum — matches R's definition in R_ext/RStartup.h
// Used to set CharacterMode in structRstart (RGui=0, RTerm=1, LinkDLL=2)
typedef enum { RGui = 0, RTerm = 1, LinkDLL = 2 } UImode;

// ─── structRstart — exact layout from R 4.4.1 R_ext/RStartup.h ──────────────
//
// CRITICAL: This struct MUST match the memory layout that R_DefParams /
// R_DefParamsEx writes into. Any mismatch causes field corruption and crashes.
//
// Layout verified against:
//   C:\Program Files\R\R-4.4.1\include\R_ext\RStartup.h
//
// RstartVersion 1 (introduced in R 4.2.0) is used via R_DefParamsEx(Rp, 1).
// This enables the extra fields (CleanUp, ClearerrConsole, etc.) at the end.
// If R_DefParamsEx is unavailable, fall back to R_DefParams(Rp) which only
// initialises the version-0 fields.
//
// sizeof(structRstart) on x64 = 216 bytes (verified with MSVC x64).
//
typedef struct {
    // ── Version 0 fields (available with R_DefParams and R_DefParamsEx) ──────
    Rboolean R_Quiet;           // offset  0
    Rboolean R_NoEcho;          // offset  4
    Rboolean R_Interactive;     // offset  8
    Rboolean R_Verbose;         // offset 12
    Rboolean LoadSiteFile;      // offset 16
    Rboolean LoadInitFile;      // offset 20
    Rboolean DebugInitFile;     // offset 24
    SA_TYPE  RestoreAction;     // offset 28   (SA_TYPE == int)
    SA_TYPE  SaveAction;        // offset 32
    // R_SIZE_T = size_t = 8 bytes on x64
    size_t   vsize;             // offset 40   (after 4 bytes of padding: 36+4=40)
    size_t   nsize;             // offset 48
    size_t   max_vsize;         // offset 56
    size_t   max_nsize;         // offset 64
    size_t   ppsize;            // offset 72
    // Bit-fields: NoRenviron:16 + RstartVersion:16 = 32 bits total = 4 bytes
    int      NoRenviron    : 16; // offset 80
    int      RstartVersion : 16; // offset 80+2 bytes
    int      nconnections;       // offset 84

    // ── Win32-specific fields ─────────────────────────────────────────────
    char    *rhome;                                       // offset  88
    char    *home;                                        // offset  96
    int    (*ReadConsole)(const char *, unsigned char *, int, int); // offset 104
    void   (*WriteConsole)(const char *, int);            // offset 112
    void   (*CallBack)(void);                             // offset 120
    void   (*ShowMessage)(const char *);                  // offset 128
    int    (*YesNoCancel)(const char *);                  // offset 136
    void   (*Busy)(int);                                  // offset 144
    int      CharacterMode;                               // offset 152  (UImode == int)
    int      _pad1;                                       // offset 156  (alignment pad)
    void   (*WriteConsoleEx)(const char *, int, int);     // offset 160  (added R 2.5.0)
    Rboolean EmitEmbeddedUTF8;                            // offset 168  (added R 4.0.0)
    int      _pad2;                                       // offset 172  (alignment pad)

    // ── Version 1 fields (added R 4.2.0, only valid when RstartVersion==1) ──
    void   (*CleanUp)(SA_TYPE, int, int);                 // offset 176
    void   (*ClearerrConsole)(void);                      // offset 184
    void   (*FlushConsole)(void);                         // offset 192
    void   (*ResetConsole)(void);                         // offset 200
    void   (*Suicide)(const char *);                      // offset 208
                                                          // total = 216 bytes
} REngineStartParams, *REngineRstart;

typedef struct R_CallMethodDef {
    const char *name;
    DL_FUNC     fun;
    int         numArgs;
} R_CallMethodDef, *R_CallMethodDefPtr;

// ─── ParseStatus (R's parse result type) ─────────────────────────────────────
// Use a simple int typedef for the loader; the actual enum values are defined
// in the project's Include/R_ext/Parse.h mock.  Using int here avoids
// redefinition conflicts when both headers are visible.
typedef int RParseStatus;
typedef void   (*R_CFinalizer_t)(SEXP);
typedef void   *DllInfo;

// Standard integer type for R lengths (intptr_t covers 32/64-bit)
typedef intptr_t R_xlen_t;

// ─── cetype_t (character encoding) ───────────────────────────────────────────
// Use int to avoid redefinition; the real enum is in the project's Rinternals.h mock.
// The values are: CE_NATIVE=0, CE_UTF8=1, CE_LATIN1=2, CE_SYMBOL=3, CE_ANY=4
typedef int REcetype;

// ─── Typedefs for every R C API function used by NEVEN ───────────────────────

// --- Startup / Shutdown ---
typedef void   (*FnRSetStartTime)     (void);
typedef void   (*FnRDefParams)        (REngineRstart);
typedef int    (*FnRDefParamsEx)      (REngineRstart, int);  // R 4.2+
typedef void   (*FnRSetParams)        (REngineRstart);
typedef void   (*FnRSetCommandLineArgs)(int argc, char **argv);
typedef void   (*FnGA_initapp)        (int, char **);
typedef void   (*FnReadconsolecfg)    (void);
typedef void   (*FnSetup_Rmainloop)   (void);
typedef void   (*FnRun_Rmainloop)     (void);
typedef void   (*FnRf_endEmbeddedR)   (int);
typedef const char *(*FnGetDLLVersion)(void);

// --- R events / periodic ---
typedef void   (*FnR_ProcessEvents)   (void);

// --- Memory / protection ---
typedef SEXP   (*FnRf_allocVector)    (unsigned int type, R_xlen_t length);
typedef SEXP   (*FnRf_allocMatrix)    (unsigned int type, int nrow, int ncol);
typedef SEXP   (*FnRf_protect)        (SEXP s);
typedef void   (*FnRf_unprotect)      (int n);

// --- Scalar constructors ---
typedef SEXP   (*FnRf_ScalarReal)     (double v);
typedef SEXP   (*FnRf_ScalarInteger)  (int v);
typedef SEXP   (*FnRf_ScalarLogical)  (int v);
typedef SEXP   (*FnRf_ScalarComplex)  (Rcomplex v);
typedef SEXP   (*FnRf_mkString)       (const char *s);
typedef SEXP   (*FnRf_mkChar)         (const char *s);
typedef SEXP   (*FnRf_mkCharCE)       (const char *s, int enc);
typedef SEXP   (*FnRf_install)        (const char *name);
typedef SEXP   (*FnRf_list2)          (SEXP s1, SEXP s2);

// --- Type-checking predicates ---
typedef int    (*FnRf_isLogical)      (SEXP s);
typedef int    (*FnRf_isInteger)      (SEXP s);
typedef int    (*FnRf_isReal)         (SEXP s);
typedef int    (*FnRf_isNumber)       (SEXP s);
typedef int    (*FnRf_isString)       (SEXP s);
typedef int    (*FnRf_isComplex)      (SEXP s);
typedef int    (*FnRf_isNull)         (SEXP s);
typedef int    (*FnRf_isEnvironment)  (SEXP s);
typedef int    (*FnRf_isFrame)        (SEXP s);
typedef int    (*FnRf_isMatrix)       (SEXP s);
typedef int    (*FnRf_isFactor)       (SEXP s);
typedef int    (*FnRf_inherits)       (SEXP s, const char *cls);
typedef int    (*FnRf_nrows)          (SEXP s);
typedef int    (*FnRf_ncols)          (SEXP s);
typedef R_xlen_t(*FnRf_length)        (SEXP s);
typedef int    (*FnTYPEOF)            (SEXP x);

// --- Data accessors ---
typedef int    *(*FnINTEGER)          (SEXP x);
typedef double *(*FnREAL)             (SEXP x);
typedef int    *(*FnLOGICAL)          (SEXP x);
typedef Rcomplex *(*FnCOMPLEX)        (SEXP x);
typedef SEXP   (*FnSTRING_ELT)        (SEXP x, int i);
typedef SEXP   (*FnSET_STRING_ELT)    (SEXP x, int i, SEXP v);
typedef SEXP   (*FnVECTOR_ELT)        (SEXP x, int i);
typedef SEXP   (*FnSET_VECTOR_ELT)    (SEXP x, int i, SEXP v);

// --- Attribute / name helpers ---
typedef SEXP   (*FnRf_getAttrib)      (SEXP x, SEXP sym);
typedef void   (*FnRf_setAttrib)      (SEXP x, SEXP sym, SEXP val);
typedef SEXP   (*FnRf_asChar)         (SEXP x);
typedef int    (*FnRf_asInteger)      (SEXP s);
typedef double (*FnRf_asReal)         (SEXP s);
typedef const char *(*FnRf_translateCharUTF8)(SEXP s);
typedef void   (*FnRf_error)          (const char *fmt, ...);

// --- Parse / eval ---
// Note: R_ParseVector takes ParseStatus* in the real API.  We use a forward-compatible
// int* typedef here because ParseStatus is defined downstream in r_api_shim.h.
// Call sites that pass ParseStatus* will work because ParseStatus is an enum backed by int.
typedef SEXP   (*FnR_ParseVector)     (SEXP text, int n, void *status, SEXP src);
typedef SEXP   (*FnR_tryEval)         (SEXP call, SEXP env, int *err);
typedef SEXP   (*FnR_tryEvalSilent)   (SEXP call, SEXP env, int *err);
typedef SEXP   (*FnRf_eval)           (SEXP call, SEXP env);

// --- Language object constructors ---
typedef SEXP   (*FnRf_lang1)          (SEXP s1);
typedef SEXP   (*FnRf_lang2)          (SEXP s1, SEXP s2);
typedef SEXP   (*FnRf_lang3)          (SEXP s1, SEXP s2, SEXP s3);
typedef SEXP   (*FnRf_GetOption1)     (SEXP name);

// --- S4 / external pointer ---
typedef SEXP   (*FnR_do_new_object)   (SEXP cls);
typedef SEXP   (*FnR_do_slot)         (SEXP obj, SEXP name);
typedef void   (*FnR_do_slot_assign)  (SEXP obj, SEXP name, SEXP value);
typedef SEXP   (*FnR_getClassDef)     (const char *cls);
typedef SEXP   (*FnR_MakeExternalPtr) (void *p, SEXP tag, SEXP prot);
typedef void   (*FnR_RegisterCFinalizerEx)(SEXP s, R_CFinalizer_t f, int onexit);
typedef void  *(*FnR_ExternalPtrAddr) (SEXP s);

// --- Routine registration ---
typedef DllInfo *(*FnR_getEmbeddingDllInfo)(void);
typedef void   (*FnR_registerRoutines)(DllInfo *info, void *cMethods,
                                       void *callMethods,
                                       void *fortranMethods, void *externalMethods);
typedef void   (*FnR_RegisterCCallable)(const char *pkg, const char *name, void *f);

// --- Globals (loaded as pointers from the DLL) ---
typedef SEXP   *(*FnGetGlobalEnv)     (void);   // not needed — we resolve via variable

// ─── REngineLoader — loads R.dll at runtime ───────────────────────────────────

/**
 * @brief Singleton loader for R.dll.
 *
 * Call REngineLoader::Load(r_home) once at startup.  After that, every
 * function pointer is valid and can be used directly by name:
 *
 *   auto sexp = REngineLoader::Rf_mkString("hello");
 *
 * If Load() fails, all pointers remain nullptr and IsLoaded() returns false.
 */
class REngineLoader {
public:
    // ── Public interface ─────────────────────────────────────────────────────

    /**
     * @brief Load R.dll from r_home (e.g. "C:/Program Files/R/R-4.6.1").
     * @return true if all required functions were resolved; false otherwise.
     */
    static bool Load(const std::string& r_home);

    /** @brief Free R.dll handle. */
    static void Unload();

    /** @return true after a successful Load() call. */
    static bool IsLoaded()  { return hR_ != nullptr; }

    /**
     * @brief Major and minor version of the loaded R library.
     * Only valid after Load().
     */
    static int  VersionMajor() { return ver_major_; }
    static int  VersionMinor() { return ver_minor_; }

    // ── Globals resolved from R.dll ──────────────────────────────────────────
    //    These mirror R's exported variables (R_GlobalEnv etc.).
    //    Initialized by Load().
    static SEXP *pR_GlobalEnv;
    static SEXP *pR_NamesSymbol;
    static SEXP *pR_DimNamesSymbol;
    static SEXP *pR_LevelsSymbol;
    static SEXP *pR_RowNamesSymbol;
    static SEXP *pR_NaString;
    static double *pR_NaReal;
    static int  *pUserBreak;

    // ── Function pointers ────────────────────────────────────────────────────

    // Startup / Shutdown
    static FnRSetStartTime      R_setStartTime;
    static FnRDefParams         R_DefParams;
    static FnRDefParamsEx       R_DefParamsEx;
    static FnRSetParams         R_SetParams;
    static FnRSetCommandLineArgs R_set_command_line_arguments;
    static FnGA_initapp         GA_initapp;
    static FnReadconsolecfg     readconsolecfg;
    static FnSetup_Rmainloop    setup_Rmainloop;
    static FnRun_Rmainloop      run_Rmainloop;
    static FnRf_endEmbeddedR    Rf_endEmbeddedR;
    static FnGetDLLVersion      getDLLVersion;

    // Events
    static FnR_ProcessEvents    R_ProcessEvents;

    // Memory
    static FnRf_allocVector     Rf_allocVector;
    static FnRf_allocMatrix     Rf_allocMatrix;
    static FnRf_protect         Rf_protect;
    static FnRf_unprotect       Rf_unprotect;

    // Scalar constructors
    static FnRf_ScalarReal      Rf_ScalarReal;
    static FnRf_ScalarInteger   Rf_ScalarInteger;
    static FnRf_ScalarLogical   Rf_ScalarLogical;
    static FnRf_ScalarComplex   Rf_ScalarComplex;
    static FnRf_mkString        Rf_mkString;
    static FnRf_mkChar          Rf_mkChar;
    static FnRf_mkCharCE        Rf_mkCharCE;
    static FnRf_install         Rf_install;
    static FnRf_list2           Rf_list2;

    // Type predicates
    static FnRf_isLogical       Rf_isLogical;
    static FnRf_isInteger       Rf_isInteger;
    static FnRf_isReal          Rf_isReal;
    static FnRf_isNumber        Rf_isNumber;
    static FnRf_isString        Rf_isString;
    static FnRf_isComplex       Rf_isComplex;
    static FnRf_isNull          Rf_isNull;
    static FnRf_isEnvironment   Rf_isEnvironment;
    static FnRf_isFrame         Rf_isFrame;
    static FnRf_isMatrix        Rf_isMatrix;
    static FnRf_isFactor        Rf_isFactor;
    static FnRf_inherits        Rf_inherits;
    static FnRf_nrows           Rf_nrows;
    static FnRf_ncols           Rf_ncols;
    static FnRf_length          Rf_length;
    static FnTYPEOF             TYPEOF;

    // Data accessors
    static FnINTEGER            INTEGER;
    static FnREAL               REAL;
    static FnLOGICAL            LOGICAL;
    static FnCOMPLEX            COMPLEX;
    static FnSTRING_ELT         STRING_ELT;
    static FnSET_STRING_ELT     SET_STRING_ELT;
    static FnVECTOR_ELT         VECTOR_ELT;
    static FnSET_VECTOR_ELT     SET_VECTOR_ELT;

    // Attribute / name helpers
    static FnRf_getAttrib       Rf_getAttrib;
    static FnRf_setAttrib       Rf_setAttrib;
    static FnRf_asChar          Rf_asChar;
    static FnRf_asInteger       Rf_asInteger;
    static FnRf_asReal          Rf_asReal;
    static FnRf_translateCharUTF8 Rf_translateCharUTF8;
    static FnRf_error           Rf_error;

    // Parse / eval
    static FnR_ParseVector      R_ParseVector;
    static FnR_tryEval          R_tryEval;
    static FnR_tryEvalSilent    R_tryEvalSilent;
    static FnRf_eval            Rf_eval;

    // Error buffer (R_curErrorBuf — optional, available since R 4.0)
    typedef const char *(*FnR_curErrorBuf)(void);
    static FnR_curErrorBuf      R_curErrorBuf;

    // Language object constructors
    static FnRf_lang1           Rf_lang1;
    static FnRf_lang2           Rf_lang2;
    static FnRf_lang3           Rf_lang3;
    static FnRf_GetOption1      Rf_GetOption1;

    // S4 / external pointer
    static FnR_do_new_object    R_do_new_object;
    static FnR_do_slot          R_do_slot;
    static FnR_do_slot_assign   R_do_slot_assign;
    static FnR_getClassDef      R_getClassDef;
    static FnR_MakeExternalPtr  R_MakeExternalPtr;
    static FnR_RegisterCFinalizerEx R_RegisterCFinalizerEx;
    static FnR_ExternalPtrAddr  R_ExternalPtrAddr;

    // Routine registration
    static FnR_getEmbeddingDllInfo  R_getEmbeddingDllInfo;
    static FnR_registerRoutines     R_registerRoutines;
    static FnR_RegisterCCallable    R_RegisterCCallable;

private:
    // ── Internal helpers ─────────────────────────────────────────────────────

    /** Resolve one function; log a warning if not found. */
    template <typename T>
    static T GetProc(const char *name, bool required = true);

    /** Resolve a pointer to a global variable exported by R.dll. */
    template <typename T>
    static T* GetVar(const char *name);

    /** Verify that all required function pointers were resolved. */
    static bool ValidateRequired();

    /** Parse "major.minor.patch" from getDLLVersion() string. */
    static void ParseVersion();

    static HMODULE hR_;
    static int     ver_major_;
    static int     ver_minor_;
    static int     ver_patch_;
};
