; ============================================================
; NEVEN Installer Script for NSIS
; Excel Add-in with R, Julia, and Python integration
; ============================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ============================================================
; General Configuration
; ============================================================

Name "NEVEN"
OutFile "NEVEN-Setup.exe"
InstallDir "C:\NEVEN"
InstallDirRegKey HKCU "Software\NEVEN" "InstallDir"
RequestExecutionLevel admin
Unicode True

; Version Information
!define VERSION "3.2.0"
!define PUBLISHER "Minor Bonilla Gomez"
!define WEBSITE "https://github.com/NEVEN-Project"

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "NEVEN"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "FileDescription" "NEVEN Excel Add-in Installer"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright (C) 2026 ${PUBLISHER}"

; ============================================================
; Modern UI Configuration
; ============================================================

!define MUI_ICON "Dist\NEVEN_studio.ico"
!define MUI_UNICON "Dist\NEVEN_studio.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "Dist\header.bmp"
!define MUI_HEADERIMAGE_RIGHT
!define MUI_WELCOMEFINISHPAGE_BITMAP "Dist\wizard.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "Dist\wizard.bmp"
!define MUI_ABORTWARNING

; Welcome Page
!define MUI_WELCOMEPAGE_TITLE "Bienvenido al instalador de NEVEN"
!define MUI_WELCOMEPAGE_TEXT "Este asistente instalara NEVEN ${VERSION} en su computadora.$\r$\n$\r$\nNEVEN es un add-in para Microsoft Excel que integra R, Julia y Python como motores de scripting embebidos.$\r$\n$\r$\nRequisitos:$\r$\n  - Windows 10/11 (64-bit)$\r$\n  - Microsoft Excel 2016 o superior$\r$\n  - R 4.4+ (opcional)$\r$\n  - Julia 1.12+ (opcional)$\r$\n  - Python 3.10+ (opcional)$\r$\n$\r$\nHaga clic en Siguiente para continuar."

; Finish Page
!define MUI_FINISHPAGE_TITLE "Instalacion completada"
!define MUI_FINISHPAGE_TEXT "NEVEN ${VERSION} se ha instalado correctamente.$\r$\n$\r$\nPara comenzar:$\r$\n1. Abra Microsoft Excel$\r$\n2. La pestana NEVEN aparecera en el Ribbon$\r$\n3. Haga clic en 'Activar NEVEN' para iniciar los motores$\r$\n$\r$\nPara usar NEVEN Studio (TaskPane integrado):$\r$\n1. Vaya a Insertar > Complementos > Mis complementos$\r$\n2. Seleccione NEVEN Studio"
!define MUI_FINISHPAGE_RUN "$INSTDIR\NEVEN Studio.vbs"
!define MUI_FINISHPAGE_RUN_TEXT "Iniciar servidor NEVEN Studio"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\docs\README.md"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Ver documentacion"

; ============================================================
; Pages
; ============================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.rtf"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ============================================================
; Language
; ============================================================

!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "English"

; ============================================================
; Installer Sections
; ============================================================

Section "NEVEN Core" SecCore
    SectionIn RO  ; Required section
    
    SetOutPath "$INSTDIR"
    
    ; Core binaries
    File "Dist\NEVEN64.xll"
    File "Dist\NEVENRibbon.dll"
    File "Dist\ControlR.exe"
    File "Dist\ControlJulia.exe"
    File "Dist\ControlPython.exe"
    
    ; Configuration files
    File "Dist\neven-config.json"
    File "Dist\neven-languages.json"
    File "Dist\packages-manifest.json"
    File "Dist\NEVEN_studio.ico"
    File "Dist\NEVEN Studio.vbs"
    
    ; Directories
    SetOutPath "$INSTDIR\functions"
    File /r "Dist\functions\*.*"
    
    SetOutPath "$INSTDIR\startup"
    File /r "Dist\startup\*.*"
    
    SetOutPath "$INSTDIR\TaskPane"
    File /r "Dist\TaskPane\*.*"
    
    SetOutPath "$INSTDIR\docs"
    File /r "Dist\docs\*.*"
    
    SetOutPath "$INSTDIR\examples"
    File /r "Dist\examples\*.*"
    
    SetOutPath "$INSTDIR\ontology"
    File /r "Dist\ontology\*.*"
    
    SetOutPath "$INSTDIR\prompts"
    File /r "Dist\prompts\*.*"
    
    SetOutPath "$INSTDIR\libreria"
    File /r "Dist\libreria\*.*"
    
    ; Create additional directories
    CreateDirectory "$INSTDIR\graphics"
    CreateDirectory "$INSTDIR\notebooks"
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\temp"
    CreateDirectory "$INSTDIR\catalog"
    
    ; Copy manifest to catalog
    SetOutPath "$INSTDIR\catalog"
    CopyFiles "$INSTDIR\TaskPane\manifest.xml" "$INSTDIR\catalog\manifest.xml"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall-NEVEN.exe"
    
    ; Registry entries
    WriteRegStr HKCU "Software\NEVEN" "InstallDir" "$INSTDIR"
    WriteRegStr HKCU "Software\NEVEN" "Version" "${VERSION}"
    
    ; Add/Remove Programs entry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                     "DisplayName" "NEVEN ${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                     "UninstallString" "$\"$INSTDIR\Uninstall-NEVEN.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                     "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                     "DisplayIcon" "$INSTDIR\NEVEN_studio.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                     "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                     "DisplayVersion" "${VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                      "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                      "NoRepair" 1
    
    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN" \
                      "EstimatedSize" "$0"

SectionEnd

