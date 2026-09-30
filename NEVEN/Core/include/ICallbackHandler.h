/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#pragma once

#include <string>
#include "variable.pb.h"
#include "result.h"

namespace rj2xcl {

  /**
   * @brief Interface for handling callbacks from the engine.
   * 
   * This allows for modular handling of different types of callbacks
   * (COM, Graphics, Language, etc.)
   */
  class ICallbackHandler {
  public:
    virtual ~ICallbackHandler() = default;

    /**
     * @brief Identifies the type of callback this handler manages.
     */
    virtual std::string GetType() const = 0;

    /**
     * @brief Processes the callback.
     * 
     * @param language The language key or name.
     * @param call The incoming call buffer.
     * @param response The response buffer to populate.
     * @return Result<void, int> Success or failure with error code.
     */
    virtual Result<void, int> Handle(const std::string &language, 
                                     const RJ2XCLBuffers::CallResponse &call, 
                                     RJ2XCLBuffers::CallResponse &response) = 0;
  };

} // namespace rj2xcl
