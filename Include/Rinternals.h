#pragma once

#ifndef RINTERNALS_H
#define RINTERNALS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Essential R types - MUST BE FIRST
#ifndef SEXP_DEFINED
#define SEXP_DEFINED
typedef struct _SEXP *SEXP;
#endif

#ifdef __cplusplus
}
#endif

// Now safe to include sub-headers
#include "R_ext/Boolean.h"
#include "R_ext/Parse.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifndef R_COMPLEX_DEFINED
#define R_COMPLEX_DEFINED
typedef struct { double r, i; } Rcomplex;
#endif

// R Constants
#define NA_INTEGER (-2147483648)
#define NA_LOGICAL (-2147483648)
extern __declspec(dllimport) double R_NaReal;
#define NA_REAL R_NaReal
extern __declspec(dllimport) SEXP R_NaString;
#define NA_STRING R_NaString

#define R_NilValue ((SEXP)0)
extern __declspec(dllimport) SEXP R_GlobalEnv;
extern __declspec(dllimport) SEXP R_NamesSymbol;
extern __declspec(dllimport) SEXP R_DimNamesSymbol;
extern __declspec(dllimport) SEXP R_LevelsSymbol;
extern __declspec(dllimport) SEXP R_RowNamesSymbol;

#define NILSXP    0
#define SYMSXP    1
#define LISTSXP   2
#define CLOSXP    3
#define ENVSXP    4
#define PROMSXP   5
#define LANGSXP   6
#define SPECIALSXP 7
#define BUILTINSXP 8
#define CHARSXP    9
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

typedef enum {
    CE_NATIVE = 0,
    CE_UTF8 = 1,
    CE_LATIN1 = 2,
    CE_SYMBOL = 3,
    CE_ANY = 4
} cetype_t;

// R Functions
SEXP Rf_allocVector(uint32_t type, intptr_t length);
SEXP Rf_allocMatrix(uint32_t type, int rows, int cols);
SEXP Rf_install(const char *name);
#define install Rf_install
SEXP Rf_lang1(SEXP s1);
SEXP Rf_lang2(SEXP s1, SEXP s2);
SEXP Rf_lang3(SEXP s1, SEXP s2, SEXP s3);
SEXP Rf_eval(SEXP call, SEXP env);
SEXP Rf_mkCharCE(const char *str, cetype_t encoding);
#define mkCharCE Rf_mkCharCE
SEXP Rf_ScalarReal(double v);
#define ScalarReal Rf_ScalarReal
SEXP Rf_ScalarInteger(int v);
#define ScalarInteger Rf_ScalarInteger
SEXP Rf_ScalarLogical(int v);
#define ScalarLogical Rf_ScalarLogical
SEXP Rf_ScalarComplex(Rcomplex v);
#define ScalarComplex Rf_ScalarComplex

SEXP Rf_protect(SEXP s);
void Rf_unprotect(int n);
int Rf_asInteger(SEXP s);
double Rf_asReal(SEXP s);
int Rf_asLogical(SEXP s);
const char *Rf_translateCharUTF8(SEXP s);
#define translateCharUTF8 Rf_translateCharUTF8
#define R_CHAR(x) ((const char*)(x))

int Rf_isLogical(SEXP s);
int Rf_isInteger(SEXP s);
int Rf_isReal(SEXP s);
int Rf_isNumber(SEXP s);
int Rf_isString(SEXP s);
int Rf_isComplex(SEXP s);
int Rf_isNull(SEXP s);
int Rf_isEnvironment(SEXP s);
int Rf_isFrame(SEXP s);
int Rf_isMatrix(SEXP s);
int Rf_isFactor(SEXP s);
int Rf_inherits(SEXP s, const char *cls);

#define isReal Rf_isReal
#define isString Rf_isString

int Rf_nrows(SEXP s);
int Rf_ncols(SEXP s);
intptr_t Rf_length(SEXP s);

typedef void (*R_CFinalizer_t)(SEXP);
SEXP R_MakeExternalPtr(void *p, SEXP tag, SEXP prot);
void R_RegisterCFinalizerEx(SEXP s, R_CFinalizer_t f, int onexit);
void *R_ExternalPtrAddr(SEXP s);

SEXP R_do_new_object(SEXP cls);
SEXP R_do_slot(SEXP obj, SEXP name);
void R_do_slot_assign(SEXP obj, SEXP name, SEXP value);
SEXP R_getClassDef(const char *cls);

SEXP Rf_list2(SEXP s1, SEXP s2);
SEXP Rf_mkString(const char *str);
SEXP Rf_mkChar(const char *str);
SEXP R_tryEvalSilent(SEXP call, SEXP env, int *err);
SEXP R_tryEval(SEXP call, SEXP env, int *err);
#define GetOption1 Rf_GetOption1
SEXP Rf_GetOption1(SEXP name);
#define getAttrib Rf_getAttrib
static inline int IsNA(double v) { 
    union { double d; int i[2]; } u;
    u.d = v;
    return (u.i[1] == 0x7ff00000 && u.i[0] == 1954);
}
#define ISNA(v) IsNA(v)
SEXP Rf_getAttrib(SEXP x, SEXP symbol);
SEXP SET_VECTOR_ELT(SEXP x, int i, SEXP v);
SEXP VECTOR_ELT(SEXP x, int i);
SEXP STRING_ELT(SEXP x, int i);
SEXP SET_STRING_ELT(SEXP x, int i, SEXP v);
void Rf_setAttrib(SEXP x, SEXP symbol, SEXP value);
void Rf_error(const char *fmt, ...);
SEXP R_ParseVector(SEXP text, int n, ParseStatus *status, SEXP src);

#define PROTECT(x) Rf_protect(x)
#define UNPROTECT(n) Rf_unprotect(n)

int *INTEGER(SEXP x);
double *REAL(SEXP x);
int *LOGICAL(SEXP x);
Rcomplex *COMPLEX(SEXP x);
int TYPEOF(SEXP x);

SEXP Rf_asChar(SEXP x);

#ifdef __cplusplus
}
#endif

#endif
