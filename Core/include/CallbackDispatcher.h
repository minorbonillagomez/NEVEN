/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#pragma once

#include "ICallbackHandler.h"
#include <map>
#include <memory>
#include <vector>

namespace rj2xcl {

  /**
   * @brief Manages and dispatches callbacks to registered handlers.
   */
  class CallbackDispatcher {
  public:
    CallbackDispatcher() = default;
    ~CallbackDispatcher() = default;

    /**
     * @brief Registers a new handler.
     */
    void RegisterHandler(std::unique_ptr<ICallbackHandler> handler);

    /**
     * @brief Dispatches the call to the appropriate handler.
     * 
     * @param type The type of callback (e.g., "COM", "graphics").
     * @param language The language name.
     * @param call The incoming call.
     * @param response The response to populate.
     * @return Result<void, int> Success or failure.
     */
    Result<void, int> Dispatch(const std::string &type, 
                               const std::string &language, 
                               const RJ2XCLBuffers::CallResponse &call, 
                               RJ2XCLBuffers::CallResponse &response);

  private:
    std::map<std::string, std::unique_ptr<ICallbackHandler>> handlers_;

    // Prevent copying
    CallbackDispatcher(const CallbackDispatcher&) = delete;
    CallbackDispatcher& operator=(const CallbackDispatcher&) = delete;
  };

} // namespace rj2xcl
