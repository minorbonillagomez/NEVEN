/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * rinterface_loop.cc -- NEVEN v2.4 Dynamic Engine Loading
 *
 * Implements RLoop() using the dynamic loader (r_engine_loader.h).
 * This file does NOT include controlr_common.h to avoid structRstart conflict.
 */

#include "controlr.h"
#include "r_engine_loader.h"
#include "child_process_log.h"
#include <windows.h>
#include <cstdio>
#include <cstring>

// Forward declarations of callbacks (defined in rinterface_win.cc + rinterface_common.cc)
int  R_ReadConsole(const char *prompt, unsigned char *buf, int len, int addtohistory);
void R_WriteConsoleEx(const char *buf, int len, int flag);
void R_AskOk(const char *info);
int  R_AskYesNoCancel(const char *question);
void R_CallBack(void);
void R_Busy(int which);
// RCallback/COMCallback: use SEXPREC (the canonical R type) to match the implementation
// in rinterface_common.cc which includes the real R headers.
struct SEXPREC;
typedef SEXPREC* SEXP_REAL;
SEXP_REAL RCallback(SEXP_REAL, SEXP_REAL);
SEXP_REAL COMCallback(SEXP_REAL, SEXP_REAL, SEXP_REAL, SEXP_REAL, SEXP_REAL);

/**
 * runs the main R loop; the rest of the code interacts via callbacks
 */
int RLoop(const char *rhome, const char *ruser, int argc, char ** argv) {

  if (!REngineLoader::IsLoaded()) {
    CHILD_LOG_ERR("RLoop: REngineLoader not loaded");
    return -1;
  }

  REngineStartParams* Rp = new REngineStartParams();
  CHILD_LOG("structRstart allocated -- sizeof=%zu", sizeof(REngineStartParams));

  char *local_rhome = new char[MAX_PATH];
  if(rhome) strcpy_s(local_rhome, MAX_PATH, rhome);
  else local_rhome[0] = 0;

  char *local_ruser = new char[MAX_PATH];
  if(ruser) strcpy_s(local_ruser, MAX_PATH, ruser);
  else local_ruser[0] = 0;

  REngineLoader::R_setStartTime();

  if (REngineLoader::R_DefParamsEx) {
      REngineLoader::R_DefParamsEx(Rp, 1);
  } else {
      REngineLoader::R_DefParams(Rp);
  }

  Rp->rhome = local_rhome;
  Rp->home  = local_ruser;
  Rp->CharacterMode = LinkDLL;
  Rp->R_Interactive = 1;

  Rp->ReadConsole   = reinterpret_cast<int(*)(const char*, unsigned char*, int, int)>(R_ReadConsole);
  Rp->WriteConsole  = nullptr;
  Rp->WriteConsoleEx = reinterpret_cast<void(*)(const char*, int, int)>(R_WriteConsoleEx);
  Rp->Busy          = reinterpret_cast<void(*)(int)>(R_Busy);
  Rp->CallBack      = reinterpret_cast<void(*)(void)>(R_CallBack);
  Rp->ShowMessage   = reinterpret_cast<void(*)(const char*)>(R_AskOk);
  Rp->YesNoCancel   = reinterpret_cast<int(*)(const char*)>(R_AskYesNoCancel);
  Rp->RestoreAction = SA_NORESTORE;
  Rp->SaveAction    = SA_NOSAVE;

  REngineLoader::R_SetParams(Rp);
  REngineLoader::R_set_command_line_arguments(argc, argv);
  FlushConsoleInputBuffer(GetStdHandle(STD_INPUT_HANDLE));

  if (REngineLoader::GA_initapp) REngineLoader::GA_initapp(0, 0);
  if (REngineLoader::readconsolecfg) REngineLoader::readconsolecfg();

  REngineLoader::setup_Rmainloop();

  // Register C-callables for COM interop (no method table needed for this path)
  REngineLoader::R_RegisterCCallable("RJ2XCLControlR", "Callback",    reinterpret_cast<void*>(RCallback));
  REngineLoader::R_RegisterCCallable("RJ2XCLControlR", "COMCallback", reinterpret_cast<void*>(COMCallback));

  REngineLoader::run_Rmainloop();

  delete[] local_ruser;
  delete[] local_rhome;
  delete Rp;

  REngineLoader::Rf_endEmbeddedR(0);
  return 0;
}
