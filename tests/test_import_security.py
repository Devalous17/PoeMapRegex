import base64
import unittest
import zlib

from backend.pob import BuildInputError, decode_build


def export(raw):
    return base64.urlsafe_b64encode(zlib.compress(raw)).decode()


class ImportSecurityTests(unittest.TestCase):
    def test_utf8_export_still_imports(self):
        self.assertEqual(decode_build(export(b'<PathOfBuilding><Build/></PathOfBuilding>')).tag, 'PathOfBuilding')

    def test_entity_declarations_are_rejected_in_all_encodings(self):
        xml = '<!DOCTYPE PathOfBuilding [<!ENTITY x "expanded">]><PathOfBuilding><Build>&x;</Build></PathOfBuilding>'
        for encoding in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-32'):
            with self.subTest(encoding=encoding), self.assertRaises(BuildInputError):
                decode_build(export(xml.encode(encoding)))

    def test_trailing_compressed_payload_is_rejected(self):
        code = base64.urlsafe_b64encode(zlib.compress(b'<PathOfBuilding/>') + zlib.compress(b'other payload')).decode()
        with self.assertRaises(BuildInputError):
            decode_build(code)

    def test_compression_bomb_is_rejected(self):
        with self.assertRaises(BuildInputError):
            decode_build(export(b'<PathOfBuilding>' + b' ' * 2_000_001 + b'</PathOfBuilding>'))
