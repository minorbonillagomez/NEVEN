/**
 * rcall_seh.cc - SEH wrapper stubs for ControlR (NEVEN v2.4)
 *
 * This translation unit is compiled with /Od /GL- (no optimization, no LTCG)
 * to ensure __except blocks are never eliminated. Currently contains no active
 * code - reserved for future SEH-wrapped R API call wrappers if needed.
 *
 * The separate compilation unit is kept so build_controlr.ps1 can pre-compile
 * it with the correct flags before the full MSBuild pass.
 */

#include "controlr.h"
