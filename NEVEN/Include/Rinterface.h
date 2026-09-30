#ifndef RINTERFACE_H
#define RINTERFACE_H

#include <Rinternals.h>

#ifdef __cplusplus
extern "C" {
#endif

extern int R_interactive;

// Windows specific startup params
typedef enum {
    RTerm,
    RGui
} R_AppType;

typedef enum {
    SA_NOSAVE,
    SA_SAVE,
    SA_SAVEASK,
    SA_SUICIDE
} SA_TYPE;

#define SA_NORESTORE 0x10

typedef struct {
    char *rhome;
    char *home;
    int (*ReadConsole)(const char *, char *, int, int);
    void (*WriteConsole)(const char *, int);
    void (*WriteConsoleEx)(const char *, int, int);
    void (*Busy)(int);
    void (*CallBack)(void);
    void (*ShowMessage)(const char *);
    int (*YesNoCancel)(const char *);
    SA_TYPE RestoreAction;
    SA_TYPE SaveAction;
    R_AppType R_Quiet;
    int R_Interactive;
    int R_Verbose;
    int R_LoadSiteFile;
    int R_LoadProfile;
    int R_NoRenviron;
    int R_NoHistory;
    int R_RestoreHistory;
    int R_SaveHistory;
    SA_TYPE CharacterMode;
    int ShowMessage2; // dummy to avoid conflict with ShowMessage function
} structRstart, *Rstart, *R_StartParams;

void R_DefParams(R_StartParams);
void R_SetParams(R_StartParams);
void R_set_command_line_arguments(int argc, char **argv);

// Routine registration
typedef struct {
    const char *name;
    DL_FUNC fun;
    int numArgs;
} R_CallMethodDef;

typedef void* DllInfo;
DllInfo *R_getEmbeddingDllInfo(void);
void R_registerRoutines(DllInfo *info, void *cMethods, R_CallMethodDef *callMethods, void *fortranMethods, void *externalMethods);
void R_RegisterCCallable(const char *pkg, const char *name, DL_FUNC f);

// Misc Windows
void GA_initapp(int, char **);
void readconsolecfg(void);

#ifdef __cplusplus
}
#endif

#endif
