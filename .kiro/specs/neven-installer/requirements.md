# Requirements Document — NEVEN Installer (One-Click Installation)

## Introduction

NEVEN is a C++17 Excel XLL add-in that integrates R 4.4.1, Julia 1.12.6, and Python 3.13 as scripting engines. Currently, installation requires manually copying files, installing runtimes, registering COM DLLs, and creating junction links — a process that causes most prospective users to abandon setup. This feature delivers a one-click installer (PowerShell script) that automates the entire deployment so that a user can go from download to `=NEVEN.R("1+1")` returning 2 within five minutes. An accompanying uninstaller provides clean removal of all installed components.

## Glossary

- **Installer**: The PowerShell script (`Install-NEVEN.ps1`) that automates the full NEVEN deployment process on Windows 10+ (64-bit).
- **Uninstaller**: The PowerShell script (`Uninstall-NEVEN.ps1`) that reverses all changes made by the Installer.
- **NEVEN_Home**: The directory where NEVEN binaries and configuration are installed (default `C:\NEVEN\`).
- **User_Functions_Dir**: The per-user directory for custom scripts, located at `%USERPROFILE%\Documents\NEVEN\functions\`.
- **User_Graphics_Dir**: The per-user directory for generated graphics, located at `%USERPROFILE%\Documents\NEVEN\graphics\`.
- **Dist_Directory**: The `Build/Dist/` folder containing all compiled NEVEN artifacts ready for deployment.
- **XLL**: An Excel add-in DLL format recognized by Excel (NEVEN64.xll).
- **Ribbon_COM**: The NEVENRibbon.dll COM add-in that provides the NEVEN tab in the Excel ribbon.
- **Language_Runtime**: An external interpreter (R, Julia, or Python) that NEVEN uses as a scripting engine.
- **R_Home**: The root directory of the R installation (e.g., `C:\Program Files\R\R-4.4.1\`).
- **Julia_Home**: The root directory of the Julia installation (e.g., `%LOCALAPPDATA%\Programs\Julia-1.12.6\`).
- **Python_Home**: The root directory of the Python installation.
- **Quarto_Junction**: A directory junction `C:\Quarto` pointing to `C:\Program Files\Quarto\` to work around a Dart/Sass path-with-spaces bug.
- **Excel_Addin_Registry**: The registry path `HKCU:\Software\Microsoft\Office\<version>\Excel\Options` where Excel stores registered add-ins.
- **Ribbon_Registry**: The registry path `HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect` where the COM ribbon is registered.

## Requirements

### Requirement 1: Language Runtime Detection

**User Story:** As a user, I want the installer to detect which language runtimes are already installed on my system, so that I know what is ready and what needs to be installed before proceeding.

#### Acceptance Criteria

1. WHEN the Installer starts, THE Installer SHALL scan the system for R installations by checking the Windows registry (`HKLM:\SOFTWARE\R-core\R`) and the PATH environment variable for `Rscript.exe`.
2. WHEN the Installer starts, THE Installer SHALL scan the system for Julia installations by checking common installation paths (`%LOCALAPPDATA%\Programs\Julia-*`) and the PATH environment variable for `julia.exe`.
3. WHEN the Installer starts, THE Installer SHALL scan the system for Python installations by checking the PATH environment variable for `python.exe` and the Windows registry (`HKLM:\SOFTWARE\Python\PythonCore`).
4. WHEN a Language_Runtime is detected, THE Installer SHALL extract and display the version number of the detected runtime.
5. WHEN R is detected with a version equal to or greater than 4.4.1, THE Installer SHALL display R status as "Found" with a green indicator.
6. WHEN R is detected with a version lower than 4.4.1, THE Installer SHALL display R status as "Found (version too old)" with a yellow indicator and recommend upgrading.
7. WHEN R is not detected, THE Installer SHALL display R status as "Not found (REQUIRED)" with a red indicator.
8. WHEN Julia is detected with a version equal to or greater than 1.12.6, THE Installer SHALL display Julia status as "Found" with a green indicator.
9. WHEN Julia is not detected, THE Installer SHALL display Julia status as "Not found (optional)" with a yellow indicator.
10. WHEN Python is detected with a version equal to or greater than 3.10, THE Installer SHALL display Python status as "Found" with a green indicator.
11. WHEN Python is not detected, THE Installer SHALL display Python status as "Not found (optional)" with a yellow indicator.

### Requirement 2: Missing Runtime Guidance

**User Story:** As a user, I want the installer to guide me when a required or optional runtime is missing, so that I can install it before or after NEVEN setup.

#### Acceptance Criteria

1. WHEN R is not detected or the detected version is below 4.4.1, THE Installer SHALL display the download URL `https://cran.r-project.org/bin/windows/base/` and brief installation instructions.
2. WHEN R is not detected, THE Installer SHALL prompt the user to confirm whether to continue without R or abort the installation.
3. WHEN Julia is not detected, THE Installer SHALL display the download URL `https://julialang.org/downloads/` and note that Julia is optional.
4. WHEN Python is not detected, THE Installer SHALL display the download URL `https://www.python.org/downloads/` and note that Python is optional.
5. WHEN the user chooses to continue without R, THE Installer SHALL proceed with installation and log a warning that R-based functions will not work until R is installed.

### Requirement 3: NEVEN File Deployment

**User Story:** As a user, I want the installer to copy all NEVEN files to the correct location, so that the add-in is ready to load in Excel.

#### Acceptance Criteria

1. THE Installer SHALL prompt the user for an installation directory with a default value of `C:\NEVEN\`.
2. WHEN the user confirms the installation directory, THE Installer SHALL create the NEVEN_Home directory if it does not exist.
3. THE Installer SHALL copy the following files from the Dist_Directory to NEVEN_Home: `NEVEN64.xll`, `ControlR.exe`, `ControlJulia.exe`, `ControlPython.exe`, `NEVENRibbon.dll`, `neven-config.json`, and `neven-languages.json`.
4. THE Installer SHALL create a `startup` subdirectory inside NEVEN_Home and copy `startup.r`, `startup.jl`, and `startup.py` into it.
5. THE Installer SHALL create an `examples` subdirectory inside NEVEN_Home and copy all files from `Dist/examples/` into it.
6. WHEN a file already exists at the destination, THE Installer SHALL overwrite the file and log that the file was updated.
7. IF a file copy operation fails, THEN THE Installer SHALL log the error with the file name and path, and continue with the remaining files.

### Requirement 4: Excel XLL Registration

**User Story:** As a user, I want the installer to register the XLL add-in in Excel automatically, so that NEVEN loads when I open Excel without manual configuration.

#### Acceptance Criteria

1. WHEN file deployment completes, THE Installer SHALL add the full path of `NEVEN64.xll` to the Excel add-in registry under `HKCU:\Software\Microsoft\Office\<version>\Excel\Options` with a new `OPEN` string value.
2. WHEN an existing NEVEN XLL registration is found in the Excel registry, THE Installer SHALL update the path to the new installation location.
3. THE Installer SHALL detect all installed Excel versions (2013, 2016, 2019, 365) by scanning registry keys under `HKCU:\Software\Microsoft\Office\` for versions 15.0, 16.0.
4. IF the Excel registry key does not exist, THEN THE Installer SHALL log a warning that Excel was not detected and skip XLL registration.

### Requirement 5: Ribbon COM Registration

**User Story:** As a user, I want the installer to register the NEVEN Ribbon COM add-in, so that the NEVEN tab appears in the Excel ribbon.

#### Acceptance Criteria

1. WHEN file deployment completes, THE Installer SHALL execute `regsvr32 /s` on `NEVENRibbon.dll` located in NEVEN_Home.
2. WHEN `regsvr32` succeeds, THE Installer SHALL create the Ribbon_Registry key with `FriendlyName` set to "NEVEN", `Description` set to "NEVEN Ribbon Menu", and `LoadBehavior` set to 3 (load at startup).
3. IF `regsvr32` fails due to insufficient privileges, THEN THE Installer SHALL log a warning and offer to retry with elevated privileges using `Start-Process -Verb RunAs`.
4. IF `regsvr32` fails after retry, THEN THE Installer SHALL log the error and continue installation, noting that the Ribbon will not be available until manual registration.

### Requirement 6: User Directory Creation

**User Story:** As a user, I want the installer to create my personal NEVEN directories, so that I have a place for custom scripts and generated graphics.

#### Acceptance Criteria

1. THE Installer SHALL create the User_Functions_Dir at `%USERPROFILE%\Documents\NEVEN\functions\`.
2. THE Installer SHALL create the User_Graphics_Dir at `%USERPROFILE%\Documents\NEVEN\graphics\`.
3. WHEN the User_Functions_Dir already exists, THE Installer SHALL preserve existing files and log that the directory was already present.
4. WHEN the User_Graphics_Dir already exists, THE Installer SHALL preserve existing files and log that the directory was already present.

### Requirement 7: Example File Deployment

**User Story:** As a user, I want the installer to copy example scripts to my functions directory, so that I have working examples to learn from immediately.

#### Acceptance Criteria

1. THE Installer SHALL copy example R files (`.r`) from the examples subdirectory in NEVEN_Home to the User_Functions_Dir.
2. THE Installer SHALL copy example Julia files (`.jl`) from the examples subdirectory in NEVEN_Home to the User_Functions_Dir.
3. THE Installer SHALL copy example Python files (`.py`) from the examples subdirectory in NEVEN_Home to the User_Functions_Dir.
4. WHEN an example file already exists in the User_Functions_Dir, THE Installer SHALL skip the copy and log that the existing file was preserved.

### Requirement 8: Quarto Junction Creation

**User Story:** As a user, I want the installer to create the Quarto junction link if Quarto is installed, so that Quarto rendering works without path-related errors.

#### Acceptance Criteria

1. WHEN Quarto is installed at `C:\Program Files\Quarto\`, THE Installer SHALL create a directory junction at `C:\Quarto` pointing to `C:\Program Files\Quarto\`.
2. WHEN the Quarto_Junction already exists, THE Installer SHALL verify it points to the correct target and log that it is already configured.
3. WHEN Quarto is not installed, THE Installer SHALL skip junction creation and log that Quarto was not detected.
4. IF junction creation fails due to insufficient privileges, THEN THE Installer SHALL log a warning and provide the manual command: `mklink /J C:\Quarto "C:\Program Files\Quarto"`.

### Requirement 9: R Package Installation

**User Story:** As a user, I want the installer to optionally install required R packages, so that NEVEN statistical functions work on first use.

#### Acceptance Criteria

1. WHEN R is detected, THE Installer SHALL prompt the user whether to install R packages now or skip.
2. WHEN the user chooses to install R packages, THE Installer SHALL invoke `Rscript.exe` to install the base package set: `stargazer`, `svDialogs`, `lmtest`, `sandwich`, `margins`, `plm`, `rpart`, `rpart.plot`, `PerformanceAnalytics`, `tseries`, `mFilter`, `e1071`, `wooldridge`, `lme4`, `survival`, `psych`, `car`, `Hmisc`, `forecast`.
3. WHEN the user chooses to install R packages, THE Installer SHALL invoke `Rscript.exe` to install the visualization package set: `plotly`, `htmlwidgets`, `ggplot2`, `corrplot`.
4. THE Installer SHALL display progress for each package being installed.
5. IF an R package installation fails, THEN THE Installer SHALL log the package name and error, and continue with the remaining packages.
6. WHEN the user chooses to skip R package installation, THE Installer SHALL log that packages were skipped and note they can be installed later.

### Requirement 10: Desktop Shortcut Creation

**User Story:** As a user, I want the installer to optionally create a desktop shortcut, so that I can quickly open Excel with NEVEN loaded.

#### Acceptance Criteria

1. THE Installer SHALL prompt the user whether to create a desktop shortcut.
2. WHEN the user chooses to create a shortcut, THE Installer SHALL create a `.lnk` file on the Desktop that launches Excel with the NEVEN XLL loaded.
3. THE Installer SHALL set the shortcut icon to the NEVEN icon if available, or the default Excel icon otherwise.
4. WHEN a NEVEN desktop shortcut already exists, THE Installer SHALL update the shortcut target path.

### Requirement 11: Uninstaller

**User Story:** As a user, I want a clean uninstaller that removes all NEVEN files, registry entries, and COM registrations, so that my system is restored to its pre-installation state.

#### Acceptance Criteria

1. THE Installer SHALL create an `Uninstall-NEVEN.ps1` script in the NEVEN_Home directory during installation.
2. WHEN the Uninstaller runs, THE Uninstaller SHALL prompt the user to confirm the uninstallation.
3. WHEN the user confirms, THE Uninstaller SHALL check if Excel is running and prompt the user to close it before proceeding.
4. WHEN Excel is closed, THE Uninstaller SHALL execute `regsvr32 /u /s` on `NEVENRibbon.dll` to unregister the COM add-in.
5. WHEN Excel is closed, THE Uninstaller SHALL remove the NEVEN XLL entry from the Excel_Addin_Registry for all detected Excel versions.
6. WHEN Excel is closed, THE Uninstaller SHALL remove the Ribbon_Registry key.
7. THE Uninstaller SHALL prompt the user whether to delete user scripts in the User_Functions_Dir and User_Graphics_Dir.
8. WHEN the user chooses to delete user scripts, THE Uninstaller SHALL remove the `%USERPROFILE%\Documents\NEVEN\` directory tree.
9. WHEN the user chooses to keep user scripts, THE Uninstaller SHALL preserve the `%USERPROFILE%\Documents\NEVEN\` directory.
10. THE Uninstaller SHALL remove the Quarto_Junction if it exists and was created by the Installer.
11. THE Uninstaller SHALL remove the NEVEN_Home directory and all its contents.
12. THE Uninstaller SHALL remove the NEVEN desktop shortcut if it exists.
13. THE Uninstaller SHALL display a summary of all removed components upon completion.

### Requirement 12: Idempotent Execution

**User Story:** As a user, I want to be able to run the installer multiple times without breaking my existing installation, so that I can safely update or repair NEVEN.

#### Acceptance Criteria

1. WHEN the Installer detects an existing NEVEN installation in the target NEVEN_Home, THE Installer SHALL inform the user and offer to update or reinstall.
2. WHEN updating, THE Installer SHALL overwrite binary files and configuration templates while preserving user-modified `neven-config.json` by backing it up as `neven-config.json.bak`.
3. WHEN updating, THE Installer SHALL preserve existing user scripts in the User_Functions_Dir.
4. WHEN the Installer is run a second time, THE Installer SHALL not create duplicate XLL entries in the Excel_Addin_Registry.
5. WHEN the Installer is run a second time, THE Installer SHALL not create duplicate Ribbon_Registry entries.

### Requirement 13: Privilege Management

**User Story:** As a user, I want the installer to work without admin rights for basic installation, and only request elevation when needed for specific operations, so that I can install NEVEN on managed corporate machines.

#### Acceptance Criteria

1. THE Installer SHALL execute without requiring administrator privileges for file copy, directory creation, user registry writes, and XLL registration.
2. WHEN COM registration via `regsvr32` requires elevated privileges, THE Installer SHALL request elevation only for that specific operation.
3. WHEN Quarto_Junction creation requires elevated privileges, THE Installer SHALL request elevation only for that specific operation.
4. IF the user declines elevation, THEN THE Installer SHALL skip the privileged operation, log a warning, and continue with the remaining installation steps.

### Requirement 14: Installation Logging and Verification

**User Story:** As a user, I want the installer to log all actions and verify the installation, so that I can troubleshoot issues and confirm everything is working.

#### Acceptance Criteria

1. THE Installer SHALL write a timestamped log file to `NEVEN_Home\install.log` recording every action performed.
2. THE Installer SHALL log the start time, end time, and total duration of the installation.
3. WHEN installation completes, THE Installer SHALL run a verification check that confirms: NEVEN64.xll exists in NEVEN_Home, ControlR.exe exists in NEVEN_Home, neven-config.json exists in NEVEN_Home, the XLL is registered in the Excel registry, and the User_Functions_Dir exists.
4. WHEN all verification checks pass, THE Installer SHALL display a success message with the instruction to test by entering `=NEVEN.R("1+1")` in an Excel cell.
5. WHEN one or more verification checks fail, THE Installer SHALL display a warning listing the failed checks and suggest consulting the install.log file.

### Requirement 15: Windows Compatibility

**User Story:** As a user, I want the installer to work on all supported Windows versions, so that I can install NEVEN regardless of my Windows edition.

#### Acceptance Criteria

1. THE Installer SHALL require Windows 10 or later (64-bit) and verify this at startup.
2. THE Installer SHALL require PowerShell 5.1 or later and verify this at startup.
3. IF the operating system is not Windows 10+ (64-bit), THEN THE Installer SHALL display an error message and exit.
4. IF the PowerShell version is below 5.1, THEN THE Installer SHALL display an error message and exit.
5. THE Installer SHALL use only PowerShell cmdlets and .NET APIs available in PowerShell 5.1 to ensure compatibility without additional module dependencies.
