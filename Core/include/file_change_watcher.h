/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#include <vector>
#include <string>

#include "UniqueHandle.h"
#include "Constants.h"

// the loop timeout also functions as a debounce timeout,
// because we receive duplicate notifications on file changes.
// we can use separate timeouts for debouncing...

#define FILE_WATCH_EVENT_MASK (FILE_NOTIFY_CHANGE_LAST_WRITE|FILE_NOTIFY_CHANGE_FILE_NAME)

typedef void (*FileWatchCallback)(void*, const std::vector<std::string>&);

/**
 * @brief Watches directories for file changes and notifies via callback.
 *
 * Runs a background thread that monitors registered directories using
 * ReadDirectoryChangesW. When changes are detected (after debouncing),
 * invokes the registered callback with the list of changed files.
 */
class FileChangeWatcher {

private:
  std::vector < std::string > watched_directories_;
  rj2xcl::UniqueHandle update_watch_list_handle_;
  CRITICAL_SECTION critical_section_;

  void *callback_argument_;
  FileWatchCallback callback_function_;

private:

  /** @brief Thread start routine (static entry point). */
  static uint32_t __stdcall StartThread(void *data);

  /**
   * @brief Processes directory change notifications.
   * @param directory_list List of directories with changes.
   * @param update_time Timestamp of the change event.
   */
  void NotifyDirectoryChanges(const std::vector<std::string> &directory_list, FILETIME update_time);

  /** @brief Instance thread routine (runs the watch loop). */
  uint32_t InstanceStartThread();

  /** @brief Control flag for the watch loop. */
  bool running_;

public:
  /**
   * @brief Constructs a FileChangeWatcher with an optional callback.
   * @param callback Function pointer called when files change.
   * @param argument Opaque pointer passed to the callback.
   */
  FileChangeWatcher(FileWatchCallback callback = 0, void *argument = 0);
  ~FileChangeWatcher();

public:
  /**
   * @brief Adds a directory to the watch list.
   * @param directory Absolute path to the directory to monitor.
   */
  void WatchDirectory(const std::string &directory);

  /**
   * @brief Removes a directory from the watch list.
   * @param directory Absolute path to the directory to stop monitoring.
   */
  void UnwatchDirectory(const std::string &directory);

  /** @brief Starts the background watch thread. */
  void StartWatch();

  /** @brief Stops the watch thread and releases resources. */
  void Shutdown();

};
