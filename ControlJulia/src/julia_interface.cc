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

#include "julia_interface.h"
#include "child_process_log.h"

#define JULIA_ENABLE_THREADING 1
#include "julia.h"
#include "julia_compat.h"

#include "windows_api_functions.h"
#include "result.h"
#include "json11/json11.hpp"

// Julia 1.x+ does not use jl_ptls_t directly
// jl_ptls_t ptls; // REMOVED for Julia 1.x compatibility

jl_value_t * VariableToJlValue(const RJ2XCLBuffers::Variable *variable) {

  jl_value_t* value = jl_nothing;

  switch (variable->value_case()) {
  case RJ2XCLBuffers::Variable::kBoolean:
    value = jl_box_bool(variable->boolean());
    break;

  case RJ2XCLBuffers::Variable::kReal:
    value = jl_box_float64(variable->real());
    break;

  case RJ2XCLBuffers::Variable::kInteger:
    value = jl_box_int64(variable->integer());
    break;

  case RJ2XCLBuffers::Variable::kStr:
    value = jl_pchar_to_string(variable->str().c_str(), variable->str().length());
    break;

  case RJ2XCLBuffers::Variable::kComPointer:
  {
    const auto &com_pointer = variable->com_pointer();

    jl_value_t* array_type = jl_apply_array_type((jl_value_t*)jl_any_type, 1);
    jl_array_t* julia_array = jl_alloc_array_1d(array_type, 4);

    //jl_value_t *element = VariableToJlValue(&(arr.data(i)));
    //jl_arrayset(julia_array, element, i);

    // name
    jl_arrayset(julia_array,
      jl_pchar_to_string(com_pointer.interface_name().c_str(), com_pointer.interface_name().length()), 0);

    // pointer (literal)
    jl_arrayset(julia_array, jl_box_uint64(com_pointer.pointer()), 1);

    // functions
    if (com_pointer.functions_size()) {
      jl_array_t *functions_array = jl_alloc_array_1d(array_type, com_pointer.functions_size());
      for (int i = 0, len = com_pointer.functions_size(); i < len; i++) {
        const auto &function_definition = com_pointer.functions(i);

         // function definition should be name, type, index, [params]
        jl_array_t *function_def_array = jl_alloc_array_1d(array_type, 4);

        jl_arrayset(function_def_array, 
          jl_pchar_to_string(function_definition.function().name().c_str(), function_definition.function().name().length()), 0);

        std::string call_type = "method";
        switch (function_definition.call_type()) {
        case RJ2XCLBuffers::CallType::get: call_type = "get";
          break;
        case RJ2XCLBuffers::CallType::put: call_type = "put";
          break;
        }

        jl_arrayset(function_def_array, jl_pchar_to_string(call_type.c_str(), call_type.length()), 1);
        jl_arrayset(function_def_array, jl_box_uint32(function_definition.function().index()), 2);

        int arguments_count = function_definition.arguments_size();
        if (arguments_count > 0) {
          jl_array_t *arguments_array = jl_alloc_array_1d(array_type, arguments_count);
          for (int j = 0; j < arguments_count; j++) {
            const auto &argument = function_definition.arguments(j);
            jl_arrayset(arguments_array,
              jl_pchar_to_string(argument.name().c_str(), argument.name().length()), j);
          }
          jl_arrayset(function_def_array, (jl_value_t*)arguments_array, 3);
        }
        else {
          jl_arrayset(function_def_array, jl_nothing, 3);
        }

        jl_arrayset(functions_array, (jl_value_t*)function_def_array, i);
      }
      jl_arrayset(julia_array, (jl_value_t*)functions_array, 2);
    }
    else jl_arrayset(julia_array, jl_nothing, 2);

    // enums
    if (com_pointer.enums_size()) {
      jl_array_t *enums_array = jl_alloc_array_1d(array_type, com_pointer.enums_size());
      //jl_tupletype_t *tupletype = jl_apply_tuple_type(jl_svec2(jl_string_type, jl_int32_type));

      for (int i = 0, len = com_pointer.enums_size(); i < len; i++) {
        const auto &enum_definition = com_pointer.enums(i);

        jl_array_t *enum_array = jl_alloc_array_1d(array_type, 2);
        jl_arrayset(enum_array, jl_pchar_to_string(enum_definition.name().c_str(), enum_definition.name().length()), 0);

        int enum_values_length = enum_definition.values_size();
        jl_array_t *enum_values_array = jl_alloc_array_1d(array_type, enum_values_length);
        for (int j = 0; j < enum_values_length; j++) {

          auto enum_value_list = enum_definition.values(j);

          jl_value_t* jl_value_name = jl_pchar_to_string(enum_value_list.name().c_str(), enum_value_list.name().length());
          jl_value_t* jl_value_value = jl_box_int32(enum_value_list.value());
          jl_svec_t* svec = jl_svec2(jl_value_name, jl_value_value);

          jl_arrayset(enum_values_array, (jl_value_t*)svec, j);

        }
        jl_arrayset(enum_array, (jl_value_t*)enum_values_array, 1);

        jl_arrayset(enums_array, (jl_value_t*)enum_array, i);
      }
      jl_arrayset(julia_array, (jl_value_t*)enums_array, 3);
    }
    else jl_arrayset(julia_array, jl_nothing, 3);

    value = (jl_value_t*)julia_array;

    break;
  }
  case RJ2XCLBuffers::Variable::kArr:
  {
    const RJ2XCLBuffers::Array &arr = variable->arr();

    int nrows = arr.rows();
    int ncols = arr.cols();
    int len = arr.data_size();

    if (!nrows || !ncols || len != (nrows * ncols)) {
      ncols = 1;
      nrows = len;
    }

    
        // if the array is a single type (we already do this somewhat for R); then we
    // can use more efficient julia arrays and use a data pointer rather than the 
    // set() syntax

    // julia doesn't like sparse arrays [actually they are fine, but they're a 
    // separate type; we will only allow full arrays]

    MessageUtilities::TypeFlags type_flags = MessageUtilities::CheckArrayType(arr, false, false);

    jl_datatype_t *array_base_type = jl_any_type;
    if (type_flags & MessageUtilities::TypeFlags::integer) array_base_type = jl_int64_type;
    else if (type_flags & MessageUtilities::TypeFlags::numeric) array_base_type = jl_float64_type;
    else if (type_flags & MessageUtilities::TypeFlags::string) array_base_type = jl_string_type;
    else if (type_flags & MessageUtilities::TypeFlags::logical) array_base_type = jl_bool_type;

    jl_array_t *julia_array = 0; //  jl_nothing;
    if (ncols == 1) 
    {
      jl_value_t* array_type = jl_apply_array_type((jl_value_t*)array_base_type, 1);
      julia_array = jl_alloc_array_1d(array_type, nrows);
      
      for (int i = 0; i < nrows; i++) {
        jl_value_t *element = VariableToJlValue(&(arr.data(i)));
        // For primitive types, write directly to data pointer.
        // jl_arrayset does not work for inline-stored types in Julia 1.12+.
        if (array_base_type == jl_float64_type) {
          jl_array_data(julia_array, double)[i] = jl_unbox_float64(element);
        } else if (array_base_type == jl_int64_type) {
          jl_array_data(julia_array, int64_t)[i] = jl_unbox_int64(element);
        } else if (array_base_type == jl_bool_type) {
          jl_array_data(julia_array, int8_t)[i] = jl_unbox_bool(element);
        } else {
          jl_arrayset(julia_array, element, i);
        }
      }

    }
    else {

      jl_value_t* array_type = jl_apply_array_type((jl_value_t*)array_base_type, 2);
      julia_array = jl_alloc_array_2d(array_type, nrows, ncols);

      int index = 0;
      for (int i = 0; i < ncols; i++) {
        for (int j = 0; j < nrows; j++) {
          jl_value_t *element = VariableToJlValue(&(arr.data(index++)));
          int flat_index = j + nrows * i;
          if (array_base_type == jl_float64_type) {
            jl_array_data(julia_array, double)[flat_index] = jl_unbox_float64(element);
          } else if (array_base_type == jl_int64_type) {
            jl_array_data(julia_array, int64_t)[flat_index] = jl_unbox_int64(element);
          } else if (array_base_type == jl_bool_type) {
            jl_array_data(julia_array, int8_t)[flat_index] = jl_unbox_bool(element);
          } else {
            jl_arrayset(julia_array, element, flat_index);
          }
        }
      }

    }
    
    value = (jl_value_t*)julia_array;
    break;
  }

  case 0: // not set (should be missing?)
    value = jl_nothing;
    break;

  default:
    CHILD_LOG("Unhandled type in variable to jlvalue: %d", variable->value_case());
    break;
  }

  if (variable->name().length()) {

    fprintf(stderr, "warning: names\n");

    // disabling to stop naming function arguments

    /*
    // create tuple with name, value. the below creates a "DataType" type.
    // I'd prefer this to be a typed tuple, but one thing at a time.

    jl_value_t* jl_name = jl_pchar_to_string(variable->name().c_str(), variable->name().length());

    jl_svec_t * svec = jl_svec2(jl_name, value);

//    jl_value_t* tuple[] = { jl_name, value };
//    return (jl_value_t*)jl_apply_tuple_type_v(tuple, 2);
//    return jl_new_structv(jl_any_type, tuple, 2);

    return (jl_value_t*) jl_apply_tuple_type(svec);
    */

  }

  return value;
  
}

