module NEVEN

export ReadScriptFile, InstallApplicationPointer, ListFunctions, DisplayError, SetCallbacks, CreateCOMType

# Internal state
const _application_pointer = Ref{UInt64}(0)
const _com_callback_ptr = Ref{Ptr{Cvoid}}(C_NULL)
const _callback2_ptr = Ref{Ptr{Cvoid}}(C_NULL)

# 1. Read Script File - called via ResolveFunction("RJ.ReadScriptFile")
function ReadScriptFile(path::String, notify::Bool=false)
    if notify
        println("Loading script file: $path")
    end
    try
        Base.include(Main, path)
        return true
    catch e
        @error "Error loading $path" exception=(e, catch_backtrace())
        return false
    end
end

# 2. Install Application Pointer - called via ResolveFunction("NEVEN.InstallApplicationPointer")
function InstallApplicationPointer(pointer::UInt64)
    _application_pointer[] = pointer
    # Create a global EXCEL object for convenience
    global EXCEL = CreateCOMType(["Excel.Application", pointer, nothing, nothing])
    println("Excel application pointer installed: ", string(pointer, base=16))
end

# 3. List Functions - called via eval "NEVEN.ListFunctions()"
# Expected return: Array of Arrays (string arrays) 
# Format: [name, docstring, category, arg1, arg2, ...]
function ListFunctions()
    functions = Any[]
    for name in names(Main)
        if !isdefined(Main, name) continue end
        obj = getfield(Main, name)
        # Skip our own internal modules and non-functions
        if obj isa Function && name != :NEVEN && name != :RJ && name != :include && name != :eval
            m = methods(obj)
            if length(m) > 0
                entry = String[]
                push!(entry, string(name))
                
                # Docstring — wrapped in try/catch for Julia version compatibility
                doc_str = ""
                try
                    doc = Base.Docs.doc(obj)
                    doc_str = isnothing(doc) ? "" : strip(string(doc))
                catch
                    doc_str = ""
                end
                push!(entry, doc_str)
                
                # Category
                push!(entry, "Julia")
                
                # Arguments
                arg_names = Base.method_argnames(m.ms[1])[2:end]
                for arg_name in arg_names
                    push!(entry, string(arg_name))
                end
                
                push!(functions, entry)
            end
        end
    end
    return functions
end

# 4. Error Display - called via ResolveFunction("RJ.DisplayError")
function DisplayError(e)
    Base.showerror(stderr, e, catch_backtrace())
    println(stderr)
end

# 5. Set Callbacks - called via ResolveFunction("NEVEN.SetCallbacks")
function SetCallbacks(com_ptr::Ptr{Cvoid}, cb2_ptr::Ptr{Cvoid})
    _com_callback_ptr[] = com_ptr
    _callback2_ptr[] = cb2_ptr
end

# 6. Create COM Type - called via eval "NEVEN.CreateCOMType"
# Receives [name, ptr, functions, enums]
mutable struct COMObject
    name::String
    ptr::UInt64
    functions::Any
    enums::Any
end

function CreateCOMType(args)
    return COMObject(args[1], args[2], args[3], args[4])
end

# Helper to call COM methods
function CallCOMMethod(obj::COMObject, name::String, type::String, index::UInt32, args...)
    if _com_callback_ptr[] == C_NULL
        error("COM callbacks not registered.")
    end
    return ccall(_com_callback_ptr[], Any, (UInt64, Cstring, Cstring, UInt32, Any), 
                 obj.ptr, name, type, index, collect(args))
end

# Property Accessors for COMObject
function Base.getproperty(obj::COMObject, sym::Symbol)
    if sym in (:name, :ptr, :functions, :enums)
        return getfield(obj, sym)
    end
    
    name = string(sym)
    
    if !isnothing(obj.functions)
        for func in obj.functions
            if func[1] == name
                if func[3] == "get"
                    return CallCOMMethod(obj, name, "get", UInt32(func[2]))
                else
                    return (args...) -> CallCOMMethod(obj, name, "method", UInt32(func[2]), args...)
                end
            end
        end
    end
    
    return (args...) -> CallCOMMethod(obj, name, "method", UInt32(0), args...)
