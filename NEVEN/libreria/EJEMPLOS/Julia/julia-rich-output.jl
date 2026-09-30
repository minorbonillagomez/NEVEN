
"""
    JuliaReport(n::Int)

Ejemplo de función Julia con docstrings que genera datos en Excel 
y muestra un reporte HTML enriquecido en la terminal.
"""
function JuliaReport(n::Int)
    # 1. Uso de la API COM refinada (Sintaxis de punto)
    # RJ2XCL crea automáticamente el objeto global 'EXCEL'
    app = EXCEL.Application
    wb = app.ActiveWorkbook
    
    if isnothing(wb)
        wb = app.Workbooks.Add()
    end
    
    # Acceso a propiedades con sintaxis de Julia estándar
    sheet = wb.ActiveSheet
    sheet.Name = "Julia Statistics"
    
    # Generar datos aleatorios
    data = rand(n, 3)
    
    # Cálculo de estadísticas básicas
    avg = sum(data, dims=1) ./ n
    
    # Insertar datos en Excel
    range = sheet.Range("A2:C$(n+1)")
    range.Value = data
    
    # Formatear el reporte en HTML para la terminal de Excel
    report_html = """
    <div style="font-family: 'Segoe UI', sans-serif; padding: 15px; background: #f0f7ff; border-radius: 8px; border: 1px solid #0078d4;">
        <h3 style="color: #0078d4; margin-top: 0;">📊 Julia Data Report</h3>
        <p>Se procesaron <b>$n</b> registros exitosamente.</p>
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <tr style="background: #0078d4; color: white;">
                <th style="padding: 5px; text-align: left;">Dimensión</th>
                <th style="padding: 5px; text-align: right;">Promedio</th>
            </tr>
            <tr>
                <td style="padding: 5px; border-bottom: 1px solid #ddd;">Columna 1</td>
                <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: right;">$(round(avg[1], digits=4))</td>
            </tr>
            <tr>
                <td style="padding: 5px; border-bottom: 1px solid #ddd;">Columna 2</td>
                <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: right;">$(round(avg[2], digits=4))</td>
            </tr>
            <tr>
                <td style="padding: 5px; border-bottom: 1px solid #ddd;">Columna 3</td>
                <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: right;">$(round(avg[3], digits=4))</td>
            </tr>
        </table>
        <p style="font-size: 0.9em; color: #666; margin-bottom: 0;"><i>Generado por RJ2XCL Bridge</i></p>
    </div>
    """
    
    # 2. Sistema de Display MIME
    # Esto llama automáticamente a RJ2XCL.render-mime en C++
    display("text/html", report_html)
    
    return "OK: Datos enviados a Excel y reporte mostrado."
end

println("Ejemplo JuliaReport cargado. Intenta ejecutar: JuliaReport(10)")