void JlValueToVariable(RJ2XCLBuffers::Variable *variable, jl_value_t *value) {

  // nothing/null/nil
  if (jl_is_nothing(value)) {
    variable->set_nil(true);
    return;
  }
  
  // string [...]
  if (jl_typeis(value, jl_string_type)) {
    variable->set_str(std::string(jl_string_ptr(value), jl_string_len(value)));
    return;
  }

  // boolean
  if (jl_typeis(value, jl_bool_type)) {
    variable->set_boolean(jl_unbox_bool(value));
    return;
  }

  // floats
  if (jl_typeis(value, jl_float64_type)) {
    variable->set_real(jl_unbox_float64(value));
    return;
  }
  if (jl_typeis(value, jl_float32_type)) {
    variable->set_real(jl_unbox_float32(value));
    return;
  }

  // ints
  if (jl_typeis(value, jl_int64_type)) {
    variable->set_integer(jl_unbox_int64(value));
    return;
  }
  if (jl_typeis(value, jl_int32_type)) {
    variable->set_integer(jl_unbox_int32(value));
    return;
  }
  if (jl_typeis(value, jl_uint32_type)) {
    variable->set_integer(jl_unbox_uint32(value));
    return;
  }
  if (jl_typeis(value, jl_uint64_type)) {
    variable->set_integer(jl_unbox_uint64(value));
    return;
  }
  if (jl_typeis(value, jl_int16_type)) {
    variable->set_integer(jl_unbox_int16(value));
    return;
  }
  if (jl_typeis(value, jl_int8_type)) {
    variable->set_integer(jl_unbox_int8(value));
    return;
  }

  // complex...

  // array

  if (jl_is_array(value)) {

    auto results_array = variable->mutable_arr();
    auto jl_array = (jl_array_t*)value;
    auto eltype = jl_array_eltype(value);

    int ndims = jl_array_ndims(jl_array);
    int ncols = jl_array_ndims(jl_array) > 1 ? jl_array_dim(jl_array, 1) : 1;
    int nrows = jl_array_dim(jl_array, 0);
    int len = jl_array_len(jl_array);

    // if this is a 1-dimensional array, julia will return the length
    // as both rows and columns, so we need to correct. set as rows. 

    // NOTE: set as rows for consistency with R column-major convention

    // actually if it's a 1-dimensional array, the columns value is 
    // garbage, ignore it

    // if (ndims == 1 && (nrows == ncols)) ncols = 1;
    if (ndims == 1) ncols = 1;

    results_array->set_cols(ncols);
    results_array->set_rows(nrows);

    // For primitive types (Float64, Int64, etc.), access data directly.
    // jl_array_ptr treats the array as pointer-array which is wrong for
    // inline-stored types in Julia 1.12+.
    if (eltype == jl_float64_type) {
      double *d = jl_array_data(jl_array, double);
      for (int i = 0; i < len; i++) results_array->add_data()->set_real(d[i]);
      return;
    }
    else if (eltype == jl_float32_type) {
      float *d = jl_array_data(jl_array, float);
      for (int i = 0; i < len; i++) results_array->add_data()->set_real(d[i]);
      return;
    }
    else if (eltype == jl_int64_type) {
      int64_t *d = jl_array_data(jl_array, int64_t);
      for (int i = 0; i < len; i++) results_array->add_data()->set_integer(d[i]);
      return;
    }
    else if (eltype == jl_int32_type) {
      int32_t *d = jl_array_data(jl_array, int32_t);
      for (int i = 0; i < len; i++) results_array->add_data()->set_integer(d[i]);
      return;
    }
    else if (eltype == jl_bool_type) {
      int8_t *d = jl_array_data(jl_array, int8_t);
      for (int i = 0; i < len; i++) results_array->add_data()->set_boolean(d[i] != 0);
      return;
    }
    else if (eltype == jl_string_type) {
      // String arrays are pointer arrays — use jl_array_ptr_ref
      for (int i = 0; i < len; i++) {
        jl_value_t *elem = jl_array_ptr_ref(jl_array, i);
        if (elem && jl_is_string(elem)) {
          results_array->add_data()->set_str(std::string(jl_string_ptr(elem), jl_string_len(elem)));
        } else {
          results_array->add_data()->set_str("");
        }
      }
      return;
    }
    else {
      // Fallback for other types (Any, etc.) — pointer array
      jl_value_t** data = (jl_value_t**)(jl_array_ptr(jl_array));
      for (int i = 0; i < len; i++) JlValueToVariable(results_array->add_data(), data[i]);
      return;
    }
  }

  if (jl_is_cpointer(value)) {

    // where does it keep track of the underlying type? in my testing, all pointers 
    // irrespective of julia size (e.g. Ptr{UInt32}) report size = 8; so we can treat 
    // them as 64-bit pointers. but let's check anyway, just in case...

    
    jl_datatype_t* value_type = (jl_datatype_t*)(jl_typeof(value));
    if (jl_datatype_size(value_type) != 8) {
      std::cerr << "warning: pointer size not == 8 (" << jl_datatype_size(value_type) << ")" << std::endl;
    }
    else {
      auto com_pointer = variable->mutable_com_pointer();
      com_pointer->set_pointer(reinterpret_cast<uint64_t>(jl_unbox_voidpointer(value)));
      return;
    }

  }

  // Unhandled type — log for diagnostics
  jl_value_t *value_type = jl_typeof(value);
  jl_printf(JL_STDERR, "RJ2XCL: unexpected Julia type (0x%X): ", value_type);
  jl_static_show(JL_STDERR, value_type);
  jl_printf(JL_STDERR, "\n");
  
  // ?

  RJ2XCLBuffers::Error *err = variable->mutable_err();
  err->set_message("Unexpected variable type");

}

