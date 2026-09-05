/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * NEVEN is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NEVEN.  If not, see <http://www.gnu.org/licenses/>.
 */
#pragma once

#include <windows.h>
#include <cstdint>
#include "XLCALL.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_FUNCTIONS 2048
#define MAX_ARGS 16

// Dynamic Exec and Call functions are generated at runtime via BEXEC/BCALL macros.
// Excel refers to functions by name (not by ID), so constant IDs are not required.

static LPWSTR funcTemplates[][16] = {

  // these are constructed at runtime
  
  { L"RJ_Console", L"Q", L"NEVEN.Console", L"", L"1", L"NEVEN", L"", L"", L"Open interactive REPL console", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_RConsole", L"Q", L"NEVEN.Console.R", L"", L"1", L"NEVEN", L"", L"", L"Open REPL console with R focus", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_JuliaConsole", L"Q", L"NEVEN.Console.Julia", L"", L"1", L"NEVEN", L"", L"", L"Open REPL console with Julia focus", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ContextSwitch", L"QQ", L"RJ_ContextSwitch", L"", L"2", L"NEVEN", L"", L"", L"", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_UpdateFunctions", L"Q", L"RJ_UpdateFunctions", L"", L"2", L"NEVEN", L"", L"", L"", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ButtonCallback", L"QQQ", L"RJ_ButtonCallback", L"", L"2", L"NEVEN", L"", L"", L"", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_Version", L"Q", L"RJ_Version", L"", L"1", L"NEVEN", L"", L"", L"", L"", L"", L"", L"", L"", L"", L"" },

  // WebView2 Viewer functions
  { L"RJ_View", L"UQ", L"NEVEN.View", L"Content or Path", L"1", L"NEVEN", L"", L"", L"Open HTML content in embedded WebView2 viewer", L"HTML content, file path, or URL", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerClose", L"UQ", L"NEVEN.View.Close", L"ViewerID", L"1", L"NEVEN", L"", L"", L"Close a viewer window", L"Viewer identifier (viewer-N)", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerList", L"Q", L"NEVEN.View.List", L"", L"1", L"NEVEN", L"", L"", L"List active viewer windows", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerSend", L"UQQ", L"NEVEN.View.Send", L"ViewerID, JSONData", L"1", L"NEVEN", L"", L"", L"Send JSON data to a viewer via PostMessage", L"Viewer identifier (viewer-N)", L"JSON string to send", L"", L"", L"", L"", L"" },

  // Pluto.jl Advanced Mode functions
  { L"RJ_PlutoStart", L"Q", L"NEVEN.Pluto.Start", L"", L"1", L"NEVEN", L"", L"", L"Start Pluto.jl notebook server", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStop", L"Q", L"NEVEN.Pluto.Stop", L"", L"1", L"NEVEN", L"", L"", L"Stop Pluto.jl notebook server", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStatus", L"Q", L"NEVEN.Pluto.Status", L"", L"1", L"NEVEN", L"", L"", L"Get Pluto.jl server status", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoData", L"UQQ", L"NEVEN.Pluto.Data", L"DataRange, DatasetName", L"1", L"NEVEN", L"", L"", L"Send Excel range to Julia/Pluto as named dataset", L"Range with data", L"Dataset name (default: default)", L"", L"", L"", L"", L"" },

  // Notebook functions
  { L"RJ_NotebookOpen", L"UQ", L"NEVEN.Notebook.Open", L"NotebookName", L"1", L"NEVEN", L"", L"", L"Open a Pluto notebook in the viewer", L"Notebook name from library", L"", L"", L"", L"", L"", L"" },
  { L"RJ_NotebookList", L"Q", L"NEVEN.Notebook.List", L"", L"1", L"NEVEN", L"", L"", L"List available Pluto notebooks", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_NotebookExport", L"UQ", L"NEVEN.Notebook.Export", L"Title", L"1", L"NEVEN", L"", L"", L"Export last analysis as Pluto notebook", L"Notebook title", L"", L"", L"", L"", L"", L"" },

  // Presentation / Slide functions
  { L"RJ_PresentationNew", L"UQ", L"NEVEN.Slide.New", L"Title", L"1", L"NEVEN", L"", L"", L"Create a new reveal.js presentation", L"Presentation title", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PresentationAddSlide", L"UQQQ", L"NEVEN.Slide.Add", L"PresentationID, Content, SlideType", L"1", L"NEVEN", L"", L"", L"Add a slide to a presentation", L"Presentation ID", L"Content or viewer ID", L"text, viewer, or html", L"", L"", L"", L"" },
  { L"RJ_PresentationBuild", L"UQQ", L"NEVEN.Slide.Build", L"PresentationID, OutputPath", L"1", L"NEVEN", L"", L"", L"Build presentation as HTML file", L"Presentation ID", L"Output file path (optional)", L"", L"", L"", L"", L"" },

  // Information functions
  { L"RJ_About", L"Q", L"NEVEN.About", L"", L"1", L"NEVEN", L"", L"", L"Show NEVEN version and project information", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_Help", L"Q", L"NEVEN.Help", L"", L"1", L"NEVEN", L"", L"", L"List all available NEVEN Excel functions", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_Editor", L"Q", L"NEVEN.Editor", L"", L"1", L"NEVEN", L"", L"", L"Open the presentation editor in WebView2", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_LangToggle", L"Q", L"NEVEN.Lang.Toggle", L"", L"2", L"NEVEN", L"", L"", L"Toggle UI language between Spanish and English", L"", L"", L"", L"", L"", L"", L"" },

  // Command functions (type 2 = command, no aparecen en IntelliSense)
  { L"RJ_View_Dialog", L"Q", L"NEVEN.View.Dialog", L"", L"2", L"NEVEN", L"", L"", L"Open file dialog to select HTML for viewer", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_NotebookOpen_Dialog", L"Q", L"NEVEN.Notebook.Dialog", L"", L"2", L"NEVEN", L"", L"", L"Show notebook library dialog", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_About_Dialog", L"Q", L"NEVEN.About.Dialog", L"", L"2", L"NEVEN", L"", L"", L"Show About NEVEN dialog", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerCloseAll", L"Q", L"NEVEN.View.CloseAll", L"", L"2", L"NEVEN", L"", L"", L"Close all viewer windows", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStartCmd", L"Q", L"NEVEN.Pluto.Start", L"", L"2", L"NEVEN", L"", L"", L"Start Pluto server (command)", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStopCmd", L"Q", L"NEVEN.Pluto.Stop", L"", L"2", L"NEVEN", L"", L"", L"Stop Pluto server (command)", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_EditorCmd", L"Q", L"NEVEN.Editor", L"", L"2", L"NEVEN", L"", L"", L"Open presentation editor (command)", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_JuliaSysimageCmd", L"Q", L"NEVEN.Julia.Sysimage", L"", L"2", L"NEVEN", L"", L"", L"Compilar sysimage Julia (elimina retraso JIT)", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_AgenteIA", L"Q", L"NEVEN.Agente.IA", L"", L"2", L"NEVEN", L"", L"", L"Abrir NEVEN Studio AI en ventana WebView2", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_IA_Contexto", L"UQQ", L"NEVEN.IA.Contexto", L"DatosRango,ResultadosRango", L"1", L"NEVEN", L"", L"", L"Enviar datos y resultados de Excel al Agente IA", L"Rango con los datos (incluir headers)", L"Rango con los resultados del modelo (opcional)", L"", L"", L"", L"", L"" },

  { L"RJ_Q", L"UQ", L"NEVEN.Quarto", L"QMD File Path", L"1", L"NEVEN", L"", L"", L"Render a Quarto document and display in WebView2", L"Path to .qmd file", L"", L"", L"", L"", L"", L"" },

  // Status/diagnostic function
  { L"NEVEN_Status", L"Q", L"NEVEN.Status", L"", L"1", L"NEVEN", L"", L"", L"Show language engine connection status", L"", L"", L"", L"", L"", L"", L"" },

  // Julia on-demand activation
  { L"NEVEN_IniciarJulia", L"Q", L"NEVEN.Julia.Start", L"", L"1", L"NEVEN", L"", L"", L"Activar Julia bajo demanda (carga funciones J.*)", L"", L"", L"", L"", L"", L"", L"" },





  // NevenX -- Dispatcher generico de procesos (firma identica a NEVEN.Call: 1+16 args)
  { L"NevenX_R", L"UQQQQQQQQQQQQQQQQQ", L"NevenX.R", L"Proceso,A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,A11,A12,A13,A14,A15", L"1", L"NEVEN", L"", L"", L"Ejecuta un proceso R del catalogo NEVEN", L"Nombre del proceso (ej: MR_Lineal, MR_2SLS)", L"DatosY", L"DatosX", L"Datos3 (ej: instrumentos)", L"Datos4 (opcional)", L"Datos5 (opcional)", L"" },
  { L"NevenX_J", L"UQQQQQQQQQQQQQQQQQ", L"NevenX.J", L"Proceso,A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,A11,A12,A13,A14,A15", L"1", L"NEVEN", L"", L"", L"Ejecuta un proceso Julia del catalogo NEVEN", L"Nombre del proceso (ej: J_AD_Descriptiva)", L"DatosY", L"DatosX", L"Datos3 (opcional)", L"Datos4 (opcional)", L"Datos5 (opcional)", L"" },
  { L"NevenX_P", L"UQQQQQQQQQQQQQQQQQ", L"NevenX.P", L"Proceso,A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,A11,A12,A13,A14,A15", L"1", L"NEVEN", L"", L"", L"Ejecuta un proceso Python del catalogo NEVEN", L"Nombre del proceso (ej: TM_TextAnalysis)", L"DatosY", L"DatosX", L"Datos3 (opcional)", L"Datos4 (opcional)", L"Datos5 (opcional)", L"" },
	{ 0 }
};

/** Quarto render function */
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Q(
    LPXLOPER12 file_path,
    LPXLOPER12 format,
    LPXLOPER12 data_range);
// NevenX -- Dispatcher generico de procesos (firma identica a NEVEN.Call: 1+16 Q)
extern "C" void NevenX_InitGlobals();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI NevenX_R(LPXLOPER12 p,
  LPXLOPER12 a0=0,LPXLOPER12 a1=0,LPXLOPER12 a2=0,LPXLOPER12 a3=0,
  LPXLOPER12 a4=0,LPXLOPER12 a5=0,LPXLOPER12 a6=0,LPXLOPER12 a7=0,
  LPXLOPER12 a8=0,LPXLOPER12 a9=0,LPXLOPER12 a10=0,LPXLOPER12 a11=0,
  LPXLOPER12 a12=0,LPXLOPER12 a13=0,LPXLOPER12 a14=0,LPXLOPER12 a15=0);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI NevenX_J(LPXLOPER12 p,
  LPXLOPER12 a0=0,LPXLOPER12 a1=0,LPXLOPER12 a2=0,LPXLOPER12 a3=0,
  LPXLOPER12 a4=0,LPXLOPER12 a5=0,LPXLOPER12 a6=0,LPXLOPER12 a7=0,
  LPXLOPER12 a8=0,LPXLOPER12 a9=0,LPXLOPER12 a10=0,LPXLOPER12 a11=0,
  LPXLOPER12 a12=0,LPXLOPER12 a13=0,LPXLOPER12 a14=0,LPXLOPER12 a15=0);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI NevenX_P(LPXLOPER12 p,
  LPXLOPER12 a0=0,LPXLOPER12 a1=0,LPXLOPER12 a2=0,LPXLOPER12 a3=0,
  LPXLOPER12 a4=0,LPXLOPER12 a5=0,LPXLOPER12 a6=0,LPXLOPER12 a7=0,
  LPXLOPER12 a8=0,LPXLOPER12 a9=0,LPXLOPER12 a10=0,LPXLOPER12 a11=0,
  LPXLOPER12 a12=0,LPXLOPER12 a13=0,LPXLOPER12 a14=0,LPXLOPER12 a15=0);


#define BCALL(num) \
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_CallLanguage_ ## num ( \
  LPXLOPER12 func = 0 \
  , LPXLOPER12 input_0 = 0 \
	, LPXLOPER12 input_1 = 0 \
	, LPXLOPER12 input_2 = 0 \
	, LPXLOPER12 input_3 = 0 \
	, LPXLOPER12 input_4 = 0 \
	, LPXLOPER12 input_5 = 0 \
	, LPXLOPER12 input_6 = 0 \
	, LPXLOPER12 input_7 = 0 \
	, LPXLOPER12 input_8 = 0 \
	, LPXLOPER12 input_9 = 0 \
	, LPXLOPER12 input_10 = 0 \
	, LPXLOPER12 input_11 = 0 \
	, LPXLOPER12 input_12 = 0 \
	, LPXLOPER12 input_13 = 0 \
	, LPXLOPER12 input_14 = 0 \
	, LPXLOPER12 input_15 = 0 \
){ return RJ_Call_Generic( num - 1000, func, input_0, input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15 ); }

__inline LPXLOPER12 RJ_Call_Generic(
  uint32_t language_key,
  LPXLOPER12 func,
  LPXLOPER12 input_0 = 0
  , LPXLOPER12 input_1 = 0
  , LPXLOPER12 input_2 = 0
  , LPXLOPER12 input_3 = 0
  , LPXLOPER12 input_4 = 0
  , LPXLOPER12 input_5 = 0
  , LPXLOPER12 input_6 = 0
  , LPXLOPER12 input_7 = 0
  , LPXLOPER12 input_8 = 0
  , LPXLOPER12 input_9 = 0
  , LPXLOPER12 input_10 = 0
  , LPXLOPER12 input_11 = 0
  , LPXLOPER12 input_12 = 0
  , LPXLOPER12 input_13 = 0
  , LPXLOPER12 input_14 = 0
  , LPXLOPER12 input_15 = 0
);

__inline LPXLOPER12 RJ_Exec_Generic(uint32_t language_index, LPXLOPER12 code);

#define BEXEC(num) \
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_ExecLanguage_ ## num ( \
  LPXLOPER12 code = 0 \
){ return RJ_Exec_Generic( num - 1000, code ); }

/**
 * generic call dispatcher function, exported from dll
 */
__inline LPXLOPER12 RJ_FunctionCall(
  int findex,
  LPXLOPER12 input_0 = 0
  , LPXLOPER12 input_1 = 0
  , LPXLOPER12 input_2 = 0
  , LPXLOPER12 input_3 = 0
  , LPXLOPER12 input_4 = 0
  , LPXLOPER12 input_5 = 0
  , LPXLOPER12 input_6 = 0
  , LPXLOPER12 input_7 = 0
  , LPXLOPER12 input_8 = 0
  , LPXLOPER12 input_9 = 0
  , LPXLOPER12 input_10 = 0
  , LPXLOPER12 input_11 = 0
  , LPXLOPER12 input_12 = 0
  , LPXLOPER12 input_13 = 0
  , LPXLOPER12 input_14 = 0
  , LPXLOPER12 input_15 = 0
);

#define BFC(num) \
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_FunctionCall ## num ( \
	LPXLOPER12 input_0 = 0 \
	, LPXLOPER12 input_1 = 0 \
	, LPXLOPER12 input_2 = 0 \
	, LPXLOPER12 input_3 = 0 \
	, LPXLOPER12 input_4 = 0 \
	, LPXLOPER12 input_5 = 0 \
	, LPXLOPER12 input_6 = 0 \
	, LPXLOPER12 input_7 = 0 \
	, LPXLOPER12 input_8 = 0 \
	, LPXLOPER12 input_9 = 0 \
	, LPXLOPER12 input_10 = 0 \
	, LPXLOPER12 input_11 = 0 \
	, LPXLOPER12 input_12 = 0 \
	, LPXLOPER12 input_13 = 0 \
	, LPXLOPER12 input_14 = 0 \
	, LPXLOPER12 input_15 = 0 \
	){ return RJ_FunctionCall( num-1000, input_0, input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, input_11, input_12, input_13, input_14, input_15 ); }

#ifdef __cplusplus
}
#endif

