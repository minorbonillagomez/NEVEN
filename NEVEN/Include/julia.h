#ifndef JULIA_H_MOCK
#define JULIA_H_MOCK

#include <stdint.h>
#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

// Essential Julia Types
typedef struct _jl_value_t {
    uint32_t size;
} jl_value_t;

typedef jl_value_t jl_datatype_t;
typedef jl_value_t jl_sym_t;
typedef jl_value_t jl_module_t;
typedef jl_value_t jl_svec_t;

typedef struct _jl_expr_t {
    jl_sym_t *head;
    jl_svec_t *args;
} jl_expr_t;

typedef struct _jl_array_t {
    void* data;
    size_t length;
    struct {
        uint16_t how:2;
        uint16_t ndims:9;
        uint16_t pooled:1;
        uint16_t ptrarray:1;
        uint16_t isaligned:1;
        uint16_t hasptr:1;
    } flags;
    uint16_t elsize;
    uint32_t offset;
    size_t nrows;
    size_t ncols;
} jl_array_t;

typedef jl_value_t jl_function_t;

typedef struct _jl_tls_states_t {
    jl_value_t *exception_in_transit;
    size_t world_age;
} jl_tls_states_t;
typedef jl_tls_states_t *jl_ptls_t;

// Global symbols
extern __declspec(dllimport) jl_module_t *jl_main_module;
extern __declspec(dllimport) jl_value_t *jl_nothing;
extern __declspec(dllimport) jl_datatype_t *jl_string_type;
extern __declspec(dllimport) jl_datatype_t *jl_bool_type;
extern __declspec(dllimport) jl_datatype_t *jl_float64_type;
extern __declspec(dllimport) jl_datatype_t *jl_float32_type;
extern __declspec(dllimport) jl_datatype_t *jl_int64_type;
extern __declspec(dllimport) jl_datatype_t *jl_int32_type;
extern __declspec(dllimport) jl_datatype_t *jl_uint32_type;
extern __declspec(dllimport) jl_datatype_t *jl_uint64_type;
extern __declspec(dllimport) jl_datatype_t *jl_int8_type;
extern __declspec(dllimport) jl_datatype_t *jl_int16_type;
extern __declspec(dllimport) jl_sym_t *jl_incomplete_sym;
extern __declspec(dllimport) jl_datatype_t *jl_any_type;
extern __declspec(dllimport) jl_datatype_t *jl_array_type;
extern __declspec(dllimport) jl_datatype_t *jl_pointer_type;
extern __declspec(dllimport) jl_datatype_t *jl_expr_type;
extern __declspec(dllimport) jl_sym_t *jl_nothing_sym;

// Output
typedef void* jl_uv_element_t;
extern __declspec(dllimport) jl_uv_element_t *jl_stdout_stream;
extern __declspec(dllimport) jl_uv_element_t *jl_stderr_stream;
#define JL_STDOUT jl_stdout_stream
#define JL_STDERR jl_stderr_stream

void jl_printf(jl_uv_element_t*, const char*, ...);
void jl_static_show(jl_uv_element_t*, jl_value_t*);

// Version
int jl_ver_major(void);
int jl_ver_minor(void);
int jl_ver_patch(void);

// Options
typedef struct {
    int8_t quiet;
    int8_t color;
    int8_t handle_signals;
    int8_t use_precompiled;
    int8_t use_compilecache;
    int8_t fast_math;
    int8_t polly;
} jl_options_t;

extern jl_options_t jl_options;

#define JL_OPTIONS_COLOR_ON 1
#define JL_OPTIONS_HANDLE_SIGNALS_ON 1
#define JL_OPTIONS_USE_PRECOMPILED_YES 1
#define JL_OPTIONS_USE_PRECOMPILED_NO 0
#define JL_OPTIONS_USE_COMPILECACHE_YES 1
#define JL_OPTIONS_USE_COMPILECACHE_NO 0
#define JL_OPTIONS_FAST_MATH_ON 1
#define JL_OPTIONS_FAST_MATH_OFF 0
#define JL_OPTIONS_FAST_MATH_DEFAULT 2
#define JL_OPTIONS_POLLY_ON 1
#define JL_OPTIONS_POLLY_OFF 0

jl_tls_states_t *jl_get_ptls_states(void);
extern jl_ptls_t ptls;

