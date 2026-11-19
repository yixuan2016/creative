from __future__ import annotations

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from pdks_capture_runtime.service import CaptureRuntime
from pdks_capture_runtime.cli import start_dws_consumer_after_preflight
from pdks_capture_runtime.errors import ConsentRequiredError
from pdks_capture_runtime.connectors.dws import (
    DWSCLI, DWSCLIError, DWSConsumer, DWSConnector,
    DWS_EVENT_CATALOG, validate_consume_spec,
)

OWNER = "urn:pdks:owner:dws-test"
PROFILE = "corp-123:user-456"


class FakeCompleted:
    def __init__(self, stdout="{}", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode




class FakePopen:
    def __init__(self, argv, **kwargs):
        self.argv = argv
        self.stdin = StringIO()
        self.stdout = StringIO('{"event_id":"evt-stream-1","content":"hello"}\n')
        self.stderr = StringIO('[event] ready event_key=user_im_message_receive_at bus_pid=123 subscribe_id=sub-1\n')
        self.returncode = None
    def poll(self):
        return self.returncode
    def wait(self, timeout=None):
        self.returncode = 0
        return 0
    def terminate(self):
        self.returncode = -15

class DWSConnectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.runtime = CaptureRuntime(self.base / "pdks.sqlite3", self.base / "vault")
        self.runtime.create_owner(OWNER)
        self.consent = self.runtime.create_consent(
            OWNER, "dingtalk", ["personal_knowledge_capture"], ["read"],
            ["work"], ["capture"], note="DWS connector test consent"
        )
        self.connector = DWSConnector(
            self.runtime, OWNER, self.consent["consent_ref"], PROFILE,
            cli=DWSCLI(binary="/fake/dws", profile=PROFILE, runner=lambda *a, **k: FakeCompleted())
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_catalog_has_33_official_personal_event_keys(self):
        self.assertEqual(len(DWS_EVENT_CATALOG), 33)

    def test_ingests_dws_event_as_dingtalk_system_sync_source(self):
        event = {
            "event_id": "evt-001", "event_time": "2026-11-19T09:30:00+08:00",
            "content": "项目评审明天下午三点开始", "sender": "user-1",
            "conversation_id": "conv-1",
        }
        result = self.connector.ingest_event("user_im_message_receive_at", event)
        self.assertEqual(result["status"], "awaiting_agent")
        capture = self.runtime.get_capture(OWNER, result["capture_id"])
        self.assertEqual(capture["source_kind"], "dingtalk")
        self.assertEqual(capture["capture_method"], "system_sync")
        self.assertEqual(capture["origin_system"], "dingtalk_dws_cli")
        self.assertEqual(capture["occurred_at"], "2026-11-19T09:30:00+08:00")
        self.assertIn("项目评审明天下午三点开始", capture["extracted_text"])

    def test_event_ingestion_is_idempotent(self):
        event = {"event_id": "evt-002", "content": "重复消息"}
        first = self.connector.ingest_event("user_im_message_receive_at", event)
        second = self.connector.ingest_event("user_im_message_receive_at", event)
        self.assertFalse(first.get("duplicate", False))
        self.assertTrue(second.get("duplicate", False))
        self.assertEqual(first["source_id"], second["source_id"])

    def test_event_idempotency_does_not_depend_on_local_receive_clock(self):
        from unittest.mock import patch
        event = {"event_id": "evt-002-clock", "content": "重复消息"}
        with patch("pdks_capture_runtime.connectors.dws.connector.utc_now", side_effect=["2026-11-19T01:00:00Z", "2026-11-19T01:00:02Z"]):
            first = self.connector.ingest_event("user_im_message_receive_at", event)
            second = self.connector.ingest_event("user_im_message_receive_at", event)
        self.assertEqual(first["source_id"], second["source_id"])
        self.assertTrue(second.get("duplicate", False))

    def test_calendar_uses_biz_id_for_stable_identity(self):
        event = {"biz_id": "calendar-biz-9", "event_id": "stream-9", "calendar_event_id": "calendar-resource-9"}
        result = self.connector.ingest_event("user_calendar_event_changed", event)
        with self.runtime._connection() as con:
            source = con.execute("SELECT source_locator FROM source_assets WHERE source_id=?", (result["source_id"],)).fetchone()
        self.assertIn("biz_id:calendar-biz-9", source["source_locator"])

    def test_minutes_summary_enrichment_is_explicit_and_uses_read_only_command(self):
        calls = []
        def runner(argv, **kwargs):
            calls.append(argv)
            return FakeCompleted(stdout=json.dumps({"result": {"summary": "项目决定先做试点"}}))
        cli = DWSCLI(binary="/fake/dws", profile=PROFILE, runner=runner)
        connector = DWSConnector(self.runtime, OWNER, self.consent["consent_ref"], PROFILE, cli=cli)
        result = connector.enrich_minutes_summary("task-123")
        self.assertEqual(result["status"], "awaiting_agent")
        self.assertIn(["minutes", "get", "summary", "--id", "task-123", "--format", "json"], [x[3:] for x in calls])

    def test_capture_without_consent_is_rejected(self):
        connector = DWSConnector(self.runtime, OWNER, "urn:pdks:consent:missing", PROFILE)
        with self.assertRaises(ConsentRequiredError):
            connector.ingest_event("user_im_message_receive_at", {"event_id": "evt-3"})

    def test_preflight_checks_consent_profile_and_event_schema(self):
        class StubCLI:
            def auth_status(self): return {"authenticated": True, "profile": PROFILE}
            def event_schema(self, key): return {"event_key": key, "schema": {"type": "object"}}
        connector = DWSConnector(self.runtime, OWNER, self.consent["consent_ref"], PROFILE, cli=StubCLI())
        result = connector.validate_preflight(["user_im_message_receive_at"])
        self.assertEqual(result["consent"], "active")
        self.assertEqual(result["event_schemas_checked"], ["user_im_message_receive_at"])
        self.assertTrue(result["profile_verified"])

    def test_preflight_rejects_wrong_profile(self):
        class StubCLI:
            def auth_status(self): return {"authenticated": True, "profile": "another-corp:another-user"}
            def event_schema(self, key): return {}
        connector = DWSConnector(self.runtime, OWNER, self.consent["consent_ref"], PROFILE, cli=StubCLI())
        with self.assertRaises(PermissionError):
            connector.validate_preflight(["user_im_message_receive_at"])

    def test_preflight_fails_closed_for_indeterminate_or_damaged_auth_state(self):
        bad_states = [
            {"authenticated": True, "profile": PROFILE, "reason": "cannot determine local state"},
            {"authenticated": True, "profile": PROFILE, "local_state_requires_repair": True},
            {"authenticated": True, "profile": PROFILE, "local_state_unreadable": True},
            {"authenticated": True, "profile": PROFILE, "token_valid": False},
            {"profile": PROFILE},
        ]
        for auth_state in bad_states:
            class StubCLI:
                def auth_status(self_nonlocal): return auth_state
                def event_schema(self_nonlocal, key): return {"event_key": key}
            connector = DWSConnector(self.runtime, OWNER, self.consent["consent_ref"], PROFILE, cli=StubCLI())
            with self.subTest(auth_state=auth_state):
                with self.assertRaises(PermissionError):
                    connector.validate_preflight(["user_im_message_receive_at"])

    def test_preflight_requires_exact_profile_and_nonempty_schema(self):
        class StubCLI:
            def auth_status(self): return {"authenticated": True, "profile": PROFILE}
            def event_schema(self, key): return {}
        connector = DWSConnector(self.runtime, OWNER, self.consent["consent_ref"], PROFILE, cli=StubCLI())
        with self.assertRaises(PermissionError):
            connector.validate_preflight(["user_im_message_receive_at"])

    def test_consumer_is_never_started_when_preflight_fails(self):
        class BadConnector:
            def validate_preflight(self, event_keys):
                raise PermissionError("not authorized")
        class Consumer:
            started = False
            def start(self): self.started = True
        consumer = Consumer()
        with self.assertRaises(PermissionError):
            start_dws_consumer_after_preflight(BadConnector(), consumer, ["user_im_message_receive_at"])
        self.assertFalse(consumer.started)

    def test_consumer_starts_only_after_successful_preflight(self):
        order = []
        class GoodConnector:
            def validate_preflight(self, event_keys):
                order.append("preflight")
                return {"consent": "active"}
        class Consumer:
            def start(self): order.append("start")
        result = start_dws_consumer_after_preflight(GoodConnector(), Consumer(), ["user_im_message_receive_at"])
        self.assertEqual(order, ["preflight", "start"])
        self.assertEqual(result["consent"], "active")

    def test_preflight_rejects_unauthenticated_dws_profile(self):
        class StubCLI:
            def auth_status(self): return {"authenticated": False, "profile": PROFILE}
            def event_schema(self, key): return {}
        connector = DWSConnector(self.runtime, OWNER, self.consent["consent_ref"], PROFILE, cli=StubCLI())
        with self.assertRaises(PermissionError):
            connector.validate_preflight(["user_im_message_receive_at"])

    def test_unknown_event_key_is_rejected(self):
        with self.assertRaises(ValueError):
            self.connector.ingest_event("user_im_message_send", {"event_id": "evt-4"})


class DWSCLIContractTests(unittest.TestCase):
    def test_cli_binary_must_be_the_official_dws_executable(self):
        with self.assertRaises(ValueError):
            DWSCLI(binary="/bin/sh").version()

    def test_profile_is_a_global_flag_before_product_command(self):
        captured = {}
        def runner(argv, **kwargs):
            captured["argv"] = argv
            captured["kwargs"] = kwargs
            return FakeCompleted(stdout="v1.0.68\n")
        cli = DWSCLI(binary="/fake/dws", profile=PROFILE, runner=runner)
        cli.version()
        self.assertEqual(captured["argv"], ["/fake/dws", "--profile", PROFILE, "version"])
        self.assertFalse(captured["kwargs"]["shell"])

    def test_auth_status_only_returns_allowlisted_nonsecret_fields(self):
        def runner(argv, **kwargs):
            return FakeCompleted(stdout=json.dumps({
                "authenticated": True, "currentProfile": PROFILE,
                "accessToken": "do-not-return", "refreshToken": "do-not-return",
            }))
        status = DWSCLI(binary="/fake/dws", runner=runner).auth_status()
        self.assertEqual(status["authenticated"], True)
        self.assertNotIn("accessToken", status)
        self.assertNotIn("refreshToken", status)

    def test_nonzero_exit_raises_sanitized_error(self):
        cli = DWSCLI(binary="/fake/dws", runner=lambda *a, **k: FakeCompleted(stderr="error access_token=secret-value", returncode=2))
        with self.assertRaises(DWSCLIError) as ctx:
            cli.version()
        self.assertNotIn("secret-value", ctx.exception.stderr)

    def test_event_schema_only_accepts_catalogued_event_key(self):
        calls = []
        def runner(argv, **kwargs):
            calls.append(argv)
            return FakeCompleted(stdout='{"schema":{"properties":{}}}')
        cli = DWSCLI(binary="/fake/dws", runner=runner)
        cli.event_schema("user_im_message_receive_at")
        self.assertIn("--flatten", calls[0])
        with self.assertRaises(ValueError):
            cli.event_schema("rm -rf /")

    def test_command_schema_is_limited_to_read_only_commands(self):
        with self.assertRaises(ValueError):
            DWSCLI(binary="/fake/dws").command_schema("chat message send")


class DWSConsumeContractTests(unittest.TestCase):
    def test_builds_read_only_event_consume_command(self):
        consumer = DWSConsumer(
            DWSCLI(binary="/fake/dws", profile=PROFILE),
            ["user_oa_approval_task_created", "user_oa_approval_task_finished"],
            duration="10m",
        )
        argv = consumer.command()
        self.assertEqual(argv[:5], ["/fake/dws", "--profile", PROFILE, "event", "consume"])
        self.assertIn("--flatten", argv)
        self.assertIn("ndjson", argv)
        self.assertIn("--duration", argv)
        self.assertNotIn("--yes", argv)

    def test_calendar_consumer_is_isolated(self):
        with self.assertRaises(ValueError):
            validate_consume_spec(["user_calendar_event_changed", "user_minutes_task_created"])

    def test_targeted_event_requires_target(self):
        with self.assertRaises(ValueError):
            validate_consume_spec(["user_im_message_receive_o2o"])

    def test_user_and_group_targeted_events_cannot_mix(self):
        with self.assertRaises(ValueError):
            validate_consume_spec(
                ["user_im_message_receive_o2o", "user_im_message_receive_group"],
                user="u1", group="g1",
            )

    def test_todo_roles_are_explicit_and_validated(self):
        validate_consume_spec(["user_todo_task_create"], role_types=["creator", "executor"])
        with self.assertRaises(ValueError):
            validate_consume_spec(["user_todo_task_create"], role_types=["owner"])

    def test_target_values_are_validated_before_subprocess_invocation(self):
        with self.assertRaises(ValueError):
            validate_consume_spec(["user_im_message_receive_o2o"], user="--help")
        with self.assertRaises(ValueError):
            validate_consume_spec(["user_im_message_receive_group"], group="--help")
        with self.assertRaises(ValueError):
            validate_consume_spec(["user_calendar_event_changed"], change_types=["eventDeleted"])

    def test_ndjson_parser_requires_json_object(self):
        self.assertEqual(DWSConsumer._parse_line('{"event_id":"1"}\n')["event_id"], "1")
        with self.assertRaises(DWSCLIError):
            DWSConsumer._parse_line("not json\n")
        with self.assertRaises(DWSCLIError):
            DWSConsumer._parse_line("[]\n")

    def test_consumer_waits_for_official_ready_marker_and_stops_cleanly(self):
        consumer = DWSConsumer(
            DWSCLI(binary="/fake/dws"), ["user_im_message_receive_at"],
            popen_factory=FakePopen,
        ).start()
        ready = consumer.wait_ready(timeout=2)
        self.assertTrue(ready["ready"])
        self.assertEqual(ready["subscribe_ids"]["user_im_message_receive_at"], "sub-1")
        events = list(consumer.iter_events())
        self.assertEqual(events[0]["event_id"], "evt-stream-1")
        stopped = consumer.stop()
        self.assertTrue(stopped["stopped"])

    def test_multi_event_requires_output_to_identify_event_key(self):
        from pdks_capture_runtime.connectors.dws import resolve_event_key
        with self.assertRaises(DWSCLIError):
            resolve_event_key({"event_id":"e1"}, ["user_oa_approval_task_created", "user_oa_approval_task_finished"])
        self.assertEqual(
            resolve_event_key({"type":"user_oa_approval_task_created"}, ["user_oa_approval_task_created", "user_oa_approval_task_finished"]),
            "user_oa_approval_task_created",
        )


if __name__ == "__main__":
    unittest.main()
