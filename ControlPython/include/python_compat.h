/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * python_compat.h — Compatibility layer for version-independent Python linking.
 *
 * ControlPython.exe links against python3.lib (Stable ABI) to work with any
 * Python >= 3.10. However, some CPython functions are NOT exported from
 * python3.lib. This header provides replacements using only symbols
 * available in python3.lib.
 *
 * MUST be included AFTER <Python.h>.
 */

#pragma once

// ─── neven_PyRun_SimpleString ─────────────────────────────────────────────────
// PyRun_SimpleString / PyRun_SimpleStringFlags are NOT in python3.lib.
// This replacement uses Py_CompileString + PyEval_EvalCode which ARE exported.
//
// Call this function directly instead of PyRun_SimpleString() in all code.
inline int neven_PyRun_SimpleString(const char* command) {
    PyObject* main_module = PyImport_AddModule("__main__");
    if (!main_module) return -1;
    PyObject* main_dict = PyModule_GetDict(main_module);
    
    // Use the function-pointer form to avoid the macro (which expands to
    // Py_CompileStringExFlags not in python3.lib)
    PyObject* code = (Py_CompileString)(command, "<string>", Py_file_input);
    if (!code) {
        PyErr_Print();
        return -1;
    }
    
    PyObject* result = PyEval_EvalCode(code, main_dict, main_dict);
    Py_DECREF(code);
    
    if (result) {
        Py_DECREF(result);
        return 0;
    }
    PyErr_Print();
    return -1;
}

// ─── neven_Py_CompileString ──────────────────────────────────────────────────
// The macro Py_CompileString may expand to Py_CompileStringExFlags (NOT in python3.lib).
// Use this wrapper that calls the real Py_CompileString via function pointer dereference.
inline PyObject* neven_Py_CompileString(const char* str, const char* filename, int start) {
    // Parentheses around function name suppress macro expansion
    return (Py_CompileString)(str, filename, start);
}

// ─── PyUnicode_AsUTF8 replacement ───────────────────────────────────────────
// PyUnicode_AsUTF8 is NOT guaranteed in python3.lib for all versions.
// Use PyUnicode_AsUTF8AndSize (available in Stable ABI since 3.10) instead.
#ifdef PyUnicode_AsUTF8
#undef PyUnicode_AsUTF8
#endif
#define PyUnicode_AsUTF8(obj) PyUnicode_AsUTF8AndSize((obj), NULL)

