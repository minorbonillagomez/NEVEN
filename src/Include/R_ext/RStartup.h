#ifndef R_EXT_RSTARTUP_H
#define R_EXT_RSTARTUP_H

#include <Rinternals.h>

#ifdef __cplusplus
extern "C" {
#endif

// Windows specific startup params
typedef enum {
    RTerm,
    RGui,
    LinkDLL
} R_AppType;

typedef int SA_TYPE; // Changed to int to avoid cast errors on Windows
#define SA_NOSAVE 0
#define SA_SAVE 1
#define SA_SAVEASK 2
#define SA_SUICIDE 3
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
    int CharacterMode; 
    int ShowMessage2; 
} structRstart, *Rstart, *R_StartParams;

void R_setStartTime(void);
void R_DefParams(R_StartParams);
void R_SetParams(R_StartParams);
void R_set_command_line_arguments(int argc, char **argv);

// Misc Windows
void GA_initapp(int, char **);
void readconsolecfg(void);
const char *getDLLVersion(void);
extern int UserBreak;

// Routine registration symbols Often needed
typedef struct {
    const char *name;
    void* fun; 
    int numArgs;
} R_CallMethodDef;

typedef void* DllInfo;
DllInfo *R_getEmbeddingDllInfo(void);
void R_registerRoutines(DllInfo *info, void *cMethods, R_CallMethodDef *callMethods, void *fortranMethods, void *externalMethods);
void R_RegisterCCallable(const char *pkg, const char *name, void* f);

// Embedded R
void Rf_endEmbeddedR(int);
void setup_Rmainloop(void);
void run_Rmainloop(void);

#ifdef __cplusplus
}
#endif

#endif