void JuliaGetVersion(int32_t *major, int32_t *minor, int32_t *patch) {
  *major = jl_ver_major();
  *minor = jl_ver_minor();
  *patch = jl_ver_patch();
}

void JuliaInit() {

  char buffer[MAX_PATH];
  GetEnvironmentVariableA("RJ2XCL_HOME", buffer, MAX_PATH);
  std::string rj2xcl_home(buffer);

  std::string config_data;
  std::string config_path = rj2xcl_home + "rj2xcl-config.json";
  auto result = APIFunctions::FileContents(config_path);

  // Julia 1.x options — simplified, only set what we need
  jl_options.quiet = 0;
  jl_options.color = JL_OPTIONS_COLOR_ON;
  jl_options.handle_signals = JL_OPTIONS_HANDLE_SIGNALS_ON;

  if (result.is_success()) {
    config_data = result.value();
    std::string err;
    json11::Json config = json11::Json::parse(config_data, err, json11::COMMENTS);
    json11::Json julia = config["NEVEN"]["Julia"];

    if (julia["fastMath"].is_string()) {
      const std::string &compare = julia["fastMath"].string_value();
      if (compare == "on") jl_options.fast_math = JL_OPTIONS_FAST_MATH_ON;
      if (compare == "off") jl_options.fast_math = JL_OPTIONS_FAST_MATH_OFF;
      if (compare == "default") jl_options.fast_math = JL_OPTIONS_FAST_MATH_DEFAULT;
    }

    if (julia["polly"].is_string()) {
      const std::string &compare = julia["polly"].string_value();
      if (compare == "on") jl_options.polly = JL_OPTIONS_POLLY_ON;
      if (compare == "off") jl_options.polly = JL_OPTIONS_POLLY_OFF;
    }
  }

  // Check for pre-compiled sysimage (eliminates JIT delay)
  std::string sysimage_path = rj2xcl_home + "neven_julia.dll";
  DWORD sysimage_attrs = GetFileAttributesA(sysimage_path.c_str());

  if (sysimage_attrs != INVALID_FILE_ATTRIBUTES) {
    // Sysimage exists — use jl_init_with_image for fast startup
    std::string julia_bindir;
    char julia_home[MAX_PATH];
    GetEnvironmentVariableA("JULIA_BINDIR", julia_home, MAX_PATH);
    if (strlen(julia_home) == 0) {
      // Fallback: derive from PATH (Julia's bin should be prepended by XLL)
      GetEnvironmentVariableA("PATH", julia_home, MAX_PATH);
      // Use the first path entry
      char* semicolon = strchr(julia_home, ';');
      if (semicolon) *semicolon = '\0';
    }
    julia_bindir = julia_home;

    CHILD_LOG("Loading Julia sysimage: %s (bindir: %s)", sysimage_path.c_str(), julia_bindir.c_str());
    jl_init_with_image(julia_bindir.c_str(), sysimage_path.c_str());
  } else {
    // No sysimage — standard init (slow first call due to JIT)
    CHILD_LOG("No sysimage found, using standard Julia init (JIT will be slow)");
    jl_init();
  }

}

