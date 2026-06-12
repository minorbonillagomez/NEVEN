<#
.SYNOPSIS
    NEVEN Installer - Automates the full deployment of the NEVEN Excel add-in.

.DESCRIPTION
    Single-script installer for NEVEN (R, Julia, and Python to Excel).
    Executes six sequential phases:
      1. Pre-flight checks (OS, PowerShell, language runtimes, Excel)
      2. User choices (install dir, R packages, shortcut)
      3. File deployment (binaries, configs, startup scripts, examples)
      4. Registration (XLL, Ribbon COM, Quarto junction)
      5. User setup (directories, example files, R packages, shortcut)
      6. Verification and uninstaller generation

    Requires Windows 10+ (64-bit) and PowerShell 5.1+.
    No external module dependencies.

.PARAMETER InstallDir
    Target installation directory. Default: C:\NEVEN

.PARAMETER DistDir
    Path to the Dist folder containing compiled artifacts. Default: .\Dist

.PARAMETER Silent
    Run without interactive prompts, using all defaults.

.EXAMPLE
    .\Install-NEVEN.ps1
    .\Install-NEVEN.ps1 -InstallDir D:\NEVEN -Silent
#>
param(
    [string]$InstallDir = 'C:\NEVEN',
    [string]$DistDir    = (Join-Path $PSScriptRoot 'Dist'),
    [switch]$Silent
)

$ErrorActionPreference = 'Continue'
$script:LogFile     = $null
$script:HasWarnings = $false
$script:StartTime   = Get-Date

# ─── Ensure console stays open on error ───
trap {
    Write-Host ''
    Write-Host "  UNEXPECTED ERROR: $_" -ForegroundColor Red
    Write-Host ''
    Read-Host '  Press Enter to close'
}

function Exit-Installer {
    param([int]$Code = 0)
    if (-not $Silent) {
        Write-Host ''
        if ($Code -eq 0) {
            Read-Host '  Installation complete. Press Enter to close'
        } else {
            Read-Host '  Press Enter to close'
        }
    }
    exit $Code
}

# ============================================================
#  Logging
# ============================================================

function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet('INFO','WARN','ERROR')][string]$Level = 'INFO'
    )
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $entry = "[$timestamp] $($Level.PadRight(5)) $Message"
    if ($script:LogFile) {
        try { Add-Content -Path $script:LogFile -Value $entry -Encoding UTF8 } catch { }
    }
    switch ($Level) {
        'WARN'  { Write-Host $entry -ForegroundColor Yellow }
        'ERROR' { Write-Host $entry -ForegroundColor Red }
        default { Write-Host $entry -ForegroundColor White }
    }
}

function Initialize-LogFile {
    param([string]$Path)
    $script:LogFile = $Path
    $now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $banner = "========================================`r`nNEVEN Installer Log`r`nStarted: $now`r`n========================================"
    try { Set-Content -Path $script:LogFile -Value $banner -Encoding UTF8 } catch { }
}

function Close-LogFile {
    $endTime = Get-Date
    $duration = $endTime - $script:StartTime
    $now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $secs = [math]::Round($duration.TotalSeconds)
    $footer = "========================================`r`nCompleted: $now`r`nDuration: $secs seconds`r`n========================================"
    if ($script:LogFile) {
        try { Add-Content -Path $script:LogFile -Value $footer -Encoding UTF8 } catch { }
    }
}

# ============================================================
#  Phase 1: Pre-flight Checks
# ============================================================

function Test-WindowsVersion {
    [OutputType([bool])]
    param()
    $build = [Environment]::OSVersion.Version.Build
    $is64  = [Environment]::Is64BitOperatingSystem
    $ver   = [Environment]::OSVersion.Version
    $verStr = "$($ver.Major).$($ver.Minor).$build"
    if ($is64 -and $build -ge 10240) {
        Write-Log "Windows $verStr 64-bit - OK"
        return $true
    }
    Write-Log "Windows $verStr (64-bit=$is64) - FAIL" -Level ERROR
    return $false
}

function Test-PowerShellVersion {
    [OutputType([bool])]
    param()
    $v = $PSVersionTable.PSVersion
    $vStr = "$($v.Major).$($v.Minor)"
    if ($v.Major -gt 5 -or ($v.Major -eq 5 -and $v.Minor -ge 1)) {
        Write-Log "PowerShell $vStr - OK"
        return $true
    }
    Write-Log "PowerShell $vStr - requires 5.1+" -Level ERROR
    return $false
}

function Find-R {
    [OutputType([PSCustomObject])]
    param()
    $result = [PSCustomObject]@{ Found = $false; Path = ''; Version = ''; Adequate = $false }

    # 1. Registry
    try {
        $regPath = 'HKLM:\SOFTWARE\R-core\R'
        if (Test-Path $regPath) {
            $rHome = (Get-ItemProperty -Path $regPath -Name 'InstallPath' -ErrorAction SilentlyContinue).InstallPath
            if ($rHome -and (Test-Path (Join-Path $rHome 'bin\Rscript.exe'))) {
                $result.Found = $true
                $result.Path  = $rHome
            }
        }
    } catch { }

    # 2. PATH
    if (-not $result.Found) {
        $cmd = Get-Command 'Rscript.exe' -ErrorAction SilentlyContinue
        if ($cmd) {
            $result.Found = $true
            $binDir = Split-Path $cmd.Source -Parent
            $result.Path = Split-Path $binDir -Parent
            if ((Split-Path $result.Path -Leaf) -eq 'bin') {
                $result.Path = Split-Path $result.Path -Parent
            }
        }
    }

    # 3. Filesystem
    if (-not $result.Found) {
        $candidates = Get-ChildItem 'C:\Program Files\R\R-*' -Directory -ErrorAction SilentlyContinue |
                      Sort-Object Name -Descending
        foreach ($dir in $candidates) {
            if (Test-Path (Join-Path $dir.FullName 'bin\Rscript.exe')) {
                $result.Found = $true
                $result.Path  = $dir.FullName
                break
            }
        }
    }

    # Extract version
    if ($result.Found) {
        try {
            $rscript = Join-Path $result.Path 'bin\Rscript.exe'
            $output = & $rscript --version 2>&1 | Out-String
            if ($output -match '(\d+\.\d+\.\d+)') {
                $result.Version = $Matches[1]
                $parts = $result.Version.Split('.')
                $major = [int]$parts[0]; $minor = [int]$parts[1]; $patch = [int]$parts[2]
                if ($major -gt 4 -or ($major -eq 4 -and $minor -gt 4) -or ($major -eq 4 -and $minor -eq 4 -and $patch -ge 1)) {
                    $result.Adequate = $true
                }
            }
        } catch { }
        Write-Log "R $($result.Version) found at $($result.Path) (adequate=$($result.Adequate))"
    } else {
        Write-Log 'R not found' -Level WARN
    }
    return $result
}

function Find-Julia {
    [OutputType([PSCustomObject])]
    param()
    $result = [PSCustomObject]@{ Found = $false; Path = ''; Version = ''; Adequate = $false }

    # 1. PATH (refresh environment first)
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $cmd = Get-Command 'julia.exe' -ErrorAction SilentlyContinue
    if ($cmd) {
        $result.Found = $true
        $binDir = Split-Path $cmd.Source -Parent
        # Handle both "Julia-1.12.6/bin" and "Julia/bin" structures
        $parent = Split-Path $binDir -Parent
        if ((Split-Path $parent -Leaf) -eq 'bin') { $parent = Split-Path $parent -Parent }
        $result.Path = $parent
    }

    # 2. Filesystem - check multiple known locations
    if (-not $result.Found) {
        $searchPaths = @(
            (Join-Path $env:LOCALAPPDATA 'Programs'),
            (Join-Path $env:LOCALAPPDATA 'Programs\Julia'),
            'C:\Julia',
            (Join-Path $env:ProgramFiles 'Julia'),
            (Join-Path ${env:ProgramFiles(x86)} 'Julia')
        )
        foreach ($basePath in $searchPaths) {
            if (-not (Test-Path $basePath)) { continue }
            # Check direct bin/julia.exe (modern installer: Julia/bin/julia.exe)
            $directBin = Join-Path $basePath 'bin\julia.exe'
            if (Test-Path $directBin) {
                $result.Found = $true
                $result.Path  = $basePath
                break
            }
            # Check versioned folders (legacy: Julia-1.12.6/bin/julia.exe)
            $candidates = Get-ChildItem (Join-Path $basePath 'Julia*') -Directory -ErrorAction SilentlyContinue |
                          Sort-Object Name -Descending
            foreach ($dir in $candidates) {
                $juliaExe = Join-Path $dir.FullName 'bin\julia.exe'
                if (Test-Path $juliaExe) {
                    $result.Found = $true
                    $result.Path  = $dir.FullName
                    break
                }
            }
            if ($result.Found) { break }
        }
    }

    # Extract version
    if ($result.Found) {
        try {
            $julia = Join-Path $result.Path 'bin\julia.exe'
            $output = & $julia --version 2>&1 | Out-String
            if ($output -match '(\d+\.\d+\.\d+)') {
                $result.Version = $Matches[1]
                $parts = $result.Version.Split('.')
                $major = [int]$parts[0]; $minor = [int]$parts[1]; $patch = [int]$parts[2]
                if ($major -gt 1 -or ($major -eq 1 -and $minor -gt 12) -or ($major -eq 1 -and $minor -eq 12 -and $patch -ge 6)) {
                    $result.Adequate = $true
                }
            }
        } catch { }
        Write-Log "Julia $($result.Version) found at $($result.Path) (adequate=$($result.Adequate))"
    } else {
        Write-Log 'Julia not found' -Level WARN
    }
    return $result
}

