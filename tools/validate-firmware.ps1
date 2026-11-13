param([string]$OutputFolder='releases\unificado-20261022')
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$cli=Join-Path $env:LOCALAPPDATA 'Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
$public=Join-Path $taskRoot 'firmware\PastilleroESP32'
$private=Join-Path $taskRoot 'private\firmware\PastilleroESP32'
$libraries=Join-Path $taskRoot 'toolchain\libraries'
$existingLibraries=Join-Path $env:USERPROFILE 'OneDrive\Documentos\Arduino\libraries'
$output=[IO.Path]::GetFullPath((Join-Path $taskRoot $OutputFolder))
$releaseRoot=[IO.Path]::GetFullPath((Join-Path $taskRoot 'releases'))+[IO.Path]::DirectorySeparatorChar
if(-not $output.StartsWith($releaseRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output outside project releases' }
$source=Join-Path $public 'PastilleroESP32.ino'
if(-not ([IO.File]::ReadAllText($source)).Contains('#define PASTILLERO_DRY_RUN 1')) { throw 'Simulation must remain the default' }
& python (Join-Path $PSScriptRoot 'generate_private_firmware.py')
if($LASTEXITCODE -ne 0) { throw 'Private sketch generation failed' }
New-Item -ItemType Directory -Path $output -Force | Out-Null
foreach($variant in @(@{name='public-simulation';sketch=$public;flag=1},@{name='public-hardware';sketch=$public;flag=0},@{name='private-hardware';sketch=$private;flag=0},@{name='private-simulation';sketch=$private;flag=1})) {
    $build=Join-Path $taskRoot ('firmware\build\unified-'+$variant.name)
    $log=Join-Path $taskRoot ('reports\unified-'+$variant.name+'-build.log')
    & $cli compile --verbose --fqbn 'esp32:esp32:esp32doit-devkit-v1:UploadSpeed=921600,FlashFreq=80,DebugLevel=none,EraseFlash=none' --jobs 4 --libraries $libraries --libraries $existingLibraries --build-property ('compiler.cpp.extra_flags=-DPASTILLERO_DRY_RUN='+$variant.flag) --build-path $build $variant.sketch *> $log
    if($LASTEXITCODE -ne 0) { throw ('Firmware compile failed: '+$variant.name) }
    $binary=Join-Path $output ('PastilleroESP32-'+$variant.name+'.bin')
    if(Test-Path -LiteralPath $binary) {
        $saved=Join-Path $taskRoot ('archives\firmware-unified-prior-'+[guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $saved | Out-Null
        Copy-Item -LiteralPath $binary -Destination $saved
    }
    Copy-Item -LiteralPath (Join-Path $build 'PastilleroESP32.ino.bin') -Destination $binary
}
Write-Output 'PASS: unified public/private firmware hardware and simulation compiled; default simulation; no hardware contacted'
