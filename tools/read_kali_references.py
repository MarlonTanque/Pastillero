"""Lee exclusivamente sketches Arduino del VDI en modo rb, sin modificar la máquina virtual."""
from pathlib import Path
import hashlib
import json
import logging
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'toolchain/inspection-extra'), str(ROOT / 'toolchain/inspection')]
from dissect.hypervisor.disk.vdi import VDI
from dissect.volume.disk.disk import Disk
from dissect.extfs.extfs import ExtFS

IMAGE = Path('C:/Users/milit/Downloads/D/kali-linux-2026.2-virtualbox-amd64/Kali Linux MT/kali-linux-2026.2-virtualbox-amd64.vdi')
DESTINATION = ROOT / 'private/kali-reference'


def inspect():
    logging.disable(logging.CRITICAL)
    records = []
    DESTINATION.mkdir(parents=True, exist_ok=True)
    # Es un lector de bloques: no se monta el sistema ni se abre el disco para escritura.
    with IMAGE.open('rb') as file:
        stream = VDI(file).open()
        for partition in Disk(stream).partitions:
            try:
                filesystem = ExtFS(partition.open())
                base = filesystem.get('/home/kali/Arduino')
            except (ValueError, FileNotFoundError):
                continue
            for directory in base.iterdir():
                if directory.filename in ('.', '..', 'libraries') or directory.filetype != stat.S_IFDIR:
                    continue
                for entry in directory.iterdir():
                    if not entry.filename.endswith('.ino') or entry.filetype != stat.S_IFREG:
                        continue
                    with entry.open() as source:
                        data = source.read()
                    with entry.open() as source:
                        if data != source.read():
                            raise RuntimeError('El sketch cambió durante la lectura; no usar una copia inconsistente')
                    name = directory.filename.replace('.', '_') + '__' + entry.filename
                    destination = DESTINATION / name
                    assert destination.parent.resolve() == DESTINATION.resolve()
                    destination.write_bytes(data)
                    text = data.decode('utf-8-sig')
                    records.append({'guestPath': '/home/kali/Arduino/' + directory.filename + '/' + entry.filename,
                                    'privateCopy': str(destination), 'bytes': len(data),
                                    'lines': len(text.splitlines()), 'sha256': hashlib.sha256(data).hexdigest()})
    if not records:
        raise RuntimeError('No se encontraron sketches Arduino en la partición legible')
    report = {'imageOpenedReadOnly': True, 'guestFilesModified': False, 'references': records}
    (ROOT / 'reports/kali-reference-inspection.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for record in records:
        print(record['guestPath'], record['lines'], 'líneas; copia privada verificada')


if __name__ == '__main__':
    inspect()
