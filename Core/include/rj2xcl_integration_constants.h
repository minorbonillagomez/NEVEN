/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 */

#pragma once

namespace rj2xcl {
namespace constants {

  /**
   * @brief Excel Macro names used for integration.
   * 
   * These names correspond to macros defined in the Excel add-in 
   * or the Excel application itself that are triggered by the engine.
   */
  
  // TRIGGER: Called when language functions need to be re-mapped in Excel
  static constexpr const char* kUpdateFunctionsMacro = "RJ.UpdateFunctions";

  // TRIGGER: Called when a language context switch occurs (e.g. from R to Julia)
  static constexpr const char* kContextSwitchMacro = "RJ.ContextSwitch";

  // TRIGGER: Called for specific Excel callbacks
  static constexpr const char* kExcelCallbackMacro = "RJ.ExcelCallback";

} // namespace constants
} // namespace rj2xcl
