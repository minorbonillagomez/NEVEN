using PackageCompiler

output_path    = "C:\\NEVEN\\neven_julia.dll"
precompile_path = "C:\\NEVEN\\startup\\sysimage_init.jl"

println("=" ^ 50)
println("Construyendo sysimage NEVEN Julia v5...")
println("Precompile: ", precompile_path)
println("Salida: ", output_path)
println("=" ^ 50)

create_sysimage(
    nothing;
    sysimage_path             = output_path,
    precompile_execution_file = precompile_path,
    cpu_target                = "native"
)

sz = round(filesize(output_path) / 1024 / 1024, digits=1)
println()
println("SYSIMAGE OK: ", sz, " MB")

ver = string(VERSION.major) * "." * string(VERSION.minor) * "." * string(VERSION.patch)
open("C:\\NEVEN\\neven_julia.version", "w") do f
    write(f, ver)
end
println("Version file: ", ver)
println("Reinicia Excel con Julia enabled=true para verificar.")