void JuliaShutdown() {

  // [from docs]

  // strongly recommended: notify Julia that the program is about to terminate. 
  // this allows Julia time to cleanup pending write requests and run all 
  // finalizers

  jl_atexit_hook(0);

}

jl_function_t* ResolveFunction(const std::string &function) {

  jl_function_t *function_pointer = jl_nothing;

  if (!function.length()) return function_pointer;
  std::vector<std::string> elements;
  StringUtilities::Split(function, '.', 1, elements);

  if (elements.size() == 1) function_pointer = jl_get_function(jl_main_module, function.c_str());
  else {
    function_pointer = jl_get_global(jl_main_module, jl_symbol(elements[0].c_str()));
    for (int i = 1; i< elements.size(); i++) function_pointer = jl_get_global((jl_module_t*)function_pointer, jl_symbol(elements[i].c_str()));
  }

  return function_pointer;

}

void ReportJuliaException(const char *tag, bool backtrace = false) {

  CHILD_LOG("* CATCH [%s]", tag);

  if (backtrace) /* jlbacktrace removed for Julia 1.x */;

  // can cache?

  jl_function_t *function_pointer = ResolveFunction("NEVEN.DisplayError");
  if (function_pointer) {
    jl_call1(function_pointer, jl_current_exception(jl_current_task));
    jl_printf(JL_STDERR, "\n");
  }
  else {

    // Cache JL_STDERR lookup for performance (called frequently)

    jl_value_t *jl_stderr = jl_get_global(jl_main_module, jl_symbol("STDERR"));
    if (jl_stderr == jl_nothing) {
      jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
    }
    else {
      jl_call2(jl_get_function(jl_main_module, "showerror"), jl_stderr, jl_current_exception(jl_current_task));
    }

    jl_printf(JL_STDERR, "\n\n"); // matches julia repl
  }

  jl_exception_clear();

}

