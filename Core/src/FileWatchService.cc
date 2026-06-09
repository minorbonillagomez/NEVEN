/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 */

#include "stdafx.h"
#include "FileWatchService.h"
#include "LanguageManager.h"
#include "rj2xcl.h"

namespace rj2xcl {

  FileWatchService::FileWatchService() {
    watcher_ = std::make_unique<FileChangeWatcher>(FileWatchService::WatcherCallback, this);
  }

  FileWatchService::~FileWatchService() {
    Stop();
  }

  void FileWatchService::WatchDirectory(const std::string &directory, bool load_existing) {
    if (watcher_) {
      if (load_existing) {
        // Initial load of existing files in the directory
        std::vector<std::pair<std::string, FILETIME>> entries = APIFunctions::ListDirectory(directory);
        for (const auto &file_info : entries) {
           LoadLanguageFile(file_info.first);
        }
      }
      watcher_->WatchDirectory(directory);
    }
  }

  void FileWatchService::Start() {
    if (watcher_) {
      watcher_->StartWatch();
    }
  }

  void FileWatchService::Stop() {
    if (watcher_) {
      watcher_->Shutdown();
    }
  }

  void FileWatchService::WatcherCallback(void *argument, const std::vector<std::string> &files) {
    FileWatchService *service = reinterpret_cast<FileWatchService*>(argument);
    if (service) {
      service->OnFilesChanged(files);
    }
  }

  void FileWatchService::OnFilesChanged(const std::vector<std::string> &files) {
    bool updated = false;
    for (const auto &file : files) {
      updated = updated || LoadLanguageFile(file);
    }

    if (updated) {
      RJ2XCL_LOG_INFO("Hot-reload triggered: Source files updated.");
      // Trigger macro update in Excel to reflect potential new functions
      RJ2XCL_Engine::Instance()->UpdateFunctions();
    }
  }

  bool FileWatchService::LoadLanguageFile(const std::string &file) {
    // Check available languages via LanguageManager
    for (auto language_service : rj2xcl::LanguageManager::Instance().GetServices()) {
      if (language_service->ValidFile(file)) {
        RJ2XCL_LOG_DEBUG("File watch: matched %s to %s", file.c_str(), language_service->name().c_str());
        
        // Load the source into the service
        language_service->ReadSourceFile(file);
        return true;
      }
    }
    return false;
  }

} // namespace rj2xcl
