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
#include "convert.h"
#include "child_process_log.h"
#include <cstdio>












/**
 * we're now basing "exec" commands on the standard repl; otherwise
 * we have to have two parallel paths for exec and debug.
 */
int R_ReadConsole(const char *prompt, unsigned char *buf, int len, int addtohistory) {

  // Note: Continuation prompt detection disabled — GetOption1("continue") inside
  // R_ReadConsole callback causes crash in R.dll (offset 0x11b111) on some R 4.4.x
  // builds. The is_continuation feature is cosmetic only (affects console display).
  bool is_continuation = false;

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

/** read a number from a version string (e.g. 3.4.1) */
int PartialVersion(const char **ptr) {

  char buffer[32];
  memset(buffer, 0, 32);

  for (int i = 0; i < 32; i++, (*ptr)++) {
    char c = **ptr;
    if (!c || c == '.') break;
    buffer[i] = c;
  }

  return atoi(buffer);
}


void RGetVersion(int32_t *major, int32_t *minor, int32_t *patch) {

  *major = *minor = *patch = 0;

  const char *version = getDLLVersion();
  if (!version) return;

  if (*version) *major = PartialVersion(&version);
  if (*version && *(++version)) *minor = PartialVersion(&version);
  if (*version && *(++version)) *patch = PartialVersion(&version);

}
