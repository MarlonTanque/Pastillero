"""Genera el sketch privado desde el único .ino público; nunca imprime credenciales."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('WIFI_SSID', 'WIFI_PASSWORD', 'FIREBASE_DATABASE_URL', 'FIREBASE_API_KEY',
          'DEVICE_EMAIL', 'DEVICE_PASSWORD', 'DEVICE_ID')
DATABASE_URL = 'https://pastillerobadi-default-rtdb.firebaseio.com'


def render_private(source, values):
    """Sustituye solo siete literales marcados; conserva el resto de la implementación."""
    if set(values) != set(FIELDS) or any(not isinstance(value, str) for value in values.values()):
        raise ValueError('Configuración local incompleta o con campos desconocidos')
    if values['FIREBASE_DATABASE_URL'] != DATABASE_URL or values['DEVICE_ID'] != 'pastillero-01':
        raise ValueError('Proyecto o dispositivo inesperado; no se generó el sketch')
    for name in FIELDS:
        if '\x00' in values[name]:
            raise ValueError('Un campo contiene un terminador interno')
        try:
            values[name].encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError('El dato local no es una cadena Unicode válida') from None
        pattern = r'(?m)^(const char\* ' + name + r' = )"(?:\\.|[^"\\])*"(; // CONFIG_LOCAL)$'
        replacement = json.dumps(values[name], ensure_ascii=False)
        source, count = re.subn(pattern, lambda m: m[1] + replacement + m[2], source)
        if count != 1:
            raise ValueError('Cada campo local debe tener una única declaración marcada')
    return source


def import_config_values(public, private):
    """Permite editar los datos en Arduino IDE, aceptando solo cambios de sus siete literales."""
    values = {}
    for name in FIELDS:
        pattern = r'(?m)^(const char\* ' + name + r' = )("(?:\\.|[^"\\])*")(; // CONFIG_LOCAL)$'
        matches = list(re.finditer(pattern, private))
        if len(matches) != 1:
            raise ValueError('No se encontró una única declaración local marcada')
        try:
            values[name] = json.loads(matches[0][2])
        except ValueError:
            raise ValueError('Literal local inválido: conservar las comillas y escapes del ejemplo') from None
        private = re.sub(pattern, lambda m: m[1] + '"NORMALIZADO"' + m[3], private)
        public, count = re.subn(pattern, lambda m: m[1] + '"NORMALIZADO"' + m[3], public)
        if count != 1:
            raise ValueError('La fuente pública no tiene el marcador esperado')
    if public != private:
        raise ValueError('Hay cambios fuera de la configuración: editar la lógica en la fuente pública')
    render_private(public, values)  # Reutiliza validación de campos/proyecto antes de guardar.
    return values


def generate(import_config=False):
    public = ROOT / 'firmware/PastilleroESP32/PastilleroESP32.ino'
    local = ROOT / 'private/firmware.local.json'
    if not local.exists():
        raise SystemExit('Falta private/firmware.local.json; completar valores localmente, sin enviarlos al chat')
    source = public.read_text(encoding='utf-8-sig')
    destination = ROOT / 'private/firmware/PastilleroESP32'
    destination.mkdir(parents=True, exist_ok=True)
    sketch = destination / 'PastilleroESP32.ino'
    if import_config:
        values = import_config_values(source, sketch.read_text(encoding='utf-8-sig'))
        saved = ROOT / 'archives' / ('private-config-before-import-' + uuid.uuid4().hex[:12])
        saved.mkdir(parents=True)
        shutil.copy2(local, saved / 'firmware.local.json')
        local.write_text(json.dumps(values, indent=2) + '\n', encoding='utf-8')
    values = json.loads(local.read_text(encoding='utf-8-sig'))
    rendered = render_private(source, values)
    # Si existía otra copia, preservarla antes de regenerar; no importar cambios de lógica.
    if sketch.exists() and sketch.read_text(encoding='utf-8-sig') != rendered:
        digest = hashlib.sha256(sketch.read_bytes()).hexdigest()[:12]
        saved = ROOT / 'archives' / ('private-sketch-' + digest) / 'PastilleroESP32.ino'
        saved.parent.mkdir(parents=True, exist_ok=True)
        if not saved.exists():
            shutil.copy2(sketch, saved)
    temporary = sketch.with_suffix('.ino.tmp')
    temporary.write_text(rendered, encoding='utf-8', newline='\n')
    temporary.replace(sketch)
    shutil.copy2(public.parent / 'partitions.csv', destination / 'partitions.csv')
    report = {'publicSource': str(public), 'privateSketch': str(sketch),
              'sourceSha256': hashlib.sha256(public.read_bytes()).hexdigest(),
              'privateMatchesGeneratedSource': True, 'defaultSimulation': True}
    (ROOT / 'reports/private-firmware-generation.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: copia privada generada desde el .ino público, sin cabeceras propias ni valores impresos')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-config', action='store_true', help='Conservar datos editados en el .ino privado; rechaza cambios de lógica')
    generate(parser.parse_args().import_config)
