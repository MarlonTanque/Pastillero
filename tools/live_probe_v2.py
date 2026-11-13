"""Sondeo REST V2 de privilegio mínimo: solo PING de QA, sin planes ni eventos de dosis."""
from pathlib import Path
import json, time, uuid, urllib.request, urllib.error, urllib.parse, subprocess

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://pastillerobadi-default-rtdb.firebaseio.com'
report = {'projectId': 'pastillerobadi', 'protocolVersion': 2, 'hardwareUsed': False,
          'tests': {}, 'status': 'PENDING'}

def http(url, method='GET', value=None):
    request = urllib.request.Request(url, method=method,
        data=None if value is None else json.dumps(value).encode(),
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, None

def run():
    config = json.loads((ROOT/'app/google-services.json').read_text(encoding='utf-8-sig'))
    assert config['project_info']['project_id'] == 'pastillerobadi'
    client = next(c for c in config['client']
                  if c['client_info']['android_client_info']['package_name'] == 'mx.edu.badi.pastillero')
    key = client['api_key'][0]['current_key']
    credentials = {}
    for line in (ROOT/'private/integration.local.properties').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            name, value = line.split('=', 1)
            credentials[name.strip()] = value
    identities = {}
    for role in ('owner', 'device'):
        code, body = http('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key='+key,
            'POST', {'email': credentials[role+'.email'], 'password': credentials[role+'.password'],
                     'returnSecureToken': True})
        assert code == 200, 'Authentication unavailable'
        identities[role] = body
    base = URL+'/devices/pastillero-01/v2/'
    def db(role, path, method='GET', body=None):
        auth = '' if role is None else '?auth='+urllib.parse.quote(identities[role]['idToken'])
        return http(base+path+'.json'+auth, method, body)
    def check(name, role, path, method='GET', body=None, allowed=True):
        code, value = db(role, path, method, body)
        report['tests'][name] = code == 200 if allowed else code in (401, 403)
        return value
    check('anonymousReadDenied', None, 'program', allowed=False)
    check('anonymousWriteDenied', None, 'program', 'PUT', {'version': 2}, allowed=False)
    check('deviceCannotPublishProgram', 'device', 'program', 'PUT', {'version': 2}, allowed=False)
    check('ownerInvalidProgramRejected', 'owner', 'program', 'PUT', {'version': 2}, allowed=False)
    identifier = 'qa-'+uuid.uuid4().hex
    now = int(time.time()*1000)
    command = {'type': 'PING', 'requestedBy': identities['owner']['localId'],
               'requestedAt': now, 'expiresAt': now+600000,
               'targetMode': 'simulation', 'planRevision': 0}
    path = 'commandRequests/'+identifier
    check('deviceCannotRequest', 'device', path, 'PUT', command, allowed=False)
    check('ownerRequestsPing', 'owner', path, 'PUT', command)
    check('identicalRetryAccepted', 'owner', path, 'PUT', command)
    value = check('deviceReadsRequest', 'device', path)
    report['tests']['devicePayloadMatches'] = value == command
    check('invalidMovementCommandDenied', 'owner', path, 'PUT', {**command, 'type': 'DISPENSE'}, allowed=False)
    decision = subprocess.check_output([str(ROOT/'reports/command-bridge.exe'),
        'PING', 'simulation', '1', str(now), str(now+600000), str(int(time.time()*1000)), '0', '0'], text=True).strip()
    report['tests']['sameFirmwareCppValidatorOnPC'] = decision == 'OK'
    result = {'status': 'COMPLETED', 'reason': 'OK', 'requestedAt': now,
              'executedAt': int(time.time()*1000), 'planRevision': 0, 'simulation': True}
    path = 'commandResults/simulation/'+identifier
    check('ownerCannotForgeDeviceResult', 'owner', path, 'PUT', result, allowed=False)
    check('deviceWritesSimulationResult', 'device', path, 'PUT', result)
    check('deviceResultRetryAccepted', 'device', path, 'PUT', result)
    value = check('ownerReadsSimulationResult', 'owner', path)
    report['tests']['resultPayloadMatches'] = value == result
    check('resultMutationRejected', 'device', path, 'PUT', {**result, 'executedAt': result['executedAt']+1}, allowed=False)
    report['status'] = 'PASS' if all(report['tests'].values()) else 'FAIL'
    report['limitations'] = ['PC executes only the pure C++ command validator, not ESP32 runtime',
        'Only qa-* PING requests/results in simulation; no schedules or dose events written',
        'No Wi-Fi outage, radio, motor, peripherals or NVS tested']

try:
    run()
except Exception as error:
    report['status'] = 'ERROR'
    report['errorType'] = type(error).__name__
finally:
    target = ROOT/'reports/firebase-setup/live-probe-v2.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Firebase V2 REST:', report['status'], '; checks:', len(report['tests']))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
