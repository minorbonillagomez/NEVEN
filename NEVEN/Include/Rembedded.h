#ifndef REMBEDDED_H
#define REMBEDDED_H

#include <Rinternals.h>

#ifdef __cplusplus
extern "C" {
#endif

int Rf_initEmbeddedR(int argc, char **argv);
void Rf_endEmbeddedR(int fatal);

#ifdef __cplusplus
}
#endif

#endif
