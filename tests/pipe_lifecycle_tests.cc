/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Unit tests for pipe lifecycle and handle cleanup.
 * Validates: Requirements 8.1, 8.2, 11.1, 11.2, 11.3
 *
 * Tests verify that SafePipeHandle correctly manages Windows pipe handles
 * through their full lifecycle: creation, use, move semantics, and cleanup.
 */

#include <gtest/gtest.h>
#include "IPC/SafePipeHandle.h"

#include <windows.h>
#include <string>
#include <cstdio>

namespace rj2xcl {
namespace ipc {

class PipeLifecycleTests : public ::testing::Test {
protected:
    /**
     * @brief Creates a named pipe for testing and returns its handle.
     *
     * Uses a unique pipe name per test to avoid collisions.
     */
    HANDLE CreateTestPipe() {
        std::string pipe_name = "\\\\.\\pipe\\neven_test_pipe_" +
            std::to_string(GetCurrentProcessId()) + "_" +
            std::to_string(pipe_counter_++);

        HANDLE h = CreateNamedPipeA(
            pipe_name.c_str(),
            PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
            1,       // max instances
            4096,    // out buffer size
            4096,    // in buffer size
            0,       // default timeout
            nullptr  // default security
        );

        if (h != INVALID_HANDLE_VALUE) {
            created_pipe_names_.push_back(pipe_name);
        }
        return h;
    }

    /**
     * @brief Creates a connected pipe pair (server + client) for read/write tests.
     */
    bool CreateConnectedPipePair(HANDLE& server, HANDLE& client) {
        std::string pipe_name = "\\\\.\\pipe\\neven_test_pipe_" +
            std::to_string(GetCurrentProcessId()) + "_" +
            std::to_string(pipe_counter_++);

        server = CreateNamedPipeA(
            pipe_name.c_str(),
            PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
            1, 4096, 4096, 0, nullptr
        );

        if (server == INVALID_HANDLE_VALUE) return false;

        // Connect client side
        client = CreateFileA(
            pipe_name.c_str(),
            GENERIC_READ | GENERIC_WRITE,
            0, nullptr, OPEN_EXISTING,
            FILE_FLAG_OVERLAPPED, nullptr
        );

        if (client == INVALID_HANDLE_VALUE) {
            CloseHandle(server);
            server = INVALID_HANDLE_VALUE;
            return false;
        }

        return true;
    }

private:
    static int pipe_counter_;
    std::vector<std::string> created_pipe_names_;
};

int PipeLifecycleTests::pipe_counter_ = 0;

// ---------------------------------------------------------------------------
// Test 1: Default construction produces an invalid handle
// Validates: Requirement 8.1 — handle validity check before operations
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_DefaultConstruction_IsInvalid) {
    SafePipeHandle handle;
    EXPECT_FALSE(handle.IsValid());
    EXPECT_EQ(handle.Get(), INVALID_HANDLE_VALUE);
}

// ---------------------------------------------------------------------------
// Test 2: Wrapping a valid handle reports valid
// Validates: Requirement 8.1 — handle validity check
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_ValidHandle_IsValid) {
    HANDLE raw = CreateTestPipe();
    ASSERT_NE(raw, INVALID_HANDLE_VALUE) << "Failed to create test pipe";

    SafePipeHandle handle(raw);
    EXPECT_TRUE(handle.IsValid());
    EXPECT_EQ(handle.Get(), raw);
    // handle destructor will close it
}

// ---------------------------------------------------------------------------
// Test 3: Close() sets handle to invalid
// Validates: Requirement 8.2, 11.1 — close handle and free resources
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_Close_InvalidatesHandle) {
    HANDLE raw = CreateTestPipe();
    ASSERT_NE(raw, INVALID_HANDLE_VALUE);

    SafePipeHandle handle(raw);
    EXPECT_TRUE(handle.IsValid());

    handle.Close();
    EXPECT_FALSE(handle.IsValid());
    EXPECT_EQ(handle.Get(), INVALID_HANDLE_VALUE);
}

