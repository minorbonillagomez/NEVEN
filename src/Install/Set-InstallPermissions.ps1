<#
.SYNOPSIS
    Endurece y audita los permisos del directorio de instalacion de NEVEN.

.DESCRIPTION
    El directorio por defecto es C:\NEVEN, y un directorio creado bajo C:\ hereda de
    la raiz del disco el ACE 'NT AUTHORITY\Authenticated Users:(OI)(CI)(IO)(M)':
    comprobado con icacls sobre una instalacion real, los ficheros de dentro quedan
    modificables por cualquier usuario autenticado. Entre ellos estan los que NEVEN
    ejecuta sin que el usuario los invoque (startup\*.py, functions\*.R, TaskPane\*,
    los ejecutables de los motores), de modo que cualquier usuario de la maquina
    podria sustituir uno y esperar a que NEVEN lo ejecutase.

    El script declara dos clases de ruta y las aplica con icacls:

      - Clase codigo: lo que NEVEN ejecuta o carga. Pierde la herencia de la raiz
        del disco y queda en F para Administradores y SYSTEM, y en RX para los
        usuarios autenticados.
      - Clase datos: lo que NEVEN escribe desde la sesion del usuario, sin elevar.
        Conserva la escritura, con el motivo declarado en la tabla de abajo.

    Se usan SIDs conocidos y no nombres, porque los grupos estan localizados.

    Toda operacion de permisos comprueba su codigo de salida y lo registra: un
    endurecimiento que no se pudo aplicar se informa, nunca se omite en silencio.

.PARAMETER InstallDir
    Directorio de instalacion. Por defecto C:\NEVEN.

.PARAMETER AuditOnly
    No cambia nada: mide la DACL real de cada ruta y reporta lo que queda
    escribible por usuarios sin privilegios.

.PARAMETER Probe
    Comprueba si el endurecimiento es posible antes de desplegar: crea
    $InstallDir\.neven-acl-probe, le aplica el modelo de ACE de la raiz, lo audita
    y lo borra. No toca el resto del directorio.

.PARAMETER Json
    Emite el resultado como JSON en vez de texto, sin ninguna otra salida.

.OUTPUTS
    Codigo de salida 0 sin hallazgos, 1 con hallazgos de ACL, 2 si alguna
    operacion de permisos fallo.

.EXAMPLE
    powershell -NoProfile -File Set-InstallPermissions.ps1 -InstallDir C:\NEVEN
    powershell -NoProfile -File Set-InstallPermissions.ps1 -InstallDir C:\NEVEN -AuditOnly
    powershell -NoProfile -File Set-InstallPermissions.ps1 -InstallDir C:\NEVEN -Probe
#>
[CmdletBinding()]
param(
    [string]$InstallDir = 'C:\NEVEN',
    [switch]$AuditOnly,
    [switch]$Probe,
    [switch]$Json
)

$ErrorActionPreference = 'Continue'

$script:Operations = @()
$script:Findings   = @()

# ============================================================
#  Tabla declarada
# ============================================================

