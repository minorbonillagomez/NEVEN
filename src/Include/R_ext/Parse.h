#ifndef R_EXT_PARSE_H
#define R_EXT_PARSE_H

#ifndef SEXP_DEFINED
#define SEXP_DEFINED
typedef struct _SEXP *SEXP;
#endif

typedef enum {
    PARSE_NULL,
    PARSE_OK,
    PARSE_INCOMPLETE,
    PARSE_ERROR,
    PARSE_EOF
} ParseStatus;

#ifdef __cplusplus
extern "C" {
#endif

SEXP Rf_R_ParseVector(SEXP, int, ParseStatus *, SEXP);

#ifdef __cplusplus
}
#endif

#endif
