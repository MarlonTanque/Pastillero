"""Pruebas Android solo en los AVD del proyecto; nunca selecciona teléfonos físicos."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk'
ADB = SDK / 'platform-tools/adb.exe'
EMULATOR = SDK / 'emulator/emulator.exe'
APK = ROOT / 'app/build/outputs/apk/debug/app-debug.apk'
TEST_APK = ROOT / 'app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
ENV = dict(os.environ, ANDROID_AVD_HOME=str(ROOT / 'toolchain/avd'), PYTHONUTF8='1')
RESULTS = []


def adb(serial, *args, timeout=180):
    if serial not in ('emulator-5580', 'emulator-5582'):
        raise ValueError('Solo AVD dedicados')
    result = subprocess.run([str(ADB), '-s', serial, *args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError('Falló una operación del AVD dedicado')
    return result.stdout + result.stderr


def validate(name, port, classes, expected, live=False):
    serial = 'emulator-' + str(port)
    owned = None
    opened_logs = []
    try:
        devices = subprocess.check_output([str(ADB), 'devices'], text=True)
        if serial + '\tdevice' not in devices:
            for stream in ('stdout', 'stderr'):
                opened_logs.append((ROOT / ('reports/unified-' + name + '-' + stream + '.log')).open('w', encoding='utf-8'))
            owned = subprocess.Popen([str(EMULATOR), '-avd', name, '-port', str(port), '-no-window',
                                      '-no-audio', '-no-snapshot', '-no-boot-anim', '-gpu', 'swiftshader_indirect'],
                                     env=ENV, stdout=opened_logs[0], stderr=opened_logs[1],
                                     creationflags=subprocess.CREATE_NO_WINDOW)
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            try:
                if adb(serial, 'shell', 'getprop', 'sys.boot_completed', timeout=8).strip() == '1':
                    break
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
            if owned and owned.poll() is not None:
                raise RuntimeError('El AVD no pudo iniciar')
            time.sleep(3)
        else:
            raise RuntimeError('El AVD no terminó el arranque')
        assert adb(serial, 'emu', 'avd', 'name').splitlines()[0].strip() == name
        adb(serial, 'install', '-r', str(APK))
        adb(serial, 'install', '-r', str(TEST_APK))
        if port == 5582:
            adb(serial, 'shell', 'pm', 'grant', 'mx.edu.badi.pastillero', 'android.permission.POST_NOTIFICATIONS')
        output = adb(serial, 'shell', 'am', 'instrument', '-w', '-e', 'class', classes,
                     'mx.edu.badi.pastillero.test/androidx.test.runner.AndroidJUnitRunner', timeout=300)
        (ROOT / ('reports/unified-' + name + '-tests.log')).write_text(output, encoding='utf-8')
        assert 'OK (' + str(expected) + ' tests)' in output, 'Pruebas nativas incompletas'
        RESULTS.append({'avd': name, 'tests': expected, 'status': 'PASS', 'physicalDevice': False})
        if live:
            result = subprocess.run([sys.executable, str(ROOT / 'tools/run_android_live.py')],
                                    cwd=ROOT, env=dict(ENV, BADI_QA_SERIAL=serial))
            assert result.returncode == 0, 'Firebase SDK real no aprobado'
    finally:
        if owned:
            try:
                if adb(serial, 'emu', 'avd', 'name').splitlines()[0].strip() == name:
                    adb(serial, 'emu', 'kill')
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
            try:
                owned.wait(timeout=30)
            except subprocess.TimeoutExpired:
                raise RuntimeError('El AVD iniciado por QA no cerró; no se terminaron otros procesos')
        for file in opened_logs:
            file.close()


if __name__ == '__main__':
    before = hashlib.sha256(APK.read_bytes()).hexdigest()
    with zipfile.ZipFile(APK) as package:
        for file in (ROOT / 'app/src/main/assets/dashboard').rglob('*'):
            if file.is_file():
                assert package.read('assets/dashboard/' + file.relative_to(ROOT / 'app/src/main/assets/dashboard').as_posix()) == file.read_bytes()
    try:
        validate('PastilleroBadiQA', 5580, 'mx.edu.badi.pastillero.RoomOfflineTest,mx.edu.badi.pastillero.RoomVersionTwoTest,mx.edu.badi.pastillero.LegacyWebViewTest', 6, live=True)
        validate('PastilleroBadiV2QA', 5582, 'mx.edu.badi.pastillero.DashboardBridgeTest', 3)
        assert hashlib.sha256(APK.read_bytes()).hexdigest() == before
        print('PASS: 6 pruebas Room/alternativa clásica, 3 puente nativo y 2 SDK Firebase real; sin teléfono físico')
    finally:
        (ROOT / 'reports/unified-android-emulators.json').write_text(json.dumps(RESULTS, indent=2) + '\n', encoding='utf-8')
