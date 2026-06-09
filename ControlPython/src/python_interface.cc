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

#include "python_interface.h"
#include "child_process_log.h"
#include "windows_api_functions.h"
#include "result.h"
#include "json11/json11.hpp"
#include "string_utilities.h"

#include <Python.h>

// ─── Global state ────────────────────────────────────────────────────────────

static bool g_startup_failed = false;

static const int kMaxStartupRetries = 3;
static const int kRetryDelayMs = 100;

// ─── Type Conversion: Variable ↔ PyObject ────────────────────────────────────

/**
 * @brief Convert a Protobuf Variable to a Python object.
 */
static PyObject* VariableToPyObject(const RJ2XCLBuffers::Variable& variable) {
  switch (variable.value_case()) {
    case RJ2XCLBuffers::Variable::kBoolean:
      return PyBool_FromLong(variable.boolean() ? 1 : 0);

    case RJ2XCLBuffers::Variable::kReal:
      return PyFloat_FromDouble(variable.real());

    case RJ2XCLBuffers::Variable::kInteger:
      return PyLong_FromLongLong(variable.integer());

    case RJ2XCLBuffers::Variable::kStr:
      return PyUnicode_FromStringAndSize(variable.str().c_str(), variable.str().length());

    case RJ2XCLBuffers::Variable::kNil:
      Py_RETURN_NONE;

    case RJ2XCLBuffers::Variable::kArr: {
      const RJ2XCLBuffers::Array& arr = variable.arr();
      int len = arr.data_size();
      int nrows = arr.rows();
      int ncols = arr.cols();

      if (ncols <= 1 || len == nrows) {
        // 1D array → Python list
        PyObject* list = PyList_New(len);
        for (int i = 0; i < len; i++) {
          PyObject* item = VariableToPyObject(arr.data(i));
          PyList_SET_ITEM(list, i, item); // steals reference
        }
        return list;
      }
      else {
        // 2D array → list of lists (row-major)
        PyObject* outer = PyList_New(nrows);
        for (int r = 0; r < nrows; r++) {
          PyObject* row = PyList_New(ncols);
          for (int c = 0; c < ncols; c++) {
            int idx = r + nrows * c; // column-major storage
            PyObject* item = VariableToPyObject(arr.data(idx));
            PyList_SET_ITEM(row, c, item);
          }
          PyList_SET_ITEM(outer, r, row);
        }
        return outer;
      }
    }

    default:
      Py_RETURN_NONE;
  }
}

/**
 * @brief Convert a Python object to a Protobuf Variable.
 */
static void PyObjectToVariable(RJ2XCLBuffers::Variable* variable, PyObject* obj) {
  if (obj == Py_None || obj == nullptr) {
    variable->set_nil(true);
    return;
  }

  if (PyBool_Check(obj)) {
    variable->set_boolean(obj == Py_True);
    return;
  }

  if (PyLong_Check(obj)) {
    long long val = PyLong_AsLongLong(obj);
    if (val == -1 && PyErr_Occurred()) {
      PyErr_Clear();
      // Overflow — try as float
      double dval = PyLong_AsDouble(obj);
      variable->set_real(dval);
    }
    else {
      variable->set_integer(val);
    }
    return;
  }

  if (PyFloat_Check(obj)) {
    variable->set_real(PyFloat_AsDouble(obj));
    return;
  }

  if (PyUnicode_Check(obj)) {
    Py_ssize_t size;
    const char* str = PyUnicode_AsUTF8AndSize(obj, &size);
    if (str) {
      variable->set_str(std::string(str, size));
    }
    else {
      PyErr_Clear();
      variable->set_str("");
    }
    return;
  }

  if (PyList_Check(obj) || PyTuple_Check(obj)) {
    Py_ssize_t len = PySequence_Size(obj);
    auto arr = variable->mutable_arr();
    arr->set_rows((int)len);
    arr->set_cols(1);
    for (Py_ssize_t i = 0; i < len; i++) {
      PyObject* item = PySequence_GetItem(obj, i);
      PyObjectToVariable(arr->add_data(), item);
      Py_XDECREF(item);
    }
    return;
  }

  if (PyDict_Check(obj)) {
    // Convert dict to a list of [key, value] pairs
    PyObject* items = PyDict_Items(obj);
    Py_ssize_t len = PyList_Size(items);
    auto arr = variable->mutable_arr();
    arr->set_rows((int)len);
    arr->set_cols(2);
    for (Py_ssize_t i = 0; i < len; i++) {
      PyObject* pair = PyList_GetItem(items, i);
      PyObject* key = PyTuple_GetItem(pair, 0);
      PyObject* val = PyTuple_GetItem(pair, 1);
      PyObjectToVariable(arr->add_data(), key);
      PyObjectToVariable(arr->add_data(), val);
    }
    Py_DECREF(items);
    return;
  }

  // Fallback: convert to string representation
  PyObject* repr = PyObject_Repr(obj);
  if (repr) {
    Py_ssize_t size;
    const char* str = PyUnicode_AsUTF8AndSize(repr, &size);
    if (str) variable->set_str(std::string(str, size));
    Py_DECREF(repr);
  }
  else {
    PyErr_Clear();
    variable->set_str("<unconvertible>");
  }
}

