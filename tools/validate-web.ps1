$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$savedBrowserPath=$env:PLAYWRIGHT_BROWSERS_PATH
# Navegadores de QA dentro del proyecto; no usa sesiones personales de Brave.
$env:PLAYWRIGHT_BROWSERS_PATH=Join-Path $projectRoot 'toolchain\browsers'
Push-Location (Join-Path $projectRoot 'web')
try {
    & npm run test *> (Join-Path $projectRoot 'reports\web-v2-unit-tests.log')
    if($LASTEXITCODE -ne 0) { throw 'React unit tests failed' }
    & npm run build *> (Join-Path $projectRoot 'reports\web-v2-build.log')
    if($LASTEXITCODE -ne 0) { throw 'TypeScript/Vite build failed' }
    & npm run test:e2e *> (Join-Path $projectRoot 'reports\web-v2-e2e.log')
    if($LASTEXITCODE -ne 0) { throw 'Desktop/mobile browser tests failed' }
} finally {
    Pop-Location
    $env:PLAYWRIGHT_BROWSERS_PATH=$savedBrowserPath
}
Write-Output 'PASS: React tests, production assets and desktop/mobile browser cases'