void JuliaRunUVLoop(bool until_done) {
  // uv_run removed for Julia 1.x — event loop handled internally
  (void)until_done;
}

__inline bool ReportException(const char *tag) {
  if (jl_exception_occurred()) {
    CHILD_LOG("* [%s] EXCEPTION", tag);
    jl_printf(JL_STDERR, "[%s] error during run:\n", tag);
    jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
    jl_exception_clear();
    jl_printf(JL_STDERR, "\n\n");
    return true;
  }
  return false;
}

bool ReadSourceFile(const std::string &file, bool notify) {

  // should be able to cache this one
  //jl_function_t *function_pointer = jl_get_function(jl_main_module, "include");
  jl_function_t *function_pointer = ResolveFunction("NEVEN.ReadScriptFile");
  if (!function_pointer || jl_is_nothing(function_pointer)) return false;

  jl_value_t *function_result = jl_nothing;

  JL_TRY{
    function_result = jl_call2(function_pointer, jl_pchar_to_string(file.c_str(), file.length()), jl_box_bool(notify ? 1 : 0));
    ReportException("read-source-file");
  }
  JL_CATCH{
    CHILD_LOG("* CATCH [RSF]");
    jl_printf(JL_STDERR, "\nparser error:\n");
    jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
    jl_printf(JL_STDERR, "\n");
    /* jlbacktrace removed for Julia 1.x */;
    jl_exception_clear();
  }

  JuliaRunUVLoop(true);

  return function_result; // false;
}

/**
 * shell exec: response is printed to output stream. 
 * 
 * shell supports multi-line entry, which may be incomplete as of
 * any given line. previous lines are stored in a buffer (now as a 
 * concatenated string). Ctrl+C or other break should clear buffer.
 *
 * this function is not responsible for maintaining or appending
 * the buffer. caller can do that (if desired) when response is 
 * "incomplete".
 */
ExecResult JuliaShellExec(const std::string &command, const std::string &shell_buffer) {

  // this is used for tagging

  static char filename[] = "shell";
  static int filename_len = (int)strlen(filename);

  std::string tmp = shell_buffer;
  tmp += command;
  
  // this is a little hacky, but we are trying to emulate the 
  // stock julia parser to the extent that's reasonable

  if (StringUtilities::EndsWith(StringUtilities::Trim(tmp), ";")) {
    tmp = tmp + "nothing";
  }
  
  // same: help commands start with ?

  // NOTE: strings with special chars could break Julia parser
  // Help commands start with ?

  if (tmp.length() && tmp.c_str()[0] == '?') {
    std::string help = "NEVEN.ShellHelp(\"";
    help += tmp.substr(1);
    help += "\")";
    tmp = help;
  }

  ExecResult result = ExecResult::Success;

  JL_TRY{

    jl_value_t *val = jl_parse_input_line(tmp.c_str(), tmp.length(), filename, filename_len);

    // when does this get set, vs. throwing?

    if (jl_exception_occurred()) {
      CHILD_LOG("* [JSE] EXCEPTION, command: %s", tmp.c_str());

      jl_printf(JL_STDERR, "[JSE] error during run:\n");
      jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
      jl_exception_clear();
      result = ExecResult::Error;
    }
    else if (val) {

      if (jl_is_expr(val) && (((jl_expr_t*)val)->head == jl_symbol("incomplete"))){
        result = ExecResult::Incomplete;
      }
      else if(result == ExecResult::Success) {

        // from jl_eval_string

        JL_GC_PUSH1(&val);
        // world_age management removed for Julia 1.x
        // world_age management removed for Julia 1.x
        jl_value_t *r = jl_toplevel_eval_in(jl_main_module, val);
        // world_age management removed for Julia 1.x
        JL_GC_POP();
        jl_exception_clear();

        if (!jl_is_nothing(r)) {

          // better for some, not for others. we need to figure out
          // what repl is doing with output.

          //jl_static_show(JL_STDERR, r);
          jl_call1(jl_get_function(jl_main_module, "display"), r);

          // jl_printf(JL_STDOUT, "\n");
        }

        // to match julia REPL, always an extra newline
        jl_printf(JL_STDOUT, "\n");

      }
    }

  }
  JL_CATCH{
    ReportJuliaException("JSE");
    result = ExecResult::Error;
  }

  JuliaRunUVLoop(true);

  return result;

}

void PushConsoleMimeData(const std::string &mime_type, void *data) {

  RJ2XCLBuffers::CallResponse message;
  auto mime_data = message.mutable_console()->mutable_mime_data();

  if (jl_is_array((jl_value_t*)data)) {
    jl_array_t* arr = (jl_array_t*)data;
    size_t size = jl_array_len(arr);
    if (size > 0) {
      //std::cout << "array len is " << size << std::endl;
      void* data = jl_array_ptr(arr);
      mime_data->set_data(data, size);
    }
  }

  //mime_data->set_data()
  mime_data->set_mime_type(mime_type);

  PushConsoleMessage(message);

}

