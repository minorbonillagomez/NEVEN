#include "XLCALL.h"

int pascal Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) {
    return xlretSuccess;
}

int pascal Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]) {
    return xlretSuccess;
}
