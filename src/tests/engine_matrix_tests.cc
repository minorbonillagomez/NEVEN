/**
 * Copyright (c) 2026 NEVEN Project
 *
 * @file engine_matrix_tests.cc
 * @brief The eight combinations of present/absent engines (R, Julia, Python).
 *
 * Runs without R, Julia or Python installed (INV-TEST-03): presence is
 * simulated with a temporary directory as the engine "home", which
 * DiscoveryService accepts as an override, and absence is simulated by leaving
 * the engine out of neven-config.json.
 */

#include <gtest/gtest.h>
#include <windows.h>

#include <cstring>
#include <string>
#include <vector>

#include "LanguageManager.h"
#include "basic_functions.h"
#include "rj2xcl.h"
#include "engine_availability.h"
#include "PlutoManager.h"
#include "callback_info.h"
#include "com_object_map.h"
#include "json11/json11.hpp"

// NEVEN.Status is exported from the DLL but not declared in basic_functions.h.
extern "C" LPXLOPER12 WINAPI NEVEN_Status();

namespace rj2xcl {
namespace {

/** @brief Reads an XLOPER12 string result back as narrow text (ASCII payload). */
std::string XloperText(LPXLOPER12 value) {
    if (!value) return "";
    if ((value->xltype & ~(xlbitDLLFree | xlbitXLFree)) != xltypeStr) return "";
    int length = value->val.str[0];
    std::wstring wide(value->val.str + 1, length);
    return std::string(wide.begin(), wide.end());
}

/** @brief Excel string argument with the length-prefixed buffer XLOPER12 needs. */
class XlString {
public:
    explicit XlString(const std::wstring& text) {
        buffer_.push_back(static_cast<wchar_t>(text.size()));
        buffer_.append(text);
        oper_.xltype = xltypeStr;
        oper_.val.str = &buffer_[0];
    }
    LPXLOPER12 get() { return &oper_; }

private:
    std::wstring buffer_;
    XLOPER12 oper_ = {};
};

/** @brief The connection catalog, same shape as Install/neven-languages.json. */
json11::Json LanguageCatalogJson() {
    return json11::Json::array{
        json11::Json::object{
            { "name", "R" },
            { "executable", "ControlR.exe" },
            { "prefix", "R" },
            { "extensions", json11::Json::array{ "r", "R" } },
            { "command_arguments", "-r \"$HOME\"" },
            { "prepend_path", "$HOME\\bin\\x64" },
            { "priority", 10 },
            { "startup_resource", "startup.r" }
        },
        json11::Json::object{
            { "name", "Julia" },
            { "executable", "ControlJulia.exe" },
            { "prefix", "J" },
            { "extensions", json11::Json::array{ "jl" } },
            { "command_arguments", "" },
            { "prepend_path", "$HOME\\bin" },
            { "priority", 10 },
            { "startup_resource", "startup.jl" }
        },
        json11::Json::object{
            { "name", "Python" },
            { "executable", "ControlPython.exe" },
            { "prefix", "P" },
            { "extensions", json11::Json::array{ "py" } },
            { "command_arguments", "" },
            { "prepend_path", "$HOME" },
            { "priority", 10 },
            { "startup_resource", "startup.py" }
        }
    };
}

/** @brief Base fixture: temporary engine homes plus singleton isolation. */
class EngineMatrixFixture : public ::testing::Test {
protected:
    void SetUp() override {
        RJ2XCL_Engine::Instance()->ResetForTesting();

        char temp_path[MAX_PATH] = {};
        ASSERT_GT(GetTempPathA(MAX_PATH, temp_path), 0u);

        home_directory_ = std::string(temp_path) + "neven_engine_matrix_"
            + std::to_string(GetCurrentProcessId()) + "\\";
        CreateDirectoryA(home_directory_.c_str(), nullptr);

        for (const auto& entry : EngineCatalog()) {
            std::string engine_home = home_directory_ + entry.name;
            CreateDirectoryA(engine_home.c_str(), nullptr);
            engine_homes_.push_back(engine_home);
        }
    }

    void TearDown() override {
        RJ2XCL_Engine::Instance()->ResetForTesting();
        for (const auto& engine_home : engine_homes_) {
            RemoveDirectoryA(engine_home.c_str());
        }
        engine_homes_.clear();
        RemoveDirectoryA(home_directory_.c_str());
    }

    /** @brief Configures the engines whose bit is set in the subset mask. */
    void ConfigureSubset(int subset_mask) {
        json11::Json::object engines;
        const auto& catalog = EngineCatalog();
        for (size_t i = 0; i < catalog.size(); i++) {
            if (subset_mask & (1 << i)) {
                engines[catalog[i].name] = json11::Json::object{
                    { "home", engine_homes_[i] },
                    { "enabled", true }
                };
            }
        }
        Configure(json11::Json::object{ { "NEVEN", engines } });
    }

    /** @brief Runs phase 1 of the language lifecycle with the given config. */
    void Configure(const json11::Json& config) {
        LanguageManager::Instance().ConfigureLanguages(
            0, config, home_directory_, LanguageCatalogJson(), callback_info_, object_map_);
    }