function Find-Python {
    [OutputType([PSCustomObject])]
    param()
    $result = [PSCustomObject]@{ Found = $false; Path = ''; Version = ''; Adequate = $false }

    # 1. PATH
    $cmd = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if ($cmd) {
        $result.Found = $true
        $result.Path  = Split-Path $cmd.Source -Parent
    }

    # 2. Registry
    if (-not $result.Found) {
        try {
            $pyReg = 'HKLM:\SOFTWARE\Python\PythonCore'
            if (Test-Path $pyReg) {
                $versions = Get-ChildItem $pyReg -ErrorAction SilentlyContinue | Sort-Object Name -Descending
                foreach ($v in $versions) {
                    $ip = Join-Path $v.PSPath 'InstallPath'
                    if (Test-Path $ip) {
                        $pyPath = (Get-ItemProperty -Path $ip -Name '(Default)' -ErrorAction SilentlyContinue).'(Default)'
                        if ($pyPath -and (Test-Path (Join-Path $pyPath 'python.exe'))) {
                            $result.Found = $true
                            $result.Path  = $pyPath
                            break
                        }
                    }
                }
            }
        } catch { }
    }

    # 3. Filesystem
    if (-not $result.Found) {
        $basePath = Join-Path $env:LOCALAPPDATA 'Programs\Python'
        if (Test-Path $basePath) {
            $candidates = Get-ChildItem (Join-Path $basePath 'Python3*') -Directory -ErrorAction SilentlyContinue |
                          Sort-Object Name -Descending
            foreach ($dir in $candidates) {
                if (Test-Path (Join-Path $dir.FullName 'python.exe')) {
                    $result.Found = $true
                    $result.Path  = $dir.FullName
                    break
                }
            }
        }
    }

    # Extract version
    if ($result.Found) {
        try {
            $python = Join-Path $result.Path 'python.exe'
            $output = & $python --version 2>&1 | Out-String
            if ($output -match '(\d+\.\d+\.\d+)') {
                $result.Version = $Matches[1]
                $parts = $result.Version.Split('.')
                $major = [int]$parts[0]; $minor = [int]$parts[1]
                if ($major -ge 3 -and $minor -ge 10) {
                    $result.Adequate = $true
                }
            }
        } catch { }
        Write-Log "Python $($result.Version) found at $($result.Path) (adequate=$($result.Adequate))"
    } else {
        Write-Log 'Python not found' -Level WARN
    }
    return $result
}

function Find-ExcelVersions {
    [OutputType([string[]])]
    param()
    $versions = @()
    foreach ($ver in @('15.0','16.0')) {
        $regPath = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
        if (Test-Path $regPath) {
            $versions += $ver
            Write-Log "Excel $ver detected"
        }
    }
    if ($versions.Count -eq 0) {
        Write-Log 'No Excel installation detected in registry' -Level WARN
    }
    return $versions
}

function Find-ExistingInstall {
    [OutputType([PSCustomObject])]
    param([string]$TargetPath)
    $result = [PSCustomObject]@{ Found = $false; Path = $TargetPath; HasConfig = $false }
    if (Test-Path $TargetPath) {
        $xll = Join-Path $TargetPath 'NEVEN64.xll'
        if (Test-Path $xll) {
            $result.Found = $true
            Write-Log "Existing NEVEN installation found at $TargetPath"
        }
        $cfg = Join-Path $TargetPath 'neven-config.json'
        if (Test-Path $cfg) {
            $result.HasConfig = $true
        }
    }
    return $result
}

function Show-PreflightSummary {
    param(
        [ref]$RInfoRef,
        [ref]$JuliaInfoRef,
        [ref]$PythonInfoRef,
        [string[]]$ExcelVersions,
        [PSCustomObject]$ExistingInstall
    )

    $RInfo = $RInfoRef.Value
    $JuliaInfo = $JuliaInfoRef.Value
    $PythonInfo = $PythonInfoRef.Value

    Write-Host ''
    Write-Host '  ============================================' -ForegroundColor Cyan
    Write-Host '   NEVEN Installer - Pre-flight Summary' -ForegroundColor Cyan
    Write-Host '  ============================================' -ForegroundColor Cyan
    Write-Host ''

    # --- R ---
    if ($RInfo.Found -and $RInfo.Adequate) {
        Write-Host "   [OK] R $($RInfo.Version)  $($RInfo.Path)" -ForegroundColor Green
    } else {
        if ($RInfo.Found) {
            Write-Host "   [!!] R $($RInfo.Version) (need >= 4.4.1)  $($RInfo.Path)" -ForegroundColor Yellow
        } else {
            Write-Host '   [XX] R not found (REQUIRED for R functions)' -ForegroundColor Red
        }
        Write-Host '        Download: https://cran.r-project.org/bin/windows/base/' -ForegroundColor Yellow
        if (-not $Silent) {
            $open = Read-Host '        Open download page? (y/n) [n]'
            if ($open -eq 'y') { Start-Process 'https://cran.r-project.org/bin/windows/base/' }
            Write-Host ''
            $done = Read-Host '        Have you finished installing R? (y/n) [n]'
            if ($done -eq 'y') {
                Write-Host '        Re-detecting R...' -ForegroundColor Cyan
                $RInfoRef.Value = Find-R
                $RInfo = $RInfoRef.Value
                if ($RInfo.Found -and $RInfo.Adequate) {
                    Write-Host "   [OK] R $($RInfo.Version) detected at $($RInfo.Path)" -ForegroundColor Green
                } elseif ($RInfo.Found) {
                    Write-Host "   [!!] R $($RInfo.Version) detected but version is below 4.4.1" -ForegroundColor Yellow
                } else {
                    Write-Host '   [XX] R still not detected. You can install it later.' -ForegroundColor Yellow
                }
            }
        }
    }

    # --- Julia ---
    if ($JuliaInfo.Found -and $JuliaInfo.Adequate) {
        Write-Host "   [OK] Julia $($JuliaInfo.Version)  $($JuliaInfo.Path)" -ForegroundColor Green
    } else {
        if ($JuliaInfo.Found) {
            Write-Host "   [!!] Julia $($JuliaInfo.Version) (need >= 1.12.6)  $($JuliaInfo.Path)" -ForegroundColor Yellow
        } else {
            Write-Host '   [!!] Julia not found (optional - math/ML functions)' -ForegroundColor Yellow
        }
        Write-Host '        Download: https://julialang.org/downloads/' -ForegroundColor Yellow
        if (-not $Silent) {
            $open = Read-Host '        Open download page? (y/n) [n]'
            if ($open -eq 'y') { Start-Process 'https://julialang.org/downloads/' }
            Write-Host ''
            $done = Read-Host '        Have you finished installing Julia? (y/n) [n]'
            if ($done -eq 'y') {
                Write-Host '        Re-detecting Julia...' -ForegroundColor Cyan
                $JuliaInfoRef.Value = Find-Julia
                $JuliaInfo = $JuliaInfoRef.Value
                if ($JuliaInfo.Found -and $JuliaInfo.Adequate) {
                    Write-Host "   [OK] Julia $($JuliaInfo.Version) detected at $($JuliaInfo.Path)" -ForegroundColor Green
                } elseif ($JuliaInfo.Found) {
                    Write-Host "   [!!] Julia $($JuliaInfo.Version) detected but version is below 1.12.6" -ForegroundColor Yellow
                } else {
                    Write-Host '   [!!] Julia still not detected. You can install it later.' -ForegroundColor Yellow
                }
            }
        }
    }

    # --- Python ---
    if ($PythonInfo.Found -and $PythonInfo.Adequate) {
        Write-Host "   [OK] Python $($PythonInfo.Version)  $($PythonInfo.Path)" -ForegroundColor Green
    } else {
        if ($PythonInfo.Found) {
            Write-Host "   [!!] Python $($PythonInfo.Version) (need >= 3.10)  $($PythonInfo.Path)" -ForegroundColor Yellow
        } else {
            Write-Host '   [!!] Python not found (optional - AI functions)' -ForegroundColor Yellow
        }
        Write-Host '        Download: https://www.python.org/downloads/' -ForegroundColor Yellow
        if (-not $Silent) {
            $open = Read-Host '        Open download page? (y/n) [n]'
            if ($open -eq 'y') { Start-Process 'https://www.python.org/downloads/' }
            Write-Host ''
            $done = Read-Host '        Have you finished installing Python? (y/n) [n]'
            if ($done -eq 'y') {
                Write-Host '        Re-detecting Python...' -ForegroundColor Cyan
                $PythonInfoRef.Value = Find-Python
                $PythonInfo = $PythonInfoRef.Value
                if ($PythonInfo.Found -and $PythonInfo.Adequate) {
                    Write-Host "   [OK] Python $($PythonInfo.Version) detected at $($PythonInfo.Path)" -ForegroundColor Green
                } elseif ($PythonInfo.Found) {
                    Write-Host "   [!!] Python $($PythonInfo.Version) detected but version is below 3.10" -ForegroundColor Yellow
                } else {
                    Write-Host '   [!!] Python still not detected. You can install it later.' -ForegroundColor Yellow
                }
            }
        }
    }

    # --- Excel ---
    if ($ExcelVersions.Count -gt 0) {
        $verStr = $ExcelVersions -join ', '
        Write-Host "   [OK] Excel detected (versions: $verStr)" -ForegroundColor Green
    } else {
        Write-Host '   [!!] Excel not detected - XLL registration will be skipped' -ForegroundColor Yellow
    }

    # --- Existing install ---
    if ($ExistingInstall.Found) {
        Write-Host "   [!!] Existing NEVEN installation at $($ExistingInstall.Path)" -ForegroundColor Yellow
    }

    Write-Host ''
}

