/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * Integration tests for CallbackDispatcher.
 */

#include <gtest/gtest.h>
#include "CallbackDispatcher.h"
#include "ICallbackHandler.h"
#include <memory>

namespace rj2xcl {

class MockHandler : public ICallbackHandler {
public:
    MockHandler(const std::string& type) : type_(type), handled_count(0) {}

    virtual std::string GetType() const override { return type_; }

    virtual Result<void, int> Handle(const std::string &language, 
                                     const RJ2XCLBuffers::CallResponse &call, 
                                     RJ2XCLBuffers::CallResponse &response) override {
        handled_count++;
        last_language = language;
        return Result<void, int>::Success();
    }

    std::string type_;
    int handled_count;
    std::string last_language;
};

TEST(CallbackDispatcherTest, RegisterAndDispatch) {
    CallbackDispatcher dispatcher;
    
    auto com_handler_ptr = new MockHandler("COM");
    auto graphics_handler_ptr = new MockHandler("graphics");
    
    dispatcher.RegisterHandler(std::unique_ptr<ICallbackHandler>(com_handler_ptr));
    dispatcher.RegisterHandler(std::unique_ptr<ICallbackHandler>(graphics_handler_ptr));

    RJ2XCLBuffers::CallResponse call, response;
    
    // Dispatch COM
    auto res1 = dispatcher.Dispatch("COM", "R", call, response);
    EXPECT_TRUE(res1.is_success());
    EXPECT_EQ(com_handler_ptr->handled_count, 1);
    EXPECT_EQ(com_handler_ptr->last_language, "R");
    EXPECT_EQ(graphics_handler_ptr->handled_count, 0);

    // Dispatch Graphics
    auto res2 = dispatcher.Dispatch("graphics", "Julia", call, response);
    EXPECT_TRUE(res2.is_success());
    EXPECT_EQ(graphics_handler_ptr->handled_count, 1);
    EXPECT_EQ(graphics_handler_ptr->last_language, "Julia");
}

TEST(CallbackDispatcherTest, MissingHandler) {
    CallbackDispatcher dispatcher;
    RJ2XCLBuffers::CallResponse call, response;

    auto res = dispatcher.Dispatch("unknown", "R", call, response);
    EXPECT_TRUE(res.is_failure());
    EXPECT_EQ(res.error(), -1); // Assuming -1 for missing handler
}

} // namespace rj2xcl
