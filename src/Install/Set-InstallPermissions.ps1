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
        Conserva la escritura, con el motivo declarado en la tabla de abajo, pero
        solo donde el destino ya la concedia: el script mide el destino antes de
        tocarlo y nunca concede un permiso que no estuviese ahi. En una carpeta
        protegida las rutas de datos quedan en solo lectura, y el informe lo dice
        junto con lo que eso implica.

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
# Que se concedio en la clase datos y que no, con la medicion que lo decidio.
$script:DataGrants = @()
# Estado de cada ruta de la clase datos: escribible por los usuarios o no. Lo
# llena el modo que corresponda, y de ahi sale el informe de exposicion residual.
$script:DataWritable = @{}

# ============================================================
#  Tabla declarada
# ============================================================

# Clase datos: rutas que NEVEN escribe desde la sesion del usuario, sin elevar.
# Conservan la escritura de los usuarios autenticados DONDE EL DESTINO YA LA
# CONCEDIA. Bajo C:\ la concedia la herencia de la raiz del disco, pero el destino
# lo elige el usuario y una carpeta protegida (C:\Program Files\...) no concede
# escritura a nadie sin privilegios: conceder ahi esta tabla crearia el mismo
# vector que el script cierra. Por eso se mide antes (Get-DataBaseline) y solo se
# emite la concesion que ya existia.
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
$script:ResidualExposureFixed = @(
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

# Grupos a los que pertenece cualquier usuario de la maquina. Son los unicos cuya
# escritura previa sobre el destino justifica conceder la de la clase datos: un ACE
# para una cuenta concreta no significa que todos los usuarios pudieran escribir
# ahi, y conceder a S-1-5-11 por ese ACE ampliaria el acceso en vez de restringirlo.
$script:BroadUserSids = @(
    'S-1-1-0'       # Todos
    'S-1-5-11'      # Usuarios autenticados
    'S-1-5-32-545'  # Usuarios
    'S-1-5-4'       # INTERACTIVE
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

# Lo que concede cada concesion de la clase datos, en bits de escritura. Se compara
# con lo que el destino ya concedia: una concesion solo se emite si todos sus bits
# estaban ahi antes, de modo que el script restringe en todos los caminos y en
# ninguno amplia.
#   (M)      Modify: escribir, anadir y borrar
#   (RX,W)   leer, ejecutar y escribir en sitio, sin borrar
$script:DataDirGrantMask  = [int]($FSR::Modify) -band $script:WriteMask
$script:DataFileGrantMask = $script:DataFileMask

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

function Measure-BroadWrite {
    <#
      Mide que escritura tiene ya sobre una ruta cualquier usuario de la maquina,
      contando solo los grupos amplios de $script:BroadUserSids y restando lo que
      un Deny les quite. Devuelve 0 si la ruta no existe o no se puede leer: sin
      medicion no se concede nada.
    #>
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    try { $acl = Get-Acl -LiteralPath $Path -ErrorAction Stop } catch { return 0 }
    $allow = 0
    $deny = 0
    foreach ($rule in $acl.Access) {
        # Un ACE InheritOnly no concede nada sobre el objeto que lo lleva.
        if (([int]$rule.PropagationFlags -band [int][System.Security.AccessControl.PropagationFlags]::InheritOnly) -ne 0) { continue }
        if (-not ($script:BroadUserSids -contains (Resolve-RuleSid -Rule $rule))) { continue }
        $rights = Get-WriteRights -Rights $rule.FileSystemRights
        if ($rule.AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Deny) { $deny = $deny -bor $rights }
        else { $allow = $allow -bor $rights }
    }
    return ($allow -band (-bnot $deny))
}

function Measure-InheritedBroadWrite {
    <#
      Lo mismo, pero para una ruta que todavia no existe: mide que heredaria de su
      directorio padre. Es lo que permite decidir sobre los directorios de la clase
      datos que el propio script crea.
    #>
    param([Parameter(Mandatory)][string]$Path, [switch]$ForFile)
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    try { $acl = Get-Acl -LiteralPath $Path -ErrorAction Stop } catch { return 0 }
    $flag = if ($ForFile) { [int][System.Security.AccessControl.InheritanceFlags]::ObjectInherit }
            else { [int][System.Security.AccessControl.InheritanceFlags]::ContainerInherit }
    $allow = 0
    $deny = 0
    foreach ($rule in $acl.Access) {
        if (([int]$rule.InheritanceFlags -band $flag) -eq 0) { continue }
        if (-not ($script:BroadUserSids -contains (Resolve-RuleSid -Rule $rule))) { continue }
        $rights = Get-WriteRights -Rights $rule.FileSystemRights
        if ($rule.AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Deny) { $deny = $deny -bor $rights }
        else { $allow = $allow -bor $rights }
    }
    return ($allow -band (-bnot $deny))
}

function Get-DataBaseline {
    <#
      Mide, ANTES de tocar nada, la escritura que el destino ya concedia a los
      usuarios en la raiz y en cada ruta de la clase datos. El destino no esta
      acotado a C:\: el usuario puede elegir cualquier carpeta en los dos
      instaladores, y una carpeta protegida (C:\Program Files\...) no concede
      escritura a nadie sin privilegios. Conceder ahi la clase datos crearia el
      mismo vector que esta tarea cierra, asi que se mide y solo se concede lo que
      ya existia.
    #>
    param([Parameter(Mandatory)][string]$Root)
    $parent = Split-Path -Parent $Root.TrimEnd('\')
    $rootExists = Test-Path -LiteralPath $Root
    $rootMask = if ($rootExists) { Measure-BroadWrite -Path $Root }
                elseif ($parent) { Measure-InheritedBroadWrite -Path $parent }
                else { 0 }
    # De donde hereda una ruta de datos que aun no existe: de la raiz si ya esta, y
    # si no, de lo que la raiz heredara de su padre.
    $inheritDir  = if ($rootExists) { Measure-InheritedBroadWrite -Path $Root } else { $rootMask }
    $inheritFile = if ($rootExists) { Measure-InheritedBroadWrite -Path $Root -ForFile } else { $rootMask }

    $paths = @{}
    foreach ($entry in $script:DataDirs) {
        $path = Join-Path $Root $entry.Path
        $paths[$entry.Path] = if (Test-Path -LiteralPath $path) { Measure-BroadWrite -Path $path } else { $inheritDir }
    }
    foreach ($entry in $script:DataFiles) {
        $path = Join-Path $Root $entry.Path
        $paths[$entry.Path] = if (Test-Path -LiteralPath $path) { Measure-BroadWrite -Path $path } else { $inheritFile }
    }
    return [pscustomobject]@{
        RootMask   = $rootMask
        RootAppend = (($rootMask -band $script:RootMask) -ne 0)
        Paths      = $paths
    }
}

function Get-DataGrant {
    <#
      Traduce la medicion a la concesion que se puede emitir sin ampliar nada:
      la declarada si todos sus bits ya estaban, la mas corta si solo estaban los de
      escribir en sitio, y ninguna si el destino no concedia escritura.
    #>
    param(
        [Parameter(Mandatory)][int]$Baseline,
        [Parameter(Mandatory)][ValidateSet('dir', 'file')][string]$Kind
    )
    if ($Kind -eq 'dir') {
        if (($Baseline -band $script:DataDirGrantMask) -eq $script:DataDirGrantMask) { return '*S-1-5-11:(OI)(CI)(M)' }
        if (($Baseline -band $script:DataFileGrantMask) -eq $script:DataFileGrantMask) { return '*S-1-5-11:(OI)(CI)(RX,W)' }
        return ''
    }
    if (($Baseline -band $script:DataFileGrantMask) -eq $script:DataFileGrantMask) { return '*S-1-5-11:(RX,W)' }
    return ''
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
    param(
        [Parameter(Mandatory)][string]$Target,
        [bool]$AllowAppend = $true
    )
    $code = Invoke-Icacls -Path $Target -Purpose 'ACE de la raiz' `
                          -Arguments (@('/inheritance:r', '/grant:r') + $script:RootGrants)
    if ($code -ne 0) { return $code }
    # El (AD) tampoco se concede si el destino no lo concedia ya: en una carpeta
    # protegida, dejar crear subdirectorios en el directorio de los ejecutables
    # seria un permiso nuevo.
    if (-not $AllowAppend) { return 0 }
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
    <#
      Concede la escritura de la clase datos solo donde el destino ya la concedia,
      segun la medicion que Get-DataBaseline tomo antes de tocar nada. Donde no
      existia no se emite ninguna concesion: la ruta queda en solo lectura y el
      informe lo dice con su consecuencia.
    #>
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)]$Baseline
    )
    foreach ($item in @(
            @{ Entries = $script:DataDirs;  Kind = 'dir' }
            @{ Entries = $script:DataFiles; Kind = 'file' }
        )) {
        foreach ($entry in $item.Entries) {
            $path = Join-Path $Root $entry.Path
            if (-not (Test-Path -LiteralPath $path)) { continue }
            $mask = 0
            if ($Baseline.Paths.ContainsKey($entry.Path)) { $mask = [int]$Baseline.Paths[$entry.Path] }
            $grant = Get-DataGrant -Baseline $mask -Kind $item.Kind
            $script:DataGrants += [pscustomobject]@{
                Path         = $entry.Path
                Kind         = $item.Kind
                BaselineMask = $mask
                Granted      = ($grant -ne '')
                Grant        = $grant
                Reason       = $entry.Reason
            }
            if ($grant -eq '') { continue }
            Invoke-Icacls -Path $path -Purpose "escritura de $($entry.Path)" `
                          -Arguments @('/grant', $grant) | Out-Null
        }
    }
}

function Invoke-Apply {
    param([Parameter(Mandatory)][string]$Root)
    # Se mide antes de crear y antes de limpiar nada: la clase datos solo puede
    # conceder lo que el destino ya concedia, y despues de endurecer la raiz esa
    # medicion ya no estaria disponible.
    $baseline = Get-DataBaseline -Root $Root
    if (Test-Path -LiteralPath $Root) {
        New-DataClassPath -Root $Root
        Remove-ForeignGrant -Root $Root
    }
    if ((Set-CodeClassAcl -Target $Root -AllowAppend $baseline.RootAppend) -ne 0) { return 0 }
    Set-DataClassAcl -Root $Root -Baseline $baseline
    $checked = Invoke-AclAudit -Root $Root -IncludeOwner -IncludeParent
    Measure-DataState -Root $Root
    return $checked
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
    $baseline = Get-DataBaseline -Root $Root
    Set-DataStateFromBaseline -Baseline $baseline
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
        if ((Set-CodeClassAcl -Target $probe -AllowAppend $baseline.RootAppend) -ne 0) { return 0 }
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

function Test-DataWritable {
    param([Parameter(Mandatory)][string]$Relative)
    if ($script:DataWritable.ContainsKey($Relative)) { return [bool]$script:DataWritable[$Relative] }
    # Sin medicion no se afirma que la ruta quede cerrada: se informa de ella.
    return $true
}

function Measure-DataState {
    <#
      Mide que rutas de la clase datos quedan escribibles por los usuarios. Es lo
      que hace que el informe diga lo medido y no lo que la tabla pretendia.
    #>
    param([Parameter(Mandatory)][string]$Root)
    foreach ($entry in ($script:DataDirs + $script:DataFiles)) {
        $path = Join-Path $Root $entry.Path
        if (-not (Test-Path -LiteralPath $path)) { continue }
        $mask = Measure-BroadWrite -Path $path
        $script:DataWritable[$entry.Path] = (($mask -band $script:DataFileGrantMask) -eq $script:DataFileGrantMask)
    }
}

function Set-DataStateFromBaseline {
    <#
      Lo mismo para el sondeo, que corre antes de copiar el primer fichero: ahi no
      hay estado final que medir, pero la medicion del destino ya dice que recibira
      cada ruta de la clase datos, y el usuario tiene que saberlo antes de instalar.
    #>
    param([Parameter(Mandatory)]$Baseline)
    foreach ($entry in $script:DataDirs) {
        $mask = 0
        if ($Baseline.Paths.ContainsKey($entry.Path)) { $mask = [int]$Baseline.Paths[$entry.Path] }
        $script:DataWritable[$entry.Path] = ((Get-DataGrant -Baseline $mask -Kind 'dir') -ne '')
    }
    foreach ($entry in $script:DataFiles) {
        $mask = 0
        if ($Baseline.Paths.ContainsKey($entry.Path)) { $mask = [int]$Baseline.Paths[$entry.Path] }
        $script:DataWritable[$entry.Path] = ((Get-DataGrant -Baseline $mask -Kind 'file') -ne '')
    }
}

function Get-ResidualExposure {
    <#
      La exposicion residual se deriva de lo medido, no de la tabla: en un destino
      protegido la clase datos no recibe escritura, y decir que 'sigue escribible'
      seria falso en un sentido y, al reves, callar que ahi guardar funciones exige
      elevacion dejaria al usuario sin el motivo.
    #>
    $lines = @()
    if ((Test-DataWritable -Relative 'functions') -or (Test-DataWritable -Relative 'prompts')) {
        $lines += 'functions\ y prompts\ son escribibles por cualquier usuario autenticado, y NEVEN carga functions\*.R en R dentro de Excel. Cerrarlo exige una decision de producto sobre /api/functions/create, /api/script/save y el FileWatchService.'
    }
    if (Test-DataWritable -Relative 'neven-config.json') {
        $lines += 'neven-config.json es escribible: es el fichero por el que se puede apagar el sandbox, y el que reescriben Studio > Settings > Motores y -ConfigureOnly.'
    }
    $lines += $script:ResidualExposureFixed
    $closed = @($script:DataWritable.Keys | Where-Object { -not $script:DataWritable[$_] } | Sort-Object)
    if ($closed.Count -gt 0) {
        $lines += ('El destino no concedia escritura a los usuarios antes de instalar, asi que estas rutas de datos quedan en solo lectura y no se les concede nada: ' +
                   ($closed -join ', ') + '. Guardar funciones o prompts, reconfigurar los motores y escribir los logs ahi exigira una consola elevada.')
    }
    return $lines
}

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
        Write-Host '  Clase datos, medida en el destino:' -ForegroundColor White
        foreach ($entry in ($script:DataDirs + $script:DataFiles)) {
            if (Test-DataWritable -Relative $entry.Path) {
                Write-Host "    $($entry.Path)  escribible sin elevar: $($entry.Reason)" -ForegroundColor Gray
            } else {
                Write-Host "    $($entry.Path)  solo lectura: el destino no concedia escritura a los usuarios antes de instalar" -ForegroundColor Yellow
            }
        }
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
    foreach ($line in (Get-ResidualExposure)) { Write-Host "    - $line" -ForegroundColor Gray }
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
        'auditoria' {
            $checked = Invoke-AclAudit -Root $root -IncludeOwner -IncludeParent
            Measure-DataState -Root $root
        }
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
        InstallDir   = $root
        Mode         = $mode
        Checked      = $checked
        ExitCode     = $exitCode
        Operations   = @($script:Operations)
        Findings     = @($script:Findings)
        Residual     = @(Get-ResidualExposure)
        DataClass    = @($script:DataGrants)
        DataWritable = $script:DataWritable
    }
    Write-Output ($payload | ConvertTo-Json -Depth 5)
} else {
    Write-Report -Root $root -Mode $mode -Checked $checked -ExitCode $exitCode
}

exit $exitCode
