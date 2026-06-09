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

// fwd
class LanguageService;

/**
 * @brief Describes a function argument: name, description, and default value.
 */
class ArgumentDescriptor {
public:
  std::string name_;           ///< Argument name as shown in Excel's function wizard
  std::string description_;    ///< Help text for the argument
  std::string default_value_;  ///< String representation of the default value

public:
  /**
   * @brief Constructs an argument descriptor.
   * @param name Argument name.
   * @param default_value Default value representation.
   * @param description Help text.
   */
  ArgumentDescriptor(const std::string &name = "", const std::string &default_value = "", const std::string &description = "")
    : name_(name)
    , description_(description)
    , default_value_(default_value) {}

  ArgumentDescriptor(const ArgumentDescriptor &rhs) {
    name_ = rhs.name_;
    description_ = rhs.description_;
    default_value_ = rhs.default_value_;
  }
};

/** @brief List of argument descriptors for a function. */
typedef std::vector<std::shared_ptr<ArgumentDescriptor>> ARGUMENT_LIST;

/**
 * @brief Describes a registered language function: name, metadata, and arguments.
 *
 * Used to register functions with Excel's function wizard (xlfRegister)
 * and to dispatch calls back to the correct language service.
 */
class FunctionDescriptor {

public:

  /** @brief Optional alias used as the Excel function name (if empty, name_ is used). */
  std::string alias_;

  /** @brief Internal function name passed back to the language service. */
  std::string name_;

  /** @brief Category shown in Excel's function wizard. */
  std::string category_;

  /** @brief Description shown in Excel's function wizard. */
  std::string description_;

  /** @brief Numeric key identifying the language service that owns this function. */
  uint32_t language_key_;

  /** @brief Language display name for reverse lookup (e.g., "R", "Julia"). */
  std::string language_name_;

  /** @brief List of argument descriptors for this function. */
  ARGUMENT_LIST arguments_;

  /** @brief Shared pointer to the owning language service. */
  std::shared_ptr<LanguageService> language_service_;

  /** @brief Opaque flags field for language-specific use (e.g., R remapped functions). */
  uint32_t flags_;

  /**
   * @brief Excel registration ID assigned by xlfRegister.
   *
   * Needed for xlfUnregister when rebuilding the function list.
   * Excel uses double for this value.
   */
  double register_id_;

public:
  FunctionDescriptor(const std::string &name, const std::string &alias, const std::string &language_name, uint32_t language_key, const std::string &category = "", const std::string &description = "", const ARGUMENT_LIST &args = {}, uint32_t flags = 0, std::shared_ptr<LanguageService> language_service = 0)
    : name_(name)
    , alias_(alias)
    , language_name_(language_name)
    , language_key_(language_key)
    , category_(category)
    , description_(description)
    , flags_(flags)
    , register_id_(0)
    , language_service_(language_service)
  {
    for (auto arg : args) arguments_.push_back(arg);
  }

  ~FunctionDescriptor() {
    // ...
  }

  FunctionDescriptor(const FunctionDescriptor &rhs) {
    name_ = rhs.name_;
    alias_ = rhs.alias_;
    language_name_ = rhs.language_name_;
    category_ = rhs.category_;
    flags_ = rhs.flags_;
    description_ = rhs.description_;
    register_id_ = rhs.register_id_;
    language_key_ = rhs.language_key_;
    language_service_ = rhs.language_service_;
    for (auto arg : rhs.arguments_) arguments_.push_back(arg);
  }
};

typedef std::vector<std::shared_ptr<FunctionDescriptor>> FUNCTION_LIST;

