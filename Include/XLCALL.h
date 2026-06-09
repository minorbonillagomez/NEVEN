#ifndef XLCALL_H
#define XLCALL_H

#include <windows.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef wchar_t XCHAR;
typedef XCHAR* LPXSTR;

typedef struct xlref12 {
    int rwFirst;
    int rwLast;
    int colFirst;
    int colLast;
} XLREF12, *LPXLREF12;

typedef struct xlmref12 {
    int count;
    XLREF12 reftbl[1];
} XLMREF12, *LPXLMREF12;

// xloper12 Structure
typedef struct xloper12 {
    union {
        double num;
        XCHAR* str;
        int xbool;
        int err;
        int w;
        struct {
            struct xloper12* lparray;
            int rows;
            int columns;
        } array;
        struct {
            int ID;
            XLREF12 ref;
            int count; // Added count for SRef
        } sref;
        struct {
            XLMREF12* lpmref;
            uint64_t idSheet; // Added idSheet for Ref
        } mref;
    } val;
    unsigned int xltype;
} XLOPER12, *LPXLOPER12;

// Types
#define xltypeNum 0x0001
#define xltypeStr 0x0002
#define xltypeBool 0x0004
#define xltypeErr 0x0010
#define xltypeMulti 0x0040
#define xltypeMissing 0x0080
#define xltypeNil 0x0100
#define xltypeSRef 0x0400
#define xltypeRef 0x0800
#define xltypeInt 0x2000

// Memory flags
#define xlbitXLFree 0x1000
#define xlbitDLLFree 0x4000

// Return codes
#define xlretSuccess 0
#define xlretAbort 1
#define xlretInvXloper 2

// Error codes
#define xlerrNull 0
#define xlerrDiv0 7
#define xlerrValue 15
#define xlerrRef 23
#define xlerrName 29
#define xlerrNum 36
#define xlerrNA 42

// Function codes
#define xlfRegister     149
#define xlfUnregister   201
#define xlfCaller       89

// xl-prefixed functions (high bit set = 0x4000)
#define xlFree          (0 | 0x4000)
#define xlCoerce        (2 | 0x4000)
#define xlGetName       (0x19 | 0x4000)
#define xlcFree         0

// Additional function codes for timer and utility
#define xlfNow          74
#define xlcOnTime        32550

// Calling Functions
int pascal Excel12(int xlfn, LPXLOPER12 operRes, int count, ...);
int pascal Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]);

#ifdef __cplusplus
}
#endif

#endif // XLCALL_H
