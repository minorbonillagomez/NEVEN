/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * r_engine_loader.cc — NEVEN v2.4 Dynamic Engine Loading
 *
 * Implementation of REngineLoader::Load() / Unload().
 * Loads R.dll at runtime and resolves every R C API function pointer.
 *
 * DESIGN NOTES:
 *  - "Required" functions: missing → Load() returns false (fatal).
 *  - "Optional" functions: missing → pointer stays nullptr, guarded at call site.
 *  - No R headers are included here — all types come from r_engine_loader.h.
 *  - This file depends only on Windows.h + r_engine_loader.h.
 */

#include "r_engine_loader.h"
#include "child_process_log.h"

#include <sstream>
#include <cstring>

// ─── Static member definitions ───────────────────────────────────────────────

HMODULE  REngineLoader::hR_            = nullptr;
int      REngineLoader::ver_major_     = 0;
int      REngineLoader::ver_minor_     = 0;
int      REngineLoader::ver_patch_     = 0;

// Globals
SEXP    *REngineLoader::pR_GlobalEnv      = nullptr;
SEXP    *REngineLoader::pR_NamesSymbol    = nullptr;
SEXP    *REngineLoader::pR_DimNamesSymbol = nullptr;
SEXP    *REngineLoader::pR_LevelsSymbol   = nullptr;
SEXP    *REngineLoader::pR_RowNamesSymbol = nullptr;
SEXP    *REngineLoader::pR_NaString       = nullptr;
double  *REngineLoader::pR_NaReal         = nullptr;
int     *REngineLoader::pUserBreak        = nullptr;

// Startup / Shutdown
FnRSetStartTime       REngineLoader::R_setStartTime              = nullptr;
FnRDefParams          REngineLoader::R_DefParams                 = nullptr;
FnRSetParams          REngineLoader::R_SetParams                 = nullptr;
FnRSetCommandLineArgs REngineLoader::R_set_command_line_arguments = nullptr;
FnGA_initapp          REngineLoader::GA_initapp                  = nullptr;
FnReadconsolecfg      REngineLoader::readconsolecfg              = nullptr;
FnSetup_Rmainloop     REngineLoader::setup_Rmainloop             = nullptr;
FnRun_Rmainloop       REngineLoader::run_Rmainloop               = nullptr;
FnRf_endEmbeddedR     REngineLoader::Rf_endEmbeddedR             = nullptr;
FnGetDLLVersion       REngineLoader::getDLLVersion               = nullptr;

// Events
FnR_ProcessEvents     REngineLoader::R_ProcessEvents             = nullptr;

// Memory
FnRf_allocVector      REngineLoader::Rf_allocVector              = nullptr;
FnRf_allocMatrix      REngineLoader::Rf_allocMatrix              = nullptr;
FnRf_protect          REngineLoader::Rf_protect                  = nullptr;
FnRf_unprotect        REngineLoader::Rf_unprotect                = nullptr;

// Scalar constructors
FnRf_ScalarReal       REngineLoader::Rf_ScalarReal               = nullptr;
FnRf_ScalarInteger    REngineLoader::Rf_ScalarInteger            = nullptr;
FnRf_ScalarLogical    REngineLoader::Rf_ScalarLogical            = nullptr;
FnRf_ScalarComplex    REngineLoader::Rf_ScalarComplex            = nullptr;
FnRf_mkString         REngineLoader::Rf_mkString                 = nullptr;
FnRf_mkChar           REngineLoader::Rf_mkChar                   = nullptr;
FnRf_mkCharCE         REngineLoader::Rf_mkCharCE                 = nullptr;
FnRf_install          REngineLoader::Rf_install                  = nullptr;
FnRf_list2            REngineLoader::Rf_list2                    = nullptr;

// Type predicates
FnRf_isLogical        REngineLoader::Rf_isLogical                = nullptr;
FnRf_isInteger        REngineLoader::Rf_isInteger                = nullptr;
FnRf_isReal           REngineLoader::Rf_isReal                   = nullptr;
FnRf_isNumber         REngineLoader::Rf_isNumber                 = nullptr;
FnRf_isString         REngineLoader::Rf_isString                 = nullptr;
FnRf_isComplex        REngineLoader::Rf_isComplex                = nullptr;
FnRf_isNull           REngineLoader::Rf_isNull                   = nullptr;
FnRf_isEnvironment    REngineLoader::Rf_isEnvironment            = nullptr;
FnRf_isFrame          REngineLoader::Rf_isFrame                  = nullptr;
FnRf_isMatrix         REngineLoader::Rf_isMatrix                 = nullptr;
FnRf_isFactor         REngineLoader::Rf_isFactor                 = nullptr;
FnRf_inherits         REngineLoader::Rf_inherits                 = nullptr;
FnRf_nrows            REngineLoader::Rf_nrows                    = nullptr;
FnRf_ncols            REngineLoader::Rf_ncols                    = nullptr;
FnRf_length           REngineLoader::Rf_length                   = nullptr;
FnTYPEOF              REngineLoader::TYPEOF                      = nullptr;

