/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file MenuService.h
 * @brief Creates a bilingual CommandBar toolbar in Excel from the XLL.
 *
 * Uses COM automation (IDispatch) to add an "RJ2XCL" toolbar with
 * buttons for Viewer, Pluto, Notebooks, etc. Supports ES/EN toggle.
 */

#pragma once

#include <windows.h>
#include <string>

namespace rj2xcl {

enum class Language { ES, EN };

class MenuService {
public:
    /**
     * @brief Create the RJ2XCL toolbar in Excel.
     * Must be called after Excel is fully initialized.
     */
    static bool CreateMenu();

    /**
     * @brief Remove the RJ2XCL toolbar from Excel.
     * Called from xlAutoClose.
     */
    static void RemoveMenu();

    /**
     * @brief Toggle between Spanish and English, then recreate the toolbar.
     */
    static void ToggleLanguage();

    /**
     * @brief Get the current UI language.
     */
    static Language GetLanguage();

private:
    static bool menu_created_;
    static Language current_language_;
};

} // namespace rj2xcl
