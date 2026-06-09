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
 
#include "pipe.h"
#include "Constants.h"

Pipe::Pipe()
  : handle_()
  , buffer_size_(rj2xcl::Constants::kPipeBufferSize)
  , read_buffer_(0)
  , reading_(false)
  , writing_(false)
  , connected_(false)
  , error_(false)
{
  memset(&read_io_, 0, sizeof(read_io_));
  memset(&write_io_, 0, sizeof(write_io_));
}

Pipe::~Pipe() {
  // SafePipeHandle RAII handles pipe closure automatically.
  // Cancel pending I/O before handle destruction.
  if (handle_.IsValid()) {
    CancelIo(handle_.Get());
  }
  // handle_ destructor will CloseHandle via SafePipeHandle::Close()

  if (read_io_.hEvent) CloseHandle(read_io_.hEvent);
  if (write_io_.hEvent) CloseHandle(write_io_.hEvent);
  if (read_buffer_) delete[] read_buffer_;
}

HANDLE Pipe::pipe_handle() { return handle_.Get(); }

HANDLE Pipe::wait_handle_read() { return read_io_.hEvent; }

HANDLE Pipe::wait_handle_write() { return write_io_.hEvent; }

DWORD Pipe::buffer_size() { return buffer_size_; }

void Pipe::QueueWrites(std::vector<std::string> &list) {
  for (auto entry : list) {
    write_stack_.push_back(entry);
  }
}

void Pipe::PushWrite(const std::string &message) {
  write_stack_.push_back(message);
  NextWrite();
}

int Pipe::StartRead() {
  if (reading_ || error_ || !connected_) return 0;
  reading_ = true;
  ResetEvent(read_io_.hEvent);
  handle_.AtomicRead(read_buffer_, buffer_size_, 0, &read_io_);
  return 0;
}

void Pipe::ClearError() {
  error_ = false;
}

void Pipe::Connect(bool start_read) {
  connected_ = true;
  // (pipe log removed — shared code)
  if (start_read) StartRead();
}

DWORD Pipe::Reset() {

  CancelIo(handle_.Get());
  ResetEvent(read_io_.hEvent);
  ResetEvent(write_io_.hEvent);
  DisconnectNamedPipe(handle_.Get());

  connected_ = reading_ = writing_ = error_ = false;
  message_buffer_.clear();

  if (ConnectNamedPipe(handle_.Get(), &read_io_)) {
  // (pipe log removed — shared code)
  }
  else {
    switch (GetLastError()) {
    case ERROR_PIPE_CONNECTED:
      SetEvent(read_io_.hEvent);
      break;
    case ERROR_IO_PENDING:
      break;
    default:
  // (pipe log removed — shared code)
      return GetLastError();
      break;
    }
  }

  return 0;
}

int Pipe::NextWrite() {

  DWORD bytes, result;

  if (write_stack_.size() == 0) {
    ResetEvent(write_io_.hEvent);
    writing_ = false;
    return 0; // no write
  }
  else if (writing_) {

    // if we are currently in a write operation, 
    // check if it's complete.

//    result = GetOverlappedResultEx(handle_, &write_io_, &bytes, 0, FALSE);
    result = GetOverlappedResult(handle_.Get(), &write_io_, &bytes, FALSE);
    if (!result) {
      DWORD err = GetLastError();
      switch (err) {
      case WAIT_TIMEOUT:
      case WAIT_IO_COMPLETION:
      case ERROR_IO_INCOMPLETE:
        return 0; // write in progress
      default:
        error_ = true;
        // error logged via return code
        return 0; // err (need a flag here)
      }
    }
  }

  // at this point we're safe to write. we can push more than
  // one write if they complete immediately

  while (write_stack_.size()) {

    ResetEvent(write_io_.hEvent);
    std::string message = write_stack_.front();
    write_stack_.pop_front();
    handle_.AtomicWrite(message.c_str(), (DWORD)message.length(), NULL, &write_io_);
    //result = GetOverlappedResultEx(handle_, &write_io_, &bytes, 0, FALSE);
    result = GetOverlappedResult(handle_.Get(), &write_io_, &bytes, FALSE);
    if (result) {
      // std::cout << "immediate write success (" << bytes << ")" << std::endl;
      ResetEvent(write_io_.hEvent);
      writing_ = false;
    }
    else {
      // std::cout << "write pending" << std::endl;
      writing_ = true;
      return 0;
    }
  }

  return 1;
}

DWORD Pipe::Read(std::string &buf, bool block) {

  // Message mode: if buffer is too small, GetLastError returns ERROR_MORE_DATA.
  // The caller must accumulate partial reads via message_buffer_.

  DWORD bytes = 0;
//  DWORD success = GetOverlappedResultEx(handle_, &read_io_, &bytes, block ? INFINITE : 0, FALSE);
  DWORD success = GetOverlappedResult(handle_.Get(), &read_io_, &bytes, block ? TRUE : FALSE);

  if (success) {
    if (message_buffer_.length()) {
      // std::cout << "appending long mesage (" << bytes << "), this is the end" << std::endl;
      buf = message_buffer_;
      buf.append(read_buffer_, bytes);
      message_buffer_.clear();
    }
    else buf.assign(read_buffer_, bytes);
    reading_ = false;
    return 0;
  }
  else {
    DWORD err = GetLastError();
    if (err == ERROR_MORE_DATA) {
      // std::cout << "appending long mesage (" << bytes << "), this is a chunk" << std::endl;
      message_buffer_.append(read_buffer_, bytes);
      reading_ = false;
      StartRead();
      return err;
    }
    if (err != WAIT_TIMEOUT) error_ = true;
    return err;
  }

}

std::string Pipe::full_name() {
  std::stringstream pipename;
  pipename << "\\\\.\\pipe\\" << name_;
  return pipename.str().c_str();
}

DWORD Pipe::Start(std::string name, bool wait) {

  name_ = name;

  HANDLE raw_handle = CreateNamedPipeA(full_name().c_str(),
    PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
    PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
    rj2xcl::Constants::kMaxPipeCount,
    rj2xcl::Constants::kPipeBufferSize,
    rj2xcl::Constants::kPipeBufferSize,
    100,
    NULL);

  if (NULL == raw_handle || raw_handle == INVALID_HANDLE_VALUE) {
    // error logged via return code
    return -1;
  }

  handle_ = rj2xcl::ipc::SafePipeHandle(raw_handle);

  read_io_.hEvent = CreateEvent(0, TRUE, FALSE, 0);
  write_io_.hEvent = CreateEvent(0, TRUE, FALSE, 0);

  read_buffer_ = new char[buffer_size_];
  
  if (ConnectNamedPipe(handle_.Get(), &read_io_)) {
  // (pipe log removed — shared code)
  }
  else {
    switch (GetLastError()) {
    case ERROR_PIPE_CONNECTED:
      SetEvent(read_io_.hEvent);
      break;
    case ERROR_IO_PENDING:
      break;
    default:
  // (pipe log removed — shared code)
      return GetLastError();
      break;
    }
  }

  if (!wait) return 0;

  while (true) {

    DWORD bytes;

    WaitForSingleObject(read_io_.hEvent, 1000);
    DWORD rslt = GetOverlappedResult(handle_.Get(), &read_io_, &bytes, FALSE);


    if (rslt) {
  // (pipe log removed — shared code)
      return 0;
    }
    else {
      DWORD err = GetLastError();
      if (err != WAIT_TIMEOUT) {
        error_ = true;
        return err;
      }
    }

  }


  return -2;
}