// Data accessors
FnINTEGER             REngineLoader::INTEGER                     = nullptr;
FnREAL                REngineLoader::REAL                        = nullptr;
FnLOGICAL             REngineLoader::LOGICAL                     = nullptr;
FnCOMPLEX             REngineLoader::COMPLEX                     = nullptr;
FnSTRING_ELT          REngineLoader::STRING_ELT                  = nullptr;
FnSET_STRING_ELT      REngineLoader::SET_STRING_ELT              = nullptr;
FnVECTOR_ELT          REngineLoader::VECTOR_ELT                  = nullptr;
FnSET_VECTOR_ELT      REngineLoader::SET_VECTOR_ELT              = nullptr;

// Attribute / name helpers
FnRf_getAttrib        REngineLoader::Rf_getAttrib                = nullptr;
FnRf_setAttrib        REngineLoader::Rf_setAttrib                = nullptr;
FnRf_asChar           REngineLoader::Rf_asChar                   = nullptr;
FnRf_asInteger        REngineLoader::Rf_asInteger                = nullptr;
FnRf_asReal           REngineLoader::Rf_asReal                   = nullptr;
FnRf_translateCharUTF8 REngineLoader::Rf_translateCharUTF8       = nullptr;
FnRf_error            REngineLoader::Rf_error                    = nullptr;

// Parse / eval
FnR_ParseVector       REngineLoader::R_ParseVector               = nullptr;
FnR_tryEval           REngineLoader::R_tryEval                   = nullptr;
FnR_tryEvalSilent     REngineLoader::R_tryEvalSilent             = nullptr;
FnRf_eval             REngineLoader::Rf_eval                     = nullptr;
REngineLoader::FnR_curErrorBuf REngineLoader::R_curErrorBuf      = nullptr;

// Language object constructors
FnRf_lang1            REngineLoader::Rf_lang1                    = nullptr;
FnRf_lang2            REngineLoader::Rf_lang2                    = nullptr;
FnRf_lang3            REngineLoader::Rf_lang3                    = nullptr;
FnRf_GetOption1       REngineLoader::Rf_GetOption1               = nullptr;

// S4 / external pointer
FnR_do_new_object     REngineLoader::R_do_new_object             = nullptr;
FnR_do_slot           REngineLoader::R_do_slot                   = nullptr;
FnR_do_slot_assign    REngineLoader::R_do_slot_assign            = nullptr;
FnR_getClassDef       REngineLoader::R_getClassDef               = nullptr;
FnR_MakeExternalPtr   REngineLoader::R_MakeExternalPtr           = nullptr;
FnR_RegisterCFinalizerEx REngineLoader::R_RegisterCFinalizerEx   = nullptr;
FnR_ExternalPtrAddr   REngineLoader::R_ExternalPtrAddr           = nullptr;

// Routine registration
FnR_getEmbeddingDllInfo REngineLoader::R_getEmbeddingDllInfo     = nullptr;
FnR_registerRoutines  REngineLoader::R_registerRoutines          = nullptr;
FnR_RegisterCCallable REngineLoader::R_RegisterCCallable         = nullptr;

// ─── Internal helpers ─────────────────────────────────────────────────────────

template <typename T>
T REngineLoader::GetProc(const char *name, bool required) {
    auto fn = reinterpret_cast<T>(GetProcAddress(hR_, name));
    if (!fn) {
        if (required)
            CHILD_LOG_ERR("REngineLoader: required symbol '%s' not found in R.dll", name);
        else
            CHILD_LOG("REngineLoader: optional symbol '%s' not found (skipped)", name);
    }
    return fn;
}

template <typename T>
T* REngineLoader::GetVar(const char *name) {
    auto ptr = reinterpret_cast<T*>(GetProcAddress(hR_, name));
    if (!ptr)
        CHILD_LOG_ERR("REngineLoader: exported variable '%s' not found in R.dll", name);
    return ptr;
}

// ─── ParseVersion ─────────────────────────────────────────────────────────────

