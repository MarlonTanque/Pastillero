"""Cierra artefactos del firmware unificado únicamente después de cuatro compilaciones aprobadas."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]

def read(path):
    data=path.read_bytes()
    return data.decode('utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig').replace('\r','')

validation=read(ROOT/'reports/unified-firmware-validation.log')
if 'PASS: unified public/private firmware hardware and simulation compiled' not in validation:
    raise SystemExit('PENDING: deben terminar las cuatro compilaciones antes del cierre')
folder=ROOT/'releases/unificado-20261022'
files=sorted(p for p in folder.iterdir() if p.suffix in ('.apk','.bin'))
assert len(files)==5 and len([p for p in files if p.suffix=='.bin'])==4
manifest=[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in files]
(ROOT/'reports/artifact-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
for script,log in [('verify_project.py','integrity.log'),('verify_compilation.py','compiled-source-validation.log'),('verify_version2.py','version2-integrity.log')]:
    result=subprocess.run([sys.executable,str(ROOT/'tools'/script)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    (ROOT/'reports'/log).write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode: raise SystemExit('Falló la validación: '+script)
stats={}
for variant in ('public-simulation','public-hardware','private-hardware','private-simulation'):
    content=read(ROOT/('reports/unified-'+variant+'-build.log'))
    code=re.search(r'Sketch uses (\d+) bytes',content)
    ram=re.search(r'Global variables use (\d+) bytes',content)
    assert code and ram,variant
    stats[variant]={'programBytes':int(code[1]),'globalRamBytes':int(ram[1])}
(ROOT/'reports/firmware-sizes.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
print('PASS: APK y cuatro binarios unificados; instrucciones compiladas, particiones, privacidad y hashes verificados')
