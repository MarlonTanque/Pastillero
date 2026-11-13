"""Configura el proyecto dedicado y genera el .ino privado; no imprime valores locales."""
import json
from pathlib import Path
from generate_private_firmware import generate, DATABASE_URL

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'app/google-services.json').read_text(encoding='utf-8-sig'))
if config['project_info']['project_id'] != 'pastillerobadi':
    raise SystemExit('Proyecto Firebase inesperado')
client = next(c for c in config['client'] if c['client_info']['android_client_info']['package_name'] == 'mx.edu.badi.pastillero')
path = ROOT / 'private/firmware.local.json'
values = json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {
    'WIFI_SSID': '', 'WIFI_PASSWORD': '', 'DEVICE_EMAIL': '', 'DEVICE_PASSWORD': ''}
values.update(FIREBASE_DATABASE_URL=DATABASE_URL, FIREBASE_API_KEY=client['api_key'][0]['current_key'], DEVICE_ID='pastillero-01')
props = {}
for line in (ROOT / 'private/integration.local.properties').read_text(encoding='utf-8-sig').splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        props[key.strip()] = value
for field, property_name in [('WIFI_SSID', 'wifi.ssid'), ('WIFI_PASSWORD', 'wifi.password'),
                             ('DEVICE_EMAIL', 'device.email'), ('DEVICE_PASSWORD', 'device.password')]:
    if props.get(property_name):
        values[field] = props[property_name]
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(values, indent=2) + '\n', encoding='utf-8')
(ROOT / 'firebase-config.properties').write_text('databaseUrl=' + DATABASE_URL + '\ndeviceId=pastillero-01\ncommandMode=simulation\n', encoding='utf-8')
generate()
