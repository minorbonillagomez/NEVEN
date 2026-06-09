### A Pluto.jl notebook ###
# v0.20.4

using Markdown
using InteractiveUtils

# ╔═╡ Cell 1 — Title
md"""
# 🚀 NASA HL-20 Reentry Trajectory (Simplified 3-DOF)

This notebook demonstrates a simplified atmospheric reentry simulation inspired by
the NASA HL-20 lifting body vehicle. The model uses 3 degrees of freedom (altitude,
velocity, flight path angle) with representative aerodynamic parameters.

**Data source:** User-defined initial conditions from Excel via `=NEVEN.pluto.data()`

**Purpose:** Demonstrate that NEVEN + Julia can solve aerospace engineering problems
directly from an Excel workflow — the user defines parameters in cells, sends them
to Julia, and interacts with the simulation results reactively.

> This is a pedagogical model. For production aerospace simulations, replace the
> constant aerodynamic coefficients with Mach/alpha-dependent lookup tables from
> NASA TM-4302.
"""

# ╔═╡ Cell 2 — Parameters
md"""
## Vehicle & Atmosphere Parameters

Adjust these to explore different reentry scenarios:
"""

# ╔═╡ Cell 3 — HL-20 Constants
begin
    # HL-20 approximate parameters
    m = 10000.0       # Vehicle mass [kg]
    S = 28.0          # Reference area [m²]
    CL = 0.8          # Lift coefficient (constant, simplified)
    CD = 0.4          # Drag coefficient (constant, simplified)
    L_D = CL / CD     # Lift-to-drag ratio ≈ 2.0

    # Earth & atmosphere
    Re = 6371000.0    # Earth radius [m]
    g0 = 9.81         # Surface gravity [m/s²]
    rho0 = 1.225      # Sea-level air density [kg/m³]
    H = 7500.0        # Scale height [m]

    md"""
    | Parameter | Value | Unit |
    |:---|:---|:---|
    | Mass (m) | $(m) | kg |
    | Reference area (S) | $(S) | m² |
    | Lift coefficient (CL) | $(CL) | - |
    | Drag coefficient (CD) | $(CD) | - |
    | L/D ratio | $(round(L_D, digits=2)) | - |
    | Scale height (H) | $(H) | m |
    """
end

# ╔═╡ Cell 4 — Initial conditions
begin
    # Default initial conditions (user can override from Excel)
    h0 = 120000.0     # Initial altitude [m] (120 km — entry interface)
    V0 = 7500.0       # Initial velocity [m/s] (~orbital speed)
    gamma0 = -1.5     # Initial flight path angle [deg] (shallow entry)

    # Convert to radians
    gamma0_rad = gamma0 * π / 180.0
end

# ╔═╡ Cell 5 — Try loading Excel data
begin
    local excel_params = nothing
    local data_file = "C:\\NEVEN\\data\\hl20_params.tsv"

    if isfile(data_file)
        local raw = readdlm(data_file, '\t')
        if size(raw, 1) >= 1 && size(raw, 2) >= 3
            h0 = Float64(raw[1, 1])      # Altitude from Excel
            V0 = Float64(raw[1, 2])      # Velocity from Excel
            gamma0 = Float64(raw[1, 3])  # Angle from Excel
            gamma0_rad = gamma0 * π / 180.0
            excel_params = true
        end
    end

    if excel_params === nothing
        md"""
        > ℹ️ Using default initial conditions. To load from Excel:
        > ```
        > =NEVEN.pluto.data(A1:C1, "hl20_params")
        > ```
        > Where A1=altitude(m), B1=velocity(m/s), C1=angle(deg)
        """
    else
        md"""
        > ✅ Initial conditions loaded from Excel:
        > h₀ = $(round(h0/1000, digits=1)) km,
        > V₀ = $(round(V0, digits=0)) m/s,
        > γ₀ = $(gamma0)°
        """
    end
end

# ╔═╡ Cell 6 — ODE System
md"""
## 3-DOF Equations of Motion

The simplified planar reentry dynamics:

$$\dot{h} = V \sin\gamma$$
$$\dot{V} = -\frac{\rho V^2 S C_D}{2m} - g\sin\gamma$$
$$\dot{\gamma} = \frac{\rho V S C_L}{2m} - \frac{g - V^2/r}{V}\cos\gamma$$

where $\rho = \rho_0 e^{-h/H}$ and $r = R_e + h$.
"""

