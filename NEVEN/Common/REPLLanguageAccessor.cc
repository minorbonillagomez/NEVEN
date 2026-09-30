/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file REPLLanguageAccessor.cc
 * @brief Static member initialization for REPLLanguageAccessor.
 */

#include "REPLLanguageAccessor.h"

namespace rj2xcl {

REPLLanguageAccessor* REPLLanguageAccessor::instance_ = nullptr;

void REPLLanguageAccessor::Register(REPLLanguageAccessor* accessor) {
    instance_ = accessor;
}

REPLLanguageAccessor* REPLLanguageAccessor::Get() {
    return instance_;
}

} // namespace rj2xcl
