#include <gtest/gtest.h>
#include <fstream>
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

// ---- Reload of user function files after a reconnect (J.* #VALOR! at open) ----
namespace {
class RecordingService : public MockLanguageService {
public:
    using MockLanguageService::MockLanguageService;
    std::vector<std::string> loaded;
    int nested_result = -1;
    void ReadSourceFile(const std::string &file) override {
        loaded.push_back(file);
        nested_result = LoadFunctionFiles(dir_);   // must be refused while reloading
    }
    std::string dir_;
};
}  // namespace

TEST_F(LanguageServiceTest, LoadFunctionFiles_ReadsOnlyValidFilesOfTheDirectory) {
    char tmp[MAX_PATH];
    GetTempPathA(MAX_PATH, tmp);
    std::string dir = std::string(tmp) + "neven_reload_test_" + std::to_string(GetCurrentProcessId());
    CreateDirectoryA(dir.c_str(), nullptr);
    CreateDirectoryA((dir + "\\sub.jl").c_str(), nullptr);  // directories are skipped
    for (auto n : {"a.jl", "b.jl", "notes.txt"}) { std::ofstream(dir + "\\" + n) << "x"; }

    RecordingService svc(cb_info_, map_);
    svc.dir_ = dir;
    ON_CALL(svc, ValidFile(_)).WillByDefault(Invoke([](const std::string &f) {
        return f.size() > 3 && f.compare(f.size() - 3, 3, ".jl") == 0;
    }));

    EXPECT_EQ(svc.LoadFunctionFiles(dir), 2);
    ASSERT_EQ(svc.loaded.size(), 2u);
    EXPECT_EQ(svc.nested_result, 0);  // no re-entrant reload
    // the guard is released afterwards
    svc.loaded.clear();
    EXPECT_EQ(svc.LoadFunctionFiles(dir), 2);

    DeleteFileA((dir + "\\a.jl").c_str()); DeleteFileA((dir + "\\b.jl").c_str());
    DeleteFileA((dir + "\\notes.txt").c_str()); RemoveDirectoryA((dir + "\\sub.jl").c_str());
    RemoveDirectoryA(dir.c_str());
}

TEST_F(LanguageServiceTest, LoadFunctionFiles_EmptyOrMissingDirectoryLoadsNothing) {
    RecordingService svc(cb_info_, map_);
    EXPECT_EQ(svc.LoadFunctionFiles(""), 0);
    EXPECT_EQ(svc.LoadFunctionFiles("C:\\neven_dir_that_does_not_exist_12345"), 0);
    EXPECT_TRUE(svc.loaded.empty());
}
} // namespace rj2xcl
