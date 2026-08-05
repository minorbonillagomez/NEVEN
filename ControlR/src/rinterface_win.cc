/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "controlr.h"
#include "controlr_common.h"
#include "r_version_compat.h"
#include "convert.h"
#include "child_process_log.h"
#include <cstdio>

/**
 * R_ReadConsole — the actual implementation forwarded to by both
 * ReadConsole_OldSignature and ReadConsole_NewSignature in r_version_compat.cc.
 *
 * In v2.4 this function is no longer registered directly in structRstart.
 * Instead, RVersionCompat::ApplyReadConsoleCallback() selects the correct
 * wrapper (old/new signature) at runtime and stores it in Rp->ReadConsole.
 * Both wrappers ultimately call InputStreamRead(), defined in controlr.cc.
 *
 * The function below is kept as a named callback for backward compatibility
 * with any code that calls it by name (e.g. unit tests).
 */
int R_ReadConsole(const char *prompt, unsigned char *buf, int len, int addtohistory) {

  // every time?
  const char *cprompt = R_CHAR(STRING_ELT(GetOption1(install("continue")), 0));
  bool is_continuation = (!strcmp(cprompt, prompt));

  return InputStreamRead(prompt, buf, len, addtohistory, is_continuation);
}


/**
 * console messages are passed through.  note the signature is different on
 * windows/linux so implementation is platform dependent.
 */
void R_WriteConsoleEx(const char *buf, int len, int flag) {

  // I cannot figure out how to get R to output UTF8 when it has windows cp 
  // strings. it just seems to ignore all the things I set. temporarily let's
  // do this the hard way.

  if (ValidUTF8(buf, len)) {
    return ConsoleMessage(buf, len, flag);
  }

  char *string;
  int length;

  WindowsCPToUTF8(buf, len, &string, &length);
  ConsoleMessage(string, length, flag);

}

/**
 * "ask ok" has no return value.  I guess that means "ask, then press OK",
 * not "ask if this is ok".
 *
 * NOTE: Will integrate with console client when REPL is re-enabled.
 */
void R_AskOk(const char *info) {
  ::MessageBoxA(0, info, "Message from R", MB_OK);
}

/**
 * 1 (yes) or -1 (no), I believe (based on #defines)
 *
 * NOTE: Will integrate with console client when REPL is re-enabled.
 */
int R_AskYesNoCancel(const char *question) {
  return (IDYES == ::MessageBoxA(0, question, "Message from R", MB_YESNOCANCEL)) ? 1 : -1;
}

/** function pointer cannot be null */
void R_CallBack(void) {}

/** function pointer cannot be null */
void R_Busy(int which) {}

/**
 * break; on windows this is polled
 */
void RSetUserBreak(const char *msg) {

  // Synchronization note: UserBreak is set from ManagementThread and read
  // from R's main thread. Atomic would be ideal but R defines it as int.
  // In practice, single-word writes are atomic on x86/x64.

  // r-set-user-break (logged to file, not stdout)

  UserBreak = 1;

  //if( msg ) ConsoleMessage( msg, 0, 1 );
  //else ConsoleMessage("user break", 0, 1);

}

/** call periodically to handle queued events / window messages */
void RTick() {
  R_ProcessEvents();
}

/**
 * returns version as reported by the loaded R library
 * v2.4: delegates to REngineLoader (resolved at runtime)
 */
void RGetVersion(int32_t *major, int32_t *minor, int32_t *patch) {

  *major = REngineLoader::VersionMajor();
  *minor = REngineLoader::VersionMinor();
  // patch: parse from getDLLVersion if available
  *patch = 0;
  if (REngineLoader::getDLLVersion) {
    const char *version = REngineLoader::getDLLVersion();
    if (version) {
      int dots = 0;
      char buf[16] = {};
      int idx = 0;
      for (const char *p = version; *p; ++p) {
        if (*p == '.') { dots++; idx = 0; continue; }
        if (dots == 2 && idx < 15) buf[idx++] = *p;
      }
      if (idx > 0) *patch = atoi(buf);
    }
  }

}

/**
 * runs the main R loop; the rest of the code interacts via callbacks
 */
int RLoop(const char *rhome, const char *ruser, int argc, char ** argv) {

  // v2.4: R.dll was already loaded in main() before version check.
  // Validate it's still loaded (defensive check).
  if (!REngineLoader::IsLoaded()) {
    CHILD_LOG_ERR("RLoop: REngineLoader not loaded — call Load() before RLoop()");
    return -1;
  }

  REngineRstart Rp = new REngineStartParams;
  CHILD_LOG("structRstart allocated");

  char *local_rhome = new char[MAX_PATH];
  if(rhome) strcpy_s(local_rhome, MAX_PATH, rhome);
  else local_rhome[0] = 0;

  char *local_ruser = new char[MAX_PATH];
  if(ruser) strcpy_s(local_ruser, MAX_PATH, ruser);
  else local_ruser[0] = 0;

  R_setStartTime();
  CHILD_LOG("R_setStartTime done");
  R_DefParams(Rp);
  CHILD_LOG("R_DefParams done");

  Rp->rhome = local_rhome;
  Rp->home = local_ruser;

  // typedef enum {RGui, RTerm, LinkDLL} UImode;
  Rp->CharacterMode = LinkDLL;  // No GUI needed — we handle I/O via pipes
  Rp->R_Interactive = TRUE;

  // v2.4: select the correct ReadConsole signature for this R version
  RVersionCompat::ApplyReadConsoleCallback(Rp);
  Rp->WriteConsole = NULL;
  Rp->WriteConsoleEx = R_WriteConsoleEx;

  Rp->Busy = R_Busy;
  Rp->CallBack = R_CallBack;
  Rp->ShowMessage = R_AskOk;
  Rp->YesNoCancel = R_AskYesNoCancel;

  // we can handle these in code, more flexible
  Rp->RestoreAction = SA_NORESTORE;
  Rp->SaveAction = SA_NOSAVE;

  R_SetParams(Rp);
  CHILD_LOG("R_SetParams done");
  R_set_command_line_arguments(argc, argv);
  CHILD_LOG("R_set_command_line_arguments done");
  FlushConsoleInputBuffer(GetStdHandle(STD_INPUT_HANDLE));
  CHILD_LOG("FlushConsoleInputBuffer done");
  GA_initapp(0, 0);
  CHILD_LOG("GA_initapp done");
  readconsolecfg();
  CHILD_LOG("readconsolecfg done");

  // call setup separately so we can install functions
  CHILD_LOG("setup_Rmainloop start");
  setup_Rmainloop();
  CHILD_LOG("setup_Rmainloop done");

  // Install R callbacks — static array required by R API
  static REngineCallMethodDef methods[] = {
    { "RJ2XCL.Callback", (void*)&RCallback, 2 },
    { "RJ2XCL.COMCallback", (void*)&COMCallback, 5 },
    { 0, 0, 0 }
  };
  R_registerRoutines(R_getEmbeddingDllInfo(), NULL, methods, NULL, NULL);

  // Register as C-callable for COM interop
  R_RegisterCCallable("RJ2XCLControlR", "Callback", (void*)RCallback);
  R_RegisterCCallable("RJ2XCLControlR", "COMCallback", (void*)COMCallback);

  // now run the loop
  CHILD_LOG("run_Rmainloop start");
  run_Rmainloop();
  CHILD_LOG("run_Rmainloop returned!");

  // clean up
  delete[] local_ruser;
  delete[] local_rhome;

  delete Rp;

  Rf_endEmbeddedR(0);
  REngineLoader::Unload();

  return 0;

}