// ─── Startup ─────────────────────────────────────────────────────────────────

void PythonInit(const std::string& config_path) {

  // Locate startup.py
  std::string startup_path = config_path;
  if (!startup_path.empty() && startup_path.back() != '\\' && startup_path.back() != '/') {
    startup_path += "\\";
  }
  startup_path += "startup\\startup.py";

  CHILD_LOG("Loading startup.py from: %s", startup_path.c_str());

  auto startup_result = APIFunctions::FileContents(startup_path);
  if (!startup_result.is_success()) {
    CHILD_LOG_ERR("Failed to read startup.py: %s", startup_path.c_str());
    g_startup_failed = true;
    return;
  }

  const std::string& startup_code = startup_result.value();
  CHILD_LOG("startup.py loaded (%zu bytes)", startup_code.size());

  // Retry loop: execute startup.py with up to kMaxStartupRetries attempts
  for (int attempt = 1; attempt <= kMaxStartupRetries; attempt++) {
    int rc = PyRun_SimpleString(startup_code.c_str());
    if (rc == 0) {
      CHILD_LOG("startup.py executed successfully (attempt %d/%d)", attempt, kMaxStartupRetries);
      return; // Success
    }

    // Failure — clear Python error state and retry
    PyErr_Clear();
    CHILD_LOG_WARN("startup.py attempt %d/%d failed (rc=%d)", attempt, kMaxStartupRetries, rc);

    if (attempt < kMaxStartupRetries) {
      Sleep(kRetryDelayMs);
    }
  }

  // All retries exhausted
  CHILD_LOG_ERR("startup.py failed after %d attempts — marking startup as failed", kMaxStartupRetries);
  g_startup_failed = true;
}

bool PythonStartupSucceeded() {
  return !g_startup_failed;
}

// ─── Exec ────────────────────────────────────────────────────────────────────

void PythonExec(RJ2XCLBuffers::CallResponse& response, const RJ2XCLBuffers::CallResponse& call) {

  // Assemble code from lines
  std::string code;
  for (int i = 0; i < call.code().line_size(); i++) {
    if (i > 0) code += "\n";
    code += call.code().line(i);
  }

  if (code.empty()) {
    response.mutable_result()->set_nil(true);
    return;
  }

  int rc = PyRun_SimpleString(code.c_str());
  if (rc != 0) {
    PyErr_Clear();
    auto err = response.mutable_result()->mutable_err();
    err->set_message("Python execution error");
    CHILD_LOG_ERR("PythonExec failed (rc=%d)", rc);
  }
  else {
    response.mutable_result()->set_boolean(true);
  }
}

// ─── Call ────────────────────────────────────────────────────────────────────

void PythonCall(RJ2XCLBuffers::CallResponse& response, const RJ2XCLBuffers::CallResponse& call) {

  std::string function_name = call.function_call().function();

  // Get the function from __main__
  PyObject* main_module = PyImport_AddModule("__main__");
  if (!main_module) {
    PyErr_Clear();
    auto err = response.mutable_result()->mutable_err();
    err->set_message("Failed to get __main__ module");
    return;
  }

  PyObject* main_dict = PyModule_GetDict(main_module);
  PyObject* func = PyDict_GetItemString(main_dict, function_name.c_str());

  if (!func || !PyCallable_Check(func)) {
    auto err = response.mutable_result()->mutable_err();
    err->set_message("Function not found or not callable: " + function_name);
    CHILD_LOG_ERR("PythonCall: function '%s' not found", function_name.c_str());
    return;
  }

  // Build arguments tuple
  int arg_count = call.function_call().arguments_size();
  PyObject* args = PyTuple_New(arg_count);
  for (int i = 0; i < arg_count; i++) {
    PyObject* arg = VariableToPyObject(call.function_call().arguments(i));
    PyTuple_SET_ITEM(args, i, arg); // steals reference
  }

  // Call the function
  PyObject* result = PyObject_CallObject(func, args);
  Py_DECREF(args);

  if (result) {
    PyObjectToVariable(response.mutable_result(), result);
    Py_DECREF(result);
  }
  else {
    PyErr_Clear();
    auto err = response.mutable_result()->mutable_err();
    err->set_message("Python function call failed: " + function_name);
    CHILD_LOG_ERR("PythonCall: '%s' raised an exception", function_name.c_str());
  }
}