jl_value_t* Callback2(const char *command, void *data1, void *data2, void *data3) {

  // local methods

  std::string string_command(command);

  if (!string_command.compare("render-mime")) {
  
    std::string mime_type;
    jl_value_t *value1 = (jl_value_t*)data1;

    if (jl_typeis(value1, jl_string_type)) {
      mime_type.assign(jl_string_ptr(value1), jl_string_len(value1));
      //std::cout << "Render mime type: " << mime_type << std::endl;
      PushConsoleMimeData(mime_type, data2);
    }

    // Non-array return — error not reported to caller (returns jl_nothing)

    return jl_nothing;
  }

  /*

  if (!string_command.compare("render-html")) {
    PushConsoleMimeData("text/html", data1);
    return jl_nothing;
  }
  else if (!string_command.compare("render-png")) {
    PushConsoleMimeData("image/png", data1);
    return jl_nothing;
  }
  else if (!string_command.compare("render-gif")) {
    PushConsoleMimeData("image/gif", data1);
    return jl_nothing;
  }
  else if (!string_command.compare("render-jpeg")) {
    PushConsoleMimeData("image/jpeg", data1);
    return jl_nothing;
  }

  */

  // NOTE: COMCallback and Callback2 share similar patterns — could unify in future

  /*
  std::cout << "CB2: " << command << std::endl;
  if (data) {
    RJ2XCLBuffers::Variable var;
    JlValueToVariable(&var, reinterpret_cast<jl_value_t*>(data), true);
    DumpJSON(var, 0);
  }
  */
  
  static uint32_t callback_id = 1;
  jl_value_t *jl_result = jl_nothing;

  if (!command || !command[0]) return jl_result;

  RJ2XCLBuffers::CallResponse *call = new RJ2XCLBuffers::CallResponse;
  RJ2XCLBuffers::CallResponse *response = new RJ2XCLBuffers::CallResponse;

  call->set_id(callback_id++);
  call->set_wait(true);

  auto callback = call->mutable_function_call();
  callback->set_function(command);

  if (data1) //SEXPToVariable(callback->add_arguments(), reinterpret_cast<SEXP>(data));
    JlValueToVariable(callback->add_arguments(), reinterpret_cast<jl_value_t*>(data1));

  bool success = Callback(*call, *response);
  // cout << "callback (2) complete (" << success << ")" << endl;

  if (success) jl_result = VariableToJlValue(&(response->result()));

  delete call;
  delete response;

  if (!success) {
    // error_return("internal method failed");
  }
  
  return jl_result;

}


jl_value_t *JuliaCallJlValue(const RJ2XCLBuffers::CompositeFunctionCall &call) {

  jl_function_t *function_pointer = ResolveFunction(call.function());
  jl_value_t *function_result = jl_nothing;
  if (!function_pointer || jl_is_nothing(function_pointer)) return function_result;

  JL_TRY{

    // call here, with or without arguments
    int len = call.arguments().size();
  if (len > 0) {
    std::vector<jl_value_t*> arguments_vector;
    for (auto argument : call.arguments()) {
      arguments_vector.push_back(VariableToJlValue(&argument));
    }
    function_result = jl_call(function_pointer, &(arguments_vector[0]), len);
  }
  else {
    function_result = jl_call0(function_pointer);
  }
  ReportException("JCJV");

  }
    JL_CATCH{

    // external exception; return error

    CHILD_LOG("* CATCH [JCJV]");
  jl_printf(JL_STDERR, "\nparser error:\n");

  jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
  jl_printf(JL_STDERR, "\n");
  /* jlbacktrace removed for Julia 1.x */;
  jl_exception_clear();

  //response.set_err("external exception");

  }

  return function_result;
}

