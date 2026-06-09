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
  { L"RJ_View", L"UQ", L"NEVEN.v", L"Content or Path", L"1", L"NEVEN", L"", L"", L"Open HTML content in embedded WebView2 viewer", L"HTML content, file path, or URL", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerClose", L"UQ", L"NEVEN.v.close", L"ViewerID", L"1", L"NEVEN", L"", L"", L"Close a viewer window", L"Viewer identifier (viewer-N)", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerList", L"Q", L"NEVEN.v.list", L"", L"1", L"NEVEN", L"", L"", L"List active viewer windows", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerSend", L"UQQ", L"NEVEN.v.send", L"ViewerID, JSONData", L"1", L"NEVEN", L"", L"", L"Send JSON data to a viewer via PostMessage", L"Viewer identifier (viewer-N)", L"JSON string to send", L"", L"", L"", L"", L"" },

  // Pluto.jl Advanced Mode functions
  { L"RJ_PlutoStart", L"Q", L"NEVEN.pluto.start", L"", L"1", L"NEVEN", L"", L"", L"Start Pluto.jl notebook server", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStop", L"Q", L"NEVEN.pluto.stop", L"", L"1", L"NEVEN", L"", L"", L"Stop Pluto.jl notebook server", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStatus", L"Q", L"NEVEN.pluto.status", L"", L"1", L"NEVEN", L"", L"", L"Get Pluto.jl server status", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoData", L"UQQ", L"NEVEN.pluto.data", L"DataRange, DatasetName", L"1", L"NEVEN", L"", L"", L"Send Excel range to Julia/Pluto as named dataset", L"Range with data", L"Dataset name (default: default)", L"", L"", L"", L"", L"" },

  // Notebook functions
  { L"RJ_NotebookOpen", L"UQ", L"NEVEN.notebook.open", L"NotebookName", L"1", L"NEVEN", L"", L"", L"Open a Pluto notebook in the viewer", L"Notebook name from library", L"", L"", L"", L"", L"", L"" },
  { L"RJ_NotebookList", L"Q", L"NEVEN.notebook.list", L"", L"1", L"NEVEN", L"", L"", L"List available Pluto notebooks", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_NotebookExport", L"UQ", L"NEVEN.notebook.export", L"Title", L"1", L"NEVEN", L"", L"", L"Export last analysis as Pluto notebook", L"Notebook title", L"", L"", L"", L"", L"", L"" },

  // Presentation functions
  { L"RJ_PresentationNew", L"UQ", L"NEVEN.presentation.new", L"Title", L"1", L"NEVEN", L"", L"", L"Create a new reveal.js presentation", L"Presentation title", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PresentationAddSlide", L"UQQQ", L"NEVEN.presentation.add.slide", L"PresentationID, Content, SlideType", L"1", L"NEVEN", L"", L"", L"Add a slide to a presentation", L"Presentation ID", L"Content or viewer ID", L"text, viewer, or html", L"", L"", L"", L"" },
  { L"RJ_PresentationBuild", L"UQQ", L"NEVEN.presentation.build", L"PresentationID, OutputPath", L"1", L"NEVEN", L"", L"", L"Build presentation as HTML file", L"Presentation ID", L"Output file path (optional)", L"", L"", L"", L"", L"" },

  // Information functions
  { L"RJ_About", L"Q", L"NEVEN.about", L"", L"1", L"NEVEN", L"", L"", L"Show NEVEN version and project information", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_Help", L"Q", L"NEVEN.help", L"", L"1", L"NEVEN", L"", L"", L"List all available NEVEN Excel functions", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_Editor", L"Q", L"NEVEN.editor", L"", L"1", L"NEVEN", L"", L"", L"Open the Impress.js presentation editor in WebView2", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_LangToggle", L"Q", L"NEVEN.lang.toggle", L"", L"2", L"NEVEN", L"", L"", L"Toggle UI language between Spanish and English", L"", L"", L"", L"", L"", L"", L"" },

  // Menu command functions (type 2 = command)
  { L"RJ_View_Dialog", L"Q", L"NEVEN.v.dialog", L"", L"2", L"NEVEN", L"", L"", L"Open file dialog to select HTML for viewer", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_NotebookOpen_Dialog", L"Q", L"NEVEN.notebook.dialog", L"", L"2", L"NEVEN", L"", L"", L"Show notebook library dialog", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_About_Dialog", L"Q", L"NEVEN.about.dialog", L"", L"2", L"NEVEN", L"", L"", L"Show About NEVEN dialog", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ViewerCloseAll", L"Q", L"NEVEN.v.closeall", L"", L"2", L"NEVEN", L"", L"", L"Close all viewer windows", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStartCmd", L"Q", L"NEVEN.cmd.pluto.start", L"", L"2", L"NEVEN", L"", L"", L"Start Pluto server (command)", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_PlutoStopCmd", L"Q", L"NEVEN.cmd.pluto.stop", L"", L"2", L"NEVEN", L"", L"", L"Stop Pluto server (command)", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_EditorCmd", L"Q", L"NEVEN.cmd.editor", L"", L"2", L"NEVEN", L"", L"", L"Open presentation editor (command)", L"", L"", L"", L"", L"", L"", L"" },

  { L"RJ_Q", L"UQ", L"NEVEN.q", L"QMD File Path", L"1", L"NEVEN", L"", L"", L"Render a Quarto document and display in WebView2", L"Path to .qmd file", L"", L"", L"", L"", L"", L"" },

  // Status/diagnostic function
  { L"NEVEN_Status", L"Q", L"NEVEN.status", L"", L"1", L"NEVEN", L"", L"", L"Show language engine connection status", L"", L"", L"", L"", L"", L"", L"" },

  // Julia on-demand activation
  { L"NEVEN_IniciarJulia", L"Q", L"NEVEN.iniciar.J", L"", L"1", L"NEVEN", L"", L"", L"Activar Julia bajo demanda (carga funciones J.*)", L"", L"", L"", L"", L"", L"", L"" },

	{ 0 }
};

static LPWSTR callTemplates[][16] = {
  { L"RJ_CallLanguage_", L"UQQQQQQQQQQQQQQQQQ", L"NEVEN.Call", L"Function, Argument", L"1", L"NEVEN", L"", L"99", L"", L"", L"", L"", L"", L"", L"", L"" },
  { L"RJ_ExecLanguage_", L"UQ", L"NEVEN.Exec", L"Code", L"1", L"NEVEN", L"", L"97", L"Exec Language Code", L"", L"", L"", L"", L"", L"", L"" }
};

/** exported function */
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_SetPointers(ULONG_PTR excel_pointer, ULONG_PTR ribbon_pointer);

/** exported function */
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Console();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_RConsole();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_JuliaConsole();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_UpdateFunctions();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_ContextSwitch(LPXLOPER12 argument);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_ButtonCallback(LPXLOPER12 button_id, LPXLOPER12 language);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Version();

// WebView2 Viewer exports
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_View(LPXLOPER12 content_or_path);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_ViewerClose(LPXLOPER12 viewer_id);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_ViewerList();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_ViewerSend(LPXLOPER12 viewer_id, LPXLOPER12 json_data);

// Pluto.jl Advanced Mode exports
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PlutoStart();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PlutoStop();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PlutoStatus();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PlutoData(LPXLOPER12 data_range, LPXLOPER12 dataset_name);

// Notebook exports
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_NotebookOpen(LPXLOPER12 notebook_name);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_NotebookList();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_NotebookExport(LPXLOPER12 title);

// Presentation exports
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PresentationNew(LPXLOPER12 title);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PresentationAddSlide(LPXLOPER12 pres_id, LPXLOPER12 content, LPXLOPER12 slide_type);
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PresentationBuild(LPXLOPER12 pres_id, LPXLOPER12 output_path);

// Information exports
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_About();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Help();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Editor();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_LangToggle();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PlutoStartCmd();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_PlutoStopCmd();
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_EditorCmd();

/** Quarto render function */
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Q(
    LPXLOPER12 file_path,
    LPXLOPER12 format,
    LPXLOPER12 data_range);


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

