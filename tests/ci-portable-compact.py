"""Portable subset of legacy tests without real Windows profiles or runner paths.

We deliberately do not run machine-bound tests here: the project security
policy requires absolute Windows paths and local supervisor installation.
"""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("legacy_compact_ci",ROOT/"tests/test-onboarding-compact.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PORTABLE=(
    "test_compact_roundtrip",
    "test_criteria_count_cap",
    "test_duplicate_key_denied",
    "test_fixed_policies_are_derived_not_generated",
    "test_live_overview_required",
    "test_long_utf8_fixture",
    "test_loopback_research_denied",
    "test_multiple_yaml_documents_denied",
    "test_multisource_research_lowers_to_query",
    "test_nan_denied",
    "test_native_incomplete_denied",
    "test_native_loaded_tools_denied_before_inference",
    "test_native_oversize_denied",
    "test_native_request_caps_and_schema",
    "test_native_tool_call_denied",
    "test_native_wrong_route_denied",
    "test_no_push_policy_fixed",
    "test_raw_byte_cap",
    "test_seed_byte_cap",
    "test_seed_must_be_source_string",
    "test_single_json_fence_supported",
    "test_summary_cannot_repeat_brief",
    "test_task_count_cap",
    "test_unique_explicit_research_source_lowered",
    "test_web_policy_matches_plan",
    "test_yaml_alias_denied",
    "test_yaml_custom_tag_denied",
    "test_yaml_duplicate_denied",
    "test_yaml_literal_source_quotes_preserved",
)
suite=unittest.TestSuite(module.Compact(method) for method in PORTABLE)
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