    std::string home_directory_;
    std::vector<std::string> engine_homes_;
    CallbackInfo callback_info_;
    COMObjectMap object_map_;
};

/** @brief Parametrized over the 8 subsets of {R, Julia, Python}. */
class EngineSubsetTest : public EngineMatrixFixture,
                         public ::testing::WithParamInterface<int> {
};

TEST_P(EngineSubsetTest, ServicesContainExactlyTheSubset) {
    const int subset_mask = GetParam();
    ConfigureSubset(subset_mask);

    std::vector<std::string> expected;
    const auto& catalog = EngineCatalog();
    for (size_t i = 0; i < catalog.size(); i++) {
        if (subset_mask & (1 << i)) expected.push_back(catalog[i].name);
    }

    std::vector<std::string> actual;
    for (const auto& service : LanguageManager::Instance().GetServices()) {
        actual.push_back(service->name());
    }

    EXPECT_EQ(actual, expected);
}

TEST_P(EngineSubsetTest, AbsentEngineReportsItselfAndNeverAnotherEngine) {
    const int subset_mask = GetParam();
    ConfigureSubset(subset_mask);

    const auto& catalog = EngineCatalog();
    for (size_t i = 0; i < catalog.size(); i++) {
        if (subset_mask & (1 << i)) continue;

        const std::string name = catalog[i].name;
        RJ2XCLBuffers::CallResponse call, response;
        call.set_wait(true);
        call.mutable_code()->add_line("1");
        LanguageManager::Instance().CallLanguageByName(name, response, call);

        const std::string err = response.err();
        EXPECT_NE(err.find(name), std::string::npos) << "asked for " << name << ": " << err;
        EXPECT_NE(err.find(catalog[i].download_url), std::string::npos) << err;
        EXPECT_NE(err.find("NEVEN no instala motores"), std::string::npos) << err;

        // Regression guard for the crossed dispatch: the answer must not come
        // from, or point at, a different engine.
        for (size_t j = 0; j < catalog.size(); j++) {
            if (j == i) continue;
            EXPECT_EQ(err.find(catalog[j].download_url), std::string::npos) << err;
            if (strlen(catalog[j].name) > 1) {
                EXPECT_EQ(err.find(catalog[j].name), std::string::npos) << err;
            }
        }
    }
}

TEST_P(EngineSubsetTest, NevenXFunctionsReportTheirOwnAbsentEngine) {
    const int subset_mask = GetParam();
    ConfigureSubset(subset_mask);

    XlString process(L"MR_Lineal");
    XLOPER12 missing = {};
    missing.xltype = xltypeMissing;

    const auto& catalog = EngineCatalog();
    for (size_t i = 0; i < catalog.size(); i++) {
        if (subset_mask & (1 << i)) continue;

        LPXLOPER12 result = nullptr;
        const std::string name = catalog[i].name;
        if (name == "R") {
            result = NevenX_R(process.get(), &missing, &missing, &missing, &missing,
                &missing, &missing, &missing, &missing, &missing, &missing,
                &missing, &missing, &missing, &missing, &missing, &missing);
        }
        else if (name == "Julia") {
            result = NevenX_J(process.get(), &missing, &missing, &missing, &missing,
                &missing, &missing, &missing, &missing, &missing, &missing,
                &missing, &missing, &missing, &missing, &missing, &missing);
        }
        else {
            result = NevenX_P(process.get(), &missing, &missing, &missing, &missing,
                &missing, &missing, &missing, &missing, &missing, &missing,
                &missing, &missing, &missing, &missing, &missing, &missing);
        }

        const std::string text = XloperText(result);
        EXPECT_NE(text.find(name), std::string::npos) << "asked for " << name << ": " << text;
        EXPECT_NE(text.find(catalog[i].download_url), std::string::npos) << text;
        for (size_t j = 0; j < catalog.size(); j++) {
            if (j == i) continue;
            EXPECT_EQ(text.find(catalog[j].download_url), std::string::npos) << text;
        }
    }
}

TEST_P(EngineSubsetTest, PresentButUnconnectedEngineReportsNotConnected) {
    const int subset_mask = GetParam();
    ConfigureSubset(subset_mask);

    const auto& catalog = EngineCatalog();
    for (size_t i = 0; i < catalog.size(); i++) {
        if (!(subset_mask & (1 << i))) continue;

        RJ2XCLBuffers::CallResponse call, response;
        call.set_wait(true);
        call.mutable_code()->add_line("1");
        LanguageManager::Instance().CallLanguageByName(catalog[i].name, response, call);

        // The engine is configured but its child process is not there, so the
        // call reaches LanguageService::Call and fails on the pipe, not on the
        // availability check.
        EXPECT_NE(response.err().find("not connected"), std::string::npos)
            << catalog[i].name << ": " << response.err();
    }
}

TEST_P(EngineSubsetTest, StatusNamesTheThreeEnginesWithTheirUrls) {
    const int subset_mask = GetParam();
    ConfigureSubset(subset_mask);

    const std::string status = XloperText(NEVEN_Status());

    const auto& catalog = EngineCatalog();
    for (size_t i = 0; i < catalog.size(); i++) {
        EXPECT_NE(status.find(catalog[i].name), std::string::npos) << status;
        if (!(subset_mask & (1 << i))) {
            EXPECT_NE(status.find(catalog[i].download_url), std::string::npos) << status;
        }
    }
    EXPECT_NE(status.find("NEVEN Studio > Settings > Motores"), std::string::npos) << status;
}

INSTANTIATE_TEST_SUITE_P(EngineMatrix, EngineSubsetTest, ::testing::Range(0, 8));

/** @brief Cases that do not depend on the subset. */
class EngineMatrixTest : public EngineMatrixFixture {
};

TEST_F(EngineMatrixTest, StatusWithoutAnyEngineNamesAllThreeAndTheirUrls) {
    Configure(json11::Json::object{ { "NEVEN", json11::Json::object{} } });

    ASSERT_TRUE(LanguageManager::Instance().GetServices().empty());

    const std::string status = XloperText(NEVEN_Status());
    for (const auto& entry : EngineCatalog()) {
        EXPECT_NE(status.find(entry.name), std::string::npos) << status;
        EXPECT_NE(status.find(entry.download_url), std::string::npos) << status;
    }
    EXPECT_NE(status.find("NEVEN no instala motores"), std::string::npos) << status;
    EXPECT_NE(status.find("NEVEN Studio > Settings > Motores"), std::string::npos) << status;
}

TEST_F(EngineMatrixTest, ConfigStatesDistinguishDisabledFromMissing) {
    json11::Json config = json11::Json::object{
        { "NEVEN", json11::Json::object{
            { "R", json11::Json::object{ { "home", engine_homes_[0] } } },
            { "Julia", json11::Json::object{ { "home", engine_homes_[1] }, { "enabled", false } } }
            // Python is left out of the config on purpose.
        } }
    };
    Configure(config);

    auto& manager = LanguageManager::Instance();
    EXPECT_EQ(manager.GetLanguageState("R"), LanguageConfigState::Configured);
    EXPECT_EQ(manager.GetLanguageState("Julia"), LanguageConfigState::DisabledByUser);
    EXPECT_EQ(manager.GetLanguageState("Python"), LanguageConfigState::NotInConfig);

    EXPECT_EQ(manager.GetUnavailableLanguages().size(), 2u);

    RJ2XCLBuffers::CallResponse call, response;
    call.set_wait(true);
    call.mutable_code()->add_line("1");
    manager.CallLanguageByName("Julia", response, call);
    EXPECT_NE(response.err().find("desactivado por el usuario"), std::string::npos)
        << response.err();
}

TEST_F(EngineMatrixTest, UndiscoverableEngineIsReportedAsNotFound) {
    // An engine declared and enabled whose installation cannot be discovered.
    // "Ruby" is not a language DiscoveryService knows how to look for, so the
    // discovery always fails here, with or without engines on the machine.
    json11::Json catalog = json11::Json::array{
        json11::Json::object{
            { "name", "Ruby" },
            { "executable", "ControlRuby.exe" },
            { "prefix", "Rb" },
            { "extensions", json11::Json::array{ "rb" } }
        }
    };
    json11::Json config = json11::Json::object{
        { "NEVEN", json11::Json::object{
            { "Ruby", json11::Json::object{ { "enabled", true } } }
        } }
    };

    LanguageManager::Instance().ConfigureLanguages(
        0, config, home_directory_, catalog, callback_info_, object_map_);

    EXPECT_TRUE(LanguageManager::Instance().GetServices().empty());
    EXPECT_EQ(LanguageManager::Instance().GetLanguageState("Ruby"), LanguageConfigState::NotFound);
}

TEST_F(EngineMatrixTest, NumericKeysOutOfRangeStillFail) {
    ConfigureSubset(0);

    RJ2XCLBuffers::CallResponse call, response;
    call.set_wait(true);
    call.mutable_code()->add_line("1");
    LanguageManager::Instance().CallLanguage(7, response, call);

    EXPECT_EQ(response.err(), "invalid language key");
}

TEST_F(EngineMatrixTest, PlutoStartWithoutJuliaNamesJuliaAndItsUrl) {
    // PlutoManager::Initialize() is never called in the test process, so
    // julia_path_ is empty and StartPluto() returns before touching the port
    // or launching anything.
    ASSERT_FALSE(PlutoManager::Instance().IsRunning());

    const std::string message = PlutoManager::Instance().StartPluto();

    EXPECT_NE(message.find("Julia"), std::string::npos) << message;
    EXPECT_NE(message.find(EngineDownloadUrl("Julia")), std::string::npos) << message;
    EXPECT_NE(message.find("NEVEN no instala motores"), std::string::npos) << message;
}

} // namespace
} // namespace rj2xcl
