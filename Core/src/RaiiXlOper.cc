/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 */

#include "stdafx.h"
#include "RaiiXlOper.h"
#include "rj2xcl.h"

namespace rj2xcl {

RaiiXlOper::RaiiXlOper() {
    oper_.xltype = xltypeNil;
}

RaiiXlOper::RaiiXlOper(const XLOPER12& oper) : oper_(oper) {
}

RaiiXlOper::~RaiiXlOper() {
    Free();
}

RaiiXlOper::RaiiXlOper(RaiiXlOper&& other) noexcept : oper_(other.oper_) {
    other.oper_.xltype = xltypeNil;
}

RaiiXlOper& RaiiXlOper::operator=(RaiiXlOper&& other) noexcept {
  if (this != std::addressof(other)) {
        Free();
        oper_ = other.oper_;
        other.oper_.xltype = xltypeNil;
    }
    return *this;
}

XLOPER12* RaiiXlOper::get() {
    return &oper_;
}

const XLOPER12* RaiiXlOper::get() const {
    return &oper_;
}

XLOPER12* RaiiXlOper::operator&() {
    return &oper_;
}

XLOPER12* RaiiXlOper::operator->() {
    return &oper_;
}

const XLOPER12* RaiiXlOper::operator->() const {
    return &oper_;
}

void RaiiXlOper::Free() {
    if (oper_.xltype & xlbitXLFree) {
        auto engine = RJ2XCL_Engine::Instance();
        if (engine && engine->Excel()) {
            engine->Excel()->Excel12(xlFree, 0, 1, &oper_);
        }
    } else if (oper_.xltype & xlbitDLLFree) {
        if (oper_.xltype & xltypeMulti) {
            int count = oper_.val.array.rows * oper_.val.array.columns;
            for (int i = 0; i < count; i++) {
                if (oper_.val.array.lparray[i].xltype & xltypeStr) {
                    delete[] oper_.val.array.lparray[i].val.str;
                }
            }
            delete[] oper_.val.array.lparray;
        } else if (oper_.xltype & xltypeStr) {
            delete[] oper_.val.str;
        } else if (oper_.xltype & xltypeRef) {
             if (oper_.val.mref.lpmref) delete oper_.val.mref.lpmref;
        }
    }
    oper_.xltype = xltypeNil;
}

void RaiiXlOper::Reset(const XLOPER12& oper) {
    Free();
    oper_ = oper;
}

} // namespace rj2xcl
