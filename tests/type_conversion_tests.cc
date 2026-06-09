/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * NEVEN is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NEVEN.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <gtest/gtest.h>
#include "type_conversions.h"
#include <windows.h>
#include <vector>
#include <thread>
#include <string>

TEST(TypeConversionsTest, WideStringToUtf8_ThreadSafety) {
    const std::wstring test_str = L"Test String with Special Chars: \u00C1\u00E9\u00ED\u00F3\u00FA";
    const std::string expected_u8 = "Test String with Special Chars: \xC3\x81\xC3\xA9\xC3\xAD\xC3\xB3\xC3\xBA";

    auto worker = [&]() {
        for (int i = 0; i < 1000; ++i) {
            std::string result = Convert::WideStringToUtf8(test_str.c_str(), (int)test_str.length());
            EXPECT_EQ(result, expected_u8);
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(worker);
    }

    for (auto& t : threads) {
        t.join();
    }
}

TEST(TypeConversionsTest, XLOPERToString_MultiByte) {
    XLOPER12 x;
    std::wstring input = L"Hello \u00A0 World"; // Non-breaking space
    x.xltype = xltypeStr;
    
    std::vector<WCHAR> buffer(input.length() + 1);
    buffer[0] = (WCHAR)input.length();
    memcpy(&buffer[1], input.c_str(), input.length() * sizeof(WCHAR));
    x.val.str = buffer.data();

    std::string result = Convert::XLOPERToString(&x);
    EXPECT_EQ(result, "Hello \xC2\xA0 World");
}

TEST(TypeConversionsTest, XLOPERToVariable_Matrix) {
    XLOPER12 x;
    int rows = 2, cols = 3;
    x.xltype = xltypeMulti;
    x.val.array.rows = rows;
    x.val.array.columns = cols;
    
    std::vector<XLOPER12> oper_array(rows * cols);
    for (int i = 0; i < rows * cols; ++i) {
        oper_array[i].xltype = xltypeNum;
        oper_array[i].val.num = (double)(i + 1);
    }
    x.val.array.lparray = oper_array.data();

    RJ2XCLBuffers::Variable var;
    Convert::XLOPERToVariable(&var, &x);

    EXPECT_TRUE(var.has_arr());
    auto arr = var.arr();
    EXPECT_EQ(arr.rows(), rows);
    EXPECT_EQ(arr.cols(), cols);
    EXPECT_EQ(arr.data_size(), rows * cols);

    // Excel Row-Major: [1, 2, 3]
    //                  [4, 5, 6]
    // R Column-Major expectation: [1, 4, 2, 5, 3, 6]
    
    EXPECT_EQ(arr.data(0).real(), 1.0);
    EXPECT_EQ(arr.data(1).real(), 4.0); // Next in column
    EXPECT_EQ(arr.data(2).real(), 2.0);
    EXPECT_EQ(arr.data(3).real(), 5.0);
    EXPECT_EQ(arr.data(4).real(), 3.0);
    EXPECT_EQ(arr.data(5).real(), 6.0);
}
