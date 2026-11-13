param([switch]$HardwareVariant)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$cli=Join-Path $env:LOCALAPPDATA 'Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
$sdk=Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
New-Item -ItemType Directory -Path (Join-Path $taskRoot 'reports') -Force | Out-Null
$propertyPath=$sdk.Replace('\','/').Replace(':','\:')
[IO.File]::WriteAllText((Join-Path $taskRoot 'local.properties'),"sdk.dir=$propertyPath")
Push-Location $taskRoot
try {
    & .\gradlew.bat :app:assembleDebug :app:testDebugUnitTest :app:lintDebug :app:assembleDebugAndroidTest --console=plain
    if($LASTEXITCODE -ne 0) { throw 'Android validation failed' }
} finally { Pop-Location }
$variant=if($HardwareVariant){'hardware'}else{'simulation'}
$flag=if($HardwareVariant){'-DPASTILLERO_DRY_RUN=0'}else{'-DPASTILLERO_DRY_RUN=1'}
$libraries=Join-Path $taskRoot 'toolchain\libraries'
$existingLibraries=Join-Path $env:USERPROFILE 'OneDrive\Documentos\Arduino\libraries'
& $cli compile --fqbn 'esp32:esp32:esp32doit-devkit-v1:UploadSpeed=921600,FlashFreq=80,DebugLevel=none,EraseFlash=none' --libraries $libraries --libraries $existingLibraries --build-property "compiler.cpp.extra_flags=$flag" --build-path (Join-Path $taskRoot "firmware\build\$variant") (Join-Path $taskRoot 'firmware\PastilleroESP32')
if($LASTEXITCODE -ne 0) { throw 'Firmware validation failed' }
# Deliberately contains no upload, serial-monitor or board-control commands.