Section "Registro COM Ribbon" SecRibbon
    SectionIn RO
    
    ; Register NEVENRibbon.dll
    ExecWait 'regsvr32 /s "$INSTDIR\NEVENRibbon.dll"'
    
    ; Create Ribbon registry key
    WriteRegStr HKCU "Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect" \
                     "FriendlyName" "NEVEN"
    WriteRegStr HKCU "Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect" \
                     "Description" "NEVEN Ribbon Menu"
    WriteRegDWORD HKCU "Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect" \
                      "LoadBehavior" 3

SectionEnd

Section "Registro Office Add-in" SecOfficeAddin
    SectionIn RO
    
    ; Register TaskPane manifest in Excel Trusted Catalogs
    ; Use localhost admin share path (works without creating SMB share)
    WriteRegStr HKCU "Software\Microsoft\Office\16.0\Wef\TrustedCatalogs\{NEVEN-STUDIO-CATALOG}" \
                     "Url" "\\localhost\C$$\NEVEN\catalog"
    WriteRegDWORD HKCU "Software\Microsoft\Office\16.0\Wef\TrustedCatalogs\{NEVEN-STUDIO-CATALOG}" \
                      "Flags" 1

SectionEnd

Section "Excel Trusted Location" SecTrustedLocation
    SectionIn RO
    
    ; Add NEVEN as Excel Trusted Location
    WriteRegStr HKCU "Software\Microsoft\Office\16.0\Excel\Security\Trusted Locations\NEVEN" \
                     "Path" "$INSTDIR\"
    WriteRegDWORD HKCU "Software\Microsoft\Office\16.0\Excel\Security\Trusted Locations\NEVEN" \
                      "AllowSubFolders" 1

SectionEnd

Section "Accesos directos" SecShortcuts
    
    ; Start Menu
    CreateDirectory "$SMPROGRAMS\NEVEN"
    CreateShortcut "$SMPROGRAMS\NEVEN\NEVEN Studio.lnk" "$INSTDIR\NEVEN Studio.vbs" \
                   "" "$INSTDIR\NEVEN_studio.ico"
    CreateShortcut "$SMPROGRAMS\NEVEN\Documentacion.lnk" "$INSTDIR\docs\README.md"
    CreateShortcut "$SMPROGRAMS\NEVEN\Desinstalar NEVEN.lnk" "$INSTDIR\Uninstall-NEVEN.exe"
    
    ; Desktop (optional)
    CreateShortcut "$DESKTOP\NEVEN Studio.lnk" "$INSTDIR\NEVEN Studio.vbs" \
                   "" "$INSTDIR\NEVEN_studio.ico"

SectionEnd

; ============================================================
; Uninstaller Section
; ============================================================

Section "Uninstall"
    
    ; Close Excel if running
    ExecWait 'taskkill /f /im excel.exe' $0
    
    ; Unregister COM
    ExecWait 'regsvr32 /u /s "$INSTDIR\NEVENRibbon.dll"'
    
    ; Remove XLL from Excel (XLSTART)
    Delete "$APPDATA\Microsoft\Excel\XLSTART\NEVEN64.xll"
    
    ; Remove registry entries
    DeleteRegKey HKCU "Software\NEVEN"
    DeleteRegKey HKCU "Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect"
    DeleteRegKey HKCU "Software\Microsoft\Office\16.0\Wef\TrustedCatalogs\{NEVEN-STUDIO-CATALOG}"
    DeleteRegKey HKCU "Software\Microsoft\Office\16.0\Excel\Security\Trusted Locations\NEVEN"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEVEN"
    
    ; Remove shortcuts
    Delete "$DESKTOP\NEVEN Studio.lnk"
    RMDir /r "$SMPROGRAMS\NEVEN"
    
    ; Remove files (careful - preserve user data)
    Delete "$INSTDIR\NEVEN64.xll"
    Delete "$INSTDIR\NEVENRibbon.dll"
    Delete "$INSTDIR\ControlR.exe"
    Delete "$INSTDIR\ControlJulia.exe"
    Delete "$INSTDIR\ControlPython.exe"
    Delete "$INSTDIR\neven-config.json"
    Delete "$INSTDIR\neven-languages.json"
    Delete "$INSTDIR\packages-manifest.json"
    Delete "$INSTDIR\NEVEN_studio.ico"
    Delete "$INSTDIR\NEVEN Studio.vbs"
    Delete "$INSTDIR\Uninstall-NEVEN.exe"
    
    ; Remove directories (only if empty or system-created)
    RMDir /r "$INSTDIR\startup"
    RMDir /r "$INSTDIR\TaskPane"
    RMDir /r "$INSTDIR\docs"
    RMDir /r "$INSTDIR\examples"
    RMDir /r "$INSTDIR\ontology"
    RMDir /r "$INSTDIR\prompts"
    RMDir /r "$INSTDIR\libreria"
    RMDir /r "$INSTDIR\catalog"
    RMDir /r "$INSTDIR\temp"
    RMDir /r "$INSTDIR\logs"
    
    ; Keep user directories (functions, graphics, notebooks) - let user delete manually
    
    ; Try to remove install dir (will fail if user files exist - that's OK)
    RMDir "$INSTDIR"
    
SectionEnd

; Section descriptions removed - requires Components page

; ============================================================
; Callback Functions
; ============================================================

Function .onInit
    ; Check if already installed
    ReadRegStr $0 HKCU "Software\NEVEN" "InstallDir"
    StrCmp $0 "" continue
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "NEVEN ya esta instalado en $0.$\r$\n$\r$\nDesea reinstalar?" \
            IDYES continue
        Abort
    continue:
FunctionEnd

Function un.onInit
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Esta seguro que desea desinstalar NEVEN?$\r$\n$\r$\nNota: Sus archivos personales en C:\NEVEN\functions y C:\NEVEN\notebooks se conservaran." \
        IDYES +2
    Abort
FunctionEnd
