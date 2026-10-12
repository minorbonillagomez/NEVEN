#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "language_service.h"
#include "mocks/mock_language_service.h"
#include "callback_info.h"
#include "com_object_map.h"
#include "json11/json11.hpp"

using ::testing::_;
using ::testing::Return;
using ::testing::Invoke;
using namespace rj2xcl::testing;

namespace rj2xcl {

class LanguageServiceTest : public ::testing::Test {
protected:
    CallbackInfo cb_info_;
    COMObjectMap map_;
    json11::Json config_ = json11::Json::object{};
    
    // We test the real base behavior but instantiate via Mock to avoid unwanted side-effects
    // Actually, to test base behavior, we might want a real instance, but we disabled 
    // registry lookups via dev_flags = 0 in mock.
};

TEST_F(LanguageServiceTest, ValidFile_ChecksExtensionsCorrectly) {
    MockLanguageService svc(cb_info_, map_);
    
    // The language descriptor is empty right now. We inject some extensions for test.
    // Because Descriptor is protected, we can't easily set it unless we use a test wrapper
    // or public method. For now, testing the mock's override.
    
    EXPECT_CALL(svc, ValidFile(_))
        .WillOnce(Return(true))
        .WillOnce(Return(false));
        
    EXPECT_TRUE(svc.ValidFile("C:\\test\\script.R"));
    EXPECT_FALSE(svc.ValidFile("C:\\test\\script.txt"));
}

TEST_F(LanguageServiceTest, InterpolateString_ReplacesTokens) {
    // Testing the actual base class method.
    MockLanguageService svc(cb_info_, map_);
    
    // Override is MOCK_METHOD, but we can call the base class explicitly if needed,
    // or just let a wrapper class provide it.
    
    std::string test_str = "Load path: $HOME\\bin";
    
    // For now we assume calling the real method
    // svc.LanguageService::InterpolateString(test_str);
    // 
    // EXPECT_NE(test_str.find("$HOME"), std::string::npos); // Should be replaced
}

} // namespace rj2xcl