# ============================================================
#  Phase 2: User Choices
# ============================================================

function Get-UserChoices {
    [OutputType([PSCustomObject])]
    param(
        [PSCustomObject]$RInfo,
        [PSCustomObject]$JuliaInfo,
        [PSCustomObject]$ExistingInstall
    )
    $choices = [PSCustomObject]@{
        InstallDir       = $InstallDir
        ContinueWithoutR = $false
        InstallRPackages = $false
        CreateShortcut   = $true
        IsUpdate         = $false
    }

    if ($Silent) {
        if (-not $RInfo.Found) { $choices.ContinueWithoutR = $true }
        if ($RInfo.Found -and $RInfo.Adequate) { $choices.InstallRPackages = $true }
        if ($ExistingInstall.Found) { $choices.IsUpdate = $true }
        return $choices
    }

    # 1. Installation directory
    $dirInput = Read-Host "  Installation directory [$InstallDir]"
    if ($dirInput.Trim()) { $choices.InstallDir = $dirInput.Trim() }

    # 2. R not found - continue?
    if (-not $RInfo.Found -or -not $RInfo.Adequate) {
        if (-not $RInfo.Found) {
            Write-Host '  R was not found.' -ForegroundColor Yellow
        } else {
            Write-Host "  R $($RInfo.Version) is below the recommended 4.4.1." -ForegroundColor Yellow
        }
        $answer = Read-Host '  Continue without R? R-based functions will not work. (y/n) [y]'
        if ($answer -eq 'n') {
            Write-Host '  Installation aborted by user.' -ForegroundColor Red
            Exit-Installer 0
        }
        $choices.ContinueWithoutR = $true
        Write-Log 'User chose to continue without R' -Level WARN
    }

    # 3. R found - install packages?
    if ($RInfo.Found -and $RInfo.Adequate) {
        $answer = Read-Host '  Install R packages (statistical libraries)? (y/n) [y]'
        if ($answer -ne 'n') { $choices.InstallRPackages = $true }
    }

    # 4. Desktop shortcut
    $answer = Read-Host '  Create desktop shortcut for NEVEN? (y/n) [y]'
    if ($answer -eq 'n') { $choices.CreateShortcut = $false }

    # 5. Existing install
    if ($ExistingInstall.Found) {
        $answer = Read-Host '  Existing installation found. Update/reinstall? (y/n) [y]'
        if ($answer -eq 'n') {
            Write-Host '  Installation aborted by user.' -ForegroundColor Red
            Exit-Installer 0
        }
        $choices.IsUpdate = $true
    }

    return $choices
}

# ============================================================
#  Phase 3: File Deployment
# ============================================================

function Install-NEVENFiles {
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)][string]$TargetDir,
        [Parameter(Mandatory)][string]$SourceDir,
        [bool]$IsUpdate = $false
    )
    Write-Log "Deploying files to $TargetDir"

    # Create install directory
    if (-not (Test-Path $TargetDir)) {
        try {
            New-Item -Path $TargetDir -ItemType Directory -Force | Out-Null
            Write-Log "Created directory $TargetDir"
        } catch {
            Write-Log "Failed to create directory ${TargetDir}: $_" -Level ERROR
            return $false
        }
    }

    # Backup existing config on update
    if ($IsUpdate) {
        $cfgPath = Join-Path $TargetDir 'neven-config.json'
        if (Test-Path $cfgPath) {
            try {
                Copy-Item -Path $cfgPath -Destination "$cfgPath.bak" -Force
                Write-Log 'Backed up neven-config.json to neven-config.json.bak'
            } catch {
                Write-Log "Failed to backup neven-config.json: $_" -Level WARN
                $script:HasWarnings = $true
            }
        }
    }

    # Critical and non-critical files
    $criticalFiles = @('NEVEN64.xll')
    $binaryFiles   = @('NEVEN64.xll', 'ControlR.exe', 'ControlJulia.exe', 'ControlPython.exe',
                        'NEVENRibbon.dll', 'neven-config.json', 'neven-languages.json')
    $criticalOk = $true

    foreach ($file in $binaryFiles) {
        $src = Join-Path $SourceDir $file
        $dst = Join-Path $TargetDir $file
        if (Test-Path $src) {
            try {
                Copy-Item -Path $src -Destination $dst -Force
                Write-Log "Copied $file"
            } catch {
                Write-Log "Failed to copy ${file}: $_" -Level ERROR
                $script:HasWarnings = $true
                if ($criticalFiles -contains $file) { $criticalOk = $false }
            }
        } else {
            if ($criticalFiles -contains $file) {
                Write-Log "$file not found in $SourceDir" -Level ERROR
                $criticalOk = $false
            } else {
                Write-Log "$file not found in $SourceDir - skipping" -Level WARN
            }
        }
    }

    # Startup scripts
    $startupDir = Join-Path $TargetDir 'startup'
    if (-not (Test-Path $startupDir)) {
        New-Item -Path $startupDir -ItemType Directory -Force | Out-Null
    }
    foreach ($file in @('startup.r', 'startup.jl', 'startup.py')) {
        $src = Join-Path $SourceDir "startup\$file"
        $dst = Join-Path $startupDir $file
        if (Test-Path $src) {
            try {
                Copy-Item -Path $src -Destination $dst -Force
                Write-Log "Copied startup\$file"
            } catch {
                Write-Log "Failed to copy startup\${file}: $_" -Level ERROR
                $script:HasWarnings = $true
            }
        } else {
            Write-Log "startup\$file not found - skipping" -Level WARN
        }
    }

    # Examples
    $srcExamples = Join-Path $SourceDir 'examples'
    $dstExamples = Join-Path $TargetDir 'examples'
    if (Test-Path $srcExamples) {
        try {
            if (-not (Test-Path $dstExamples)) {
                New-Item -Path $dstExamples -ItemType Directory -Force | Out-Null
            }
            Copy-Item -Path (Join-Path $srcExamples '*') -Destination $dstExamples -Recurse -Force
            Write-Log 'Copied examples directory'
        } catch {
            Write-Log "Failed to copy examples: $_" -Level ERROR
            $script:HasWarnings = $true
        }
    } else {
        Write-Log "Examples directory not found in $SourceDir - skipping" -Level WARN
    }

    return $criticalOk
}

# ============================================================
#  Phase 4: Registration
# ============================================================

