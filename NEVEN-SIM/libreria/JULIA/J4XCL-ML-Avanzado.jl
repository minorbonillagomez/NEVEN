# J4XCL ML Avanzado - Julia puro, sin dependencias
# TipoOutput: 0=info, 1=metricas, 2=importancia, 3=predicciones, 4=confusion, 5=resumen

using Statistics, Random, LinearAlgebra

function _ml_html_report(model_name, metrics, importances, confusion, classes, params)
    metrics_parts = String[]
    for (k, v) in metrics
        if v isa Number
            push!(metrics_parts, "\"" * string(k) * "\":" * string(v))
        else
            push!(metrics_parts, "\"" * string(k) * "\":\"" * string(v) * "\"")
        end
    end
    metrics_json = "{" * join(metrics_parts, ",") * "}"
    imp_json = if importances !== nothing && length(importances) > 0
        "[" * join(["[\"" * string(n) * "\"," * string(v) * "]" for (n,v) in importances], ",") * "]"
    else
        "[]"
    end
    conf_json = if confusion !== nothing && length(confusion) > 0
        nr, nc2 = size(confusion)
        "[" * join(["[" * join([string(Int(confusion[i,j])) for j in 1:nc2], ",") * "]" for i in 1:nr], ",") * "]"
    else
        "[]"
    end
    cls_json = if classes !== nothing && length(classes) > 0
        "[" * join(["\"" * string(c) * "\"" for c in classes], ",") * "]"
    else
        "[]"
    end
    params_parts = ["\"" * string(k) * "\":\"" * string(v) * "\"" for (k,v) in params]
    params_json = "{" * join(params_parts, ",") * "}"
    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>NEVEN ML - $(model_name)</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Segoe UI",sans-serif;background:#2d2d2d;color:#e0e0e0;padding:20px}
