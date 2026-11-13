"""Verifica respaldo, fuente única, equivalencia del control y ausencia de cabeceras propias."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
from generate_private_firmware import FIELDS, render_private

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return path.read_text(encoding='utf-8-sig')


def masked(source):
    pattern = r'R"(?P<delimiter>\w*)\([\s\S]*?\)(?P=delimiter)"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/'
    return re.sub(pattern, lambda m: ' ' * len(m[0]), source)


def block(source, start):
    code = masked(source)
    brace = code.index('{', start)
    depth, end = 1, brace + 1
    while depth:
        depth += (code[end] == '{') - (code[end] == '}')
        end += 1
    return source[start:end]


def functions(source):
    return {m[1]: block(source, m.start()) for m in
            re.finditer(r'(?m)^(?:int64_t|bool|void|String) (\w+)\([^;{}]*?\)\s*\{', source)}


def tokens(source):
    lexer = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/|\w+|[^\s]'
    return [x for x in re.findall(lexer, source) if not x.startswith(('//', '/*'))]


def verify(compiled=False):
    backup = Path(json.loads(read(ROOT / 'reports/unification-backup.json'))['backup'])
    records = json.loads(read(backup / 'backup-manifest.json'))
    for record in records:
        assert hashlib.sha256((backup / record['file']).read_bytes()).hexdigest() == record['sha256']
    folder = ROOT / 'firmware/PastilleroESP32'
    source = read(folder / 'PastilleroESP32.ino')
    assert {p.name for p in folder.iterdir() if p.is_file()} == {'PastilleroESP32.ino', 'partitions.csv'}
    assert not re.search(r'#\s*include\s+"', source)
    assert '#define PASTILLERO_DRY_RUN 1' in source
    assert re.findall(r'^// (\d+)\. ', source, re.M) == [str(n) for n in range(1, 18)]
    values = json.loads(read(ROOT / 'private/firmware.local.json'))
    private = ROOT / 'private/firmware/PastilleroESP32'
    assert read(private / 'PastilleroESP32.ino') == render_private(source, values)
    assert {p.name for p in private.iterdir() if p.is_file()} == {'PastilleroESP32.ino', 'partitions.csv'}
    assert (folder / 'partitions.csv').read_bytes() == (backup / 'firmware/PastilleroESP32/partitions.csv').read_bytes()
    for key in FIELDS:
        assert source.count('const char* ' + key + ' = ') == 1
    for file in (ROOT / 'tests').glob('*.cpp'):
        assert not re.search(r'#\s*include\s*["<](?:[^"\n]*/)?(?:Commands|Controller|config|secrets|trust)\.h[">]', read(file))
    old = read(backup / 'firmware/PastilleroESP32/PastilleroESP32.ino')
    before, after = functions(old), functions(source)
    assert set(after) == set(before) | {'atenderDispensacion'}
    expected = dict(before)
    expected['solicitudHttps'] = expected['solicitudHttps'].replace('const String& contentType = "application/json"', 'const String& contentType')
    expected['sincronizarConFirebase'] = expected['sincronizarConFirebase'].replace('String("https://") + FIREBASE_HOST', 'String(FIREBASE_DATABASE_URL)')
    expected['tareaFirebase'] = expected['tareaFirebase'].replace('strlen(FIREBASE_HOST)', 'strlen(FIREBASE_DATABASE_URL)')
    expected['setup'] = expected['setup'].replace('secuencia 1,2,3.', 'secuencia 1,2,3,4 y regreso a cero.')
    loop = before['loop']
    first, last = loop.index('    auto previous ='), loop.index('    actualizarIndicadores(ms);')
    expected['loop'] = loop[:first] + '    atenderDispensacion(ms);\n' + loop[last:]
    expected['atenderDispensacion'] = 'void atenderDispensacion(uint32_t ms) {\n' + loop[first:last] + '}\n'
    for name in expected:
        assert tokens(after[name]) == tokens(expected[name]), 'Cambio inesperado de instrucciones: ' + name
    # Obtener nombres de declaraciones sin confundir palabras incluidas en comentarios.
    classes = re.findall(r'\bclass\s+(\w+)', masked(old))
    for name in set(classes):
        old_match = re.search(r'\bclass\s+' + re.escape(name) + r'\s*(?::[^{}]+)?\s*\{', old)
        new_match = re.search(r'\bclass\s+' + re.escape(name) + r'\s*(?::[^{}]+)?\s*\{', source)
        assert old_match and new_match
        assert tokens(block(old, old_match.start())) == tokens(block(source, new_match.start())), name
    assert set(re.findall(r'\bclass\s+(\w+)', masked(source))) == set(classes)
    # Solo DashboardActivity cambia en Android; Room, DAO, entidades y migraciones quedan idénticos.
    for record in records:
        name = record['file']
        if name.startswith('app/src/') and not name.endswith('/DashboardActivity.java'):
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == record['sha256'], name
    for record in json.loads(read(ROOT / 'reports/crudsqlite1-reference-source-hashes.json')):
        assert hashlib.sha256(Path(record['file']).read_bytes()).hexdigest() == record['sha256']
    report = {'backupFilesVerified': len(records), 'ownHeaderIncludes': 0, 'ownHeadersRequired': False,
              'publicFolderFiles': sorted(p.name for p in folder.iterdir() if p.is_file()),
              'sections': 17, 'preservedEsp32Functions': len(before), 'extractedHelper': 'atenderDispensacion',
              'newFirmwareClasses': 0, 'existingClassInstructionsPreserved': True,
              'roomAndOtherAndroidSourceBytesPreserved': True, 'crudsqlite1SourceHashesUnchanged': True,
              'privateMatchesSinglePublicSource': True, 'defaultSimulation': True, 'hardwareUsed': False}
    if compiled:
        subprocess.run([sys.executable, str(ROOT / 'tools/verify_compilation.py')], cwd=ROOT, check=True)
        report['fourCompilationsVerified'] = True
    (ROOT / 'reports/unification-integrity.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: fuente única, 17 secciones, 22 funciones conservadas, cero cabeceras propias y Room/CRUDSQLITE1 intactos')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiled', action='store_true')
    verify(parser.parse_args().compiled)