jl_value_t * COMCallback(uint64_t pointer, const char *name, const char *calltype, uint32_t index, void *arguments_list) {

  /*

  std::cout << "CB1: " << pointer << ", " << name << ", " << calltype << ", " << index << std::endl;
  if (arguments_list) {
    RJ2XCLBuffers::Variable var;
    JlValueToVariable(&var, (jl_value_t*)arguments_list, true);
    DumpJSON(var, 0);
  }
  return jl_box_int32(44);
//  return jl_nothing;

  */
  
  static uint32_t callback_id = 1;
  jl_value_t *jl_result = jl_nothing;

  if (!name || !name[0]) return jl_result;

  RJ2XCLBuffers::CallResponse *call = new RJ2XCLBuffers::CallResponse;
  RJ2XCLBuffers::CallResponse *response = new RJ2XCLBuffers::CallResponse;

  call->set_id(callback_id++);
  call->set_wait(true);

  //auto callback = call->mutable_com_callback();
  auto callback = call->mutable_function_call();
  callback->set_target(RJ2XCLBuffers::CallTarget::COM);
  callback->set_function(name);

  callback->set_index(index);
  callback->set_pointer(pointer);

  callback->set_type(RJ2XCLBuffers::CallType::method);
  if (calltype) {
    if (!strcmp(calltype, "get")) callback->set_type(RJ2XCLBuffers::CallType::get);
    else if (!strcmp(calltype, "put")) callback->set_type(RJ2XCLBuffers::CallType::put);
  }

  if (arguments_list) {
    RJ2XCLBuffers::Variable var;
    JlValueToVariable(&var, (jl_value_t*)arguments_list);
    int len = var.arr().data_size();
    for (int i = 0; i < len; i++) {
      callback->add_arguments()->CopyFrom(var.arr().data(i)); // Flatten array args
    }
    //std::cout << "arguments list:" << std::endl;
    //DumpJSON(var, 0);
  }

  bool success = Callback(*call, *response);

  if (success) {
    int err = 0;
    if (response->operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kFunctionCall) {

      // sexp_result = RCallSEXP(response->function_call(), true, err); // ??
      jl_result = jl_box_int32(100);
    }
    else if (response->operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kResult
      && response->result().value_case() == RJ2XCLBuffers::Variable::ValueCase::kComPointer) {

      jl_result = jl_box_int32(200);

      RJ2XCLBuffers::CompositeFunctionCall *function_call = new RJ2XCLBuffers::CompositeFunctionCall;
      function_call->set_function("NEVEN.CreateCOMType");
      auto argument = function_call->add_arguments();

      // I want to borrow this, not copy, can we do that?
      argument->mutable_com_pointer()->CopyFrom(response->result().com_pointer());

      //sexp_result = RCallSEXP(*function_call, true, err);
      //argument->release_com_pointer();

      jl_result = JuliaCallJlValue(*function_call);

      delete function_call;
      //*/
    }
    else jl_result = VariableToJlValue(&(response->result()));
  }

  delete call;
  delete response;

  if (!success) {
    jl_printf(JL_STDERR, "Error in COM call (...)\n");
  }

  return jl_result;
}



bool JuliaPostInit() {
  
  jl_function_t *function_pointer = ResolveFunction("NEVEN.SetCallbacks");
  if (!function_pointer || jl_is_nothing(function_pointer)) return false;

  std::vector<jl_value_t*> arguments_vector = {
    jl_box_voidpointer(&COMCallback),
    jl_box_voidpointer(&Callback2)
  };
  
  JL_TRY{
    jl_call(function_pointer, &(arguments_vector[0]), arguments_vector.size());
    ReportException("post-install");
  }
  JL_CATCH{
    CHILD_LOG("* CATCH [post-install]");
    jl_printf(JL_STDERR, "\nparser error:\n");
    jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
    jl_printf(JL_STDERR, "\n");
    /* jlbacktrace removed for Julia 1.x */;
    jl_exception_clear();
  }

  /*

  auto mutable_function_call = translated_call.mutable_function_call();
  mutable_function_call->set_target(RJ2XCLBuffers::CallTarget::language);
  mutable_function_call->set_function("NEVEN.SetCallbacks");
  mutable_function_call->add_arguments()->set_u64((uint64_t)&COMCallback);
  mutable_function_call->add_arguments()->set_u64((uint64_t)&Callback2);
  JuliaCall(response, translated_call);

  */

  return true;
}

void JuliaCall(RJ2XCLBuffers::CallResponse &response, const RJ2XCLBuffers::CallResponse &call) {

  response.set_id(call.id());

  std::string function = call.function_call().function();

  // lookup in main includes our defined functions plus (apparently) Base, which 
  // is attached is some fashion. can we dereference pacakges? [A: no, probably 
  // need to do that manually]. [moved to function]

  jl_function_t *function_pointer = ResolveFunction(function);
  if (!function_pointer || jl_is_nothing(function_pointer)) return;
  jl_value_t *function_result;

  JL_TRY {

    // call here, with or without arguments
    int len = call.function_call().arguments().size();
    if (len > 0) {
      std::vector<jl_value_t*> arguments_vector;
      for (auto argument : call.function_call().arguments()) {
        arguments_vector.push_back(VariableToJlValue(&argument));
      }
      function_result = jl_call(function_pointer, &(arguments_vector[0]), len);
    }
    else {
      function_result = jl_call0(function_pointer);
    }

    // check for a julia exception (handled)
    if (jl_exception_occurred()) {

      ReportJuliaException("JC", false);

      // set err
      response.set_err("julia exception");
    }
    else 
    {
      // success: return result or nil as an empty success value
      if (function_result) {
        JlValueToVariable(response.mutable_result(), function_result);
      }
      else {
        response.mutable_result()->set_nil(true);
      }
    }

  }
  JL_CATCH {

    // external exception; return error

    CHILD_LOG("* CATCH [JC]");
    jl_printf(JL_STDERR, "\nparser error:\n");

    jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
    jl_printf(JL_STDERR, "\n");
    /* jlbacktrace removed for Julia 1.x */;

    jl_exception_clear();

    response.set_err("external exception");

  }

  JuliaRunUVLoop(true);

  // JlValueToVariable(response.mutable_result(), function_result);

}