// Functions
jl_value_t *jl_eval_string(const char*);
jl_value_t *jl_call0(jl_function_t*);
jl_value_t *jl_call1(jl_function_t*, jl_value_t*);
jl_value_t *jl_call2(jl_function_t*, jl_value_t*, jl_value_t*);
jl_value_t *jl_call(jl_function_t*, jl_value_t**, int);
void jl_init(void);
void jl_atexit_hook(int);
void jl_exception_clear(void);
jl_value_t *jl_exception_occurred(void);
#define jl_is_nothing(v) ((v) == jl_nothing)
jl_value_t *jl_get_global(jl_module_t*, jl_sym_t*);
jl_sym_t *jl_symbol(const char*);
void jlbacktrace(void);

jl_value_t *jl_typeof(jl_value_t*);
jl_value_t *jl_pchar_to_string(const char*, size_t);
#define jl_string_len(s) (((size_t*)(s))[1])
#define jl_string_ptr(s) ((const char*)((size_t*)(s) + 2))
jl_value_t *jl_box_bool(int8_t);
jl_value_t *jl_box_int32(int32_t);
jl_value_t *jl_box_int64(int64_t);
jl_value_t *jl_box_uint32(uint32_t);
jl_value_t *jl_box_uint64(uint64_t);
jl_value_t *jl_box_float64(double);
jl_value_t *jl_box_voidpointer(void*);
int8_t jl_unbox_bool(jl_value_t*);
double jl_unbox_float64(jl_value_t*);
float jl_unbox_float32(jl_value_t*);
int64_t jl_unbox_int64(jl_value_t*);
int32_t jl_unbox_int32(jl_value_t*);
uint32_t jl_unbox_uint32(jl_value_t*);
uint64_t jl_unbox_uint64(jl_value_t*);
int16_t jl_unbox_int16(jl_value_t*);
int8_t jl_unbox_int8(jl_value_t*);
void *jl_unbox_voidpointer(jl_value_t*);


#define jl_is_array(v) (jl_typeof(v) == (jl_value_t*)jl_array_type)
#define jl_is_cpointer(v) (jl_typeof(v) == (jl_value_t*)jl_pointer_type)
#define jl_is_expr(v) (jl_typeof(v) == (jl_value_t*)jl_expr_type)

#define jl_array_data(a) (((jl_array_t*)(a))->data)
#define jl_array_len(a) (((jl_array_t*)(a))->length)
#define jl_array_ndims(a) (((jl_array_t*)(a))->flags.ndims)
#define jl_array_eltype(a) (jl_apply_type((jl_value_t*)jl_array_type, jl_svec1(jl_typeof(a)))) 
// Warning: simple shim for eltype

jl_value_t *jl_svec1(jl_value_t*);
jl_value_t *jl_apply_type(jl_value_t*, jl_value_t*);

jl_value_t *jl_apply_array_type(jl_value_t*, size_t);
jl_array_t *jl_alloc_array_1d(jl_value_t*, size_t);
jl_array_t *jl_alloc_array_2d(jl_value_t*, size_t, size_t);
void jl_arrayset(jl_array_t*, jl_value_t*, size_t);
#define jl_typeis(v, t) (jl_typeof(v) == (jl_value_t*)(t))
#define jl_get_function(m, name) ((jl_function_t*)jl_get_global(m, jl_symbol(name)))

size_t jl_get_world_counter(void);
jl_value_t *jl_toplevel_eval_in(jl_module_t*, jl_value_t*);
jl_value_t *jl_parse_input_line(const char*, size_t, const char*, size_t);
jl_value_t *jl_load_file_string(const char*, size_t, const char*);

jl_svec_t *jl_svec2(jl_value_t*, jl_value_t*);

// Macros
#define JL_TRY if(1)
#define JL_CATCH else if(0)
#define JL_GC_PUSH1(x) (void)(x)
#define JL_GC_POP()

// Event loop
typedef void* uv_loop_t;
typedef enum { UV_RUN_DEFAULT = 0, UV_RUN_ONCE, UV_RUN_NOWAIT = 2 } uv_run_mode;
uv_loop_t *jl_global_event_loop(void);
int uv_run(uv_loop_t*, int);

#define jl_world_counter (jl_get_world_counter())

#ifdef __cplusplus
}
// C++ Overloads
inline void jl_static_show(jl_value_t* v) { jl_static_show(JL_STDERR, v); }
#endif

#endif // JULIA_H_MOCK
