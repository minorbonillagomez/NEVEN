/*
 * r_ge_stubs.cc -- NEVEN v2.4
 *
 * GE function stubs. Contains pure C code despite the .cc extension.
 * Compiled as C via CompileAs=CompileAsC in the vcxproj (set by /TC in CMakeLists).
 * For full rebuilds (--clean-first): always produces C linkage symbols.
 * For incremental builds: use build_controlr.ps1 to pre-compile this file.
 *
 * Functions resolve lazily from R.dll via GetProcAddress on first call.
 */

#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#include <stddef.h>

typedef struct _DevDesc*   pDevDesc;
typedef struct _GEDevDesc* pGEDevDesc;
typedef struct _SEXP*      SEXP;

static HMODULE get_R_dll(void) {
    return GetModuleHandleA("R.dll");
}

#define RESOLVE(name, sig) \
    static sig fn = NULL; \
    if (!fn) { HMODULE h = get_R_dll(); if (h) fn = (sig)GetProcAddress(h, #name); }

int GEdeviceNumber(pGEDevDesc gd) {
    typedef int (*Fn)(pGEDevDesc);
    RESOLVE(GEdeviceNumber, Fn)
    return fn ? fn(gd) : -1;
}

void GEaddDevice2(pGEDevDesc gd, const char *name) {
    typedef void (*Fn)(pGEDevDesc, const char*);
    RESOLVE(GEaddDevice2, Fn)
    if (fn) fn(gd, name);
}

void GEinitDisplayList(pGEDevDesc gd) {
    typedef void (*Fn)(pGEDevDesc);
    RESOLVE(GEinitDisplayList, Fn)
    if (fn) fn(gd);
}

int R_GE_str2col(const char *s) {
    typedef int (*Fn)(const char*);
    RESOLVE(R_GE_str2col, Fn)
    return fn ? fn(s) : 0;
}

size_t Rf_ucstoutf8(char *s, const unsigned int c) {
    typedef size_t (*Fn)(char*, unsigned int);
    RESOLVE(Rf_ucstoutf8, Fn)
    return fn ? fn(s, c) : 0;
}

pGEDevDesc GEcreateDevDesc(pDevDesc dev) {
    typedef pGEDevDesc (*Fn)(pDevDesc);
    RESOLVE(GEcreateDevDesc, Fn)
    return fn ? fn(dev) : NULL;
}

pGEDevDesc GEgetDevice(int devNum) {
    typedef pGEDevDesc (*Fn)(int);
    RESOLVE(GEgetDevice, Fn)
    return fn ? fn(devNum) : NULL;
}

void GEkillDevice(pGEDevDesc gd) {
    typedef void (*Fn)(pGEDevDesc);
    RESOLVE(GEkillDevice, Fn)
    if (fn) fn(gd);
}

SEXP Rf_ScalarInteger(int v) {
    typedef SEXP (*Fn)(int);
    RESOLVE(Rf_ScalarInteger, Fn)
    return fn ? fn(v) : NULL;
}