# Clase datos: rutas que NEVEN escribe desde la sesion del usuario, sin elevar.
# Conservan la escritura de los usuarios autenticados. Ninguna entrada de esta
# tabla concede un permiso que la DACL heredada de C:\ no concediese ya.
$script:DataDirs = @(
    @{ Path = 'functions';     Reason = '/api/functions/create, /api/script/save y el FileWatchService escriben los .R y sus sidecars' }
    @{ Path = 'prompts';       Reason = 'el guardado de prompts escribe aqui, y tambien en backup\ y custom\' }
    @{ Path = 'logs';          Reason = 'logs del servidor HTTP y de los motores' }
    @{ Path = 'temp';          Reason = 'ficheros intermedios de las llamadas' }
    @{ Path = 'graphics';      Reason = 'graficos que generan R, Julia y Python' }
    @{ Path = 'notebooks';     Reason = 'notebooks de Pluto y Quarto del usuario' }
    @{ Path = 'data';          Reason = 'indice del RAG, creado en el primer uso' }
    @{ Path = 'workspace';     Reason = 'viewersDir por defecto del visor HTML' }
    @{ Path = 'webview2-data'; Reason = 'perfil de WebView2' }
    @{ Path = 'crashes';       Reason = 'volcados del CrashHandler' }
    @{ Path = 'user-charts';   Reason = 'graficos que el usuario guarda desde Studio' }
    @{ Path = 'bridge';        Reason = 'canal de ficheros entre el TaskPane y el XLL' }
)

# Ficheros de la clase datos. Reciben (RX,W) y no (M): escribirlos es abrirlos en
# sitio, no hace falta DELETE, y hoy tienen (M) heredado, asi que el cambio
# restringe tambien aqui.
$script:DataFiles = @(
    @{ Path = 'neven-config.json';          Reason = 'Studio > Settings > Motores y -ConfigureOnly lo reescriben sin elevar' }
    @{ Path = 'neven-config.json.bak';      Reason = 'backup que escribe el propio guardado de la configuracion' }
    @{ Path = 'install.log';                Reason = '-ConfigureOnly reabre el log de la instalacion' }
    @{ Path = 'packages-status-cache.json'; Reason = 'cache de estado de paquetes del package_manager_service' }
    @{ Path = 'neven.log';                  Reason = 'log del package_manager_service' }
)

# Lo que sigue expuesto despues de endurecer. Se imprime siempre, porque la
# politica del producto es que lo que falta se dice con su motivo.
$script:ResidualExposure = @(
    'functions\ y prompts\ siguen escribibles por cualquier usuario autenticado, y NEVEN carga functions\*.R en R dentro de Excel. Cerrarlo exige una decision de producto sobre /api/functions/create, /api/script/save y el FileWatchService.'
    'neven-config.json sigue escribible: es el fichero por el que se puede apagar el sandbox, y el que reescriben Studio > Settings > Motores y -ConfigureOnly.'
    'certs\localhost.key deja de ser escribible, pero sigue siendo legible por usuarios autenticados: el servidor HTTP lo lee sin elevar.'
    'studio.pid y neven_julia.version ya no se pueden crear en la raiz desde una sesion sin privilegios, asi que generar la sysimage de Julia despues de instalar necesita una consola elevada.'
    'Desinstalar sin elevacion ya no borra los ficheros endurecidos: el desinstalador avisa de que C:\NEVEN puede quedarse.'
)

# ACE de la raiz, heredables, que resuelven todo el arbol de la clase codigo: los
# hijos que hoy traen ACE heredados (I) los pierden y reciben estos.
#   S-1-5-32-544  Administradores
#   S-1-5-18      SYSTEM
#   S-1-5-11      Usuarios autenticados, solo leer y ejecutar
#   S-1-3-0       CREATOR OWNER sobre objetos nuevos: sin este ACE, /inheritance:r
#                 lo borraria y un directorio creado en tiempo de ejecucion no
#                 seria escribible por quien lo creo
$script:RootGrants = @(
    '*S-1-5-32-544:(OI)(CI)(F)'
    '*S-1-5-18:(OI)(CI)(F)'
    '*S-1-5-11:(OI)(CI)(RX)'
    '*S-1-3-0:(OI)(CI)(IO)(F)'
)

# Crear subdirectorios en la raiz, sin propagar: es lo que necesitan los
# os.makedirs de tiempo de ejecucion. No se concede (WD): anadir ficheros al
# directorio de los ejecutables es plantado de DLL junto a ControlR.exe.
$script:RootAppendGrant = '*S-1-5-11:(AD)'

$script:PrivilegedSids = @(
    'S-1-5-32-544'  # Administradores
    'S-1-5-18'      # SYSTEM
    'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'  # TrustedInstaller
)

# SIDs que conceden a quien sea dueno del objeto, no a una cuenta concreta:
# CREATOR OWNER y OWNER RIGHTS. No amplian lo que la propiedad ya permite (el
# dueno tiene WRITE_DAC implicito), asi que la auditoria los reporta por la via
# de la propiedad y no como una concesion mas.
$script:OwnerEquivalentSids = @('S-1-3-0', 'S-1-3-4')

$FSR = [System.Security.AccessControl.FileSystemRights]

# Mascara de escritura: lo que permite cambiar lo que NEVEN ejecuta.
# WriteAttributes y WriteExtendedAttributes quedan fuera a proposito: no permiten
# cambiar el contenido de un fichero ni sustituirlo.
$script:WriteMask = [int]($FSR::WriteData -bor $FSR::AppendData -bor $FSR::Delete -bor
                          $FSR::DeleteSubdirectoriesAndFiles -bor $FSR::ChangePermissions -bor
                          $FSR::TakeOwnership)
$script:DataFileMask = [int]($FSR::WriteData -bor $FSR::AppendData)
$script:RootMask     = [int]$FSR::CreateDirectories
$script:DeleteMask   = [int]($FSR::Delete -bor $FSR::DeleteSubdirectoriesAndFiles)

# ============================================================
#  Helpers
# ============================================================

function Add-Finding {
    param(
        [Parameter(Mandatory)][string]$Class,
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Detail
    )
    $script:Findings += [pscustomobject]@{ Class = $Class; Path = $Path; Detail = $Detail }
}

function Invoke-Icacls {
    <#
      Unico punto por el que pasa cualquier operacion de permisos: captura la
      salida y $LASTEXITCODE, los registra, y convierte un codigo distinto de cero
      en un hallazgo OperationFailed. Es lo que hace que un fallo se detecte en vez
      de pasar inadvertido.
    #>
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$Purpose
    )
    $exe = Join-Path $env:SystemRoot 'System32\icacls.exe'
    $output = ''
    $code = 0
    try {
        # icacls escribe el motivo del fallo en stderr. Se convierte a texto en vez
        # de dejarlo como ErrorRecord para que el motivo quede legible en el informe.
        $output = (& $exe @(@($Path) + $Arguments) 2>&1 |
                   ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { $_ } } |
                   Out-String)
        $code = $LASTEXITCODE
    } catch {
        $output = $_.Exception.Message
        $code = -1
    }
    $script:Operations += [pscustomobject]@{
        Path     = $Path
        Purpose  = $Purpose
        Args     = ($Arguments -join ' ')
        ExitCode = $code
        Output   = $output.Trim()
        Ok       = ($code -eq 0)
    }
    if ($code -ne 0) {
        Add-Finding -Class 'OperationFailed' -Path $Path `
                    -Detail "icacls ($Purpose) devolvio ${code}: $($output.Trim())"
    }
    return $code
}

function Reset-InheritedAcl {
    <#
      Devuelve una ruta a la herencia de su padre y le quita los ACE explicitos.
      Lo usa el sondeo para poder borrar su propio directorio: una vez endurecido,
      ni su dueno tiene DELETE sobre el, y un sondeo que se deja el directorio
      detras entra luego en la auditoria como una ruta mas.
    #>
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    # Con icacls /reset y no con Set-Acl: Set-Acl escribe el descriptor completo y
    # pide SeSecurityPrivilege, que una sesion sin elevar no tiene, mientras que
    # /reset solo toca la DACL y al dueno le basta su WRITE_DAC implicito.
    Invoke-Icacls -Path $Path -Purpose 'devolver el sondeo a la herencia de su padre' `
                  -Arguments @('/reset', '/T', '/C', '/Q') | Out-Null
}

