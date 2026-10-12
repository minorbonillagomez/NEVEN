/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#pragma once

#include "IExcelBridge.h"
#include <map>

namespace rj2xcl {

  /**
   * @brief Mock implementation of IExcelBridge for unit testing.
   */
  class MockExcelBridge : public IExcelBridge {
  public:
    MockExcelBridge() = default;
    virtual ~MockExcelBridge() = default;

    virtual int Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) override {
      call_counts_[xlfn]++;
      return xlretSuccess;
    }

    virtual int Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]) override {
      call_counts_[xlfn]++;
      return xlretSuccess;
    }

    /**
     * @brief Gets how many times a specific Excel function was called.
     */
    int GetCallCount(int xlfn) const {
      auto it = call_counts_.find(xlfn);
      return (it != call_counts_.end()) ? it->second : 0;
    }

    /**
     * @brief Resets all call counts.
     */
    void ClearCalls() {
      call_counts_.clear();
    }

  private:
    std::map<int, int> call_counts_;
  };

} // namespace rj2xcl
