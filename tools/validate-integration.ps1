$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
Push-Location $projectRoot
try {
    $sourceFiles=@('firmware\PastilleroESP32\PastilleroESP32.ino','tests\contract_controller.cpp','tests\event_json_test.cpp','tests\snapshot_test.cpp','app\src\test\java\mx\edu\badi\pastillero\ContractFixtureTest.java','app\src\main\java\mx\edu\badi\pastillero\ScheduleEngine.java','firebase\contract.integration.test.mjs','firebase\database.rules.json')
    $sourceHashes=@{}
    foreach($source in $sourceFiles) { $sourceHashes[$source]=(Get-FileHash -LiteralPath $source).Hash }
    # Solo compilador de PC: el adaptador incluye el .ino con PASTILLERO_HOST_TEST.
    $zig=Join-Path $projectRoot 'toolchain\zig\zig.exe'
    if(-not (Test-Path -LiteralPath $zig)) { throw 'Falta el compilador C++ de QA configurado' }
    & $zig c++ -std=c++17 -I 'toolchain\libraries\ArduinoJson-7.3.2\src' tests\contract_controller.cpp -o reports\contract-controller.exe
    if($LASTEXITCODE -ne 0) { throw 'No compiló el controlador de PC' }
    & $zig c++ -std=c++17 -I 'toolchain\libraries\ArduinoJson-7.3.2\src' tests\event_json_test.cpp -o reports\event-json-tests.exe
    if($LASTEXITCODE -ne 0) { throw 'No compiló la prueba de propiedad de cadenas JSON' }
    & .\reports\event-json-tests.exe *> reports\event-json-tests.log
    if($LASTEXITCODE -ne 0) { throw 'Falló la conservación de identificadores de eventos' }
    & $zig c++ -std=c++17 -I 'toolchain\libraries\ArduinoJson-7.3.2\src' tests\snapshot_test.cpp -o reports\snapshot-tests.exe
    if($LASTEXITCODE -ne 0) { throw 'No compiló la prueba de instantáneas persistentes' }
    & .\reports\snapshot-tests.exe *> reports\snapshot-tests.log
    if($LASTEXITCODE -ne 0) { throw 'Falló el contrato de almacenamiento de instantáneas' }
    & $zig c++ -std=c++17 tests\controller_test.cpp -o reports\controller-v2-tests.exe
    if($LASTEXITCODE -ne 0) { throw 'No compilaron las pruebas históricas del controlador' }
    & .\reports\controller-v2-tests.exe *> reports\controller-v2-tests.log
    if($LASTEXITCODE -ne 0) { throw 'Regresión en controlador histórico' }
    & $zig c++ -std=c++17 tests\version2_test.cpp -o reports\firmware-v2-new-tests.exe
    if($LASTEXITCODE -ne 0) { throw 'No compilaron las pruebas V2 del controlador' }
    & .\reports\firmware-v2-new-tests.exe *> reports\firmware-v2-new-tests.log
    if($LASTEXITCODE -ne 0) { throw 'Regresión en controlador V2' }
    # Se regenera la fixture temporal inmediatamente antes del emulador; no contiene credenciales.
    & .\gradlew.bat :app:testDebugUnitTest --rerun-tasks --console=plain *> reports\integration-v2-jvm.log
    if($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas Java/fixtures' }
    Push-Location firebase
    try {
        & .\node_modules\.bin\firebase.cmd emulators:exec --project demo-pastillero --only database 'node --test contract.integration.test.mjs' *> ..\reports\integration-v2-contract.log
        if($LASTEXITCODE -ne 0) { throw 'Falló la integración local Java/Firebase/C++' }
    } finally { Pop-Location }
    foreach($source in $sourceFiles) {
        if((Get-FileHash -LiteralPath $source).Hash -ne $sourceHashes[$source]) { throw 'Una fuente cambió durante QA; repetir integración' }
    }
    $sourceHashes | ConvertTo-Json | Set-Content -LiteralPath reports\integration-v2-source-hashes.json -Encoding utf8
} finally { Pop-Location }
Write-Output 'PASS: contrato Java → Firebase emulado → Controller C++ → eventos; sin hardware ni producción'