function Get-RelativePath {
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$Full)
    $root = $Root.TrimEnd('\')
    if ($Full.Length -le $root.Length) { return '' }
    return $Full.Substring($root.Length).TrimStart('\')
}

function Get-PathPolicy {
    <#
      Clasifica una ruta relativa contra la tabla declarada y devuelve la mascara
      de escritura que un usuario sin privilegios puede tener sobre ella.
    #>
    param([string]$Relative)
    if ([string]::IsNullOrEmpty($Relative)) {
        return [pscustomobject]@{
            Class = 'root'; AllowedMask = $script:RootMask
            Reason = 'la raiz admite crear subdirectorios (os.makedirs de tiempo de ejecucion), no anadir ficheros'
        }
    }
    foreach ($entry in $script:DataDirs) {
        if ($Relative -eq $entry.Path -or $Relative -like ($entry.Path + '\*')) {
            return [pscustomobject]@{
                Class = 'data'; AllowedMask = $script:WriteMask; Reason = $entry.Reason
            }
        }
    }
    foreach ($entry in $script:DataFiles) {
        if ($Relative -eq $entry.Path) {
            return [pscustomobject]@{
                Class = 'data'; AllowedMask = $script:DataFileMask; Reason = $entry.Reason
            }
        }
    }
    return [pscustomobject]@{
        Class = 'code'; AllowedMask = 0; Reason = 'NEVEN lo ejecuta o lo carga'
    }
}

function Resolve-RuleSid {
    param([Parameter(Mandatory)]$Rule)
    $id = $Rule.IdentityReference
    if ($id -is [System.Security.Principal.SecurityIdentifier]) { return $id.Value }
    try { return $id.Translate([System.Security.Principal.SecurityIdentifier]).Value }
    catch { return $id.Value }
}

function Get-WriteRights {
    param([Parameter(Mandatory)]$Rights)
    $value = [int]$Rights
    # GENERIC_ALL y GENERIC_WRITE: algunas DACL llevan los bits genericos sin mapear.
    if (($value -band 0x10000000) -ne 0 -or ($value -band 0x40000000) -ne 0) {
        return $script:WriteMask
    }
    return ($value -band $script:WriteMask)
}

function Get-AuditTargets {
    <#
      Recorre el arbol sin seguir reparse points, para que un junction no lleve la
      auditoria fuera del directorio de instalacion.
    #>
    param([Parameter(Mandatory)][string]$Root)
    $targets = @([pscustomobject]@{ Path = $Root; IsContainer = $true })
    $pending = New-Object System.Collections.Stack
    $pending.Push($Root)
    while ($pending.Count -gt 0) {
        $dir = $pending.Pop()
        try {
            $children = @(Get-ChildItem -LiteralPath $dir -Force -ErrorAction Stop)
        } catch {
            Add-Finding -Class 'OperationFailed' -Path $dir `
                        -Detail "no se pudo enumerar para auditarlo: $($_.Exception.Message)"
            continue
        }
        foreach ($child in $children) {
            $targets += [pscustomobject]@{ Path = $child.FullName; IsContainer = $child.PSIsContainer }
            $isLink = ($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
            if ($child.PSIsContainer -and -not $isLink) { $pending.Push($child.FullName) }
        }
    }
    return $targets
}

# ============================================================
#  Auditoria
# ============================================================

function Invoke-AclAudit {
    <#
      Mide la DACL real de cada ruta con Get-Acl, no el texto de icacls, asi que no
      depende del idioma de los grupos. Devuelve cuantas rutas se midieron.
    #>
    param(
        [Parameter(Mandatory)][string]$Root,
        [switch]$IncludeOwner,
        [switch]$IncludeParent
    )
    $rootFull = $Root.TrimEnd('\')
    $checked = 0
    $codeOwners = @{}

    foreach ($item in (Get-AuditTargets -Root $rootFull)) {
        $relative = Get-RelativePath -Root $rootFull -Full $item.Path
        $policy = Get-PathPolicy -Relative $relative
        try {
            $acl = Get-Acl -LiteralPath $item.Path -ErrorAction Stop
        } catch {
            Add-Finding -Class 'OperationFailed' -Path $item.Path `
                        -Detail "no se pudo leer su DACL: $($_.Exception.Message)"
            continue
        }
        $checked++
        $ownerSid = ''
        try { $ownerSid = $acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value } catch { }

        foreach ($rule in $acl.Access) {
            if ($rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow) { continue }
            # Un ACE InheritOnly no concede nada sobre el objeto que lo lleva: es lo
            # que hace valido el ACE de CREATOR OWNER de la raiz.
            if (([int]$rule.PropagationFlags -band [int][System.Security.AccessControl.PropagationFlags]::InheritOnly) -ne 0) { continue }
            $sid = Resolve-RuleSid -Rule $rule
            if ($script:PrivilegedSids -contains $sid) { continue }
            # El ACE del dueno no concede nada que la propiedad no conceda ya: el
            # dueno tiene WRITE_DAC implicito y puede reescribir la DACL cuando
            # quiera. Se reporta una sola vez como OwnedByNonPrivileged, en vez de
            # una vez por fichero, porque el ACE de CREATOR OWNER de la raiz se
            # propaga a cada hijo con el SID de su dueno.
            if ($ownerSid -and $sid -eq $ownerSid) { continue }
            if ($script:OwnerEquivalentSids -contains $sid) { continue }
            $excess = (Get-WriteRights -Rights $rule.FileSystemRights) -band (-bnot $policy.AllowedMask)
            if ($excess -ne 0) {
                $name = $rule.IdentityReference.Value
                Add-Finding -Class 'WritableByNonPrivileged' -Path $item.Path `
                            -Detail ("$name ($sid) tiene $($rule.FileSystemRights) sobre una ruta de clase $($policy.Class): " +
                                     ([System.Security.AccessControl.FileSystemRights]$excess).ToString() + ' sobra')
            }
        }

        if ($IncludeOwner -and $policy.Class -eq 'code') {
            if ($ownerSid -and -not ($script:PrivilegedSids -contains $ownerSid)) {
                if (-not $codeOwners.ContainsKey($ownerSid)) {
                    $codeOwners[$ownerSid] = [pscustomobject]@{ Count = 0; Sample = $item.Path }
                }
                $codeOwners[$ownerSid].Count++
            }
        }
    }

    # El dueno siempre puede reescribir la DACL, asi que una instalacion hecha sin
    # elevacion se detecta por aqui. Se agrupa por dueno para no repetir el mismo
    # hallazgo una vez por fichero.
    foreach ($sid in $codeOwners.Keys) {
        $entry = $codeOwners[$sid]
        Add-Finding -Class 'OwnedByNonPrivileged' -Path $entry.Sample `
                    -Detail ("$sid es dueno de $($entry.Count) ruta(s) de clase codigo y puede reescribir su DACL; " +
                             'instale desde una consola elevada')
    }

    if ($IncludeParent) {
        $parent = Split-Path -Parent $rootFull
        if ($parent) {
            try {
                $parentAcl = Get-Acl -LiteralPath $parent -ErrorAction Stop
                foreach ($rule in $parentAcl.Access) {
                    if ($rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow) { continue }
                    if (([int]$rule.PropagationFlags -band [int][System.Security.AccessControl.PropagationFlags]::InheritOnly) -ne 0) { continue }
                    $sid = Resolve-RuleSid -Rule $rule
                    if ($script:PrivilegedSids -contains $sid) { continue }
                    if (([int]$rule.FileSystemRights -band $script:DeleteMask) -ne 0) {
                        Add-Finding -Class 'ParentAllowsReplace' -Path $parent `
                                    -Detail ("$($rule.IdentityReference.Value) ($sid) puede borrar en el directorio padre, " +
                                             'asi que podria sustituir el directorio de instalacion completo')
                    }
                }
            } catch {
                Add-Finding -Class 'OperationFailed' -Path $parent `
                            -Detail "no se pudo leer la DACL del directorio padre: $($_.Exception.Message)"
            }
        }
    }

    return $checked
}

# ============================================================
#  Aplicacion
# ============================================================

function Set-CodeClassAcl {
    <#
      Una sola llamada sobre la raiz con ACE heredables resuelve todo el arbol de la
      clase codigo. El (AD) de la raiz va aparte, porque no se propaga.
    #>
    param([Parameter(Mandatory)][string]$Target)
    $code = Invoke-Icacls -Path $Target -Purpose 'ACE de la raiz' `
                          -Arguments (@('/inheritance:r', '/grant:r') + $script:RootGrants)
    if ($code -ne 0) { return $code }
    return (Invoke-Icacls -Path $Target -Purpose 'crear subdirectorios en la raiz' `
                          -Arguments @('/grant', $script:RootAppendGrant))
}

function New-DataClassPath {
    <#
      Crea lo que falta de la clase datos antes de endurecer: despues, un usuario sin
      privilegios ya no puede crear ficheros en la raiz, asi que un fichero de log o
      de cache que no exista no se podria crear mas tarde.
    #>
    param([Parameter(Mandatory)][string]$Root)
    foreach ($entry in $script:DataDirs) {
        $path = Join-Path $Root $entry.Path
        if (Test-Path -LiteralPath $path) { continue }
        try { New-Item -ItemType Directory -Path $path -Force -ErrorAction Stop | Out-Null }
        catch { Add-Finding -Class 'OperationFailed' -Path $path -Detail "no se pudo crear: $($_.Exception.Message)" }
    }
    # INV-INS-04: los JSON desplegados son UTF-8 sin BOM.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $seeds = @(
        @{ Path = 'packages-status-cache.json'; Content = '{}' }
        @{ Path = 'neven.log';                  Content = '' }
    )
    foreach ($seed in $seeds) {
        $path = Join-Path $Root $seed.Path
        if (Test-Path -LiteralPath $path) { continue }
        try { [System.IO.File]::WriteAllText($path, $seed.Content, $utf8NoBom) }
        catch { Add-Finding -Class 'OperationFailed' -Path $path -Detail "no se pudo crear: $($_.Exception.Message)" }
    }
}

function Remove-ForeignGrant {
    <#
      Quita los ACE explicitos de escritura que el modelo no declara. /inheritance:r
      sobre la raiz se lleva los ACE heredados, pero no los explicitos: un
      $INSTDIR que ya existia puede traer una concesion escrita a mano para una
      cuenta cualquiera, y esa sobrevivia al endurecimiento. Solo quita, nunca
      concede.
    #>
    param([Parameter(Mandatory)][string]$Root)
    foreach ($item in (Get-AuditTargets -Root $Root)) {
        $policy = Get-PathPolicy -Relative (Get-RelativePath -Root $Root -Full $item.Path)
        try {
            $acl = Get-Acl -LiteralPath $item.Path -ErrorAction Stop
        } catch {
            Add-Finding -Class 'OperationFailed' -Path $item.Path `
                        -Detail "no se pudo leer su DACL para limpiarla: $($_.Exception.Message)"
            continue
        }
        $targets = @()
        foreach ($rule in $acl.Access) {
            if ($rule.IsInherited) { continue }
            if ($rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow) { continue }
            if ((Get-WriteRights -Rights $rule.FileSystemRights) -eq 0) { continue }
            $sid = Resolve-RuleSid -Rule $rule
            if ($script:PrivilegedSids -contains $sid) { continue }
            if ($script:OwnerEquivalentSids -contains $sid) { continue }
            # Los usuarios autenticados los reescribe el modelo: en la raiz con
            # /grant:r, y en las rutas de la clase datos con su concesion propia.
            if ($sid -eq 'S-1-5-11' -and $policy.Class -ne 'code') { continue }
            $targets += $sid
        }
        foreach ($sid in ($targets | Sort-Object -Unique)) {
            Invoke-Icacls -Path $item.Path -Purpose "quitar la concesion explicita de $sid" `
                          -Arguments @('/remove:g', "*$sid") | Out-Null
        }
    }
}

function Set-DataClassAcl {
    param([Parameter(Mandatory)][string]$Root)
    foreach ($entry in $script:DataDirs) {
        $path = Join-Path $Root $entry.Path
        if (-not (Test-Path -LiteralPath $path)) { continue }
        Invoke-Icacls -Path $path -Purpose "escritura de $($entry.Path)" `
                      -Arguments @('/grant', '*S-1-5-11:(OI)(CI)(M)') | Out-Null
    }
    foreach ($entry in $script:DataFiles) {
        $path = Join-Path $Root $entry.Path
        if (-not (Test-Path -LiteralPath $path)) { continue }
        Invoke-Icacls -Path $path -Purpose "escritura de $($entry.Path)" `
                      -Arguments @('/grant', '*S-1-5-11:(RX,W)') | Out-Null
    }
}

function Invoke-Apply {
    param([Parameter(Mandatory)][string]$Root)
    if (Test-Path -LiteralPath $Root) {
        New-DataClassPath -Root $Root
        Remove-ForeignGrant -Root $Root
    }
    if ((Set-CodeClassAcl -Target $Root) -ne 0) { return 0 }
    Set-DataClassAcl -Root $Root
    return (Invoke-AclAudit -Root $Root -IncludeOwner -IncludeParent)
}

function Invoke-Probe {
    <#
      Mide si el endurecimiento es posible antes de que se copie el primer fichero:
      una unidad sin DACL o una cuenta sin permiso para cambiarla se detectan aqui,
      cuando abortar todavia no deja nada a medias.
    #>
    param([Parameter(Mandatory)][string]$Root)
    $probe = Join-Path $Root '.neven-acl-probe'
    $checked = 0
    try {
        try {
            New-Item -ItemType Directory -Path $probe -Force -ErrorAction Stop | Out-Null
            # El fichero se crea antes de endurecer, para medir que hereda un hijo
            # del modelo de la raiz. Crearlo despues mediria otra cosa: en un
            # directorio ya endurecido, escribir un fichero nuevo es justo lo que el
            # modelo niega a quien no es administrador.
            [System.IO.File]::WriteAllText((Join-Path $probe 'marker.txt'), 'probe')
        } catch {
            Add-Finding -Class 'OperationFailed' -Path $probe `
                        -Detail "no se pudo preparar el sondeo: $($_.Exception.Message)"
            return 0
        }
        if ((Set-CodeClassAcl -Target $probe) -ne 0) { return 0 }
        $checked = Invoke-AclAudit -Root $probe
    } finally {
        Reset-InheritedAcl -Path $probe
        if (Test-Path -LiteralPath $probe) {
            try { Remove-Item -LiteralPath $probe -Recurse -Force -ErrorAction Stop }
            catch {
                Add-Finding -Class 'OperationFailed' -Path $probe `
                            -Detail ("el directorio de sondeo no se pudo borrar: $($_.Exception.Message). " +
                                     'Borrelo a mano antes de reintentar la instalacion.')
            }
        }
    }
    return $checked
}

# ============================================================
#  Informe
# ============================================================

function Write-Report {
    <#
      Unica funcion que imprime el motivo de un fallo y la exposicion residual: es el
      texto que reutilizan los dos puntos de pregunta del instalador (el sondeo
      previo y la aplicacion final).
    #>
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Mode,
        [Parameter(Mandatory)][int]$Checked,
        [Parameter(Mandatory)][int]$ExitCode
    )
    Write-Host ''
    Write-Host "  Permisos de la instalacion de NEVEN ($Mode): $Root" -ForegroundColor Cyan
    Write-Host "  Rutas medidas: $Checked" -ForegroundColor Gray
    $failed = @($script:Operations | Where-Object { -not $_.Ok })
    Write-Host "  Operaciones de permisos: $($script:Operations.Count), fallidas: $($failed.Count)" -ForegroundColor Gray

    # Con una operacion fallida no se puede afirmar que clase quedo cada ruta: lo
    # unico cierto es el motivo del fallo, que se imprime mas abajo.
    if ($Mode -ne 'sondeo' -and $ExitCode -ne 2) {
        Write-Host ''
        Write-Host '  Solo lectura y ejecucion para los usuarios (clase codigo):' -ForegroundColor White
        Write-Host '    la raiz y todo lo que NEVEN ejecuta o carga desde ella' -ForegroundColor Gray
        Write-Host '  Siguen escribibles, con su motivo (clase datos):' -ForegroundColor White
        foreach ($entry in $script:DataDirs) { Write-Host "    $($entry.Path)\  $($entry.Reason)" -ForegroundColor Gray }
        foreach ($entry in $script:DataFiles) { Write-Host "    $($entry.Path)  $($entry.Reason)" -ForegroundColor Gray }
    }

    if ($script:Findings.Count -gt 0) {
        Write-Host ''
        Write-Host "  El endurecimiento no quedo completo. Motivo medido ($($script:Findings.Count) hallazgo(s)):" -ForegroundColor Yellow
        $shown = 0
        foreach ($finding in $script:Findings) {
            if ($shown -ge 20) {
                Write-Host "    ... y $($script:Findings.Count - $shown) hallazgo(s) mas" -ForegroundColor Yellow
                break
            }
            Write-Host "    [$($finding.Class)] $($finding.Path)" -ForegroundColor Yellow
            Write-Host "        $($finding.Detail)" -ForegroundColor Yellow
            $shown++
        }
        Write-Host ''
        Write-Host '  Mientras no se aplique, cualquier usuario autenticado de esta maquina puede' -ForegroundColor Yellow
        Write-Host '  sustituir un fichero que NEVEN ejecuta (startup\*.py, functions\*.R,' -ForegroundColor Yellow
        Write-Host '  TaskPane\*, los ejecutables de los motores) y esperar a que NEVEN lo ejecute.' -ForegroundColor Yellow
    } else {
        Write-Host ''
        Write-Host '  Ningun usuario sin privilegios puede escribir en lo que NEVEN ejecuta.' -ForegroundColor Green
    }

    Write-Host ''
    Write-Host '  Exposicion residual, tambien cuando el endurecimiento se aplica entero:' -ForegroundColor White
    foreach ($line in $script:ResidualExposure) { Write-Host "    - $line" -ForegroundColor Gray }
    Write-Host ''
    Write-Host "  Codigo de salida: $ExitCode  (0 sin hallazgos, 1 hallazgos de ACL, 2 operacion fallida)" -ForegroundColor Gray
    Write-Host ''
}

# ============================================================
#  Main
# ============================================================

$root = $InstallDir
try { $root = [System.IO.Path]::GetFullPath($InstallDir) } catch { }
$root = $root.TrimEnd('\')
if ($root -match '^[A-Za-z]:$') { $root = $root + '\' }

$mode = 'aplicacion'
if ($Probe)     { $mode = 'sondeo' }
elseif ($AuditOnly) { $mode = 'auditoria' }

if (-not (Test-Path -LiteralPath $root) -and $mode -ne 'aplicacion') {
    # En aplicacion se deja que icacls falle y lo registre; aqui no hay nada que medir.
    Add-Finding -Class 'OperationFailed' -Path $root -Detail 'el directorio de instalacion no existe'
    $checked = 0
} else {
    switch ($mode) {
        'sondeo'    { $checked = Invoke-Probe -Root $root }
        'auditoria' { $checked = Invoke-AclAudit -Root $root -IncludeOwner -IncludeParent }
        default     { $checked = Invoke-Apply -Root $root }
    }
}

$exitCode = 0
if (@($script:Findings | Where-Object { $_.Class -eq 'OperationFailed' }).Count -gt 0) {
    $exitCode = 2
} elseif ($script:Findings.Count -gt 0) {
    $exitCode = 1
}

if ($Json) {
    $payload = [pscustomobject]@{
        InstallDir = $root
        Mode       = $mode
        Checked    = $checked
        ExitCode   = $exitCode
        Operations = @($script:Operations)
        Findings   = @($script:Findings)
        Residual   = @($script:ResidualExposure)
    }
    Write-Output ($payload | ConvertTo-Json -Depth 5)
} else {
    Write-Report -Root $root -Mode $mode -Checked $checked -ExitCode $exitCode
}

exit $exitCode
