#ifndef R_EXT_COMPLEX_H
#define R_EXT_COMPLEX_H

/* R 4.4.1 compatible Rcomplex for MSVC */
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

#endif /* R_EXT_COMPLEX_H */
