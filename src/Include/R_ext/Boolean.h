#ifndef R_EXT_BOOLEAN_H
#define R_EXT_BOOLEAN_H

#ifndef __cplusplus
#ifndef bool
typedef int bool;
#define false 0
#define true 1
#endif
#endif

typedef int Rboolean;
#ifndef FALSE
#define FALSE 0
#endif
#ifndef TRUE
#define TRUE 1
#endif

#endif
