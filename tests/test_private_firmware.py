"""Pruebas del generador: datos ficticios, ninguna cuenta real ni acceso a hardware."""
from pathlib import Path
import json
import re
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from generate_private_firmware import render_private, import_config_values, FIELDS, DATABASE_URL


class PrivateFirmwareTest(unittest.TestCase):
    def setUp(self):
        self.source = '\n'.join('const char* ' + key + ' = "INTRODUCIR_DATO"; // CONFIG_LOCAL'
                                for key in FIELDS) + '\nvoid ejemplo() { /* conservar lógica */ }\n'
        self.values = {key: 'dato-ficticio' for key in FIELDS}
        self.values.update(FIREBASE_DATABASE_URL=DATABASE_URL, DEVICE_ID='pastillero-01')

    def test_generation_is_deterministic(self):
        self.assertEqual(render_private(self.source, self.values), render_private(self.source, self.values))

    def test_public_source_is_not_modified(self):
        before = self.source
        generated = render_private(self.source, self.values)
        self.assertEqual(before, self.source)
        self.assertNotIn('INTRODUCIR_DATO', generated)

    def test_cpp_string_escaping_preserves_data(self):
        self.values['WIFI_PASSWORD'] = 'ficticio"\\\nñ😀'
        text = render_private(self.source, self.values)
        literal = re.search(r'WIFI_PASSWORD = ("(?:\\.|[^"\\])*");', text)[1]
        self.assertEqual(json.loads(literal), self.values['WIFI_PASSWORD'])
        # Comprobar bytes en C++ real evita confundir escapes JSON con literales C++.
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='generator-test-', dir=root / 'reports') as directory:
            temporary = Path(directory).resolve()
            self.assertTrue(temporary.is_relative_to((root / 'reports').resolve()))
            expected = ','.join(hex(b) for b in self.values['WIFI_PASSWORD'].encode('utf-8')) + ',0'
            source = '#include <assert.h>\n#include <string.h>\n' + text
            source += '\nint main(){const unsigned char expected[]={' + expected + '};assert(!strcmp(WIFI_PASSWORD,reinterpret_cast<const char*>(expected)));}\n'
            (temporary / 'sample.cpp').write_text(source, encoding='utf-8')
            subprocess.run([str(root / 'toolchain/zig/zig.exe'), 'c++', '-std=c++17', str(temporary / 'sample.cpp'), '-o', str(temporary / 'sample.exe')], check=True, capture_output=True)
            subprocess.run([str(temporary / 'sample.exe')], check=True, capture_output=True)

    def test_missing_and_unknown_fields_are_rejected(self):
        missing = dict(self.values)
        missing.pop('DEVICE_PASSWORD')
        for data in (missing, dict(self.values, unknown='dato')):
            with self.assertRaises(ValueError): render_private(self.source, data)

    def test_another_database_or_device_is_rejected(self):
        for field, value in [('FIREBASE_DATABASE_URL', 'https://otro.firebaseio.com'), ('DEVICE_ID', 'otro')]:
            with self.assertRaises(ValueError): render_private(self.source, dict(self.values, **{field: value}))

    def test_non_string_or_null_terminator_is_rejected(self):
        for value in (None, 123, 'dato\x00oculto', 'surrogado\ud800'):
            with self.assertRaises(ValueError): render_private(self.source, dict(self.values, WIFI_SSID=value))

    def test_missing_or_duplicate_marker_is_rejected(self):
        for text in (self.source.replace('WIFI_SSID', 'otro'), self.source + self.source.splitlines()[0]):
            with self.assertRaises(ValueError): render_private(text, self.values)

    def test_all_non_configuration_bytes_are_preserved(self):
        generated = render_private(self.source, self.values)
        def normalized(text):
            return re.sub(r'(?m)^(const char\* \w+ = )"(?:\\.|[^"\\])*"(; // CONFIG_LOCAL)$',
                          r'\1"VALOR"\2', text)
        self.assertEqual(normalized(self.source), normalized(generated))

    def test_configuration_can_be_imported_from_private_ino(self):
        generated = render_private(self.source, self.values)
        self.assertEqual(import_config_values(self.source, generated), self.values)

    def test_import_preserves_typed_unicode_quotes_and_slashes(self):
        self.values['WIFI_PASSWORD'] = 'ficticioñ😀"\\'
        generated = render_private(self.source, self.values).replace('\\u00f1', 'ñ')
        self.assertEqual(import_config_values(self.source, generated), self.values)

    def test_import_rejects_changes_to_logic(self):
        generated = render_private(self.source, self.values).replace('void ejemplo()', 'void otraFuncion()')
        with self.assertRaises(ValueError): import_config_values(self.source, generated)

    def test_import_rejects_missing_duplicate_or_other_project(self):
        generated = render_private(self.source, self.values)
        for text in (generated.replace('WIFI_SSID', 'otro'), generated + generated.splitlines()[0],
                     generated.replace(DATABASE_URL, 'https://otro.firebaseio.com')):
            with self.assertRaises(ValueError): import_config_values(self.source, text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