inline std::string jl_string(jl_value_t *value){ return std::string(jl_string_ptr(value), jl_string_len(value)); }

void ListScriptFunctions(RJ2XCLBuffers::CallResponse &response, const RJ2XCLBuffers::CallResponse &call) {
  
  bool success = false;
  response.set_id(call.id());
  
  // ListFunctions may throw if Julia environment is not fully initialized
  
  std::string command = "NEVEN.ListFunctions()"; // newline?

  JL_TRY{

    jl_value_t *val = (jl_value_t*)jl_load_file_string(command.c_str(), command.length(), "inline (list-functions)", jl_main_module);

    if (jl_exception_occurred()) {
      CHILD_LOG("* [LSF] EXCEPTION");
      jl_exception_clear();
    }
    else {
      success = true;
      auto function_list = response.mutable_function_list();

      auto ParseEntry = [function_list](jl_value_t * element){

        // function descriptions are lists of function name, docstring, category, [arg names]
        if (jl_is_array(element)) {

          auto jl_array = (jl_array_t*)element;
          auto eltype = jl_array_eltype(element);
          auto array_length = jl_array_len(jl_array);

          // expect string[], don't handle other types...
          if (array_length >= 3 && eltype == jl_string_type) {
            auto data = (jl_value_t**)(jl_array_ptr(jl_array));
            auto function_descriptor = function_list->add_functions();

            function_descriptor->mutable_function()->set_name(jl_string(data[0]));
            function_descriptor->mutable_function()->set_description(jl_string(data[1]));
            function_descriptor->set_category(jl_string(data[2]));
            
            for (int i = 3; i < array_length; i++) {
              function_descriptor->add_arguments()->set_name(jl_string(data[i]));
            }

          }
          else if (array_length > 0 && eltype == jl_string_type) {
             // Fallback for old format [name, arg1, arg2, ...]
            auto data = (jl_value_t**)(jl_array_ptr(jl_array));
            auto function_descriptor = function_list->add_functions();
            function_descriptor->mutable_function()->set_name(jl_string(data[0]));
            for (int i = 1; i < array_length; i++) {
              function_descriptor->add_arguments()->set_name(jl_string(data[i]));
            }
          }

          /*
          std::cout << "entry length: " << array_length << std::endl;

          if (eltype == jl_string_type) {
            std::cout << "\ttype is string" << std::endl;
          }
          else if (1) {
            std::cout << "\tarray flag" << std::endl;
          }
          else {
            std::cout << "\tother type? " << eltype << std::endl;
          }
          */

        }
      };

      if (val) {

        // return value is an array of function descriptions. 

        if (jl_is_array(val)) {

          auto jl_array = (jl_array_t*)val;
          auto eltype = jl_array_eltype(val); 
          auto array_length = jl_array_len(jl_array);

          CHILD_LOG("array length %zu", array_length);

          if (1 /* ptrarray compat */) {
            auto data = (jl_value_t**)(jl_array_ptr(jl_array));
            for (int i = 0; i < array_length; i++) {
              // JlValueToVariable(results_array->add_data(), data[i]);
              ParseEntry(data[i]);
            }
            return;
          }

        }

      }
      else {
        // success, but list length is zero
        // ...

        CHILD_LOG("success, but length is zero");

      }
    }

  }
  JL_CATCH {

    CHILD_LOG("* CATCH [LSF]");
    jl_printf(JL_STDERR, "\nparser error:\n");
    jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
    jl_printf(JL_STDERR, "\n");
    /* jlbacktrace removed for Julia 1.x */;
    jl_exception_clear();

  }

  if (!success) {
    response.set_err("error listing functions");
  }

}

void JuliaExec(RJ2XCLBuffers::CallResponse &response, const RJ2XCLBuffers::CallResponse &call) {

  response.set_id(call.id());

  std::string composite;
  for (auto line : call.code().line()) {
    composite += line;
    composite += "\n";
  }

  JL_TRY{

    jl_value_t *val = (jl_value_t*)jl_load_file_string(composite.c_str(), composite.length(), "inline", jl_main_module);

    // ok so this gets called if there is an exception but we caught it; 
    // why does the catch not remove it entirely? (...)

    if (jl_exception_occurred()) {
      CHILD_LOG("* [JE] EXCEPTION");
      jl_exception_clear();
    }
    
    if (val) {
      JlValueToVariable(response.mutable_result(), val);
    }

  }
  JL_CATCH {
    CHILD_LOG("* CATCH [JE]");
    jl_printf(JL_STDERR, "\nparser error:\n");
    jl_static_show(JL_STDERR, jl_current_exception(jl_current_task));
    jl_printf(JL_STDERR, "\n");
    /* jlbacktrace removed for Julia 1.x */;
    jl_exception_clear();
  }

  // Startup flag: run post-init actions (callback registration, etc.)
  // NOTE: should this gate on success? Currently runs regardless.

  if (call.code().startup()) JuliaPostInit();

}









