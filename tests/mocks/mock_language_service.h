#pragma once

#include <gmock/gmock.h>
#include "language_service.h"

namespace rj2xcl {
namespace testing {

class MockLanguageService : public LanguageService {
public:
    MockLanguageService(CallbackInfo &callback_info, COMObjectMap &object_map)
        : LanguageService(callback_info, object_map, 0, json11::Json::object{}, "", json11::Json::object{}) {}

    MOCK_METHOD(bool, ValidFile, (const std::string &path), (override));
    MOCK_METHOD(int, StartChildProcess, (HANDLE job_handle), (override));
    MOCK_METHOD(void, Connect, (HANDLE job_handle), (override));
    MOCK_METHOD(void, Initialize, (), (override));
    MOCK_METHOD(void, Shutdown, (), (override));
    MOCK_METHOD(void, RunCallbackThread, (), (override));
    MOCK_METHOD(void, SetApplicationPointer, (LPDISPATCH application_pointer), (override));
    MOCK_METHOD(void, SetGraphicsTargets, (LPDISPATCH application_dispatch), (override));
    MOCK_METHOD(void, SetWatchFiles, (const std::vector<std::string> &files), (override));
    MOCK_METHOD(FUNCTION_LIST, MapLanguageFunctions, (uint32_t key, std::shared_ptr<LanguageService> language_service), (override));
    MOCK_METHOD(void, Call, (RJ2XCLBuffers::CallResponse &response, RJ2XCLBuffers::CallResponse &call), (override));
    MOCK_METHOD(void, InterpolateString, (std::string &str, (const std::vector<std::pair<std::string, std::string>> &additional_replacements)), (override));
};

} // namespace testing
} // namespace rj2xcl
