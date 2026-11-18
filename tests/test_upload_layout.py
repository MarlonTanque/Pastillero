"""Regresiones de la dirección de carga; no abre puertos ni llama esptool."""
from pathlib import Path
import struct
import sys
import tempfile
import json
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from upload_simulation import partitions, check_writes, make_plan


def table():
    entries = [('nvs', 1, 2, 0x9000, 0x40000), ('otadata', 1, 0, 0x49000, 0x2000),
               ('app0', 0, 0x10, 0x50000, 0x1a0000), ('app1', 0, 0x11, 0x1f0000, 0x1a0000)]
    return b''.join(struct.pack('<HBBII16sI', 0x50aa, kind, sub, start, size, name.encode(), 0)
                    for name, kind, sub, start, size in entries)


class UploadLayoutTest(unittest.TestCase):
    def test_hardware_variant_never_reaches_flash_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            build = Path(directory)
            (build / 'build.options.json').write_text(json.dumps({'customBuildProperties': 'compiler.cpp.extra_flags=-DPASTILLERO_DRY_RUN=0'}))
            with self.assertRaises(ValueError): make_plan(build, build)

    def test_custom_offsets(self):
        result = partitions(table())
        self.assertEqual(result['app0']['address'], 0x50000)
        self.assertEqual(result['otadata']['address'], 0x49000)

    def test_default_arduino_app_offset_is_rejected(self):
        with self.assertRaises(ValueError): check_writes(partitions(table()), [(0x10000, 1239904)])

    def test_default_arduino_ota_offset_is_rejected(self):
        with self.assertRaises(ValueError): check_writes(partitions(table()), [(0xe000, 8192)])

    def test_correct_offsets_preserve_nvs(self):
        check_writes(partitions(table()), [(0x1000, 23488), (0x8000, 3072), (0x49000, 8192), (0x50000, 1239904)])

    def test_overlapping_writes_rejected(self):
        with self.assertRaises(ValueError): check_writes(partitions(table()), [(0x50000, 0x3000), (0x51000, 0x1000)])

    def test_missing_or_duplicate_partition_rejected(self):
        for raw in (b'', table() + table()[:32]):
            with self.assertRaises(ValueError): partitions(raw)
