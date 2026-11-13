from pathlib import Path
import hashlib, json, re, subprocess

root=Path(__file__).resolve().parents[1]
source=root/'firmware/PastilleroESP32'
firmware=(source/'PastilleroESP32.ino').read_text(encoding='utf-8-sig')
source_code=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/','',firmware)
compact=re.sub(r'\s+','',source_code)
assert 'runToNewPosition(' not in source_code
assert not re.search(r'(?<!Task)\bdelay\s*\(',source_code)
assert not re.search(r'\bsetInsecure\s*\(', source_code)
assert '#define PASTILLERO_DRY_RUN 1' in firmware
for marker in ('PIN_PUL,PIN_DIR,0,0,false','motor.setPinsInverted(true,true)',
               'motor.setMaxSpeed(1000)','motor.setAcceleration(500)','motor.run();',
               'planModeMatches','registroLocal.overflowed()','pill-sim'):
    assert marker in compact,marker
original=(root/'original/PastilleroOriginal.ino').read_text(encoding='utf-8-sig')
assert 'Serial.println("\\n' in original and 'Serial.println("\n' not in original
for command in ('a','r','c','s'): assert "'"+command+"'" in original
for entry in json.loads((root/'reports/source-integrity.json').read_text(encoding='utf-8')):
    assert hashlib.sha256((root/entry['file']).read_bytes()).hexdigest()==entry['sha256'],entry['file']
config=json.loads((root/'app/google-services.json').read_text(encoding='utf-8-sig'))
assert config['project_info']['project_id']=='pastillerobadi'
assert config['client'][0]['client_info']['android_client_info']['package_name']=='mx.edu.badi.pastillero'
for name in ('app/google-services.json','firebase-config.properties','private/firmware.local.json',
             'private/integration.local.properties','releases/1.2/PastilleroESP32-hardware.bin'):
    assert subprocess.run(['git','check-ignore','-q',name],cwd=root).returncode==0,name
print('PASS: project integrity, inert default, original sketch, dedicated Firebase and ignored local configuration')
