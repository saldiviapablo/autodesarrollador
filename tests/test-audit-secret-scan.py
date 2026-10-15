"""Evidence comparison unit cases; never relax the actual secret sanitizer."""
import unittest
from audit_secret_scan import formatting_only
class Comparison(unittest.TestCase):
 def test_identical(self):self.assertTrue(formatting_only('safe text','safe text'))
 def test_already_redacted_json_spacing(self):self.assertTrue(formatting_only('{"password":"[REDACTED]"}','{"password": "[REDACTED]"}'))
 def test_jsonl_formatting(self):self.assertTrue(formatting_only('{"seq":1}\n{"password":"[REDACTED]"}\n','{"seq":1}\n{"password": "[REDACTED]"}\n'))
 def test_actual_redaction_denied(self):self.assertFalse(formatting_only('{"password":"unit-only-fake-value"}','{"password": "[REDACTED]"}'))
 def test_plain_text_change_denied(self):self.assertFalse(formatting_only('password=unit-only-fake-value','password: [REDACTED]'))
 def test_duplicate_key_mask_denied(self):self.assertFalse(formatting_only('{"password":"unit-only-fake-value","password":"[REDACTED]"}','{"password":"[REDACTED]","password":"[REDACTED]"}'))
 def test_nonstandard_constant_denied(self):self.assertFalse(formatting_only('{"n":NaN,"password":"unit-only-fake-value"}','{"n":NaN,"password":"[REDACTED]"}'))
 def test_unicode_json_encoding_format(self):self.assertTrue(formatting_only('{"ñ":"[REDACTED]"}','{"\u00f1": "[REDACTED]"}'))
 def test_numeric_change_denied(self):self.assertFalse(formatting_only('{"n":1}','{"n":1.0}'))
if __name__=='__main__':unittest.main(verbosity=2)