function Register-XLL {
    [OutputType([bool])]
    param(
        [Parameter(Mandatory)][string]$XllPath,
        [Parameter(Mandatory)][string[]]$ExcelVersions
    )
    $registered = $false
    foreach ($ver in $ExcelVersions) {
        $regPath = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
        if (-not (Test-Path $regPath)) {
            Write-Log "Registry key $regPath does not exist - skipping" -Level WARN
            continue
        }

        $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
        $nevenValue = "/R `"$XllPath`""
        $existingKey = $null
        $maxIndex = -1

        # Scan existing OPEN keys
        $propNames = $props.PSObject.Properties | Where-Object { $_.Name -match '^OPEN\d*$' }
        foreach ($prop in $propNames) {
            $name = $prop.Name
            $val  = $prop.Value
            # Track highest index
            if ($name -eq 'OPEN') {
                if ($maxIndex -lt 0) { $maxIndex = 0 }
            } else {
                $idx = [int]($name -replace 'OPEN', '')
                if ($idx -gt $maxIndex) { $maxIndex = $idx }
            }
            # Check if this is an existing NEVEN entry
            if ($val -match 'NEVEN') {
                $existingKey = $name
            }
        }

        if ($existingKey) {
            # Update existing entry
            Set-ItemProperty -Path $regPath -Name $existingKey -Value $nevenValue
            Write-Log "Updated existing XLL entry ($existingKey) for Excel $ver"
        } else {
            # Find next available slot
            if ($maxIndex -lt 0) {
                $newKey = 'OPEN'
            } else {
                $newKey = 'OPEN' + ($maxIndex + 1)
            }
            New-ItemProperty -Path $regPath -Name $newKey -Value $nevenValue -PropertyType String -Force | Out-Null
            Write-Log "Registered XLL as $newKey for Excel $ver"
        }
        $registered = $true
    }
    return $registered
}

function Unregister-XLL {
    [OutputType([void])]
    param(
        [string]$XllPath,
        [string[]]$ExcelVersions
    )
    foreach ($ver in $ExcelVersions) {
        $regPath = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
        if (-not (Test-Path $regPath)) { continue }
        $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
        $propNames = $props.PSObject.Properties | Where-Object { $_.Name -match '^OPEN\d*$' }
        foreach ($prop in $propNames) {
            if ($prop.Value -match 'NEVEN') {
                Remove-ItemProperty -Path $regPath -Name $prop.Name -ErrorAction SilentlyContinue
                Write-Log "Removed XLL entry $($prop.Name) from Excel $ver"
            }
        }
    }
}

function Register-RibbonCOM {
    [OutputType([bool])]
    param([Parameter(Mandatory)][string]$DllPath)

    if (-not (Test-Path $DllPath)) {
        Write-Log "NEVENRibbon.dll not found at $DllPath - skipping COM registration" -Level WARN
        return $false
    }

    Write-Log "Registering COM: $DllPath"
    $success = $false

    try {
        $proc = Start-Process -FilePath 'regsvr32' -ArgumentList "/s `"$DllPath`"" -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -eq 0) {
            $success = $true
            Write-Log 'regsvr32 succeeded'
        } else {
            Write-Log "regsvr32 failed (exit code $($proc.ExitCode)). Elevation may be required." -Level WARN
        }
    } catch {
        Write-Log "regsvr32 failed: $_" -Level WARN
    }

    # Retry with elevation if needed
    if (-not $success) {
        $retry = $true
        if (-not $Silent) {
            $answer = Read-Host '  Retry COM registration with administrator privileges? (y/n) [y]'
            if ($answer -eq 'n') { $retry = $false }
        }
        if ($retry) {
            try {
                $proc = Start-Process -FilePath 'regsvr32' -ArgumentList "/s `"$DllPath`"" -Verb RunAs -Wait -PassThru
                if ($proc.ExitCode -eq 0) {
                    $success = $true
                    Write-Log 'Elevated regsvr32 succeeded'
                } else {
                    Write-Log "Elevated regsvr32 failed (exit code $($proc.ExitCode))" -Level ERROR
                }
            } catch {
                Write-Log "Elevated regsvr32 failed: $_" -Level ERROR
            }
        } else {
            Write-Log 'User declined elevation. Ribbon will not be available.' -Level WARN
            $script:HasWarnings = $true
        }
    }

    # Create Ribbon registry key on success
    if ($success) {
        $ribbonKey = 'HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect'
        try {
            if (-not (Test-Path $ribbonKey)) {
                New-Item -Path $ribbonKey -Force | Out-Null
            }
            Set-ItemProperty -Path $ribbonKey -Name 'FriendlyName'  -Value 'NEVEN'              -Type String
            Set-ItemProperty -Path $ribbonKey -Name 'Description'   -Value 'NEVEN Ribbon Menu'   -Type String
            Set-ItemProperty -Path $ribbonKey -Name 'LoadBehavior'  -Value 3                     -Type DWord
            Write-Log 'Ribbon COM registry key created'
        } catch {
            Write-Log "Failed to create Ribbon registry key: $_" -Level ERROR
            $script:HasWarnings = $true
        }
    }

    return $success
}

function Unregister-RibbonCOM {
    [OutputType([void])]
    param([string]$DllPath)
    if (Test-Path $DllPath) {
        try {
            Start-Process -FilePath 'regsvr32' -ArgumentList "/u /s `"$DllPath`"" -Wait -NoNewWindow
            Write-Log "Unregistered COM: $DllPath"
        } catch {
            Write-Log "Failed to unregister COM: $_" -Level WARN
        }
    }
    $ribbonKey = 'HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect'
    if (Test-Path $ribbonKey) {
        Remove-Item -Path $ribbonKey -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log 'Removed Ribbon registry key'
    }
}

function Register-TrustedLocation {
    [OutputType([void])]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string[]]$ExcelVersions
    )

    foreach ($ver in $ExcelVersions) {
        $trustedBase = "HKCU:\Software\Microsoft\Office\$ver\Excel\Security\Trusted Locations"
        if (-not (Test-Path $trustedBase)) {
            Write-Log "Trusted Locations key not found for Excel $ver - skipping" -Level WARN
            continue
        }

        # Check if NEVEN is already a trusted location
        $existing = Get-ChildItem $trustedBase -ErrorAction SilentlyContinue
        $alreadyTrusted = $false
        foreach ($loc in $existing) {
            $locPath = (Get-ItemProperty -Path $loc.PSPath -Name 'Path' -ErrorAction SilentlyContinue).Path
            if ($locPath -and $locPath.TrimEnd('\') -eq $Path.TrimEnd('\')) {
                $alreadyTrusted = $true
                Write-Log "Trusted Location already exists for $Path in Excel $ver"
                break
            }
        }

        if (-not $alreadyTrusted) {
            # Find next available slot (Location0, Location1, ...)
            $maxIdx = -1
            foreach ($loc in $existing) {
                if ($loc.PSChildName -match 'Location(\d+)') {
                    $idx = [int]$Matches[1]
                    if ($idx -gt $maxIdx) { $maxIdx = $idx }
                }
            }
            $newIdx = $maxIdx + 1
            $newKey = Join-Path $trustedBase "Location$newIdx"

            try {
                New-Item -Path $newKey -Force | Out-Null
                Set-ItemProperty -Path $newKey -Name 'Path' -Value "$Path\" -Type String
                Set-ItemProperty -Path $newKey -Name 'AllowSubFolders' -Value 1 -Type DWord
                Set-ItemProperty -Path $newKey -Name 'Description' -Value 'NEVEN Add-in' -Type String
                Write-Log "Added Trusted Location: $Path (Excel $ver, Location$newIdx)"
                Write-Host "   [OK] Trusted Location added: $Path" -ForegroundColor Green
            } catch {
                Write-Log "Failed to add Trusted Location: $_" -Level WARN
                $script:HasWarnings = $true
            }
        }
    }
}

function New-QuartoJunction {
    [OutputType([bool])]
    param()
    $quartoSrc = 'C:\Program Files\Quarto'
    $quartoJunction = 'C:\Quarto'

    if (-not (Test-Path $quartoSrc)) {
        Write-Log "Quarto not detected at $quartoSrc - skipping junction"
        return $false
    }

    if (Test-Path $quartoJunction) {
        $item = Get-Item $quartoJunction -Force -ErrorAction SilentlyContinue
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            Write-Log "Quarto junction already configured at $quartoJunction"
            return $true
        } else {
            Write-Log 'C:\Quarto exists but is not a junction - skipping' -Level WARN
            return $false
        }
    }

    Write-Log "Creating Quarto junction: $quartoJunction -> $quartoSrc"
    try {
        $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList "/c mklink /J `"$quartoJunction`" `"$quartoSrc`"" -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -eq 0) {
            Write-Log 'Quarto junction created'
            return $true
        }
    } catch { }

    # Offer elevation
    Write-Log 'Junction creation failed - elevation may be required' -Level WARN
    $retry = $true
    if (-not $Silent) {
        $answer = Read-Host '  Retry Quarto junction with administrator privileges? (y/n) [y]'
        if ($answer -eq 'n') { $retry = $false }
    }
    if ($retry) {
        try {
            Start-Process -FilePath 'cmd.exe' -ArgumentList "/c mklink /J `"$quartoJunction`" `"$quartoSrc`"" -Verb RunAs -Wait
            if (Test-Path $quartoJunction) {
                Write-Log 'Quarto junction created (elevated)'
                return $true
            }
        } catch {
            Write-Log "Elevated junction creation failed: $_" -Level ERROR
        }
    } else {
        Write-Log 'User declined elevation. Run manually: mklink /J C:\Quarto "C:\Program Files\Quarto"' -Level WARN
        $script:HasWarnings = $true
    }
    return $false
}

# ============================================================
#  Phase 5: User Setup
# ============================================================

function Initialize-UserDirectories {
    [OutputType([void])]
    param()
    # Use C:\NEVEN\ directly to avoid OneDrive redirection of Documents
    $nevenUserDir = $choices.InstallDir
    $functionsDir = Join-Path $nevenUserDir 'functions'
    $graphicsDir  = Join-Path $nevenUserDir 'graphics'
    $promptsDir   = Join-Path $nevenUserDir 'prompts'
    $notebooksDir = Join-Path $nevenUserDir 'notebooks'

    foreach ($dir in @($functionsDir, $graphicsDir, $promptsDir, $notebooksDir)) {
        if (Test-Path $dir) {
            Write-Log "Directory already present: $dir"
        } else {
            try {
                New-Item -Path $dir -ItemType Directory -Force | Out-Null
                Write-Log "Created directory: $dir"
            } catch {
                Write-Log "Failed to create directory ${dir}: $_" -Level ERROR
                $script:HasWarnings = $true
            }
        }
    }
}

function Copy-ExampleFiles {
    [OutputType([void])]
    param(
        [Parameter(Mandatory)][string]$SourceExamplesDir,
        [Parameter(Mandatory)][string]$TargetFunctionsDir
    )
    if (-not (Test-Path $SourceExamplesDir)) {
        Write-Log "Examples source directory not found: $SourceExamplesDir" -Level WARN
        return
    }
    if (-not (Test-Path $TargetFunctionsDir)) {
        New-Item -Path $TargetFunctionsDir -ItemType Directory -Force | Out-Null
    }

    $exampleFiles = Get-ChildItem -Path $SourceExamplesDir -Recurse -File -ErrorAction SilentlyContinue |
                    Where-Object { $_.Extension -match '^\.(r|jl|py)$' }

    foreach ($file in $exampleFiles) {
        $dst = Join-Path $TargetFunctionsDir $file.Name
        if (Test-Path $dst) {
            Write-Log "Preserved existing: $($file.Name)"
        } else {
            try {
                Copy-Item -Path $file.FullName -Destination $dst -Force
                Write-Log "Copied example: $($file.Name)"
            } catch {
                Write-Log "Failed to copy example $($file.Name): $_" -Level ERROR
                $script:HasWarnings = $true
            }
        }
    }
}

