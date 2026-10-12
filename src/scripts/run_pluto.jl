import Pluto
println("Starting Pluto v", Pluto.PLUTO_VERSION, " on port 1235...")
Pluto.run(
    host="127.0.0.1",
    port=1235,
    launch_browser=false,
    auto_reload_from_file=true,
    require_secret_for_access=false
)