end

function Base.setproperty!(obj::COMObject, sym::Symbol, val)
    if sym in (:name, :ptr, :functions, :enums)
        return setfield!(obj, sym, val)
    end
    
    name = string(sym)
    
    if !isnothing(obj.functions)
        for func in obj.functions
            if func[1] == name && func[3] == "put"
                return CallCOMMethod(obj, name, "put", UInt32(func[2]), val)
            end
        end
    end
    
    return CallCOMMethod(obj, name, "put", UInt32(0), val)
end

# 7. MIME Display System
struct NEVENDisplay <: AbstractDisplay end

function Base.display(d::NEVENDisplay, x)
    # Priority order for display
    for mime in ["text/html", "image/png", "text/plain"]
        if showable(mime, x)
            try
                io = IOBuffer()
                show(io, mime, x)
                data = take!(io)
                if _callback2_ptr[] != C_NULL
                    # Callback2(const char *command, void *data1, void *data2, void *data3)
                    # data1 = mime_type (string), data2 = data (Array{UInt8})
                    ccall(_callback2_ptr[], Ptr{Cvoid}, (Cstring, Any, Any, Ptr{Cvoid}), 
                          "render-mime", mime, data, C_NULL)
                end
                return
            catch e
                # @warn "Error displaying with $mime" exception=(e, catch_backtrace())
                continue
            end
        end
    end
    throw(MethodError(display, (d, x)))
end

# ═══════════════════════════════════════════════════════════════════════════
# Excel ↔ Pluto Data Exchange
# ═══════════════════════════════════════════════════════════════════════════

# Named datasets from Excel — Pluto notebooks read these reactively
const _datasets = Dict{String, Any}()
const _dataset_version = Ref{Int}(0)  # Incremented on each update for Pluto reactivity

"""
    set_data(name::String, data::Matrix)

Store a dataset from Excel. Writes to a shared JSON file that
Pluto notebooks can read independently.
"""
function set_data(name::String, data)
    _datasets[name] = data
    _dataset_version[] += 1
    
    # Also write to shared file for Pluto (separate process)
    try
        dir = get(ENV, "NEVEN_HOME", "C:\\NEVEN")
        mkpath(joinpath(dir, "data"))
        filepath = joinpath(dir, "data", "$(name).tsv")
        open(filepath, "w") do io
            for i in 1:size(data, 1)
                for j in 1:size(data, 2)
                    if j > 1
                        print(io, "\t")
                    end
                    print(io, data[i, j])
                end
                println(io)
            end
        end
    catch e
        @warn "set_data: could not write shared file" exception=e
    end
    
    return "OK: $(name) ($(size(data,1))x$(size(data,2)), v$(_dataset_version[]))"
end

"""
    get_data(name::String="default")

Read a dataset sent from Excel. Use in Pluto notebooks:
```julia
data = NEVEN.get_data("ventas")
```
Returns the matrix, or `nothing` if not found.
"""
function get_data(name::String="default")
    return get(_datasets, name, nothing)
end

"""
    get_data_version()

Returns the current dataset version counter. Use in Pluto to trigger
reactivity: `v = NEVEN.get_data_version()` — Pluto re-runs cells
that depend on `v` when data changes.
"""
function get_data_version()
    return _dataset_version[]
end

"""
    list_data()

List all available dataset names from Excel.
"""
function list_data()
    return collect(keys(_datasets))
end

export set_data, get_data, get_data_version, list_data

# Register the display
function __init__()
    pushdisplay(NEVENDisplay())
end

end # module NEVEN

# Aliases
const RJ = NEVEN
