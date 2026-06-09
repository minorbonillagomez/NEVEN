/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * Pattern: Deterministic Error Handling (Result<T, E>)
 * Part of Layer 3: Common Tools
 */

#pragma once

#include <string>
#include <stdexcept>

namespace rj2xcl {

    /**
     * @brief A composite type representing either a successful result (T) 
     * or an error (E). Simple C++11 implementation.
     */
    template <typename T, typename E>
    class Result {
        bool success_;
        T value_;
        E error_;

        Result(bool success, T val, E err) : success_(success), value_(val), error_(err) {}

    public:
        static Result Success(T value) {
            return Result(true, value, E());
        }

        static Result Failure(E error) {
            return Result(false, T(), error);
        }

        bool is_success() const { return success_; }
        bool is_failure() const { return !success_; }

        const T& value() const { return value_; }
        const E& error() const { return error_; }

        T& value() { return value_; }
        E& error() { return error_; }
    };

    /**
     * @brief Specialization for void results.
     */
    template <typename E>
    class Result<void, E> {
        bool success_;
        E error_;

        Result(bool success, E err) : success_(success), error_(err) {}

    public:
        static Result Success() {
            return Result(true, E());
        }

        static Result Failure(E error) {
            return Result(false, error);
        }

        bool is_success() const { return success_; }
        bool is_failure() const { return !success_; }

        const E& error() const { return error_; }

    private:
        Result() : success_(true), error_(E()) {}
    };

} // namespace rj2xcl
