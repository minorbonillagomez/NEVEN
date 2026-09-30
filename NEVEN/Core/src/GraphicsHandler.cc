/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#include "stdafx.h"
#include "GraphicsHandler.h"
#include "rj2xcl_graphics.h"

namespace rj2xcl {

  GraphicsHandler::GraphicsHandler(DispatchProvider provider)
    : provider_(provider) {
  }

  Result<void, int> GraphicsHandler::Handle(const std::string &language, 
                                     const RJ2XCLBuffers::CallResponse &call, 
                                     RJ2XCLBuffers::CallResponse &response) {
    
    if (call.operation_case() != RJ2XCLBuffers::CallResponse::OperationCase::kFunctionCall) {
      return Result<void, int>::Failure(-1);
    }

    LPDISPATCH dispatch = provider_ ? provider_() : nullptr;
    const auto &callback = call.function_call();
    
    for (auto argument : callback.arguments()) {
      if (argument.value_case() == RJ2XCLBuffers::Variable::kGraphics) {
        const auto &graphics = argument.graphics();
        if (graphics.command() == RJ2XCLBuffers::GraphicsUpdateCommand::query_size) {
          RJ2XCLGraphics::QuerySize(graphics.name(), response, dispatch);
        }
        else {
          RJ2XCLGraphics::UpdateGraphics(graphics, dispatch);
        }
      }
    }

    return Result<void, int>::Success();
  }

} // namespace rj2xcl