h1{color:#a8e600;font-size:20px;margin-bottom:4px}
.sub{color:#b0b0b0;font-size:11px;margin-bottom:16px}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.st{background:#4a4a4a;border-radius:6px;padding:12px 18px;text-align:center;min-width:100px}
.st .v{font-size:20px;font-weight:700;color:#a8e600}
.st .l{font-size:9px;color:#b0b0b0;margin-top:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.card{background:#383838;border-radius:8px;padding:16px}
.card h2{color:#8bc34a;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.chart{height:300px}
.params{font-size:11px;color:#b0b0b0;margin-top:12px;padding:10px;background:#4a4a4a;border-radius:6px;line-height:1.8}
.params b{color:#8bc34a}
</style></head><body>
<h1>NEVEN ML Studio - $(model_name)</h1>
<p class="sub">Resultado del entrenamiento | Julia</p>
<div class="stats" id="stats"></div>
<div class="grid">
  <div class="card"><h2>Importancia de Variables</h2><div class="chart" id="ch1"></div></div>
  <div class="card"><h2>Matriz de Confusion</h2><div class="chart" id="ch2"></div></div>
</div>
<div class="params" id="info"></div>
<script>
var metrics=$(metrics_json),imp=$(imp_json),conf=$(conf_json),cls=$(cls_json),params=$(params_json);
var s="";for(var k in metrics){var v=metrics[k];if(typeof v==="number")v=v.toFixed(4);s+='<div class="st"><div class="v">'+v+'</div><div class="l">'+k+'</div></div>';}
document.getElementById("stats").innerHTML=s;
if(imp.length){var n=imp.map(x=>x[0]).reverse(),v=imp.map(x=>x[1]).reverse();Plotly.newPlot("ch1",[{y:n,x:v,type:"bar",orientation:"h",marker:{color:"#a8e600"}}],{paper_bgcolor:"#383838",plot_bgcolor:"#383838",font:{color:"#b0b0b0",size:10},xaxis:{gridcolor:"#4a4a4a"},yaxis:{gridcolor:"#4a4a4a"},margin:{t:5,r:10,b:30,l:80}},{responsive:true})}
else{document.getElementById("ch1").innerHTML='<p style="color:#555;padding:20px">No disponible</p>'}
if(conf.length&&cls.length){Plotly.newPlot("ch2",[{z:conf,x:cls,y:cls,type:"heatmap",colorscale:[[0,"#2d2d2d"],[1,"#a8e600"]],showscale:false}],{paper_bgcolor:"#383838",plot_bgcolor:"#383838",font:{color:"#b0b0b0",size:10},xaxis:{title:"Predicho"},yaxis:{title:"Real"},margin:{t:5,r:10,b:40,l:50}},{responsive:true})}
else{document.getElementById("ch2").innerHTML='<p style="color:#555;padding:20px">No disponible</p>'}
var p="<b>Modelo:</b> $(model_name)<br>";for(var k in params)p+="<b>"+k+":</b> "+params[k]+"<br>";
document.getElementById("info").innerHTML=p;
</script></body></html>"""
    path = "C:/NEVEN/workspace/ml-report.html"
    write(path, html)
    return path
end

function _ml_modo(v)
    c = Dict{eltype(v),Int}()
    for x in v; c[x] = get(c, x, 0) + 1; end
    return sort(collect(c), by=x->x[2], rev=true)[1][1]
end

function _ml_accuracy(y, p)
    return sum(y .== p) / length(y)
end

function _ml_confusion(y, p)
    cls = sort(unique(vcat(y, p)))
    nc = length(cls)
    cm = zeros(Int, nc, nc)
    for i in 1:length(y)
        ri = findfirst(==(y[i]), cls)
        pi = findfirst(==(p[i]), cls)
        if !isnothing(ri) && !isnothing(pi)
            cm[ri, pi] += 1
        end
    end
    return cm, cls
end

# === KNN ======================================================================

"""
    KNN(X, Y, K=5, TipoOutput=1)
K-Nearest Neighbors. K=vecinos, TipoOutput: 0=info 1=metricas 2=distancias 3=pred 4=confusion 5=resumen
"""
function KNN(SetDatosX, SetDatosY, K=5, TipoOutput=1)
    X = Float64.(SetDatosX)
    y = vec(SetDatosY)
    n = size(X, 1)
    k = Int(K)
    to = Int(TipoOutput)

    if to == 0
        return String["=== KNN (K=" * string(k) * ") -- Outputs Disponibles ===",
            "[0] Esta lista",
            "[1] Metricas del modelo (Accuracy)",
            "[2] Distancias promedio a vecinos",
            "[3] Predicciones del modelo",
            "[4] Matriz de confusion",
            "[5] Resumen completo"]
    end

    pred = similar(y)
    for i in 1:n
        ds = Float64[sqrt(sum((X[i,:] .- X[j,:]).^2)) for j in setdiff(1:n, i)]
        neighbors_idx = sortperm(ds)[1:min(k, length(ds))]
        real_idx = setdiff(1:n, i)
        pred[i] = _ml_modo(y[real_idx[neighbors_idx]])
    end
    acc = _ml_accuracy(y, pred)

    if to == 1
        return String["=== KNN (K=" * string(k) * ") -- Metricas ===",
            "Accuracy: " * string(round(acc*100, digits=2)) * "%",
            "N: " * string(n), "Variables: " * string(size(X,2)),
            "Clases: " * join(string.(sort(unique(y))), ", ")]
    elseif to == 2
        return String["=== KNN -- Importancia ===",
            "(No disponible para KNN - use RandomForest)"]
    elseif to == 3
        return pred
    elseif to == 4
        cm, cls = _ml_confusion(y, pred)
        r = String["=== KNN (K=" * string(k) * ") -- Matriz de Confusion ===",
            "Real\\Pred | " * join(string.(cls), " | ")]
        for i in 1:length(cls); push!(r, string(cls[i]) * " | " * join(string.(cm[i,:]), " | ")); end
        push!(r, ""); push!(r, "Accuracy: " * string(round(acc*100, digits=2)) * "%")
        return r
    elseif to == 5
        cm, cls = _ml_confusion(y, pred)
        metrics = [("Accuracy", round(acc, digits=4)), ("N", n), ("Variables", size(X,2)), ("K", k)]
        params = [("Algoritmo", "K-Nearest Neighbors"), ("K", string(k)), ("Plataforma", "Julia puro")]
        return _ml_html_report("KNN", metrics, nothing, cm, cls, params)
    end
    return String["TipoOutput no valido"]
end

# === RANDOM FOREST ============================================================

struct _RFNode
    feat::Int; thr::Float64
    left::Union{_RFNode, Nothing}; right::Union{_RFNode, Nothing}
    val::Any
end

function _rf_gini(y)
    n = length(y); n == 0 && return 0.0
    imp = 1.0
    for c in unique(y); p = sum(y .== c)/n; imp -= p^2; end
    return imp
end

function _rf_split(X, y)
    n, p = size(X); bg = Inf; bf = 1; bt = 0.0
    for j in 1:p
        vals = unique(X[:,j])
        for t in vals
            l = X[:,j] .<= t; r = .!l
            nl = sum(l); nr = sum(r)
            (nl == 0 || nr == 0) && continue
            g = (nl*_rf_gini(y[l]) + nr*_rf_gini(y[r]))/n
            if g < bg; bg=g; bf=j; bt=t; end
        end
    end
    return bf, bt
end

function _rf_build(X, y, d, md)
    if d >= md || length(unique(y)) == 1 || size(X,1) <= 2
        return _RFNode(0, 0.0, nothing, nothing, _ml_modo(y))
    end
    f, t = _rf_split(X, y)
    l = X[:,f] .<= t; r = .!l
    (sum(l)==0 || sum(r)==0) && return _RFNode(0, 0.0, nothing, nothing, _ml_modo(y))
    return _RFNode(f, t, _rf_build(X[l,:],y[l],d+1,md), _rf_build(X[r,:],y[r],d+1,md), nothing)
end

function _rf_pred(node::_RFNode, x)
    node.val !== nothing && return node.val
    return x[node.feat] <= node.thr ? _rf_pred(node.left, x) : _rf_pred(node.right, x)
end

"""
    RandomForest(X, Y, n_arboles=100, TipoOutput=1)
Random Forest. n_arboles=cantidad de arboles. TipoOutput: 0=info 1=metricas 2=importancia 3=pred 4=confusion 5=resumen
"""
function RandomForest(SetDatosX, SetDatosY, n_arboles=100, TipoOutput=1)
    X = Float64.(SetDatosX); y = vec(SetDatosY)
    n, p = size(X)
    nt = Int(n_arboles); md = 5
    to = Int(TipoOutput)

    if to == 0
        return String["=== Random Forest (n=" * string(nt) * ") -- Outputs Disponibles ===",
            "[0] Esta lista",
            "[1] Metricas del modelo (Accuracy)",
            "[2] Importancia de variables",
            "[3] Predicciones del modelo",
            "[4] Matriz de confusion",
            "[5] Resumen completo"]
    end

    rng = MersenneTwister(42)
    nf = max(1, Int(round(sqrt(p))))
    trees = []
    for _ in 1:nt
        idx = rand(rng, 1:n, n)
        fi = sort(randperm(rng, p)[1:nf])
        tree = _rf_build(X[idx, fi], y[idx], 0, md)
        push!(trees, (tree, fi))
    end

    pred = Vector{eltype(y)}(undef, n)
    for i in 1:n
        votes = Dict{eltype(y),Int}()
        for (tree, fi) in trees
            v = _rf_pred(tree, X[i, fi])
            votes[v] = get(votes, v, 0) + 1
        end
        pred[i] = sort(collect(votes), by=x->x[2], rev=true)[1][1]
    end
    acc = _ml_accuracy(y, pred)

    if to == 1
        return String["=== Random Forest (n=" * string(nt) * ") -- Metricas ===",
            "Accuracy: " * string(round(acc*100, digits=2)) * "%",
            "N: " * string(n), "Arboles: " * string(nt),
            "Features/arbol: " * string(nf) * "/" * string(p)]
    elseif to == 2
        fc = zeros(Int, p)
        function _cf(node, fi)
            node === nothing && return
            node.val !== nothing && return
            fc[fi[node.feat]] += 1
            _cf(node.left, fi); _cf(node.right, fi)
        end
        for (tree, fi) in trees; _cf(tree, fi); end
        total = max(1, sum(fc))
        imp = [(i, fc[i]/total) for i in 1:p]
        sort!(imp, by=x->x[2], rev=true)
        r = String["=== Random Forest (n=" * string(nt) * ") -- Importancia de Variables ==="]
        maxval = imp[1][2]
        for (i, v) in imp
            v > 0.001 || continue
            bar = repeat("#", Int(round(v/maxval * 40)))
            push!(r, "  Var" * string(i) * "     " * string(round(v, digits=4)) * " " * bar)
        end
        return r
    elseif to == 3
        return pred
    elseif to == 4
        cm, cls = _ml_confusion(y, pred)
        r = String["=== Random Forest (n=" * string(nt) * ") -- Matriz de Confusion ===",
            "Real\\Pred | " * join(string.(cls), " | ")]
        for i in 1:length(cls); push!(r, string(cls[i]) * " | " * join(string.(cm[i,:]), " | ")); end
        push!(r, ""); push!(r, "Accuracy: " * string(round(acc*100, digits=2)) * "%")
        return r
    elseif to == 5
        cm, cls = _ml_confusion(y, pred)
        fc2 = zeros(Int, p)
        function _cf2(node, fi)
            node === nothing && return
            node.val !== nothing && return
            fc2[fi[node.feat]] += 1
            _cf2(node.left, fi); _cf2(node.right, fi)
        end
        for (tree, fi) in trees; _cf2(tree, fi); end
        total2 = max(1, sum(fc2))
        imp2 = [(i, fc2[i]/total2) for i in 1:p]
        sort!(imp2, by=x->x[2], rev=true)
        importances = [("Var" * string(i), round(v, digits=4)) for (i,v) in imp2 if v > 0.001]
        metrics = [("Accuracy", round(acc, digits=4)), ("N", n), ("Arboles", nt), ("Features", nf)]
        params = [("Algoritmo", "Random Forest"), ("Arboles", string(nt)), ("Plataforma", "Julia puro")]
        return _ml_html_report("Random Forest", metrics, importances, cm, cls, params)
    end
    return String["TipoOutput no valido"]
end

# === ARBOL DE DECISION ========================================================

"""
    ArbolDecision(X, Y, max_depth=5, TipoOutput=1)
Arbol de Decision CART. max_depth=profundidad. TipoOutput: 0=info 1=metricas 2=importancia 3=pred 4=confusion 5=resumen
"""
function ArbolDecision(SetDatosX, SetDatosY, max_depth=5, TipoOutput=1)
    X = Float64.(SetDatosX); y = vec(SetDatosY); n = size(X,1)
    to = Int(TipoOutput)
    if to == 0
        return String["=== Arbol de Decision (depth=" * string(Int(max_depth)) * ") -- Outputs Disponibles ===",
            "[0] Esta lista",
            "[1] Metricas del modelo (Accuracy)",
            "[2] Importancia de variables",
            "[3] Predicciones del modelo",
            "[4] Matriz de confusion",
            "[5] Resumen completo"]
    end
    tree = _rf_build(X, y, 0, Int(max_depth))
    pred = [_rf_pred(tree, X[i,:]) for i in 1:n]
    acc = _ml_accuracy(y, pred)
    if to == 1
        return String["=== Arbol (depth=" * string(Int(max_depth)) * ") -- Metricas ===",
            "Accuracy: " * string(round(acc*100, digits=2)) * "%",
            "N: " * string(n), "Variables: " * string(size(X,2))]
    elseif to == 2
        return String["=== Arbol -- Importancia ===",
            "(No disponible para arbol individual - use RandomForest)"]
    elseif to == 3
        return pred
    elseif to == 4
        cm, cls = _ml_confusion(y, pred)
        r = String["=== Arbol (depth=" * string(Int(max_depth)) * ") -- Matriz de Confusion ===",
            "Real\\Pred | " * join(string.(cls), " | ")]
        for i in 1:length(cls); push!(r, string(cls[i]) * " | " * join(string.(cm[i,:]), " | ")); end
        push!(r, ""); push!(r, "Accuracy: " * string(round(acc*100, digits=2)) * "%")
        return r
    elseif to == 5
        cm, cls = _ml_confusion(y, pred)
        metrics = [("Accuracy", round(acc, digits=4)), ("N", n), ("Profundidad", Int(max_depth))]
        params = [("Algoritmo", "Arbol de Decision"), ("Profundidad", string(Int(max_depth))), ("Plataforma", "Julia puro")]
        return _ml_html_report("Arbol de Decision", metrics, nothing, cm, cls, params)
    end
    return String["TipoOutput no valido"]
end

# === PCA ======================================================================

"""
    ACP(X, n_componentes=2, TipoOutput=1)
PCA. n_componentes=dims. TipoOutput: 0=info 1=varianza 2=loadings 3=coords 4=eigenvals 5=resumen
"""
function ACP(SetDatosX, n_componentes=2, TipoOutput=1)
    X = Float64.(SetDatosX); n, p = size(X)
    nc = min(Int(n_componentes), p, n)
    to = Int(TipoOutput)
    if to == 0
        return String["=== PCA (n=" * string(nc) * ") -- Outputs Disponibles ===",
            "[0] Esta lista",
            "[1] Varianza explicada por componente",
            "[2] Loadings (pesos)",
            "[3] Coordenadas (scores)",
            "[4] Eigenvalues",
            "[5] Resumen completo"]
    end
    mu = mean(X, dims=1); sigma = std(X, dims=1)
    sigma[sigma .== 0] .= 1.0
    Z = (X .- mu) ./ sigma
    C = (Z' * Z) / (n - 1)
    ev, evec = eigen(Symmetric(C))
    idx = sortperm(ev, rev=true)
    ev = ev[idx]; evec = evec[:, idx]
    ve = ev[1:nc] ./ sum(ev)
    coords = Z * evec[:, 1:nc]
    if to == 1
        r = String["=== PCA (n=" * string(nc) * ") -- Varianza Explicada ==="]
        acum = 0.0
        for i in 1:nc; acum += ve[i]
            push!(r, "  PC" * string(i) * ": " * string(round(ve[i]*100, digits=2)) * "% (acum: " * string(round(acum*100, digits=2)) * "%)")
        end
        push!(r, ""); push!(r, "Total: " * string(round(acum*100, digits=2)) * "%")
        return r
    elseif to == 2
        r = String["=== PCA -- Loadings ==="]
        for i in 1:nc
            push!(r, "  PC" * string(i) * ": " * join([string(round(evec[j,i], digits=4)) for j in 1:p], ", "))
        end
        return r
    elseif to == 3
        return coords
    elseif to == 4
        r = String["=== PCA -- Eigenvalues ==="]
        for i in 1:min(p, 10)
            push!(r, "  L" * string(i) * ": " * string(round(ev[i], digits=4)))
        end
        return r
    elseif to == 5
        importances = [("PC" * string(i), round(ve[i], digits=4)) for i in 1:nc]
        metrics = [("Componentes", nc), ("VarTotal", round(sum(ve)*100, digits=2)), ("N", n), ("Variables", p)]
        params = [("Algoritmo", "ACP / PCA"), ("Componentes", string(nc)), ("Plataforma", "Julia puro")]
        return _ml_html_report("ACP (PCA)", metrics, importances, nothing, nothing, params)
    end
    return String["TipoOutput no valido"]
end


# === GRADIENT BOOSTING (NEVEN-Boost) ==========================================

struct _GBStump
    feat::Int; thr::Float64; lv::Float64; rv::Float64
end

function _gb_fit_stump(X, res)
    n, p = size(X); bl = Inf; bf=1; bt=0.0; blv=0.0; brv=0.0
    for j in 1:p
        vals = unique(X[:,j]); step = max(1, length(vals) / 20)
        for ti in 1:Int(ceil(step)):length(vals)
            t = vals[ti]; lm = X[:,j] .<= t; rm = .!lm
            nl = sum(lm); nr = sum(rm)
            (nl==0 || nr==0) && continue
            lval = mean(res[lm]); rval = mean(res[rm])
            loss = sum((res[lm] .- lval).^2) + sum((res[rm] .- rval).^2)
            if loss < bl; bl=loss; bf=j; bt=t; blv=lval; brv=rval; end
        end
    end
    return _GBStump(bf, bt, blv, brv)
end

function _gb_pred_stump(s::_GBStump, X)
    return [X[i,s.feat] <= s.thr ? s.lv : s.rv for i in 1:size(X,1)]
end

"""
    GradientBoosting(X, Y, n_estimadores=100, TipoOutput=1)
NEVEN-Boost: Gradient Boosting propio. n_estimadores=stumps. TipoOutput: 0=info 1=metricas 2=importancia 3=pred 4=confusion 5=html
"""
function GradientBoosting(SetDatosX, SetDatosY, n_estimadores=100, TipoOutput=1)
    X = Float64.(SetDatosX); y_raw = vec(SetDatosY); n, p = size(X)
    ne = Int(n_estimadores); to = Int(TipoOutput)

    if to == 0
        return String["=== Gradient Boosting (n=" * string(ne) * ") -- Outputs Disponibles ===",
            "[0] Esta lista",
            "[1] Metricas del modelo (Accuracy/R2)",
            "[2] Importancia de variables",
            "[3] Predicciones del modelo",
            "[4] Matriz de confusion",
            "[5] Reporte visual en Viewer"]
    end

    classes = sort(unique(y_raw))
    is_classif = length(classes) == 2

    if is_classif
        y = [v == classes[2] ? 1.0 : 0.0 for v in y_raw]
        pm = mean(y); F = fill(log(pm/(1-pm+1e-10)), n)
        stumps = _GBStump[]
        for _ in 1:ne
            probs = 1.0 ./ (1.0 .+ exp.(-F))
            res = y .- probs
            s = _gb_fit_stump(X, res)
            push!(stumps, s)
            F .+= 0.1 .* _gb_pred_stump(s, X)
        end
        fp = 1.0 ./ (1.0 .+ exp.(-F))
        pred = [p >= 0.5 ? classes[2] : classes[1] for p in fp]
        acc = _ml_accuracy(y_raw, pred)
        metric_str = "Accuracy: " * string(round(acc*100, digits=2)) * "%"
    else
        y = Float64.(y_raw); F = fill(mean(y), n)
        stumps = _GBStump[]
        for _ in 1:ne
            res = y .- F
            s = _gb_fit_stump(X, res)
            push!(stumps, s)
            F .+= 0.1 .* _gb_pred_stump(s, X)
        end
        pred = F
        ss_res = sum((y .- F).^2); ss_tot = sum((y .- mean(y)).^2)
        r2 = 1.0 - ss_res/ss_tot
        acc = r2
        metric_str = "R2: " * string(round(r2, digits=6))
    end

    fc = zeros(Int, p)
    for s in stumps; fc[s.feat] += 1; end
    imp = fc ./ max(1, sum(fc))

    if to == 1
        return String["=== Gradient Boosting (n=" * string(ne) * ") -- Metricas ===",
            metric_str, "N: " * string(n), "Variables: " * string(p),
            "Estimadores: " * string(ne), "Learning rate: 0.1"]
    elseif to == 2
        maxv = maximum(imp)
        r = String["=== Gradient Boosting (n=" * string(ne) * ") -- Importancia de Variables ==="]
        for i in sortperm(imp, rev=true)
            imp[i] > 0.001 || continue
            bar = repeat("#", Int(round(imp[i]/maxv * 40)))
            push!(r, "  Var" * string(i) * "     " * string(round(imp[i], digits=4)) * " " * bar)
        end
        return r
    elseif to == 3
        return is_classif ? pred : round.(pred, digits=4)
    elseif to == 4
        if is_classif
            cm, cls = _ml_confusion(y_raw, pred)
            r = String["=== Gradient Boosting (n=" * string(ne) * ") -- Matriz de Confusion ===",
                "Real\\Pred | " * join(string.(cls), " | ")]
            for i in 1:length(cls); push!(r, string(cls[i]) * " | " * join(string.(cm[i,:]), " | ")); end
            push!(r, ""); push!(r, metric_str)
            return r
        end
        return String["(Confusion no disponible para regresion)"]
    elseif to == 5
        importances_data = [(i, round(imp[i], digits=4)) for i in sortperm(imp, rev=true) if imp[i] > 0.001]
        importances_named = [("Var" * string(i), v) for (i,v) in importances_data]
        cm_data = nothing; cls_data = nothing
        if is_classif
            cm_data, cls_data = _ml_confusion(y_raw, pred)
        end
        metrics = [("Metrica", metric_str), ("N", n), ("Variables", p), ("Estimadores", ne)]
        params = [("Algoritmo", "Gradient Boosting"), ("Estimadores", string(ne)), ("LR", "0.1"), ("Plataforma", "Julia puro")]
        return _ml_html_report("Gradient Boosting", metrics, importances_named, cm_data, cls_data, params)
    end
    return String["TipoOutput no valido"]
end


# === RED NEURONAL =============================================================

"""
    RedNeuronal(X, Y, n_ocultas=50, TipoOutput=1)
Red neuronal 1 capa oculta (sigmoid). n_ocultas=neuronas. TipoOutput: 0=info 1=metricas 2=arquitectura 3=pred 4=confusion 5=html
"""
function RedNeuronal(SetDatosX, SetDatosY, n_ocultas=50, TipoOutput=1)
    X = Float64.(SetDatosX); y_raw = vec(SetDatosY); n, p = size(X)
    nh = Int(n_ocultas); to = Int(TipoOutput)

    if to == 0
        return String["=== Red Neuronal (n=" * string(nh) * ") -- Outputs Disponibles ===",
            "[0] Esta lista",
            "[1] Metricas del modelo (Accuracy)",
            "[2] Arquitectura de la red",
            "[3] Predicciones del modelo",
            "[4] Matriz de confusion",
            "[5] Reporte visual en Viewer"]
    end

    classes = sort(unique(y_raw))
    if length(classes) != 2
        return String["Error: Red Neuronal soporta 2 clases. Use RandomForest para multiclase."]
    end

    y = [v == classes[2] ? 1.0 : 0.0 for v in y_raw]

    # Normalizar
    mu = mean(X, dims=1); sigma = std(X, dims=1)
    sigma[sigma .== 0] .= 1.0
    Xn = (X .- mu) ./ sigma

    # Inicializar pesos
    rng = MersenneTwister(42)
    W1 = randn(rng, p, nh) * sqrt(2.0/p); b1 = zeros(nh)
    W2 = randn(rng, nh, 1) * sqrt(2.0/nh); b2 = zeros(1)
    sigmoid(z) = 1.0 ./ (1.0 .+ exp.(clamp.(-z, -500, 500)))

    # Entrenar
    for _ in 1:500
        Z1 = Xn * W1 .+ b1'; A1 = sigmoid(Z1)
        Z2 = A1 * W2 .+ b2'; A2 = sigmoid(Z2)
        dZ2 = vec(A2) .- y
        dW2 = A1' * reshape(dZ2,:,1)/n; db2 = [sum(dZ2)/n]
        dA1 = reshape(dZ2,:,1) * W2'; dZ1 = dA1 .* A1 .* (1.0 .- A1)
        dW1 = Xn' * dZ1/n; db1 = vec(sum(dZ1, dims=1)/n)
        W2 .-= 0.01 .* dW2; b2 .-= 0.01 .* db2
        W1 .-= 0.01 .* dW1; b1 .-= 0.01 .* db1
    end

    # Prediccion
    A1 = sigmoid(Xn * W1 .+ b1'); A2 = sigmoid(A1 * W2 .+ b2')
    pred = [a >= 0.5 ? classes[2] : classes[1] for a in vec(A2)]
    acc = _ml_accuracy(y_raw, pred)

    if to == 1
        return String["=== Red Neuronal (n=" * string(nh) * ") -- Metricas ===",
            "Accuracy: " * string(round(acc*100, digits=2)) * "%",
            "N: " * string(n), "Variables: " * string(p),
            "Neuronas ocultas: " * string(nh),
            "Clases: " * join(string.(classes), " vs ")]
    elseif to == 2
        total_pesos = p*nh + nh + nh*1 + 1
        return String["=== Red Neuronal -- Arquitectura ===",
            "Entrada: " * string(p) * " neuronas",
            "Oculta: " * string(nh) * " neuronas (sigmoid)",
            "Salida: 1 neurona (sigmoid)",
            "Pesos totales: " * string(total_pesos),
            "Epochs: 500 | LR: 0.01"]
    elseif to == 3
        return pred
    elseif to == 4
        cm, cls = _ml_confusion(y_raw, pred)
        r = String["=== Red Neuronal (n=" * string(nh) * ") -- Matriz de Confusion ===",
            "Real\\Pred | " * join(string.(cls), " | ")]
        for i in 1:length(cls); push!(r, string(cls[i]) * " | " * join(string.(cm[i,:]), " | ")); end
        push!(r, ""); push!(r, "Accuracy: " * string(round(acc*100, digits=2)) * "%")
        return r
    elseif to == 5
        cm, cls = _ml_confusion(y_raw, pred)
        metrics = [("Accuracy", round(acc, digits=4)), ("N", n), ("Variables", p), ("Neuronas", nh)]
        params = [("Algoritmo", "Red Neuronal (MLP)"), ("Neuronas", string(nh)), ("Epochs", "500"), ("Plataforma", "Julia puro")]
        return _ml_html_report("Red Neuronal", metrics, nothing, cm, cls, params)
    end
    return String["TipoOutput no valido"]
end
