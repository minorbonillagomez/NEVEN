/*
 * MSVC-compatible Rcomplex for R 4.4.1
 * Uses the same include guard as R's Complex.h so it won't be included twice.
 */
#ifndef R_COMPLEX_H
#define R_COMPLEX_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    double r;
    double i;
} Rcomplex;

#ifdef __cplusplus
}
#endif

#endif /* R_COMPLEX_H */
