"""Carga únicamente simulación y obtiene los offsets de la tabla real, sin escribir NVS."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]


def partitions(data):
    result = {}
    for offset in range(0, len(data) - 31, 32):
        magic, kind, subtype, address, size, label, flags = struct.unpack_from('<HBBII16sI', data, offset)
        if magic != 0x50aa:
            continue
        name = label.rstrip(b'\0').decode('ascii')
        if name in result or not size or address + size > 0x400000:
            raise ValueError('Tabla de particiones no admitida')
        result[name] = {'type': kind, 'subtype': subtype, 'address': address, 'size': size}
    if not all(key in result for key in ('nvs', 'otadata', 'app0')):
        raise ValueError('Faltan particiones requeridas')
    ranges = sorted((p['address'], p['address'] + p['size']) for p in result.values())
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise ValueError('Las particiones se solapan')
    if result['app0']['type'] != 0 or result['otadata']['size'] != 8192:
        raise ValueError('Formato de aplicación/OTA no admitido')
    return result


def check_writes(table, writes):
    protected = table['nvs']
    start, end = protected['address'], protected['address'] + protected['size']
    ordered = sorted((address, address + size) for address, size in writes)
    for a, b in ordered:
        if a < 0 or a >= b or b > 0x400000 or (a < end and b > start):
            raise ValueError('Escritura fuera de rango o sobre NVS: operación bloqueada')
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('Las escrituras se solapan')


def make_plan(build, platform):
    options = json.loads((build / 'build.options.json').read_text(encoding='utf-8-sig'))
    if options.get('customBuildProperties') != 'compiler.cpp.extra_flags=-DPASTILLERO_DRY_RUN=1':
        raise ValueError('Solo se admite el binario compilado con DRY_RUN=1')
    table_file = build / 'PastilleroESP32.ino.partitions.bin'
    table = partitions(table_file.read_bytes())
    image = build / 'PastilleroESP32.ino.bin'
    if image.read_bytes()[:1] != b'\xe9' or image.stat().st_size > table['app0']['size']:
        raise ValueError('Imagen ESP32 no válida o demasiado grande')
    files = [(0x1000, build / 'PastilleroESP32.ino.bootloader.bin'), (0x8000, table_file),
             (table['otadata']['address'], platform / 'tools/partitions/boot_app0.bin'),
             (table['app0']['address'], image)]
    check_writes(table, [(address, path.stat().st_size) for address, path in files])
    return table, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--execute', action='store_true', help='Realizar carga; sin esto solo comprueba archivos')
    args = parser.parse_args()
    if not re.fullmatch(r'COM[1-9][0-9]*', args.port):
        parser.error('Usar un puerto COM local comprobado; no se admiten endpoints remotos')
    platform = Path(os.environ['LOCALAPPDATA']) / 'Arduino15/packages/esp32/hardware/esp32/3.3.12'
    esptool = platform.parents[2] / 'tools/esptool_py/5.3.1/esptool.exe'
    build = ROOT / 'firmware/build/unified-private-simulation'
    table, files = make_plan(build, platform)
    print('Plan de simulación:', ', '.join(hex(address) for address, _ in files), '; NVS excluida')
    if not args.execute:
        return
    backup = ROOT / 'private' / ('upload-backup-' + uuid.uuid4().hex[:12])
    backup.mkdir()
    def command(after, *extra):
        result = subprocess.run([str(esptool), '--chip', 'esp32', '--port', args.port,
                                 '--baud', '115200', '--after', after, *extra],
                                capture_output=True, timeout=300)
        with (backup / 'esptool.log').open('ab') as log:
            log.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('No se completó la operación; revisar el registro privado, sin borrar la memoria')
    old_table = backup / 'partition-table.bin'
    command('no-reset', 'read-flash', '0x8000', '0x1000', str(old_table))
    actual = partitions(old_table.read_bytes())
    if any(actual[key] != table[key] for key in ('nvs', 'otadata', 'app0')):
        raise ValueError('La tabla instalada requiere migración previa; no se cambió su contenido')
    nvs = table['nvs']
    command('no-reset', 'read-flash', hex(nvs['address']), hex(nvs['size']), str(backup / 'nvs.bin'))
    arguments = ['write-flash', '--flash-mode', 'keep', '--flash-freq', 'keep', '--flash-size', 'keep']
    for address, path in files:
        arguments.extend([hex(address), str(path)])
    command('hard-reset', *arguments)
    record = {'port': args.port, 'simulation': True, 'nvsWritten': False,
              'offsets': [hex(address) for address, _ in files],
              'applicationSha256': hashlib.sha256(files[-1][1].read_bytes()).hexdigest(),
              'backup': str(backup), 'status': 'FLASH_VERIFIED_BOOT_PENDING'}
    (ROOT / 'reports/wifi-upload-layout-safe.json').write_text(json.dumps(record, indent=2) + '\n')
    print('PASS: carga verificada con offsets de la tabla y respaldo NVS; falta comprobar el arranque')


if __name__ == '__main__':
    main()
