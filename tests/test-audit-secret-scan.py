"""Evidence comparison unit cases; never relax the actual secret sanitizer."""
import unittest,subprocess,uuid
from unittest.mock import patch
from pathlib import Path
import audit_secret_scan as scanner
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
 def fixture(self):
  case=scanner.R/'logs/overnight'/('private-fixture-unit-'+uuid.uuid4().hex);root=case/'evidence/case';(root/'security').mkdir(parents=True)
  published=subprocess.check_output(['git','show','6e0a507:evidence/phase-23-attempt-3/security-smoke/secret-redaction.md'],cwd=scanner.R).decode('utf-8-sig')
  raw=published.replace('`[REDACTED]`','`TEST_SECRET_DO_NOT_LEAK_12345`',1)
  (root/scanner.RAW_CANARY).write_text(raw,encoding='utf-8')
  return case,root,published,raw
 def test_private_export_preserves_original_and_redacts_copy(self):
  case,root,published,raw=self.fixture()
  with patch.object(scanner,'R',case),patch.object(scanner.subprocess,'check_output',return_value=published.encode()):self.assertEqual(scanner.prepare_evidence_export(root),[scanner.RAW_CANARY])
  self.assertEqual((root/scanner.RAW_CANARY).read_text(),raw);self.assertNotIn('TEST_SECRET_', (root/scanner.SAFE_CANARY).read_text())
 def test_unexpected_private_content_denied(self):
  case,root,published,raw=self.fixture();(root/scanner.RAW_CANARY).write_text(raw+'unexpected appended content')
  with patch.object(scanner,'R',case),patch.object(scanner.subprocess,'check_output',return_value=published.encode()):
   with self.assertRaisesRegex(AssertionError,'UNEXPECTED_PRIVATE_FIXTURE_CONTENT'):scanner.prepare_evidence_export(root)
  self.assertFalse((root/scanner.SAFE_CANARY).exists())
 def test_changed_raw_fixture_denied(self):
  case,root,published,raw=self.fixture()
  with patch.object(scanner,'R',case),patch.object(scanner.subprocess,'check_output',return_value=published.encode()):scanner.prepare_evidence_export(root)
  (root/scanner.RAW_CANARY).write_text(raw+'changed')
  with patch.object(scanner,'R',case):
   with self.assertRaisesRegex(AssertionError,'PRIVATE_FIXTURE_HASH_CHANGED'):scanner.private_fixture_exclusions(root)
 def test_raw_fixture_must_not_be_tracked(self):
  case,root,published,raw=self.fixture()
  with patch.object(scanner,'R',case),patch.object(scanner.subprocess,'check_output',return_value=published.encode()):scanner.prepare_evidence_export(root)
  with patch.object(scanner,'R',case),patch.object(scanner.subprocess,'check_output',return_value='tracked-raw-fixture'):
   with self.assertRaisesRegex(AssertionError,'PRIVATE_FIXTURE_MUST_NOT_BE_TRACKED'):scanner.private_fixture_exclusions(root)
 def test_stage_excludes_original(self):
  case,root,published,raw=self.fixture()
  with patch.object(scanner,'R',case),patch.object(scanner.subprocess,'check_output',return_value=published.encode()):scanner.prepare_evidence_export(root)
  with patch.object(scanner,'R',case),patch.object(scanner,'private_fixture_exclusions',return_value={scanner.RAW_CANARY}),patch.object(scanner.subprocess,'run') as call:
   scanner.stage_evidence(root)
  self.assertNotIn(str((root/scanner.RAW_CANARY).relative_to(case)),call.call_args.args[0]);self.assertIn(str((root/scanner.SAFE_CANARY).relative_to(case)),call.call_args.args[0])
if __name__=='__main__':unittest.main(verbosity=2)
