/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * This file is part of NEVEN.
 */

#include <gtest/gtest.h>
#include "RaiiXlOper.h"
#include "rj2xcl.h"
#include "IExcelBridge.h"
#include <memory>
#include <vector>

namespace rj2xcl {

class TrackingMockExcelBridge : public IExcelBridge {
public:
    int free_calls = 0;
    std::vector<int> functions_called;

    virtual int Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) override {
        functions_called.push_back(xlfn);
        if (xlfn == xlFree) { // 0x4000
            free_calls++;
        }
        return 0; // xlretSuccess
    }

    virtual int Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]) override {
        functions_called.push_back(xlfn);
        if (xlfn == xlFree) { // 0x4000
            free_calls++;
        }
        return 0; // xlretSuccess
    }
};

class RaiiXlOperTest : public ::testing::Test {
protected:
    void SetUp() override {
        auto engine = RJ2XCL_Engine::Instance();
        mock_bridge = new TrackingMockExcelBridge();
        engine->SetBridge(std::unique_ptr<IExcelBridge>(mock_bridge));
    }

    TrackingMockExcelBridge* mock_bridge;
};

TEST_F(RaiiXlOperTest, DefaultConstructor) {
    RaiiXlOper oper;
    EXPECT_EQ(oper->xltype, 0x0100); // xltypeNil
}

TEST_F(RaiiXlOperTest, ResetClearsPrevious) {
    XLOPER12 x;
    x.xltype = 0x0001 | 0x1000; // xltypeNum | xlbitXLFree
    x.val.num = 1.0;

    {
        RaiiXlOper oper;
        oper.Reset(x);
        EXPECT_EQ(mock_bridge->free_calls, 0);
        
        XLOPER12 y;
        y.xltype = 0x0100; // xltypeNil
        oper.Reset(y);
        EXPECT_EQ(mock_bridge->free_calls, 1);
    }
    // Destructor should not call xlFree again since xltype is Nil
    EXPECT_EQ(mock_bridge->free_calls, 1);
}

TEST_F(RaiiXlOperTest, MoveConstructorTransfersOwnership) {
    XLOPER12 x;
    x.xltype = 0x0001 | 0x1000; // xltypeNum | xlbitXLFree
    x.val.num = 1.0;

    {
        RaiiXlOper oper1;
        oper1.Reset(x);
        
        RaiiXlOper oper2(std::move(oper1));
        EXPECT_EQ(oper1->xltype, 0x0100); // xltypeNil
        EXPECT_EQ(oper2->xltype, 0x0001 | 0x1000);
        EXPECT_EQ(mock_bridge->free_calls, 0);
    }
    EXPECT_EQ(mock_bridge->free_calls, 1);
}

TEST_F(RaiiXlOperTest, OwnershipInVector) {
    XLOPER12 x;
    x.xltype = 0x0001 | 0x1000; // xltypeNum | xlbitXLFree
    x.val.num = 1.0;

    {
        std::vector<RaiiXlOper> vec;
        RaiiXlOper oper;
        oper.Reset(x);
        vec.push_back(std::move(oper));
        EXPECT_EQ(mock_bridge->free_calls, 0);
    }
    EXPECT_EQ(mock_bridge->free_calls, 1);
}

} // namespace rj2xcl
