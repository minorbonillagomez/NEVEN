#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "basic_functions.h"
#include "rj2xcl.h"
#include "mocks/mock_language_service.h"
#include "callback_info.h"
#include "com_object_map.h"

using ::testing::_;
using ::testing::Return;
using ::testing::Invoke;

namespace rj2xcl {

class BasicFunctionsTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Reset singleton before every test to avoid cross-contamination
        RJ2XCL_Engine::Instance()->ResetForTesting();
    }

    void TearDown() override {
        RJ2XCL_Engine::Instance()->ResetForTesting();
    }
};

TEST_F(BasicFunctionsTest, RJVersionReturnsAllocatedString) {
    LPXLOPER12 result = RJ_Version();
    ASSERT_NE(result, nullptr);
    // RJ_Version uses static XLOPER12 with StringToXLOPER — no DLLFree needed
    ASSERT_EQ(result->xltype, xltypeStr);
    
    // Validate length byte in Excel string format
    int len = result->val.str[0];
    ASSERT_GT(len, 0);
    
    // Verify it contains "NEVEN"
    std::wstring version_str(result->val.str + 1, len);
    EXPECT_NE(version_str.find(L"NEVEN"), std::wstring::npos);
}

TEST_F(BasicFunctionsTest, RJFunctionCall_HandlesOutOfBoundsIndex) {
    // Attempting to call an index that hasn't been registered
    LPXLOPER12 missing = new XLOPER12;
    missing->xltype = xltypeMissing;

    // Call with index 9999
    LPXLOPER12 result = RJ_FunctionCall(9999, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing);
    
    ASSERT_NE(result, nullptr);
    EXPECT_EQ(result->xltype, xltypeErr);
    EXPECT_EQ(result->val.err, xlerrName);
    
    delete missing;
}

TEST_F(BasicFunctionsTest, RJExecGeneric_HandlesInvalidInputType) {
    XLOPER12 invalid_input;
    invalid_input.xltype = xltypeNum; // Code must be a string
    invalid_input.val.num = 42.0;

    LPXLOPER12 result = RJ_Exec_Generic(0, &invalid_input);
    
    ASSERT_NE(result, nullptr);
    EXPECT_EQ(result->xltype, xltypeErr);
    EXPECT_EQ(result->val.err, xlerrValue);
}

TEST_F(BasicFunctionsTest, RJCallGeneric_HandlesInvalidInputType) {
    XLOPER12 invalid_func;
    invalid_func.xltype = xltypeNum; // Function name must be a string
    invalid_func.val.num = 42.0;

    LPXLOPER12 missing = new XLOPER12;
    missing->xltype = xltypeMissing;

    LPXLOPER12 result = RJ_Call_Generic(0, &invalid_func, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing);
    
    ASSERT_NE(result, nullptr);
    EXPECT_EQ(result->xltype, xltypeErr);
    EXPECT_EQ(result->val.err, xlerrValue);
    
    delete missing;
}

// Additional test to inject MockLanguageService could go here
// but requires deeper exposure in LanguageManager.

} // namespace rj2xcl
