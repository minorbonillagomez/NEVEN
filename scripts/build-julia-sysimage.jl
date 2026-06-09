#!/usr/bin/env julia
"""
NEVEN Julia Sysimage Builder
Generates a pre-compiled sysimage that eliminates JIT delay on first call.

Usage (from Developer Command Prompt or PowerShell):
    julia scripts/build-julia-sysimage.jl

Output:
    C:\\NEVEN\\neven_julia.dll

This sysimage includes the NEVEN module and common Base functions
pre-compiled, reducing first-call latency from ~1-5 minutes to ~1-2 seconds.
"""

using Pkg

# Ensure PackageCompiler is available
if !haskey(Pkg.project().dependencies, "PackageCompiler")
    println("Installing PackageCompiler.jl...")
    Pkg.add("PackageCompiler")
end

using PackageCompiler

# Paths
const NEVEN_HOME = get(ENV, "NEVEN_HOME", "C:\\NEVEN\\")
const STARTUP_SCRIPT = joinpath(NEVEN_HOME, "startup", "startup.jl")
const OUTPUT_SYSIMAGE = joinpath(NEVEN_HOME, "neven_julia.dll")

# Precompile statements -- these are the operations that happen on first call
# and cause the JIT delay. By including them here, they get compiled into the sysimage.
const PRECOMPILE_SCRIPT = joinpath(NEVEN_HOME, "startup", "precompile_julia.jl")

# Create precompile execution script
precompile_code = """
# This script exercises the code paths that cause JIT delay
# PackageCompiler traces these calls and bakes them into the sysimage

# Include the NEVEN module (same as startup.jl)
include("$(replace(STARTUP_SCRIPT, "\\" => "\\\\"))")

# Exercise the module functions to trigger compilation
using .NEVEN

# ListFunctions -- called on every Excel startup
funcs = NEVEN.ListFunctions()

# Basic operations that Julia JIT-compiles on first use
sqrt(144.0)
1 + 1
1.0 + 1.0
string(1)
string(1.0)
string(true)
collect(1:10)
map(x -> x^2, [1,2,3])
sum([1,2,3,4,5])

# String operations
join(["a", "b", "c"], ", ")
strip("  hello  ")
occursin("test", "this is a test")

# Array operations
zeros(3, 3)
ones(3, 3)
rand(3, 3)

# Type checking (used in JlValueToVariable)
x = 42
typeof(x)
x isa Int64
x isa Float64
x isa String
x isa Bool

# Methods/names introspection (used in ListFunctions)
names(Main)
methods(sqrt)

println("Precompile script completed successfully")
"""

# Write precompile script
open(PRECOMPILE_SCRIPT, "w") do f
    write(f, precompile_code)
end

println("=" ^ 60)
println("NEVEN Julia Sysimage Builder")
println("=" ^ 60)
println("Startup script: $STARTUP_SCRIPT")
println("Output sysimage: $OUTPUT_SYSIMAGE")
println("Precompile script: $PRECOMPILE_SCRIPT")
println()

if !isfile(STARTUP_SCRIPT)
    error("Startup script not found: $STARTUP_SCRIPT")
end

println("Building sysimage (this may take 5-10 minutes)...")
println()

create_sysimage(
    nothing;  # No extra packages -- we only use Base
    sysimage_path = OUTPUT_SYSIMAGE,
    precompile_execution_file = PRECOMPILE_SCRIPT,
    cpu_target = "native"
)

println()
println("=" ^ 60)
println("Sysimage built successfully!")
println("Size: $(round(filesize(OUTPUT_SYSIMAGE) / 1024 / 1024, digits=1)) MB")
println("Path: $OUTPUT_SYSIMAGE")
println("=" ^ 60)
println()
println("ControlJulia.exe will automatically use this sysimage on next Excel startup.")