void REngineLoader::ParseVersion() {
    if (!getDLLVersion) return;

    const char *version = getDLLVersion();
    if (!version || !*version) return;

    // Parse "major.minor.patch" (e.g. "4.6.1")
    ver_major_ = ver_minor_ = ver_patch_ = 0;
    char buf[32] = {};
    int  part = 0, idx = 0;

    for (const char *p = version; *p && part < 3; ++p) {
        if (*p == '.') {
            buf[idx] = 0;
            int val = atoi(buf);
            if (part == 0) ver_major_ = val;
            else if (part == 1) ver_minor_ = val;
            else                ver_patch_ = val;
            ++part; idx = 0;
        } else if (idx < 30) {
            buf[idx++] = *p;
        }
    }
    // last segment
    buf[idx] = 0;
    if (idx > 0) {
        int val = atoi(buf);
        if (part == 0) ver_major_ = val;
        else if (part == 1) ver_minor_ = val;
        else                ver_patch_ = val;
    }
}

// ─── ValidateRequired ─────────────────────────────────────────────────────────

bool REngineLoader::ValidateRequired() {
    // The absolute minimum set — if any of these is null, ControlR cannot start.
    bool ok = true;
    #define CHECK(fn) if (!fn) { CHILD_LOG_ERR("REngineLoader: required fn "#fn" is null"); ok = false; }
    CHECK(R_setStartTime)
    CHECK(R_DefParams)
    CHECK(R_SetParams)
    CHECK(R_set_command_line_arguments)
    CHECK(setup_Rmainloop)
    CHECK(run_Rmainloop)
    CHECK(Rf_endEmbeddedR)
    CHECK(Rf_allocVector)
    CHECK(Rf_mkString)
    CHECK(Rf_install)
    CHECK(R_tryEval)
    CHECK(R_tryEvalSilent)
    CHECK(R_ParseVector)
    CHECK(INTEGER)
    CHECK(REAL)
    CHECK(STRING_ELT)
    CHECK(SET_STRING_ELT)
    CHECK(VECTOR_ELT)
    CHECK(SET_VECTOR_ELT)
    CHECK(Rf_length)
    CHECK(Rf_isEnvironment)
    CHECK(Rf_inherits)
    CHECK(pR_GlobalEnv)
    CHECK(pUserBreak)
    #undef CHECK
    return ok;
}

// ─── Load ─────────────────────────────────────────────────────────────────────

