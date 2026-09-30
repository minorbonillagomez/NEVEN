#ifndef R_EXT_GRAPHICSENGINE_H
#define R_EXT_GRAPHICSENGINE_H

#include <Rinternals.h>
#include <R_ext/GraphicsDevice.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _R_GE_gcontext {
    int col;
    int fill;
    double gamma;
    double lwd;
    int lty;
    int lend;
    int ljoin;
    double lmitre;
    double cex;
    double ps;
    double lineheight;
    int fontface;
    char fontfamily[201];
    SEXP patternFill;
} R_GE_gcontext;

typedef struct _GEDevDesc {
    pDevDesc dev;
    Rboolean displayListOn;
    void *gesd[24]; // MAX_GRAPHICS_SYSTEMS
} GEDevDesc, *pGEDevDesc;

void GEaddDevice2(pGEDevDesc, const char *);
void GEinitDisplayList(pGEDevDesc);
int GEdeviceNumber(pGEDevDesc);

int R_GE_str2col(const char *);
#define R_RGB(r,g,b) ((r)|((g)<<8)|((b)<<16)|0xFF000000)

size_t Rf_ucstoutf8(char *s, const unsigned int c);

#ifdef __cplusplus
}
#endif

#endif