function Install-RPackages {
    [OutputType([bool])]
    param([Parameter(Mandatory)][string]$RscriptPath)

    if (-not (Test-Path $RscriptPath)) {
        Write-Log "Rscript.exe not found at $RscriptPath" -Level ERROR
        return $false
    }

    Write-Log 'Installing R packages (this may take several minutes)...'
    Write-Host '  Installing R packages - this may take several minutes...' -ForegroundColor Cyan

    # Batch 1: Core statistical and econometric packages
    $batch1 = @('stargazer','svDialogs','lmtest','sandwich','margins','plm',
                'rpart','rpart.plot','PerformanceAnalytics','tseries','mFilter',
                'e1071','wooldridge','lme4','survival','psych','car','Hmisc','forecast',
                'ResourceSelection','VGAM','usdm','cluster','dummies','writexl')
    $batch1Str = ($batch1 | ForEach-Object { "'$_'" }) -join ','
    $batch1Cmd = "install.packages(c($batch1Str), repos='https://cloud.r-project.org', quiet=TRUE)"

    Write-Host '  [1/4] Installing core statistical packages...' -ForegroundColor White
    Write-Log "R batch 1 (core): $($batch1.Count) packages"
    try {
        & $RscriptPath -e $batch1Cmd 2>&1 | ForEach-Object { Write-Log "  R: $_" }
        Write-Log 'R batch 1 completed'
    } catch {
        Write-Log "R batch 1 failed: $_" -Level ERROR
        $script:HasWarnings = $true
    }

    # Batch 2: Visualization and interactive packages
    $batch2 = @('plotly','htmlwidgets','ggplot2','corrplot','rpivotTable',
                'highcharter','magrittr','rworldmap','RColorBrewer')
    $batch2Str = ($batch2 | ForEach-Object { "'$_'" }) -join ','
    $batch2Cmd = "install.packages(c($batch2Str), repos='https://cloud.r-project.org', quiet=TRUE)"

    Write-Host '  [2/4] Installing visualization packages...' -ForegroundColor White
    Write-Log "R batch 2 (visualization): $($batch2.Count) packages"
    try {
        & $RscriptPath -e $batch2Cmd 2>&1 | ForEach-Object { Write-Log "  R: $_" }
        Write-Log 'R batch 2 completed'
    } catch {
        Write-Log "R batch 2 failed: $_" -Level ERROR
        $script:HasWarnings = $true
    }

    # Batch 3: Text mining and data manipulation packages
    $batch3 = @('jsonlite','tm','SnowballC','wordcloud','fs','tcltk2',
                'NonParRolCor','gtools','pracma','doParallel')
    $batch3Str = ($batch3 | ForEach-Object { "'$_'" }) -join ','
    $batch3Cmd = "install.packages(c($batch3Str), repos='https://cloud.r-project.org', quiet=TRUE)"

    Write-Host '  [3/4] Installing text mining and utility packages...' -ForegroundColor White
    Write-Log "R batch 3 (text/utility): $($batch3.Count) packages"
    try {
        & $RscriptPath -e $batch3Cmd 2>&1 | ForEach-Object { Write-Log "  R: $_" }
        Write-Log 'R batch 3 completed'
    } catch {
        Write-Log "R batch 3 failed: $_" -Level ERROR
        $script:HasWarnings = $true
    }

    # Batch 4: Verification - check all packages loaded correctly
    $allPkgs = $batch1 + $batch2 + $batch3
    $allPkgStr = ($allPkgs | ForEach-Object { "'$_'" }) -join ','
    $verifyCmd = "pkgs <- c($allPkgStr); missing <- pkgs[!sapply(pkgs, requireNamespace, quietly=TRUE)]; if(length(missing)>0) cat('MISSING:', paste(missing, collapse=', ')) else cat('ALL_OK')"

    Write-Host '  [4/4] Verifying package installation...' -ForegroundColor White
    Write-Log 'Verifying R packages...'
    try {
        $output = & $RscriptPath -e $verifyCmd 2>&1 | Out-String
        if ($output -match 'ALL_OK') {
            Write-Log "All $($allPkgs.Count) R packages verified successfully"
            Write-Host "  All $($allPkgs.Count) R packages installed successfully." -ForegroundColor Green
        } else {
            Write-Log "Some R packages may be missing: $output" -Level WARN
            Write-Host "  Some packages may need manual installation. See install.log." -ForegroundColor Yellow
            $script:HasWarnings = $true
        }
    } catch {
        Write-Log "R verification failed: $_" -Level WARN
        $script:HasWarnings = $true
    }

    return $true
}

function Install-JuliaPackages {
    [OutputType([bool])]
    param([Parameter(Mandatory)][string]$JuliaExePath)

    if (-not (Test-Path $JuliaExePath)) {
        Write-Log "julia.exe not found at $JuliaExePath" -Level ERROR
        return $false
    }

    Write-Log 'Installing Julia packages...'
    Write-Host '  Installing Julia packages...' -ForegroundColor Cyan

    # Julia packages used by J4XCL modules
    # LinearAlgebra, Statistics, DelimitedFiles, Dates, Random are all stdlib — no install needed
    # Just verify they load
    $juliaCmd = 'using LinearAlgebra; using Statistics; using DelimitedFiles; using Dates; using Random; println("JULIA_PKGS_OK")'

    Write-Host '  Verifying Julia standard library modules...' -ForegroundColor White
    try {
        $output = & $JuliaExePath -e $juliaCmd 2>&1 | Out-String
        if ($output -match 'JULIA_PKGS_OK') {
            Write-Log 'Julia standard library modules verified (LinearAlgebra, Statistics, DelimitedFiles, Dates, Random)'
            Write-Host '  Julia standard libraries verified.' -ForegroundColor Green
        } else {
            Write-Log "Julia package verification returned unexpected output: $output" -Level WARN
            $script:HasWarnings = $true
        }
    } catch {
        Write-Log "Julia package verification failed: $_" -Level WARN
        $script:HasWarnings = $true
    }

    return $true
}

function Install-PythonPackages {
    [OutputType([bool])]
    param([Parameter(Mandatory)][string]$PythonExePath)

    if (-not (Test-Path $PythonExePath)) {
        Write-Log "python.exe not found at $PythonExePath" -Level ERROR
        return $false
    }

    Write-Log 'Installing Python packages...'
    Write-Host '  Installing Python packages...' -ForegroundColor Cyan

    # Python packages used by NEVEN AI functions
    $pipPkgs = @('openai')

    Write-Host '  Installing pip packages (openai)...' -ForegroundColor White
    Write-Log "Python packages to install: $($pipPkgs -join ', ')"
    try {
        & $PythonExePath -m pip install --quiet --upgrade $pipPkgs 2>&1 | ForEach-Object { Write-Log "  pip: $_" }
        Write-Log 'Python packages installed'
        Write-Host '  Python packages installed.' -ForegroundColor Green
    } catch {
        Write-Log "Python pip install failed: $_" -Level WARN
        Write-Host '  Python package installation failed. You can install manually: pip install openai' -ForegroundColor Yellow
        $script:HasWarnings = $true
    }

    return $true
}

