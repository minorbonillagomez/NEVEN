/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#include "stdafx.h"
#include "COMHandler.h"

namespace rj2xcl {

  COMHandler::COMHandler(COMObjectMap &object_map)
    : object_map_(object_map) {
  }

  Result<void, int> COMHandler::Handle(const std::string &language, 
                                  const RJ2XCLBuffers::CallResponse &call, 
                                  RJ2XCLBuffers::CallResponse &response) {
    
    if (call.operation_case() != RJ2XCLBuffers::CallResponse::OperationCase::kFunctionCall) {
      return Result<void, int>::Failure(-1);
    }

    const auto &callback = call.function_call();
    object_map_.InvokeCOMFunction(callback, response);

    return Result<void, int>::Success();
  }

} // namespace rj2xcl
