$env:Path = 'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;' + $env:Path
$b='f:\ANTIGRAVITY\2026\NEVEN\.worktrees\a03-descarga\src\Build'
cmake --build $b --config Release --target rj2xcl_tests --parallel
"BUILD_EXIT=$LASTEXITCODE"
Set-Location $b
ctest -C Release --output-on-failure
"CTEST_EXIT=$LASTEXITCODE"