// ─── Shell Exec ──────────────────────────────────────────────────────────────

int PythonShellExec(const std::string& command, std::string& shell_buffer) {

  std::string full_code = shell_buffer + command;

  // Check for incomplete input (multi-line)
  // Use compile() to check if the code is complete
  PyObject* code_obj = Py_CompileString(full_code.c_str(), "<shell>", Py_single_input);
  if (!code_obj) {
    // Check if it's a syntax error (incomplete) or a real error
    if (PyErr_ExceptionMatches(PyExc_SyntaxError)) {
      // Could be incomplete — check if adding more input might help
      PyObject *type, *value, *traceback;
      PyErr_Fetch(&type, &value, &traceback);

      // If the error message contains "unexpected EOF", it's incomplete
      PyObject* msg_str = value ? PyObject_Str(value) : nullptr;
      bool is_incomplete = false;
      if (msg_str) {
        const char* msg = PyUnicode_AsUTF8(msg_str);
        if (msg && (strstr(msg, "unexpected EOF") || strstr(msg, "was never closed"))) {
          is_incomplete = true;
        }
        Py_DECREF(msg_str);
      }

      Py_XDECREF(type);
      Py_XDECREF(value);
      Py_XDECREF(traceback);

      if (is_incomplete) {
        return 1; // Incomplete
      }
    }
    PyErr_Clear();
  }

  if (code_obj) {
    Py_DECREF(code_obj);
  }

  // Execute the complete code
  int rc = PyRun_SimpleString(full_code.c_str());
  if (rc != 0) {
    PyErr_Clear();
  }

  return 0; // Complete (success or error)
}

// ─── List Functions ──────────────────────────────────────────────────────────

void ListScriptFunctions(RJ2XCLBuffers::CallResponse& response, const RJ2XCLBuffers::CallResponse& call) {

  // Call list_functions() in __main__
  PyObject* main_module = PyImport_AddModule("__main__");
  if (!main_module) {
    PyErr_Clear();
    return;
  }

  PyObject* main_dict = PyModule_GetDict(main_module);
  PyObject* func = PyDict_GetItemString(main_dict, "list_functions");

  if (!func || !PyCallable_Check(func)) {
    CHILD_LOG_WARN("list_functions() not defined in __main__");
    response.mutable_result()->set_nil(true);
    return;
  }

  PyObject* result = PyObject_CallNoArgs(func);
  if (!result) {
    PyErr_Clear();
    CHILD_LOG_ERR("list_functions() raised an exception");
    response.mutable_result()->set_nil(true);
    return;
  }

  // Convert result to Variable
  PyObjectToVariable(response.mutable_result(), result);
  Py_DECREF(result);
}

// ─── Read Source File ────────────────────────────────────────────────────────

bool ReadSourceFile(const std::string& file, bool notify) {

  // Call read_script_file(path) in __main__
  PyObject* main_module = PyImport_AddModule("__main__");
  if (!main_module) {
    PyErr_Clear();
    return false;
  }

  PyObject* main_dict = PyModule_GetDict(main_module);
  PyObject* func = PyDict_GetItemString(main_dict, "read_script_file");

  if (!func || !PyCallable_Check(func)) {
    // Fallback: use exec(open(file).read())
    CHILD_LOG("read_script_file not defined, using exec fallback for: %s", file.c_str());
    auto file_result = APIFunctions::FileContents(file);
    if (!file_result.is_success()) {
      CHILD_LOG_ERR("Failed to read file: %s", file.c_str());
      return false;
    }
    int rc = PyRun_SimpleString(file_result.value().c_str());
    if (rc != 0) {
      PyErr_Clear();
      CHILD_LOG_ERR("Error executing file: %s", file.c_str());
      return false;
    }
    return true;
  }

  PyObject* py_path = PyUnicode_FromString(file.c_str());
  PyObject* py_notify = PyBool_FromLong(notify ? 1 : 0);
  PyObject* args = PyTuple_Pack(2, py_path, py_notify);

  PyObject* result = PyObject_CallObject(func, args);
  Py_DECREF(args);
  Py_DECREF(py_path);
  Py_DECREF(py_notify);

  if (!result) {
    PyErr_Clear();
    CHILD_LOG_ERR("read_script_file() failed for: %s", file.c_str());
    return false;
  }

  bool success = (result == Py_True || (PyLong_Check(result) && PyLong_AsLong(result) != 0));
  Py_DECREF(result);
  return success;
}
