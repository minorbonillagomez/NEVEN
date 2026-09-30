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

#include <string>

/**
 * @brief Represents a user-defined button in the Ribbon dynamic section.
 *
 * Created by R/Julia via the "add-user-button" callback. Stores the button's
 * label, language tag, icon, tooltip, and numeric ID for dispatch.
 */
class UserButton {

public:
  std::wstring label_;
  std::wstring language_tag_;
  std::wstring image_mso_;
  std::wstring tip_;
  uint32_t id_;

public:
  UserButton(
    const std::wstring &label = L"",
    const std::wstring &language_tag = L"",
    const std::wstring &image_mso = L"",
    const std::wstring &tip = L"",
    const int id = 0) {

    label_ = label;
    language_tag_ = language_tag;
    image_mso_ = image_mso;
    tip_ = tip;
    id_ = id;

  }

  UserButton(const UserButton &rhs)
    : label_(rhs.label_)
    , language_tag_(rhs.language_tag_)
    , image_mso_(rhs.image_mso_)
    , tip_(rhs.tip_)
    , id_(rhs.id_)
  {}

};
