/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * r_version_compat.cc — NEVEN v2.4 Runtime Version Compatibility
 *
 * Handles the R C API functions that changed signatures between versions:
 *
 *   R_ReadConsole
 *     R < 4.4  :  int (*ReadConsole)(const char*, char*, int, int)
 *     R >= 4.4 :  int (*ReadConsole)(const char*, unsigned char*, int, int)
 *
 * Strategy: define two wrapper callbacks with the correct signatures.
 * RVersionCompat::ApplyReadConsoleCallback() picks the right one based on
 * the version reported by REngineLoader and stores it in the REngineRstart
 * struct's ReadConsole field.
 *
 * CharacterMode / structRstart stability notes:
 *   - structRstart gained no new required fields between R 4.1 and R 4.6.
 *     Our REngineRstart mirrors the current stable layout; no runtime adaptation
 *     is needed beyond the ReadConsole signature.
 *   - LinkDLL (value = 2 in UImode enum) is stable since R 3.x.  We store it
 *     as plain int in REngineRstart to avoid depending on the enum definition.
 */

#include "r_version_compat.h"
#include "r_api_shim_clean.h"
#include "child_process_log.h"

// ─── Forward declaration of the actual read-console logic ────────────────────
// Defined in rinterface_win.cc (unchanged from v2.3).
int InputStreamRead(const char *prompt, unsigned char *buf, int len,
                    int addtohistory, bool is_continuation);

// ─── R < 4.4 callback  (buf is char*) ────────────────────────────────────────
// The R < 4.4 ReadConsole signature uses a plain char* for the buffer.
// We cast to unsigned char* and forward to our unified implementation.
static int ReadConsole_OldSignature(const char *prompt, char *buf, int len, int addtohistory) {
    // Determine continuation prompt the same way rinterface_win.cc does
    const char *cprompt = R_CHAR(REngineLoader::STRING_ELT(
        REngineLoader::Rf_GetOption1(REngineLoader::Rf_install("continue")), 0));
    bool is_continuation = (cprompt && strcmp(cprompt, prompt) == 0);
    return InputStreamRead(prompt, reinterpret_cast<unsigned char*>(buf),
                           len, addtohistory, is_continuation);
}

// ─── R >= 4.4 callback (buf is unsigned char*) ───────────────────────────────
// Matches the new signature; our InputStreamRead already uses unsigned char*.
static int ReadConsole_NewSignature(const char *prompt, unsigned char *buf, int len, int addtohistory) {
    const char *cprompt = R_CHAR(REngineLoader::STRING_ELT(
        REngineLoader::Rf_GetOption1(REngineLoader::Rf_install("continue")), 0));
    bool is_continuation = (cprompt && strcmp(cprompt, prompt) == 0);
    return InputStreamRead(prompt, buf, len, addtohistory, is_continuation);
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * @brief Assign the correct ReadConsole callback to the Rstart struct.
 *
 * Must be called after REngineLoader::Load() has resolved the version.
 * The ReadConsole field in REngineRstart is declared as void* to accept
 * either signature; it is cast to the appropriate function pointer type
 * when stored.
 *
 * @param Rp  Pointer to the REngineRstart struct to configure.
 */
void RVersionCompat::ApplyReadConsoleCallback(REngineRstart Rp) {
    int major = REngineLoader::VersionMajor();
    int minor = REngineLoader::VersionMinor();

    if (major > 4 || (major == 4 && minor >= 4)) {
        // R >= 4.4 — unsigned char* signature
        CHILD_LOG("RVersionCompat: R %d.%d — using ReadConsole_NewSignature (unsigned char*)",
                  major, minor);
        Rp->ReadConsole = reinterpret_cast<void*>(ReadConsole_NewSignature);
    } else {
        // R < 4.4 — char* signature
        CHILD_LOG("RVersionCompat: R %d.%d — using ReadConsole_OldSignature (char*)",
                  major, minor);
        Rp->ReadConsole = reinterpret_cast<void*>(ReadConsole_OldSignature);
    }
}

/**
 * @brief Validate that the fields used by NEVEN are present in structRstart.
 *
 * NEVEN uses: rhome, home, ReadConsole, WriteConsoleEx, Busy, CallBack,
 * ShowMessage, YesNoCancel, RestoreAction, SaveAction, R_Interactive,
 * CharacterMode.
 *
 * The layout has been stable across R 4.1–4.6; this function is a no-op
 * stub for future proofing — add a check here if R ever restructures the
 * startup struct.
 *
 * @return true always (currently).
 */
bool RVersionCompat::ValidateStartupStruct() {
    // No structural check needed for R 4.x–4.6.x at this time.
    // If R 5.x introduces incompatible structRstart changes, detect here
    // using REngineLoader::VersionMajor() and adapt accordingly.
    CHILD_LOG("RVersionCompat::ValidateStartupStruct — OK (R %d.%d)",
              REngineLoader::VersionMajor(), REngineLoader::VersionMinor());
    return true;
}
