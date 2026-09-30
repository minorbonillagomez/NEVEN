/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 */

#pragma once

#include <vector>
#include <string>
#include <memory>
#include "file_change_watcher.h"

namespace rj2xcl {

  /**
   * @brief Service to manage file system monitoring and hot-reloading of sources.
   * 
   * This class encapsulates FileChangeWatcher and the logic to route 
   * change notifications to the appropriate language services.
   */
  class FileWatchService {
  public:
    FileWatchService();
    ~FileWatchService();

    /**
     * @brief Adds a directory to be watched. Optionally loads existing files.
     */
    void WatchDirectory(const std::string &directory, bool load_existing = true);

    /**
     * @brief Attempts to load a source file into a compatible language service.
     */
    bool LoadLanguageFile(const std::string &file);

    /**
     * @brief Starts the background monitoring thread.
     */
    void Start();

    /**
     * @brief Stops the background monitoring thread.
     */
    void Stop();

    /**
     * @brief Internal callback triggered by the watcher thread.
     */
    void OnFilesChanged(const std::vector<std::string> &files);

  private:
    /** Wrapper for the low-level directory watcher */
    std::unique_ptr<FileChangeWatcher> watcher_;

    /** Static callback for the underlying watcher */
    static void WatcherCallback(void *argument, const std::vector<std::string> &files);
  };

} // namespace rj2xcl