// ---------------------------------------------------------------------------
// Test 4: Destructor closes the handle (RAII cleanup)
// Validates: Requirement 11.1, 11.3 — automatic resource cleanup
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_Destructor_ClosesHandle) {
    HANDLE raw = CreateTestPipe();
    ASSERT_NE(raw, INVALID_HANDLE_VALUE);

    {
        SafePipeHandle handle(raw);
        EXPECT_TRUE(handle.IsValid());
    }
    // After destruction, the handle should be closed.
    // Attempting to close it again should fail (handle no longer valid).
    BOOL close_result = CloseHandle(raw);
    EXPECT_FALSE(close_result) << "Handle should already be closed by destructor";
}

// ---------------------------------------------------------------------------
// Test 5: Move construction transfers ownership — source becomes invalid
// Validates: Requirement 11.1, 11.3 — no double-close, clean ownership transfer
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_MoveConstruction_TransfersOwnership) {
    HANDLE raw = CreateTestPipe();
    ASSERT_NE(raw, INVALID_HANDLE_VALUE);

    SafePipeHandle source(raw);
    EXPECT_TRUE(source.IsValid());

    SafePipeHandle dest(std::move(source));

    // Source should be invalid after move
    EXPECT_FALSE(source.IsValid());
    EXPECT_EQ(source.Get(), INVALID_HANDLE_VALUE);

    // Destination should own the handle
    EXPECT_TRUE(dest.IsValid());
    EXPECT_EQ(dest.Get(), raw);
}

// ---------------------------------------------------------------------------
// Test 6: Move assignment transfers ownership — old handle closed
// Validates: Requirement 11.1, 11.3 — old handle freed, no leaks
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_MoveAssignment_TransfersOwnership) {
    HANDLE raw_a = CreateTestPipe();
    HANDLE raw_b = CreateTestPipe();
    ASSERT_NE(raw_a, INVALID_HANDLE_VALUE);
    ASSERT_NE(raw_b, INVALID_HANDLE_VALUE);

    SafePipeHandle handle_a(raw_a);
    SafePipeHandle handle_b(raw_b);

    // Move-assign b into a — a's old handle (raw_a) should be closed
    handle_a = std::move(handle_b);

    // handle_a now owns raw_b
    EXPECT_TRUE(handle_a.IsValid());
    EXPECT_EQ(handle_a.Get(), raw_b);

    // handle_b (source) should be invalid
    EXPECT_FALSE(handle_b.IsValid());
    EXPECT_EQ(handle_b.Get(), INVALID_HANDLE_VALUE);

    // raw_a should have been closed by the move assignment
    BOOL close_result = CloseHandle(raw_a);
    EXPECT_FALSE(close_result) << "Old handle should have been closed by move assignment";
}

// ---------------------------------------------------------------------------
// Test 7: AtomicRead on invalid handle returns false
// Validates: Requirement 8.1, 8.2 — atomic validity check before read
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_AtomicRead_InvalidHandle_ReturnsFalse) {
    SafePipeHandle handle; // default = INVALID_HANDLE_VALUE

    char buffer[64] = {};
    DWORD bytes_read = 0;
    OVERLAPPED ov = {};
    ov.hEvent = CreateEvent(nullptr, TRUE, FALSE, nullptr);

    bool result = handle.AtomicRead(buffer, sizeof(buffer), &bytes_read, &ov);
    EXPECT_FALSE(result) << "AtomicRead should fail on invalid handle";

    if (ov.hEvent) CloseHandle(ov.hEvent);
}

// ---------------------------------------------------------------------------
// Test 8: AtomicWrite on invalid handle returns false
// Validates: Requirement 8.1, 8.2 — atomic validity check before write
// ---------------------------------------------------------------------------

TEST_F(PipeLifecycleTests, SafePipeHandle_AtomicWrite_InvalidHandle_ReturnsFalse) {
    SafePipeHandle handle; // default = INVALID_HANDLE_VALUE

    const char data[] = "test message";
    DWORD bytes_written = 0;
    OVERLAPPED ov = {};
    ov.hEvent = CreateEvent(nullptr, TRUE, FALSE, nullptr);

    bool result = handle.AtomicWrite(data, sizeof(data), &bytes_written, &ov);
    EXPECT_FALSE(result) << "AtomicWrite should fail on invalid handle";

    if (ov.hEvent) CloseHandle(ov.hEvent);
}

} // namespace ipc
} // namespace rj2xcl
