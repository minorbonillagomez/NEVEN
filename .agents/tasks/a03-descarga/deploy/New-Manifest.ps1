$wt='F:\ANTIGRAVITY\2026\NEVEN\.worktrees\a03-descarga'; $root='C:\NEVEN'
$stamp=Get-Date -Format 'yyyyMMdd-HHmm'
function Sha($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
$map=@(
 @('src\Audiobook\neven_audiobook_server.py','Audiobook\neven_audiobook_server.py'),
 @('src\Audiobook\api\routes.py','Audiobook\api\routes.py'),
 @('src\Audiobook\pipeline.py','Audiobook\pipeline.py'),
 @('src\Audiobook\muxer\ffmpeg_muxer.py','Audiobook\muxer\ffmpeg_muxer.py'),
 @('src\TaskPane\audiobook.js','taskpane\audiobook.js'))
if(Test-Path 'C:\NEVEN\docs\ontologia\neven-core'){ $map+=,@('src\docs\ontologia\neven-core\neven-ontology-p3.yaml','docs\ontologia\neven-core\neven-ontology-p3.yaml') }
$files=@()
foreach($m in $map){
 $s=Join-Path $wt $m[0]; $dst=Join-Path $root $m[1]
 $tmp=[IO.Path]::GetTempFileName()
 git -C $wt cat-file -e "12aa43d:$($m[0].Replace('\','/'))" 2>$null
 $inBase=($LASTEXITCODE -eq 0); $bh=$null
 if($inBase){ $psi=New-Object Diagnostics.ProcessStartInfo 'git',"-C `"$wt`" show 12aa43d:$($m[0].Replace('\','/'))"; $psi.RedirectStandardOutput=$true;$psi.UseShellExecute=$false
  $p=[Diagnostics.Process]::Start($psi); $fs=[IO.File]::Create($tmp); $p.StandardOutput.BaseStream.CopyTo($fs); $fs.Close(); $p.WaitForExit(); $bh=Sha $tmp }
 Remove-Item $tmp -Force
 $dh= if(Test-Path -LiteralPath $dst){Sha $dst}else{$null}
 $files+=[ordered]@{source=$s;destination=$dst;sourceSha256=(Sha $s);destSha256Current=$dh;baseSha256=$bh;destMatchesBase=($null -ne $dh -and $dh -eq $bh)}
}
$out=[ordered]@{commit=(git -C $wt rev-parse --short HEAD);baseline='12aa43d';generated=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss');prodRoot=$root;backupDir="C:\NEVEN_backup_$stamp";
 neverenConfigModified=$false;cleanPycache=@('C:\NEVEN\Audiobook\__pycache__','C:\NEVEN\Audiobook\api\__pycache__','C:\NEVEN\Audiobook\muxer\__pycache__','C:\NEVEN\taskpane\__pycache__');files=$files}
$json=$out|ConvertTo-Json -Depth 5
[IO.File]::WriteAllText("$PSScriptRoot\manifest.json",$json,(New-Object Text.UTF8Encoding($false)))
$files|%{ "{0} | src {1} | dest {2} | base {3} | match {4}" -f $_.destination.Substring(8),$_.sourceSha256.Substring(0,12),$(if($_.destSha256Current){$_.destSha256Current.Substring(0,12)}else{'(nuevo)'}),$(if($_.baseSha256){$_.baseSha256.Substring(0,12)}else{'-'}),$_.destMatchesBase }
"backup: C:\NEVEN_backup_$stamp  commit: $($out.commit)"