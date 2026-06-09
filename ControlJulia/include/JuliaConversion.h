/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */
#pragma once

#ifndef JULIA_CONVERSION_H
#define JULIA_CONVERSION_H

#include <vector>
#include <string>

// Forward declarations to avoid strict header dependencies
struct xloper12;
struct _jl_value_t;
typedef struct _jl_value_t jl_value_t;

namespace rj2xcl {
namespace julia_mapper {

    // Converts Excel types (Int, Double, String, Booleans, Ranges) into Julia generic jl_value_t
    jl_value_t* xloper12_to_jl_value(const xloper12* xl_obj);

    // Converts back from Julia native types to Excel interoperability objects
    xloper12* jl_value_to_xloper12(jl_value_t* jl_obj);

} // namespace julia_mapper
} // namespace rj2xcl

#endif // JULIA_CONVERSION_H
