#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "com_object_map.h"
#include "mocks/mock_type_info.h"
#include "variable.pb.h"
#include "string_utilities.h"

using ::testing::_;
using ::testing::Return;
using ::testing::Invoke;
using ::testing::DoAll;
using ::testing::SetArgPointee;
using namespace rj2xcl::testing;

namespace rj2xcl {

class COMObjectMapTest : public ::testing::Test {
protected:
    COMObjectMap com_map_;
    MockDispatch* mock_dispatch_;
    MockTypeInfo* mock_type_info_;

    void SetUp() override {
        mock_dispatch_ = new MockDispatch();
        mock_type_info_ = new MockTypeInfo();
    }

    void TearDown() override {
        delete mock_type_info_;
        delete mock_dispatch_;
    }
};

TEST_F(COMObjectMapTest, MapObject_FailsGracefullyWithNullDispatch) {
    std::vector<COMObjectMap::MemberFunction> member_list;
    CComBSTR match_name = L"IDispatch";

    // Should handle null pointer safely if not dereferenced directly,
    // though the map does dereference. So we won't pass null, but a failing mock.
    
    // Setup Mock behavior for GetTypeInfo to fail (simulating bad pointer or object)
    EXPECT_CALL(*mock_dispatch_, GetTypeInfo(_, _, _))
        .WillOnce(Return(E_FAIL));

    com_map_.MapObject(mock_dispatch_, member_list, match_name);
    
    EXPECT_TRUE(member_list.empty());
}

TEST_F(COMObjectMapTest, InvokeCOMFunction_InvalidPointerReturnsError) {
    RJ2XCLBuffers::CompositeFunctionCall call;
    RJ2XCLBuffers::CallResponse response;
    
    // Setup call with an invalid COM pointer (zero/null)
    call.set_pointer(0);
    call.set_type(RJ2XCLBuffers::CallType::method);
    
    com_map_.InvokeCOMFunction(call, response);
    
    EXPECT_EQ(response.operation_case(), RJ2XCLBuffers::CallResponse::OperationCase::kErr);
    EXPECT_EQ(response.err(), "Invalid COM pointer");
}

TEST_F(COMObjectMapTest, RemoveCOMPointer_ReleasesMemory) {
    // Expect Release to be called
    EXPECT_CALL(*mock_dispatch_, Release())
        .WillOnce(Return(0));

    com_map_.RemoveCOMPointer(reinterpret_cast<ULONG_PTR>(mock_dispatch_));
}

} // namespace rj2xcl
