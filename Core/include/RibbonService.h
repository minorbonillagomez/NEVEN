/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 */

#pragma once

#include <atlbase.h>
#include <atlcom.h>
#include <vector>
#include <string>
#include <memory>
#include "user_button.h"
#include "variable.pb.h"
#include "result.h"

namespace rj2xcl {

  /**
   * @brief Service to manage the Excel Ribbon integration and custom buttons.
   * 
   * This class decouples Ribbon logic from the main engine.
   */
  class RibbonService {
  public:
    RibbonService();
    ~RibbonService() = default;

    /**
     * @brief Sets the COM pointer for the ribbon.
     */
    void SetRibbonPointer(LPDISPATCH ribbon_pointer);

    /**
     * @brief Adds a user button from a call response message.
     */
    int AddUserButton(const RJ2XCLBuffers::CallResponse &call, 
                      RJ2XCLBuffers::CallResponse &response, 
                      const std::string &language);

    /**
     * @brief Executes a user button click.
     */
    void ExecUserButton(uint32_t id, const std::string &language);

    /**
     * @brief Clears all custom buttons.
     */
    void ClearUserButtons();

    /**
     * @brief Internal call to actually add the button to the UI.
     */
    HRESULT AddUserButtonInternal(const UserButton &button);

  private:
    /** Pointer to ribbon COM menu */
    CComPtr<IDispatch> ribbon_menu_dispatch_;

    /** List of buttons waiting for the ribbon to be ready */
    std::vector<UserButton> pending_user_buttons_;

    /** ID generator for custom buttons */
    uint32_t next_user_button_id_;
  };

} // namespace rj2xcl