# ╔═╡ Cell 7 — Solver (RK4)
function solve_reentry(h0, V0, gamma0_rad; dt=0.5, t_max=2000.0)
    # State: [h, V, gamma]
    t_hist = Float64[]
    h_hist = Float64[]
    V_hist = Float64[]
    gamma_hist = Float64[]
    q_hist = Float64[]  # Dynamic pressure
    g_load_hist = Float64[]

    h, V, gamma = h0, V0, gamma0_rad
    t = 0.0

    function derivatives(h, V, gamma)
        r = Re + h
        g = g0 * (Re / r)^2
        rho = rho0 * exp(-h / H)
        q = 0.5 * rho * V^2  # Dynamic pressure

        dh = V * sin(gamma)
        dV = -q * S * CD / m - g * sin(gamma)
        dgamma = q * S * CL / (m * V) - (g - V^2 / r) * cos(gamma) / V

        return dh, dV, dgamma, q
    end

    while t <= t_max && h > 0 && h < 200000 && V > 50
        dh1, dV1, dg1, q = derivatives(h, V, gamma)

        # RK4 integration
        h2, V2, g2 = h + 0.5*dt*dh1, V + 0.5*dt*dV1, gamma + 0.5*dt*dg1
        dh2, dV2, dg2, _ = derivatives(h2, V2, g2)

        h3, V3, g3 = h + 0.5*dt*dh2, V + 0.5*dt*dV2, gamma + 0.5*dt*dg2
        dh3, dV3, dg3, _ = derivatives(h3, V3, g3)

        h4, V4, g4 = h + dt*dh3, V + dt*dV3, gamma + dt*dg3
        dh4, dV4, dg4, _ = derivatives(h4, V4, g4)

        h += dt/6 * (dh1 + 2*dh2 + 2*dh3 + dh4)
        V += dt/6 * (dV1 + 2*dV2 + 2*dV3 + dV4)
        gamma += dt/6 * (dg1 + 2*dg2 + 2*dg3 + dg4)

        # g-load = total aerodynamic acceleration / g0
        g_load = q * S * sqrt(CL^2 + CD^2) / (m * g0)

        push!(t_hist, t)
        push!(h_hist, h / 1000)  # km
        push!(V_hist, V)
        push!(gamma_hist, gamma * 180 / π)
        push!(q_hist, q / 1000)  # kPa
        push!(g_load_hist, g_load)

        t += dt
    end

    return t_hist, h_hist, V_hist, gamma_hist, q_hist, g_load_hist
end

# ╔═╡ Cell 8 — Run simulation
begin
    t, h, V, gamma, q, g_load = solve_reentry(h0, V0, gamma0_rad)

    md"""
    ## Simulation Results

    | Metric | Value |
    |:---|:---|
    | Duration | $(round(t[end], digits=0)) seconds |
    | Final altitude | $(round(h[end], digits=1)) km |
    | Final velocity | $(round(V[end], digits=0)) m/s |
    | Peak dynamic pressure | $(round(maximum(q), digits=1)) kPa |
    | Peak g-load | $(round(maximum(g_load), digits=1)) g |
    | Max deceleration altitude | $(round(h[argmax(g_load)], digits=1)) km |
    """
end

# ╔═╡ Cell 9 — Altitude vs Time plot (text-based for compatibility)
begin
    using DelimitedFiles

    # Write results to TSV for Excel retrieval
    results = hcat(t, h, V, gamma, q, g_load)
    headers = ["Time_s" "Altitude_km" "Velocity_ms" "FlightPathAngle_deg" "DynPressure_kPa" "G_Load"]
    output_file = "C:\\NEVEN\\data\\hl20_results.tsv"
    try
        open(output_file, "w") do io
            writedlm(io, headers, '\t')
            writedlm(io, results, '\t')
        end
        md"""
        > 📊 Results saved to `C:\NEVEN\data\hl20_results.tsv`
        > Load in Excel with: `=NEVEN.j("NEVEN.get_data(\"hl20_results\")")`
        """
    catch
        md"> ⚠️ Could not write results file"
    end
end

# ╔═╡ Cell 10 — Summary
md"""
## How to Use This From Excel

1. **Set initial conditions** in Excel cells (altitude, velocity, angle)
2. **Send to Julia**: `=NEVEN.pluto.data(A1:C1, "hl20_params")`
3. **Open this notebook**: `=NEVEN.notebook.open("hl20_reentry")`
4. **Interact** — modify parameters above and observe trajectory changes
5. **Retrieve results** — the TSV file is available for Excel import

### Extending the Model

This simplified 3-DOF model can be extended to:
- **6-DOF** with roll/pitch/yaw (add angular rates and moments)
- **Mach-dependent aero** using interpolation tables from NASA TM-4302
- **Thermal constraints** with heat flux q̇ = k·ρ^0.5·V^3 (Sutton-Graves)
- **Guidance** with bank angle modulation for cross-range control
- **Monte Carlo** analysis varying initial conditions and atmosphere model

Each extension is a matter of adding Julia code to this notebook —
the Excel→Julia→Pluto pipeline handles data flow automatically.
"""