bool REngineLoader::Load(const std::string& r_home) {
    if (hR_) {
        CHILD_LOG("REngineLoader::Load called while already loaded — skipping");
        return true;
    }

    // R.dll lives at <R_HOME>\bin\x64\R.dll
    std::string dll_path = r_home + "\\bin\\x64\\R.dll";
    CHILD_LOG("REngineLoader: loading '%s'", dll_path.c_str());

    hR_ = LoadLibraryA(dll_path.c_str());
    if (!hR_) {
        DWORD err = GetLastError();
        CHILD_LOG_ERR("REngineLoader: LoadLibrary failed for '%s' (error %lu)", dll_path.c_str(), err);
        return false;
    }

    // ── Exported globals ─────────────────────────────────────────────────────
    pR_GlobalEnv      = GetVar<SEXP>("R_GlobalEnv");
    pR_NamesSymbol    = GetVar<SEXP>("R_NamesSymbol");
    pR_DimNamesSymbol = GetVar<SEXP>("R_DimNamesSymbol");
    pR_LevelsSymbol   = GetVar<SEXP>("R_LevelsSymbol");
    pR_RowNamesSymbol = GetVar<SEXP>("R_RowNamesSymbol");
    pR_NaString       = GetVar<SEXP>("R_NaString");
    pR_NaReal         = GetVar<double>("R_NaReal");
    pUserBreak        = GetVar<int> ("UserBreak");

    // ── Startup / Shutdown ───────────────────────────────────────────────────
    R_setStartTime               = GetProc<FnRSetStartTime>     ("R_setStartTime");
    R_DefParams                  = GetProc<FnRDefParams>        ("R_DefParams");
    R_SetParams                  = GetProc<FnRSetParams>        ("R_SetParams");
    R_set_command_line_arguments = GetProc<FnRSetCommandLineArgs>("R_set_command_line_arguments");

    // GA_initapp and readconsolecfg live in RGraphApp64.dll, not R.dll.
    // Load RGraphApp64.dll from the same bin\x64 directory.
    {
        std::string graphapp_path = r_home + "\\bin\\x64\\RGraphApp64.dll";
        HMODULE hGraphApp = LoadLibraryA(graphapp_path.c_str());
        if (hGraphApp) {
            GA_initapp     = reinterpret_cast<FnGA_initapp>    (GetProcAddress(hGraphApp, "GA_initapp"));
            readconsolecfg = reinterpret_cast<FnReadconsolecfg>(GetProcAddress(hGraphApp, "readconsolecfg"));
            if (!GA_initapp)     CHILD_LOG("REngineLoader: GA_initapp not in RGraphApp64.dll (optional)");
            if (!readconsolecfg) CHILD_LOG("REngineLoader: readconsolecfg not in RGraphApp64.dll (optional)");
        } else {
            CHILD_LOG("REngineLoader: RGraphApp64.dll not found — GA_initapp/readconsolecfg unavailable");
        }
    }
    setup_Rmainloop              = GetProc<FnSetup_Rmainloop>   ("setup_Rmainloop");
    run_Rmainloop                = GetProc<FnRun_Rmainloop>     ("run_Rmainloop");
    Rf_endEmbeddedR              = GetProc<FnRf_endEmbeddedR>   ("Rf_endEmbeddedR");
    getDLLVersion                = GetProc<FnGetDLLVersion>     ("getDLLVersion");

    // ── Events ───────────────────────────────────────────────────────────────
    R_ProcessEvents              = GetProc<FnR_ProcessEvents>   ("R_ProcessEvents");

    // ── Memory ───────────────────────────────────────────────────────────────
    Rf_allocVector               = GetProc<FnRf_allocVector>    ("Rf_allocVector");
    Rf_allocMatrix               = GetProc<FnRf_allocMatrix>    ("Rf_allocMatrix");
    Rf_protect                   = GetProc<FnRf_protect>        ("Rf_protect");
    Rf_unprotect                 = GetProc<FnRf_unprotect>      ("Rf_unprotect");

    // ── Scalar constructors ──────────────────────────────────────────────────
    Rf_ScalarReal                = GetProc<FnRf_ScalarReal>     ("Rf_ScalarReal");
    Rf_ScalarInteger             = GetProc<FnRf_ScalarInteger>  ("Rf_ScalarInteger");
    Rf_ScalarLogical             = GetProc<FnRf_ScalarLogical>  ("Rf_ScalarLogical");
    Rf_ScalarComplex             = GetProc<FnRf_ScalarComplex>  ("Rf_ScalarComplex");
    Rf_mkString                  = GetProc<FnRf_mkString>       ("Rf_mkString");
    Rf_mkChar                    = GetProc<FnRf_mkChar>         ("Rf_mkChar");
    Rf_mkCharCE                  = GetProc<FnRf_mkCharCE>       ("Rf_mkCharCE");
    Rf_install                   = GetProc<FnRf_install>        ("Rf_install");
    Rf_list2                     = GetProc<FnRf_list2>          ("Rf_list2");

    // ── Type predicates ──────────────────────────────────────────────────────
    Rf_isLogical                 = GetProc<FnRf_isLogical>      ("Rf_isLogical");
    Rf_isInteger                 = GetProc<FnRf_isInteger>      ("Rf_isInteger");
    Rf_isReal                    = GetProc<FnRf_isReal>         ("Rf_isReal");
    Rf_isNumber                  = GetProc<FnRf_isNumber>       ("Rf_isNumber");
    Rf_isString                  = GetProc<FnRf_isString>       ("Rf_isString");
    Rf_isComplex                 = GetProc<FnRf_isComplex>      ("Rf_isComplex");
    Rf_isNull                    = GetProc<FnRf_isNull>         ("Rf_isNull");
    Rf_isEnvironment             = GetProc<FnRf_isEnvironment>  ("Rf_isEnvironment");
    Rf_isFrame                   = GetProc<FnRf_isFrame>        ("Rf_isFrame");
    Rf_isMatrix                  = GetProc<FnRf_isMatrix>       ("Rf_isMatrix");
    Rf_isFactor                  = GetProc<FnRf_isFactor>       ("Rf_isFactor");
    Rf_inherits                  = GetProc<FnRf_inherits>       ("Rf_inherits");
    Rf_nrows                     = GetProc<FnRf_nrows>          ("Rf_nrows");
    Rf_ncols                     = GetProc<FnRf_ncols>          ("Rf_ncols");
    Rf_length                    = GetProc<FnRf_length>         ("Rf_length");
    TYPEOF                       = GetProc<FnTYPEOF>            ("TYPEOF");

    // ── Data accessors ───────────────────────────────────────────────────────
    INTEGER                      = GetProc<FnINTEGER>           ("INTEGER");
    REAL                         = GetProc<FnREAL>              ("REAL");
    LOGICAL                      = GetProc<FnLOGICAL>           ("LOGICAL");
    COMPLEX                      = GetProc<FnCOMPLEX>           ("COMPLEX");
    STRING_ELT                   = GetProc<FnSTRING_ELT>        ("STRING_ELT");
    SET_STRING_ELT               = GetProc<FnSET_STRING_ELT>    ("SET_STRING_ELT");
    VECTOR_ELT                   = GetProc<FnVECTOR_ELT>        ("VECTOR_ELT");
    SET_VECTOR_ELT               = GetProc<FnSET_VECTOR_ELT>    ("SET_VECTOR_ELT");

    // ── Attribute helpers ────────────────────────────────────────────────────
    Rf_getAttrib                 = GetProc<FnRf_getAttrib>      ("Rf_getAttrib");
    Rf_setAttrib                 = GetProc<FnRf_setAttrib>      ("Rf_setAttrib");
    Rf_asChar                    = GetProc<FnRf_asChar>         ("Rf_asChar");
    Rf_asInteger                 = GetProc<FnRf_asInteger>      ("Rf_asInteger");
    Rf_asReal                    = GetProc<FnRf_asReal>         ("Rf_asReal");
    Rf_translateCharUTF8         = GetProc<FnRf_translateCharUTF8>("Rf_translateCharUTF8");
    Rf_error                     = GetProc<FnRf_error>          ("Rf_error");

    // ── Parse / eval ─────────────────────────────────────────────────────────
    R_ParseVector                = GetProc<FnR_ParseVector>     ("R_ParseVector");
    R_tryEval                    = GetProc<FnR_tryEval>         ("R_tryEval");
    R_tryEvalSilent              = GetProc<FnR_tryEvalSilent>   ("R_tryEvalSilent");
    Rf_eval                      = GetProc<FnRf_eval>           ("Rf_eval");
    R_curErrorBuf                = GetProc<FnR_curErrorBuf>     ("R_curErrorBuf", /*required=*/false);

    // ── Language object constructors ─────────────────────────────────────────
    Rf_lang1                     = GetProc<FnRf_lang1>          ("Rf_lang1");
    Rf_lang2                     = GetProc<FnRf_lang2>          ("Rf_lang2");
    Rf_lang3                     = GetProc<FnRf_lang3>          ("Rf_lang3");
    Rf_GetOption1                = GetProc<FnRf_GetOption1>     ("Rf_GetOption1");

    // ── S4 / external pointer ────────────────────────────────────────────────
    R_do_new_object              = GetProc<FnR_do_new_object>   ("R_do_new_object");
    R_do_slot                    = GetProc<FnR_do_slot>         ("R_do_slot");
    R_do_slot_assign             = GetProc<FnR_do_slot_assign>  ("R_do_slot_assign");
    R_getClassDef                = GetProc<FnR_getClassDef>     ("R_getClassDef");
    R_MakeExternalPtr            = GetProc<FnR_MakeExternalPtr> ("R_MakeExternalPtr");
    R_RegisterCFinalizerEx       = GetProc<FnR_RegisterCFinalizerEx>("R_RegisterCFinalizerEx");
    R_ExternalPtrAddr            = GetProc<FnR_ExternalPtrAddr> ("R_ExternalPtrAddr");

    // ── Routine registration ─────────────────────────────────────────────────
    R_getEmbeddingDllInfo        = GetProc<FnR_getEmbeddingDllInfo>("R_getEmbeddingDllInfo");
    R_registerRoutines           = GetProc<FnR_registerRoutines>   ("R_registerRoutines");
    R_RegisterCCallable          = GetProc<FnR_RegisterCCallable>  ("R_RegisterCCallable");

    // ── Version detection ────────────────────────────────────────────────────
    ParseVersion();
    CHILD_LOG("REngineLoader: R version %d.%d.%d loaded from '%s'",
              ver_major_, ver_minor_, ver_patch_, dll_path.c_str());

    // ── Validate required functions ──────────────────────────────────────────
    if (!ValidateRequired()) {
        CHILD_LOG_ERR("REngineLoader: required functions missing — cannot start ControlR");
        FreeLibrary(hR_);
        hR_ = nullptr;
        return false;
    }

    CHILD_LOG("REngineLoader: all required symbols resolved OK");
    return true;
}

// ─── Unload ───────────────────────────────────────────────────────────────────

void REngineLoader::Unload() {
    if (hR_) {
        FreeLibrary(hR_);
        hR_ = nullptr;
        CHILD_LOG("REngineLoader: R.dll unloaded");
    }
}
