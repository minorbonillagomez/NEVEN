/*
 * Julia 0.6 → 1.x+ Compatibility Layer for RJ2XCL
 * 
 * This header provides macros and inline functions to bridge
 * API differences between Julia 0.6 (original BERT) and Julia 1.x+
 */
#ifndef JULIA_COMPAT_H
#define JULIA_COMPAT_H

#include "julia.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- jl_init_with_image for custom sysimage support ---- */
/* Not declared in all Julia header versions, but exported from libjulia.dll */
JL_DLLIMPORT void jl_init_with_image(const char *julia_bindir, const char *image_path);

/* ---- jl_array_t members removed in Julia 1.x ---- */
/* Use jl_array_len() instead of arr->length */
/* Use jl_array_ndims() for dimensions */
/* Use jl_array_dim() for specific dimension sizes */

/* ---- jl_arrayset renamed to jl_array_ptr_set with swapped params ---- */
/* Julia 0.6: jl_arrayset(arr, val, idx) */
/* Julia 1.x: jl_array_ptr_set(arr, idx, val) */
#ifndef jl_arrayset
#define jl_arrayset(arr, val, idx) jl_array_ptr_set((jl_array_t*)(arr), (size_t)(idx), (jl_value_t*)(val))
#endif

/* ---- jl_array_data now requires type argument in Julia 1.x ---- */
/* Julia 0.6: jl_array_data(arr) returned void* */
/* Julia 1.x: jl_array_data(arr, type) */
#define jl_array_data_compat(arr, type) ((type*)jl_array_ptr(arr))

/* ---- jl_ptls_t / jl_get_ptls_states removed ---- */
/* Not needed in Julia 1.x — thread state is managed internally */

/* ---- jl_static_show signature changed ---- */
/* Julia 0.6: jl_static_show(stream, value) */
/* Julia 1.x: jl_static_show(stream, value) — but stream type changed */
/* For now, replace with stderr output */
#define jl_static_show_compat(val) do { \
    jl_value_t *str = jl_call1(jl_get_function(jl_base_module, "string"), (jl_value_t*)(val)); \
    if (str) fprintf(stderr, "%s", jl_string_ptr(str)); \
} while(0)

/* ---- jl_datatype_t->size moved to layout in Julia 1.x ---- */
#define jl_datatype_size_compat(dt) (((jl_datatype_t*)(dt))->layout ? ((jl_datatype_t*)(dt))->layout->size : 0)

/* ---- jl_incomplete_sym removed in Julia 1.x ---- */
/* Use jl_get_global to check for :incomplete */

/* ---- jl_load_file_string signature changed ---- */
/* Julia 0.6: jl_load_file_string(str, len, filename) */
/* Julia 1.x: jl_load_file_string(str, len, filename, module) */
#define jl_load_file_string_compat(str, len, filename) \
    jl_load_file_string((str), (len), (filename), jl_main_module)

/* ---- JL_STDOUT/JL_STDERR redefined for Julia 1.x ---- */
/* In Julia 0.6, JL_STDOUT/JL_STDERR were jl_uv_stdout/jl_uv_stderr */
/* In Julia 1.x, use jl_stdout_stream()/jl_stderr_stream() */
#ifdef JL_STDOUT
#undef JL_STDOUT
#endif
#ifdef JL_STDERR
#undef JL_STDERR
#endif
#define JL_STDOUT jl_stdout_stream()
#define JL_STDERR jl_stderr_stream()

#ifdef __cplusplus
}
#endif

#endif /* JULIA_COMPAT_H */
