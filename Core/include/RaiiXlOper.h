/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#ifndef RJ2XCL_RAII_XLOPER_H
#define RJ2XCL_RAII_XLOPER_H

#include "XLCALL.h"
#include <algorithm>

namespace rj2xcl {

/**
 * @brief RAII wrapper for XLOPER12 structures.
 * 
 * Automates the cleanup of Excel-allocated memory using xlFree
 * when the wrapper goes out of scope.
 */
class RaiiXlOper {
public:
    /**
     * @brief Default constructor. Initializes to xltypeNil.
     */
    RaiiXlOper();

    /**
     * @brief Ownership constructor. Takes ownership of an existing XLOPER12.
     * @param oper Pointer to the XLOPER12 to manage.
     */
    explicit RaiiXlOper(const XLOPER12& oper);

    /**
     * @brief Destructor. Automatically calls xlFree if necessary.
     */
    ~RaiiXlOper();

    // Disable copy for safety, only allow move
    RaiiXlOper(const RaiiXlOper&) = delete;
    RaiiXlOper& operator=(const RaiiXlOper&) = delete;

    /**
     * @brief Move constructor.
     */
    RaiiXlOper(RaiiXlOper&& other) noexcept;

    /**
     * @brief Move assignment operator.
     */
    RaiiXlOper& operator=(RaiiXlOper&& other) noexcept;

    /**
     * @brief Access the underlying XLOPER12 pointer.
     */
    XLOPER12* get();

    /**
     * @brief Access the underlying XLOPER12 pointer (const).
     */
    const XLOPER12* get() const;

    /**
     * @brief Overload address-of operator for use in Excel12 calls.
     */
    XLOPER12* operator&();

    /**
     * @brief Overload member access operator.
     */
    XLOPER12* operator->();

    /**
     * @brief Overload member access operator (const).
     */
    const XLOPER12* operator->() const;

    /**
     * @brief Free the managed memory and reset to xltypeNil.
     */
    void Free();

    /**
     * @brief Transfer ownership from an existing pointer.
     */
    void Reset(const XLOPER12& oper);

private:
    XLOPER12 oper_;
};

} // namespace rj2xcl

#endif // RJ2XCL_RAII_XLOPER_H
