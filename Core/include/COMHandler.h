/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#pragma once

#include "ICallbackHandler.h"
#include "com_object_map.h"

namespace rj2xcl {

  /**
   * @brief Handler for COM-related callbacks.
   */
  class COMHandler : public ICallbackHandler {
  public:
    COMHandler(COMObjectMap &object_map);
    virtual ~COMHandler() = default;

    virtual std::string GetType() const override { return "COM"; }

    virtual rj2xcl::Result<void, int> Handle(const std::string &language, 
                       const RJ2XCLBuffers::CallResponse &call, 
                       RJ2XCLBuffers::CallResponse &response) override;

  private:
    COMObjectMap &object_map_;
  };

} // namespace rj2xcl
