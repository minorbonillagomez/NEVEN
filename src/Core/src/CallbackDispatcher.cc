/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#include "stdafx.h"
#include "CallbackDispatcher.h"

namespace rj2xcl {

  void CallbackDispatcher::RegisterHandler(std::unique_ptr<ICallbackHandler> handler) {
    if (handler) {
      handlers_[handler->GetType()] = std::move(handler);
    }
  }

  Result<void, int> CallbackDispatcher::Dispatch(const std::string &type, 
                                          const std::string &language, 
                                          const RJ2XCLBuffers::CallResponse &call, 
                                          RJ2XCLBuffers::CallResponse &response) {
    auto it = handlers_.find(type);
    if (it != handlers_.end()) {
      return it->second->Handle(language, call, response);
    }
    
    // No handler found
    return Result<void, int>::Failure(-1); 
  }

} // namespace rj2xcl
