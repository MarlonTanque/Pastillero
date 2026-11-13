"""Comprueba las cuatro compilaciones contra la única fuente pública y su copia generada."""
from pathlib import Path
import hashlib,json,re
from generate_private_firmware import render_private
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'firmware/PastilleroESP32'
public=(source/'PastilleroESP32.ino').read_text(encoding='utf-8-sig')
private=ROOT/'private/firmware/PastilleroESP32'
values=json.loads((ROOT/'private/firmware.local.json').read_text(encoding='utf-8-sig'))
assert (private/'PastilleroESP32.ino').read_text(encoding='utf-8-sig')==render_private(public,values)
assert not list(source.glob('*.h')) and not list(private.glob('*.h'))
assert not re.search(r'#include\s+"',public)
assert '#define PASTILLERO_DRY_RUN 1' in public

def tokens(text):
    text=re.sub(r'^#line .*$', '', text, flags=re.M)
    lexer=r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/|\w+|[^\s]'
    return [x for x in re.findall(lexer,text) if not x.startswith(('//','/*'))]

for variant in ('public-simulation','public-hardware','private-hardware','private-simulation'):
    original=private if variant.startswith('private-') else source
    build=ROOT/'firmware/build'/('unified-'+variant)
    assert (build/'partitions.csv').read_bytes()==(original/'partitions.csv').read_bytes()
    assert not list((build/'sketch').glob('*.h'))
    options=json.loads((build/'build.options.json').read_text(encoding='utf-8-sig'))
    assert 'esp32doit-devkit-v1' in options['fqbn']
    expected='1' if variant.endswith('simulation') else '0'
    assert 'compiler.cpp.extra_flags=-DPASTILLERO_DRY_RUN='+expected in options['customBuildProperties']
    compiled=(build/'sketch/PastilleroESP32.ino.cpp').read_text(encoding='utf-8-sig')
    iterator=iter(tokens(compiled))
    for token in tokens((original/'PastilleroESP32.ino').read_text(encoding='utf-8-sig')):
        assert any(candidate==token for candidate in iterator),'Compiled sketch mismatch: '+variant
for entry in json.loads((ROOT/'reports/artifact-hashes.json').read_text(encoding='utf-8-sig')):
    path=ROOT/'releases/unificado-20261022'/entry['file']
    assert path.stat().st_size==entry['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest().upper()==entry['sha256']
    if path.suffix=='.bin': assert path.read_bytes()[0]==0xe9
print('PASS: four compiled sketches, no own headers, partitions, inert default and artifact hashes match')
