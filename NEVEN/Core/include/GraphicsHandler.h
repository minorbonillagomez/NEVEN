/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#pragma once

#include "ICallbackHandler.h"
#include <atlbase.h>
#include <functional>

namespace rj2xcl {

  /**
   * @brief Handler for graphics-related callbacks.
   */
  class GraphicsHandler : public ICallbackHandler {
  public:
    using DispatchProvider = std::function<LPDISPATCH()>;

    GraphicsHandler(DispatchProvider provider);
    virtual ~GraphicsHandler() = default;

    virtual std::string GetType() const override { return "graphics"; }

    virtual rj2xcl::Result<void, int> Handle(const std::string &language, 
                       const RJ2XCLBuffers::CallResponse &call, 
                       RJ2XCLBuffers::CallResponse &response) override;

  private:
    DispatchProvider provider_;
  };

} // namespace rj2xcl