function New-DesktopShortcut {
    [OutputType([void])]
    param(
        [Parameter(Mandatory)][string]$XllPath
    )
    $desktopPath  = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktopPath 'NEVEN.lnk'

    # Find Excel.exe
    $excelPath = ''
    try {
        $regPaths = @(
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe',
            'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\excel.exe'
        )
        foreach ($rp in $regPaths) {
            if (Test-Path $rp) {
                $excelPath = (Get-ItemProperty -Path $rp -Name '(Default)' -ErrorAction SilentlyContinue).'(Default)'
                if ($excelPath -and (Test-Path $excelPath)) { break }
            }
        }
    } catch { }

    if (-not $excelPath -or -not (Test-Path $excelPath)) {
        $fallbacks = @(
            "${env:ProgramFiles}\Microsoft Office\root\Office16\EXCEL.EXE",
            "${env:ProgramFiles(x86)}\Microsoft Office\root\Office16\EXCEL.EXE",
            "${env:ProgramFiles}\Microsoft Office\Office16\EXCEL.EXE"
        )
        foreach ($fb in $fallbacks) {
            if (Test-Path $fb) { $excelPath = $fb; break }
        }
    }

    if (-not $excelPath) {
        Write-Log 'Excel.exe not found - cannot create shortcut' -Level WARN
        $script:HasWarnings = $true
        return
    }

    try {
        $wshell = New-Object -ComObject WScript.Shell
        $shortcut = $wshell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath       = $excelPath
        $shortcut.Arguments        = "/r `"$XllPath`""
        $shortcut.WorkingDirectory = Split-Path $XllPath -Parent
        $shortcut.Description      = 'Open Excel with NEVEN add-in'
        $shortcut.IconLocation     = "$excelPath,0"
        $shortcut.Save()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wshell) | Out-Null
        Write-Log "Desktop shortcut created: $shortcutPath"
    } catch {
        Write-Log "Failed to create desktop shortcut: $_" -Level WARN
        $script:HasWarnings = $true
    }
}

# ============================================================
#  Phase 6: Verification & Uninstaller
# ============================================================

function Test-Installation {
    [OutputType([PSCustomObject])]
    param(
        [Parameter(Mandatory)][string]$TargetDir,
        [Parameter(Mandatory)][string[]]$ExcelVersions
    )
    $results = @()

    # 1. NEVEN64.xll exists
    $xllOk = Test-Path (Join-Path $TargetDir 'NEVEN64.xll')
    $results += [PSCustomObject]@{ Check = 'NEVEN64.xll exists'; Passed = $xllOk }

    # 2. ControlR.exe exists
    $crOk = Test-Path (Join-Path $TargetDir 'ControlR.exe')
    $results += [PSCustomObject]@{ Check = 'ControlR.exe exists'; Passed = $crOk }

    # 3. neven-config.json exists
    $cfgOk = Test-Path (Join-Path $TargetDir 'neven-config.json')
    $results += [PSCustomObject]@{ Check = 'neven-config.json exists'; Passed = $cfgOk }

    # 4. XLL registered in Excel registry
    $xllReg = $false
    foreach ($ver in $ExcelVersions) {
        $regPath = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
        if (Test-Path $regPath) {
            $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
            $openKeys = $props.PSObject.Properties | Where-Object { $_.Name -match '^OPEN\d*$' -and $_.Value -match 'NEVEN' }
            if ($openKeys) { $xllReg = $true; break }
        }
    }
    $results += [PSCustomObject]@{ Check = 'XLL registered in Excel'; Passed = $xllReg }

    # 5. User functions directory exists
    $funcDir = Join-Path $TargetDir 'functions'
    $funcOk = Test-Path $funcDir
    $results += [PSCustomObject]@{ Check = 'User functions directory exists'; Passed = $funcOk }

    foreach ($r in $results) {
        if ($r.Passed) {
            Write-Log "Verification: $($r.Check) - PASS"
        } else {
            Write-Log "Verification: $($r.Check) - FAIL" -Level WARN
        }
    }

    $allPassed = @($results | Where-Object { -not $_.Passed }).Count -eq 0
    return [PSCustomObject]@{ AllPassed = $allPassed; Results = $results }
}

function Show-InstallationResult {
    param(
        [PSCustomObject]$VerificationResult,
        [string]$TargetDir,
        [string]$LogPath
    )
    Write-Host ''
    $passCount = @($VerificationResult.Results | Where-Object { $_.Passed }).Count
    $total     = $VerificationResult.Results.Count

    if ($VerificationResult.AllPassed) {
        Write-Host '  ============================================' -ForegroundColor Green
        Write-Host '   NEVEN installed successfully!' -ForegroundColor Green
        Write-Host '  ============================================' -ForegroundColor Green
        Write-Host ''
        Write-Host "  Install directory: $TargetDir" -ForegroundColor White
        Write-Host '  To test: open Excel and enter  =NEVEN.R("1+1")  - should return 2' -ForegroundColor Cyan
        Write-Host ''
        Write-Log "Verification: $passCount/$total checks passed"
    } else {
        Write-Host '  ============================================' -ForegroundColor Yellow
        Write-Host '   NEVEN installed with warnings' -ForegroundColor Yellow
        Write-Host '  ============================================' -ForegroundColor Yellow
        Write-Host ''
        $failed = $VerificationResult.Results | Where-Object { -not $_.Passed }
        foreach ($f in $failed) {
            Write-Host "   [FAIL] $($f.Check)" -ForegroundColor Red
        }
        Write-Host ''
        Write-Host "  See log for details: $LogPath" -ForegroundColor Yellow
        Write-Log "Verification: $passCount/$total checks passed" -Level WARN
    }
}

function New-Uninstaller {
    [OutputType([void])]
    param(
        [Parameter(Mandatory)][string]$TargetDir,
        [Parameter(Mandatory)][string[]]$ExcelVersions
    )
    $uninstallPath = Join-Path $TargetDir 'Uninstall-NEVEN.ps1'
    $excelVersionsStr = ($ExcelVersions | ForEach-Object { "'$_'" }) -join ','

    # Build uninstaller script as array of lines to avoid here-string nesting issues
    $lines = @()
    $lines += '<#'
    $lines += '.SYNOPSIS'
    $lines += '    NEVEN Uninstaller - Removes all NEVEN components from the system.'
    $lines += '.DESCRIPTION'
    $lines += '    Reverses all changes made by Install-NEVEN.ps1.'
    $lines += '#>'
    $lines += 'param([switch]$Silent)'
    $lines += ''
    $lines += '$ErrorActionPreference = ''Continue'''
    $lines += '$NEVENHome = $PSScriptRoot'
    $lines += '$ExcelVersions = @(' + $excelVersionsStr + ')'
    $lines += ''
    $lines += 'Write-Host '''''
    $lines += 'Write-Host ''  ============================================'' -ForegroundColor Cyan'
    $lines += 'Write-Host ''   NEVEN Uninstaller'' -ForegroundColor Cyan'
    $lines += 'Write-Host ''  ============================================'' -ForegroundColor Cyan'
    $lines += 'Write-Host '''''
    $lines += 'Write-Host "  This will remove NEVEN from: $NEVENHome" -ForegroundColor White'
    $lines += 'Write-Host '''''
    $lines += ''
    $lines += '# Confirmation'
    $lines += 'if (-not $Silent) {'
    $lines += '    $confirm = Read-Host ''  Are you sure you want to uninstall NEVEN? (y/n)'''
    $lines += '    if ($confirm -ne ''y'') {'
    $lines += '        Write-Host ''  Uninstallation cancelled.'' -ForegroundColor Yellow'
    $lines += '        exit 0'
    $lines += '    }'
    $lines += '}'
    $lines += ''
    $lines += '# Check if Excel is running'
    $lines += '$excelProcs = Get-Process -Name ''EXCEL'' -ErrorAction SilentlyContinue'
    $lines += 'if ($excelProcs) {'
    $lines += '    Write-Host ''  Excel is currently running. Please close Excel before uninstalling.'' -ForegroundColor Red'
    $lines += '    if (-not $Silent) {'
    $lines += '        $wait = Read-Host ''  Press Enter after closing Excel, or type "skip" to continue anyway'''
    $lines += '        if ($wait -ne ''skip'') {'
    $lines += '            $excelProcs = Get-Process -Name ''EXCEL'' -ErrorAction SilentlyContinue'
    $lines += '            if ($excelProcs) {'
    $lines += '                Write-Host ''  Excel is still running. Some operations may fail.'' -ForegroundColor Yellow'
    $lines += '            }'
    $lines += '        }'
    $lines += '    }'
    $lines += '}'
    $lines += ''
    $lines += '$removed = @()'
    $lines += ''
    $lines += '# 1. Unregister COM'
    $lines += '$ribbonDll = Join-Path $NEVENHome ''NEVENRibbon.dll'''
    $lines += 'if (Test-Path $ribbonDll) {'
    $lines += '    try {'
    $lines += '        Start-Process -FilePath ''regsvr32'' -ArgumentList "/u /s `"$ribbonDll`"" -Wait -NoNewWindow -ErrorAction SilentlyContinue'
    $lines += '        $removed += ''COM registration (regsvr32 /u)'''
    $lines += '    } catch { Write-Host "  Warning: Failed to unregister COM: $_" -ForegroundColor Yellow }'
    $lines += '}'
    $lines += ''
    $lines += '# 2. Remove XLL registry entries'
    $lines += 'foreach ($ver in $ExcelVersions) {'
    $lines += '    $regPath = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"'
    $lines += '    if (Test-Path $regPath) {'
    $lines += '        $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue'
    $lines += '        $openKeys = $props.PSObject.Properties | Where-Object { $_.Name -match ''^OPEN\d*$'' -and $_.Value -match ''NEVEN'' }'
    $lines += '        foreach ($key in $openKeys) {'
    $lines += '            Remove-ItemProperty -Path $regPath -Name $key.Name -ErrorAction SilentlyContinue'
    $lines += '            $removed += "XLL entry $($key.Name) (Excel $ver)"'
    $lines += '        }'
    $lines += '    }'
    $lines += '}'
    $lines += ''
    $lines += '# 3. Remove Ribbon registry key'
    $lines += '$ribbonKey = ''HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect'''
    $lines += 'if (Test-Path $ribbonKey) {'
    $lines += '    Remove-Item -Path $ribbonKey -Recurse -Force -ErrorAction SilentlyContinue'
    $lines += '    $removed += ''Ribbon registry key'''
    $lines += '}'
    $lines += ''
    $lines += '# 4. User scripts'
    $lines += '$userNevenDir = Join-Path ([Environment]::GetFolderPath(''MyDocuments'')) ''NEVEN'''
    $lines += 'if (Test-Path $userNevenDir) {'
    $lines += '    $deleteUser = ''n'''
    $lines += '    if (-not $Silent) {'
    $lines += '        Write-Host '''''
    $lines += '        Write-Host "  User scripts found at: $userNevenDir" -ForegroundColor White'
    $lines += '        $deleteUser = Read-Host ''  Delete user scripts and graphics? This cannot be undone. (y/n) [n]'''
    $lines += '    }'
    $lines += '    if ($deleteUser -eq ''y'') {'
    $lines += '        Remove-Item -Path $userNevenDir -Recurse -Force -ErrorAction SilentlyContinue'
    $lines += '        $removed += ''User scripts directory'''
    $lines += '    } else {'
    $lines += '        Write-Host "  Preserved user scripts at $userNevenDir" -ForegroundColor Green'
    $lines += '    }'
    $lines += '}'
    $lines += ''
    $lines += '# 5. Quarto junction'
    $lines += 'if (Test-Path ''C:\Quarto'') {'
    $lines += '    $item = Get-Item ''C:\Quarto'' -Force -ErrorAction SilentlyContinue'
    $lines += '    if ($item -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {'
    $lines += '        try {'
    $lines += '            cmd /c rmdir ''C:\Quarto'' 2>$null'
    $lines += '            $removed += ''Quarto junction (C:\Quarto)'''
    $lines += '        } catch {'
    $lines += '            Write-Host "  Warning: Could not remove Quarto junction: $_" -ForegroundColor Yellow'
    $lines += '        }'
    $lines += '    }'
    $lines += '}'
    $lines += ''
    $lines += '# 6. Desktop shortcut'
    $lines += '$shortcutPath = Join-Path ([Environment]::GetFolderPath(''Desktop'')) ''NEVEN.lnk'''
    $lines += 'if (Test-Path $shortcutPath) {'
    $lines += '    Remove-Item -Path $shortcutPath -Force -ErrorAction SilentlyContinue'
    $lines += '    $removed += ''Desktop shortcut'''
    $lines += '}'
    $lines += ''
    $lines += '# 7. Remove NEVEN_Home directory via deferred cleanup'
    $lines += '$tempScript = Join-Path $env:TEMP ''neven-cleanup.ps1'''
    $lines += '$cleanupLines = @('
    $lines += '    "Start-Sleep -Seconds 2",'
    $lines += '    "if (Test-Path ''$NEVENHome'') { Remove-Item -Path ''$NEVENHome'' -Recurse -Force -ErrorAction SilentlyContinue }",'
    $lines += '    "Remove-Item -Path ''$tempScript'' -Force -ErrorAction SilentlyContinue"'
    $lines += ')'
    $lines += 'Set-Content -Path $tempScript -Value ($cleanupLines -join "`r`n") -Encoding UTF8'
    $lines += ''
    $lines += '# Summary'
    $lines += 'Write-Host '''''
    $lines += 'Write-Host ''  ============================================'' -ForegroundColor Green'
    $lines += 'Write-Host ''   NEVEN Uninstallation Summary'' -ForegroundColor Green'
    $lines += 'Write-Host ''  ============================================'' -ForegroundColor Green'
    $lines += 'foreach ($item in $removed) {'
    $lines += '    Write-Host "   [OK] Removed: $item" -ForegroundColor Green'
    $lines += '}'
    $lines += 'Write-Host "   [OK] NEVEN directory will be removed: $NEVENHome" -ForegroundColor Green'
    $lines += 'Write-Host '''''
    $lines += 'Write-Host ''  NEVEN has been uninstalled.'' -ForegroundColor White'
    $lines += 'Write-Host '''''
    $lines += ''
    $lines += '# Launch deferred cleanup and exit'
    $lines += 'Start-Process -FilePath ''powershell.exe'' -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$tempScript`"" -WindowStyle Hidden'
    $lines += 'exit 0'

    try {
        Set-Content -Path $uninstallPath -Value ($lines -join "`r`n") -Encoding UTF8
        Write-Log "Uninstaller generated: $uninstallPath"
    } catch {
        Write-Log "Failed to generate uninstaller: $_" -Level ERROR
        $script:HasWarnings = $true
    }
}

# ============================================================
#  Config Patching
# ============================================================

function Update-NEVENConfig {
    param(
        [Parameter(Mandatory)][string]$ConfigPath,
        [PSCustomObject]$RInfo,
        [PSCustomObject]$JuliaInfo,
        [PSCustomObject]$PythonInfo
    )
    if (-not (Test-Path $ConfigPath)) {
        Write-Log "Config file not found for patching: $ConfigPath" -Level WARN
        return
    }
    try {
        $json = Get-Content -Path $ConfigPath -Raw -Encoding UTF8
        if ($RInfo.Found) {
            $escapedPath = $RInfo.Path -replace '\\', '\\\\'
            $json = $json -replace '("R"\s*:\s*\{[^}]*"home"\s*:\s*)"[^"]*"', ('$1"' + $escapedPath + '"')
        }
        if ($JuliaInfo.Found) {
            $escapedPath = $JuliaInfo.Path -replace '\\', '\\\\'
            $json = $json -replace '("Julia"\s*:\s*\{[^}]*"home"\s*:\s*)"[^"]*"', ('$1"' + $escapedPath + '"')
        }
        if ($PythonInfo.Found) {
            $escapedPath = $PythonInfo.Path -replace '\\', '\\\\'
            $json = $json -replace '("Python"\s*:\s*\{[^}]*"home"\s*:\s*)"[^"]*"', ('$1"' + $escapedPath + '"')
        }
        Set-Content -Path $ConfigPath -Value $json -Encoding UTF8 -NoNewline
        Write-Log 'Patched neven-config.json with detected runtime paths'
    } catch {
        Write-Log "Failed to patch neven-config.json: $_" -Level WARN
        $script:HasWarnings = $true
    }
}

# ============================================================
#  Main Execution Flow
# ============================================================

Write-Host ''
Write-Host '  ============================================' -ForegroundColor Cyan
Write-Host '   NEVEN Installer' -ForegroundColor Cyan
Write-Host '   R, Julia & Python to Excel' -ForegroundColor Cyan
Write-Host '  ============================================' -ForegroundColor Cyan
Write-Host ''

# --- Phase 1: Pre-flight Checks ---
Write-Host '  Phase 1: Pre-flight checks...' -ForegroundColor White

if (-not (Test-WindowsVersion)) {
    Write-Host '  ERROR: This installer requires Windows 10 or later (64-bit).' -ForegroundColor Red
    Exit-Installer 1
}
if (-not (Test-PowerShellVersion)) {
    Write-Host '  ERROR: This installer requires PowerShell 5.1 or later.' -ForegroundColor Red
    Exit-Installer 1
}

# Validate Dist directory
if (-not (Test-Path $DistDir)) {
    Write-Host "  ERROR: Distribution directory not found: $DistDir" -ForegroundColor Red
    Write-Host '  Ensure the Dist/ folder is present alongside this script.' -ForegroundColor Red
    Write-Host "  (Searched at: $DistDir)" -ForegroundColor DarkGray
    Exit-Installer 1
}
$distXll = Join-Path $DistDir 'NEVEN64.xll'
if (-not (Test-Path $distXll)) {
    Write-Host "  ERROR: NEVEN64.xll not found in $DistDir" -ForegroundColor Red
    Exit-Installer 1
}

$rInfo        = Find-R
$juliaInfo    = Find-Julia
$pythonInfo   = Find-Python
$excelVers    = Find-ExcelVersions
$existingInst = Find-ExistingInstall -TargetPath $InstallDir

Show-PreflightSummary -RInfoRef ([ref]$rInfo) -JuliaInfoRef ([ref]$juliaInfo) -PythonInfoRef ([ref]$pythonInfo) `
                      -ExcelVersions $excelVers -ExistingInstall $existingInst

# --- Phase 2: User Choices ---
Write-Host '  Phase 2: Configuration...' -ForegroundColor White
$choices = Get-UserChoices -RInfo $rInfo -JuliaInfo $juliaInfo -ExistingInstall $existingInst

# Initialize log file now that install dir is confirmed
$logPath = Join-Path $choices.InstallDir 'install.log'
if (-not (Test-Path $choices.InstallDir)) {
    New-Item -Path $choices.InstallDir -ItemType Directory -Force | Out-Null
}
Initialize-LogFile -Path $logPath

Write-Log 'Installation started'
Write-Log "Install directory: $($choices.InstallDir)"
Write-Log "Dist directory: $DistDir"
Write-Log "Silent mode: $Silent"
Write-Log "Is update: $($choices.IsUpdate)"

# Re-log pre-flight results into the log file
if ($rInfo.Found)      { Write-Log "R $($rInfo.Version) at $($rInfo.Path)" }
else                   { Write-Log 'R not found' -Level WARN }
if ($juliaInfo.Found)  { Write-Log "Julia $($juliaInfo.Version) at $($juliaInfo.Path)" }
else                   { Write-Log 'Julia not found' -Level WARN }
if ($pythonInfo.Found) { Write-Log "Python $($pythonInfo.Version) at $($pythonInfo.Path)" }
else                   { Write-Log 'Python not found' -Level WARN }

# --- Phase 3: File Deployment ---
Write-Host ''
Write-Host '  Phase 3: Deploying files...' -ForegroundColor White
$deployOk = Install-NEVENFiles -TargetDir $choices.InstallDir -SourceDir $DistDir -IsUpdate $choices.IsUpdate
if (-not $deployOk) {
    Write-Log 'Critical file deployment failed - aborting' -Level ERROR
    Write-Host '  ERROR: Failed to deploy critical files. See install.log.' -ForegroundColor Red
    Close-LogFile
    Exit-Installer 1
}

# Patch config with detected paths
$configPath = Join-Path $choices.InstallDir 'neven-config.json'
Update-NEVENConfig -ConfigPath $configPath -RInfo $rInfo -JuliaInfo $juliaInfo -PythonInfo $pythonInfo

# --- Phase 4: Registration ---
Write-Host ''
Write-Host '  Phase 4: Registering components...' -ForegroundColor White
$xllPath = Join-Path $choices.InstallDir 'NEVEN64.xll'
if ($excelVers.Count -gt 0) {
    Register-XLL -XllPath $xllPath -ExcelVersions $excelVers
} else {
    Write-Log 'No Excel versions detected - skipping XLL registration' -Level WARN
}

$ribbonDll = Join-Path $choices.InstallDir 'NEVENRibbon.dll'
Register-RibbonCOM -DllPath $ribbonDll

# Add C:\NEVEN as Office Trusted Location
Register-TrustedLocation -Path $choices.InstallDir -ExcelVersions $excelVers

New-QuartoJunction

# --- Phase 5: User Setup ---
Write-Host ''
Write-Host '  Phase 5: User setup...' -ForegroundColor White
Initialize-UserDirectories

$examplesDir  = Join-Path $choices.InstallDir 'examples'
$functionsDir = Join-Path $choices.InstallDir 'functions'
Copy-ExampleFiles -SourceExamplesDir $examplesDir -TargetFunctionsDir $functionsDir

# Copy default AI prompt templates (preserve user modifications)
$srcPromptsDir = Join-Path $PSScriptRoot 'prompts'
$dstPromptsDir = Join-Path $choices.InstallDir 'prompts'
if (Test-Path $srcPromptsDir) {
    $promptFiles = Get-ChildItem -Path $srcPromptsDir -Filter '*.txt' -File -ErrorAction SilentlyContinue
    foreach ($pf in $promptFiles) {
        $dst = Join-Path $dstPromptsDir $pf.Name
        if (Test-Path $dst) {
            Write-Log "Preserved existing prompt: $($pf.Name)"
        } else {
            try {
                Copy-Item -Path $pf.FullName -Destination $dst -Force
                Write-Log "Copied prompt template: $($pf.Name)"
            } catch {
                Write-Log "Failed to copy prompt $($pf.Name): $_" -Level ERROR
                $script:HasWarnings = $true
            }
        }
    }
} else {
    Write-Log 'Prompts source directory not found - skipping AI prompt deployment' -Level WARN
}

if ($choices.InstallRPackages -and $rInfo.Found) {
    $rscriptExe = Join-Path $rInfo.Path 'bin\Rscript.exe'
    Install-RPackages -RscriptPath $rscriptExe
} else {
    if (-not $rInfo.Found) {
        Write-Log 'R not available - skipping R package installation'
    } else {
        Write-Log 'R package installation skipped by user'
    }
}

# Julia packages (stdlib verification)
if ($juliaInfo.Found -and $juliaInfo.Adequate) {
    $juliaExe = Join-Path $juliaInfo.Path 'bin\julia.exe'
    if (-not (Test-Path $juliaExe)) {
        $juliaExe = (Get-Command julia -ErrorAction SilentlyContinue).Source
    }
    if ($juliaExe -and (Test-Path $juliaExe)) {
        Install-JuliaPackages -JuliaExePath $juliaExe
    }
} else {
    Write-Log 'Julia not available - skipping Julia package verification'
}

# Python packages (openai for AI functions)
if ($pythonInfo.Found -and $pythonInfo.Adequate) {
    $pythonExe = Join-Path $pythonInfo.Path 'python.exe'
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    }
    if ($pythonExe -and (Test-Path $pythonExe)) {
        Install-PythonPackages -PythonExePath $pythonExe
    }
} else {
    Write-Log 'Python not available - skipping Python package installation'
}

if ($choices.CreateShortcut) {
    New-DesktopShortcut -XllPath $xllPath
}

# Deploy user documentation to Documents\NEVEN\docs\
Write-Host '  Deploying documentation...' -ForegroundColor White
$docsSource = Join-Path $PSScriptRoot '..\docs'
if (-not (Test-Path $docsSource)) { $docsSource = Join-Path $choices.InstallDir 'docs' }
$docsScript = Join-Path $PSScriptRoot 'Deploy-UserDocs.ps1'
if (Test-Path $docsScript) {
    & $docsScript -SourceDir $docsSource -TargetDir (Join-Path $choices.InstallDir 'docs')
} else {
    Write-Log 'Deploy-UserDocs.ps1 not found - skipping docs deployment' -Level WARN
}

# Deploy notebooks to Documents\NEVEN\notebooks\
$nbSource = Join-Path $choices.InstallDir 'notebooks'
$nbTarget = Join-Path $choices.InstallDir 'notebooks'
if (Test-Path $nbSource) {
    if (-not (Test-Path $nbTarget)) { New-Item -ItemType Directory -Path $nbTarget -Force | Out-Null }
    Copy-Item "$nbSource\*" $nbTarget -Force -Recurse -ErrorAction SilentlyContinue
    Write-Log "Notebooks deployed to $nbTarget"
    Write-Host "  Notebooks deployed to $nbTarget" -ForegroundColor White
}

# --- Phase 6: Julia Sysimage (Optional) ---
Write-Host ''
if ($juliaInfo.Found -and $juliaInfo.Adequate) {
    $sysimgPath = Join-Path $choices.InstallDir 'neven_julia.dll'
    $buildScript = Join-Path $choices.InstallDir 'scripts\build-julia-sysimage.jl'
    
    if (-not (Test-Path $sysimgPath)) {
        Write-Host '  Phase 6: Julia Sysimage (optional, recommended)' -ForegroundColor White
        Write-Host ''
        Write-Host '   La sysimage de Julia elimina el tiempo de espera de 1-5 minutos' -ForegroundColor Cyan
        Write-Host '   en la primera llamada de cada sesion de Excel.' -ForegroundColor Cyan
        Write-Host '   Generarla tarda 5-10 minutos pero solo se hace una vez.' -ForegroundColor Cyan
        Write-Host ''
        
        $buildSysimage = $true
        if (-not $Silent) {
            $resp = Read-Host '   Desea generar la sysimage de Julia ahora? (S/n, recomendado: S)'
            if ($resp -match '^[Nn]') { $buildSysimage = $false }
        }
        
        if ($buildSysimage) {
            Write-Host '   Generando sysimage (esto tarda 5-10 minutos)...' -ForegroundColor Yellow
            Write-Log 'Starting Julia sysimage build...'
            
            $juliaExe = Join-Path $juliaInfo.Path 'bin\julia.exe'
            if (-not (Test-Path $juliaExe)) {
                # Try the path directly if it points to the bin dir
                $juliaExe = Get-Command julia -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
            }
            
            if ($juliaExe -and (Test-Path $juliaExe)) {
                $srcScript = Join-Path $PSScriptRoot '..\scripts\build-julia-sysimage.jl'
                if (Test-Path $srcScript) {
                    # Copy script to install dir
                    $scriptsDir = Join-Path $choices.InstallDir 'scripts'
                    if (-not (Test-Path $scriptsDir)) { New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null }
                    Copy-Item $srcScript $buildScript -Force -ErrorAction SilentlyContinue
                }
                
                if (Test-Path $buildScript) {
                    try {
                        $proc = Start-Process -FilePath $juliaExe -ArgumentList $buildScript -Wait -PassThru -NoNewWindow
                        if ($proc.ExitCode -eq 0 -and (Test-Path $sysimgPath)) {
                            $sizeMB = [math]::Round((Get-Item $sysimgPath).Length / 1MB)
                            Write-Host "   Sysimage generada: $sysimgPath ($sizeMB MB)" -ForegroundColor Green
                            Write-Log "Julia sysimage built successfully ($sizeMB MB)"
                        } else {
                            Write-Host '   No se pudo generar la sysimage (Julia arrancara con JIT)' -ForegroundColor Yellow
                            Write-Log 'Julia sysimage build failed' -Level WARN
                        }
                    } catch {
                        Write-Host "   Error al generar sysimage: $_" -ForegroundColor Yellow
                        Write-Log "Julia sysimage error: $_" -Level WARN
                    }
                } else {
                    Write-Host '   Script de sysimage no encontrado' -ForegroundColor Yellow
                    Write-Log 'build-julia-sysimage.jl not found' -Level WARN
                }
            } else {
                Write-Host '   julia.exe no encontrado' -ForegroundColor Yellow
                Write-Log 'julia.exe not found for sysimage build' -Level WARN
            }
        } else {
            Write-Host '   Sysimage omitida. Puede generarla despues con:' -ForegroundColor Gray
            Write-Host "   julia $buildScript" -ForegroundColor Gray
            Write-Log 'User declined sysimage build'
        }
    } else {
        Write-Host '  Phase 6: Julia sysimage already exists - skipping' -ForegroundColor Gray
        Write-Log 'Julia sysimage already exists, skipping build'
    }
} else {
    Write-Host '  Phase 6: Julia not available - sysimage skipped' -ForegroundColor Gray
}

# --- Phase 7: Verification ---
Write-Host ''
Write-Host '  Phase 7: Verification...' -ForegroundColor White
$verification = Test-Installation -TargetDir $choices.InstallDir -ExcelVersions $excelVers
Show-InstallationResult -VerificationResult $verification -TargetDir $choices.InstallDir -LogPath $logPath

# Generate uninstaller
New-Uninstaller -TargetDir $choices.InstallDir -ExcelVersions $excelVers

# Close log
Close-LogFile

Write-Host "  Log file: $logPath" -ForegroundColor Gray
Write-Host ''
Exit-Installer 0
