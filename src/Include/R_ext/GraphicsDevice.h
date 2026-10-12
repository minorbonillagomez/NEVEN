#ifndef R_EXT_GRAPHICSDEVICE_H
#define R_EXT_GRAPHICSDEVICE_H

#include <R_ext/Boolean.h>
#include <Rinternals.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _DevDesc *pDevDesc;
typedef struct _R_GE_gcontext *pGEcontext;

typedef struct _DevDesc {
    int startfill;
    int startcol;
    double startps;
    int startlty;
    int startfont;
    double startgamma;
    Rboolean wantSymbolUTF8;
    Rboolean hasTextUTF8;
    double left, top, right, bottom;
    double cra[2];
    double xCharOffset, yCharOffset, yLineBias;
    double ipr[2];
    Rboolean canClip;
    int canHAdj;
    Rboolean canChangeGamma;
    Rboolean displayListOn;
    int haveTransparency;
    int haveTransparentBg;
    int haveRaster;
    void *deviceSpecific;

    // Callbacks
    void (*newPage)(const pGEcontext, pDevDesc);
    void (*close)(pDevDesc);
    void (*line)(double, double, double, double, const pGEcontext, pDevDesc);
    void (*rect)(double, double, double, double, const pGEcontext, pDevDesc);
    void (*circle)(double, double, double, const pGEcontext, pDevDesc);
    void (*clip)(double, double, double, double, pDevDesc);
    void (*size)(double *, double *, double *, double *, pDevDesc);
    void (*metricInfo)(int, const pGEcontext, double *, double *, double *, pDevDesc);
    double (*strWidth)(const char *, const pGEcontext, pDevDesc);
    void (*text)(double, double, const char *, double, double, const pGEcontext, pDevDesc);
    void (*polygon)(int, double *, double *, const pGEcontext, pDevDesc);
    void (*polyline)(int, double *, double *, const pGEcontext, pDevDesc);
    void (*path)(double *, double *, int, int *, Rboolean, const pGEcontext, pDevDesc);
    void (*raster)(unsigned int *, int, int, double, double, double, double, double, Rboolean, const pGEcontext, pDevDesc);
    void (*textUTF8)(double, double, const char *, double, double, const pGEcontext, pDevDesc);
    double (*strWidthUTF8)(const char *, const pGEcontext, pDevDesc);
} DevDesc;

#ifdef __cplusplus
}
#endif

#endif
