"""Comprueba conservación V2 sin suponer que las funciones nuevas son idénticas a V1."""
from pathlib import Path
import hashlib, json, os, re, subprocess, zipfile

ROOT=Path(__file__).resolve().parents[1]
backup=Path(json.loads((ROOT/'reports/version2-backup.json').read_text())['backup'])
checks={}
records=json.loads((backup/'backup-manifest.json').read_text())
for record in records:
    saved=backup/record['file']
    assert hashlib.sha256(saved.read_bytes()).hexdigest()==record['sha256'], 'Backup integrity failed'
    if record['file'].startswith(('releases/','original/','app/schemas/')):
        assert saved.read_bytes()==(ROOT/record['file']).read_bytes(), record['file']
checks['backupFilesVerified']=len(records)
checks['previousReleasesOriginalSketchAndRoomSchemasPreserved']=True
for name in ('private/integration.local.properties','app/google-services.json'):
    assert (ROOT/name).read_bytes()==(backup/name).read_bytes(), 'Protected configuration changed'
    assert subprocess.run(['git','check-ignore','-q',name],cwd=ROOT).returncode==0
# Los valores anteriores ahora están en JSON privado; el certificado está dentro del .ino.
private_values=json.loads((ROOT/'private/firmware.local.json').read_text(encoding='utf-8-sig'))
old_header=(backup/'firmware/PastilleroESP32'/'secrets.h').read_text(encoding='utf-8-sig')
for key,quoted in re.findall(r'^#define (\w+) ("(?:\\.|[^"\\])*")$',old_header,re.M):
    value=json.loads(quoted)
    target='FIREBASE_DATABASE_URL' if key=='FIREBASE_HOST' else key
    assert private_values[target]==('https://'+value if key=='FIREBASE_HOST' else value)
public_source=(ROOT/'firmware/PastilleroESP32/PastilleroESP32.ino').read_text(encoding='utf-8-sig')
old_trust=(backup/'firmware/PastilleroESP32'/'trust.h').read_text(encoding='utf-8-sig')
assert old_trust.replace('#pragma once\n','',1).strip() in public_source
for name in ('private/firmware.local.json','private/firmware/PastilleroESP32/PastilleroESP32.ino'):
    assert subprocess.run(['git','check-ignore','-q',name],cwd=ROOT).returncode==0
assert not list((ROOT/'firmware/PastilleroESP32').glob('*.h'))
checks['privateConfigurationAndTrustUnchanged']=True
rules=json.loads((ROOT/'firebase/database.rules.json').read_text())
assert 'v2' in rules['rules']['devices']['$device']
rules['rules']['devices']['$device'].pop('v2')
assert rules==json.loads((backup/'firebase/database.rules.json').read_text())
checks['legacyRulesSemanticallyUnchanged']=True
config=public_source
assert '#define PASTILLERO_DRY_RUN 1' in config
assert 'DEFAULT_POSITIONS = 5' in config
for peripheral in ('LCD','EXIT','SERVO','PUMP'):
    assert '#define PASTILLERO_'+peripheral+'_AVAILABLE 0' in config
checks['simulationFivePositionsAndOptionalOutputsDisabled']=True
activity=(ROOT/'app/src/main/java/mx/edu/badi/pastillero/DashboardActivity.java').read_text()
assert not re.search(r'\.addJavascriptInterface\s*\(',activity)
assert 'Collections.singleton(BridgeProtocol.ORIGIN)' in activity
assert 'handler.cancel()' in activity
assert 'setAllowFileAccess(false)' in activity and 'setAllowContentAccess(false)' in activity
checks['originRestrictedBridgeAndTlsRejection']=True
database=(ROOT/'app/src/main/java/mx/edu/badi/pastillero/PastilleroDatabase.java').read_text()
assert 'version = 4' in database and 'MIGRATION_3_4' in database
assert 'fallbackToDestructiveMigration(' not in database and 'DROP TABLE' not in re.sub(r'/\*[\s\S]*?\*/','',database)
checks['additiveRoomMigration4']=True
# No se registran valores privados ni huellas de contraseñas.
private={}
for line in (ROOT/'private/integration.local.properties').read_text(encoding='utf-8-sig').splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        k,v=line.split('=',1)
        if k.strip().endswith(('.password','.email')) and v: private[k.strip()]=v
sources=[]
for folder in ('app/src','web/src','web/e2e','docs','firebase','admin-backend','tools','tests','firmware/PastilleroESP32'):
    # Podar dependencias antes de recorrerlas; solo se revisa código propio y documentación.
    for directory, children, names in os.walk(ROOT/folder):
        children[:] = [name for name in children if name not in ('node_modules','__pycache__','build')]
        for name in names:
            p = Path(directory)/name
            if name == 'secrets.h': continue  # Archivo privado comprobado/ignorado arriba.
            if p.suffix in ('.java','.xml','.ts','.tsx','.css','.html','.md','.mjs','.json','.py','.ps1','.cpp','.ino','.h','.csv'):
                sources.append(p)
for p in sources:
    text=p.read_text(encoding='utf-8-sig')
    assert not any(v in text for v in private.values()), 'Private value found in '+str(p.relative_to(ROOT))
apk=ROOT/'app/build/outputs/apk/debug/app-debug.apk'
if apk.exists():
    with zipfile.ZipFile(apk) as package:
        for entry in package.infolist():
            data=package.read(entry)
            assert not any(v.encode() in data or v.encode('utf-16-le') in data for v in private.values()), 'Private value in APK'
    checks['apkContainsNoAccountCredentials']=True
checks['sourceAndGuideFilesScannedWithoutCredentials']=len(sources)
(ROOT/'reports/version2-integrity.json').write_text(json.dumps(checks,indent=2)+'\n')
print('PASS: V2 preservation, additive Room migration, rules isolation, inert defaults and credential exclusion')
