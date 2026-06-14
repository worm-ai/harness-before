from __future__ import annotations

import io
import json

from abh.models import RoadmapItem, RoadmapQueue
from abh.storage import drift_json_path, write_json
from tests.support import Chdir, WorkspaceMcpTestCase


class McpServerTests(WorkspaceMcpTestCase):
    def test_mcp_server_uses_shared_command_error_payload(self) -> None:
        from abh import commands, mcp_server

        self.assertIs(mcp_server.abh_error_payload, commands.abh_error_payload)

    def test_mcp_initialize_and_tools_list_exposes_readonly_tools(self) -> None:
        init_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "0.0.1"},
                },
            }
        )

        self.assertEqual(init_response["jsonrpc"], "2.0")
        self.assertEqual(init_response["id"], 1)
        init_result = init_response["result"]
        self.assertEqual(init_result["protocolVersion"], "2025-11-25")
        self.assertEqual(init_result["capabilities"]["tools"]["listChanged"], False)
        self.assertEqual(init_result["serverInfo"]["name"], "abh")

        list_response = self.call_mcp({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = list_response["result"]["tools"]
        tool_names = {tool["name"] for tool in tools}
        self.assertIn("abh_plan_list", tool_names)
        self.assertIn("abh_plan_status", tool_names)
        self.assertIn("abh_attractor_list", tool_names)
        self.assertIn("abh_attractor_show", tool_names)
        self.assertIn("abh_attractor_active", tool_names)
        self.assertIn("abh_roadmap_list", tool_names)
        self.assertIn("abh_roadmap_next_id", tool_names)
        self.assertIn("abh_roadmap_check", tool_names)
        self.assertIn("abh_close_plan", tool_names)
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
        readonly = {tool["name"]: tool["annotations"]["readOnlyHint"] for tool in tools}
        self.assertTrue(readonly["abh_plan_list"])
        self.assertTrue(readonly["abh_attractor_active"])
        self.assertTrue(readonly["abh_roadmap_list"])
        self.assertTrue(readonly["abh_roadmap_next_id"])
        self.assertTrue(readonly["abh_roadmap_check"])
        self.assertTrue(readonly["abh_doctor"])
        self.assertFalse(readonly["abh_plan_create"])
        self.assertFalse(readonly["abh_verify_record"])
        self.assertFalse(readonly["abh_close_plan"])
        write_tool_names = {
            "abh_plan_create",
            "abh_plan_transition",
            "abh_verify_record",
            "abh_audit_request",
            "abh_audit_record",
            "abh_close_plan",
            "abh_memory_add",
            "abh_drift_analyze",
        }
        self.assertTrue(write_tool_names.issubset(tool_names))
        for tool in tools:
            if tool["name"] in write_tool_names:
                self.assertIn("confirm", tool["inputSchema"]["required"])

    def test_mcp_tools_call_returns_structured_content_for_core_reads(self) -> None:
        self.create_ready_plan()

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_status",
                    "arguments": {"plan_id": "plan-mcp-contract"},
                },
            }
        )

        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["type"], "text")
        envelope = result["structuredContent"]
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["command"], "abh_plan_status")
        self.assertEqual(envelope["data"]["plan"]["id"], "plan-mcp-contract")
        self.assertIn("verification_summary", envelope["data"])
        self.assertEqual(envelope["data"]["verification_summary"]["latest_id"], None)
        self.assertEqual(envelope["data"]["verification_summary"]["reasons"], ["no_verification_runs"])

        doctor_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "abh_doctor", "arguments": {}},
            }
        )
        doctor_envelope = doctor_response["result"]["structuredContent"]
        self.assertTrue(doctor_envelope["ok"])
        self.assertEqual(doctor_envelope["data"]["issues"], [])

        route_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "abh_route",
                    "arguments": {"question": "Can we close this plan?"},
                },
            }
        )
        route_envelope = route_response["result"]["structuredContent"]
        self.assertEqual(route_envelope["data"]["route"]["route"], "completion_audit")

    def test_mcp_attractor_read_tools_return_registry_data(self) -> None:
        code, out, err = self.run_cli(
            "attractor",
            "create",
            "--id",
            "attractor-mcp",
            "--title",
            "MCP Attractor",
            "--version",
            "1.0.0",
            "--path",
            "docs/architecture/attractors/mcp.md",
            "--intent",
            "MCP can read active attractor.",
        )
        self.assertEqual(code, 0, err)

        active_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 18,
                "method": "tools/call",
                "params": {"name": "abh_attractor_active", "arguments": {}},
            }
        )
        active = active_response["result"]["structuredContent"]["data"]["attractor"]
        self.assertEqual(active["id"], "attractor-mcp")

        show_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 19,
                "method": "tools/call",
                "params": {"name": "abh_attractor_show", "arguments": {"attractor_id": "attractor-mcp"}},
            }
        )
        self.assertEqual(show_response["result"]["structuredContent"]["data"]["attractor"]["path"], "docs/architecture/attractors/mcp.md")

        list_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {"name": "abh_attractor_list", "arguments": {}},
            }
        )
        self.assertEqual(list_response["result"]["structuredContent"]["data"]["total"], 1)

    def test_mcp_roadmap_read_tools_return_queue_data(self) -> None:
        with Chdir(self.root):
            write_json(
                self.root / ".abh" / "roadmap.json",
                RoadmapQueue(
                    items=[
                        RoadmapItem(
                            key="stage4.mcp-roadmap",
                            title="MCP Roadmap",
                            stage="stage4",
                            summary="MCP reads roadmap queue.",
                        )
                    ]
                ).to_dict(),
            )

        list_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {"name": "abh_roadmap_list", "arguments": {}},
            }
        )
        list_envelope = list_response["result"]["structuredContent"]
        self.assertTrue(list_envelope["ok"])
        self.assertEqual(list_envelope["data"]["items"][0]["key"], "stage4.mcp-roadmap")

        next_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "tools/call",
                "params": {"name": "abh_roadmap_next_id", "arguments": {}},
            }
        )
        next_envelope = next_response["result"]["structuredContent"]
        self.assertEqual(next_envelope["data"]["next_plan_id"], "plan-001")

        check_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 23,
                "method": "tools/call",
                "params": {"name": "abh_roadmap_check", "arguments": {}},
            }
        )
        self.assertEqual(check_response["result"]["structuredContent"]["data"]["issues"], [])

    def test_mcp_drift_list_reads_existing_reports_without_writing(self) -> None:
        with Chdir(self.root):
            write_json(
                drift_json_path("drift-mcp-existing"),
                {
                    "schema_version": "2",
                    "id": "drift-mcp-existing",
                    "source": "source.txt",
                    "findings": [
                        {
                            "type": "dependency_drift",
                            "evidence": "matched keywords: database",
                            "recommendation": "Review dependency drift.",
                        }
                    ],
                    "evidence": [],
                    "follow_ups": [],
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "doc_path": "",
                },
            )

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {"name": "abh_drift_list", "arguments": {}},
            }
        )

        envelope = response["result"]["structuredContent"]
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["data"]["total"], 1)
        self.assertEqual(envelope["data"]["drift_reports"][0]["id"], "drift-mcp-existing")
        finding = envelope["data"]["drift_reports"][0]["findings"][0]
        self.assertEqual(finding["severity"], "unknown")
        self.assertEqual(finding["confidence"], "unknown")

    def test_mcp_errors_are_structured(self) -> None:
        unknown_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"name": "abh_missing_tool", "arguments": {}},
            }
        )
        self.assertEqual(unknown_response["error"]["code"], -32601)
        self.assertEqual(unknown_response["error"]["data"]["category"], "not_found")

        tool_error_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_status",
                    "arguments": {"plan_id": "missing-plan"},
                },
            }
        )
        result = tool_error_response["result"]
        self.assertTrue(result["isError"])
        envelope = result["structuredContent"]
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["errors"][0]["category"], "not_found")

    def test_mcp_doctor_consistency_errors_include_issues(self) -> None:
        self.create_ready_plan("plan-mcp-doctor")
        (self.root / "docs" / "plans" / "plan-mcp-doctor.md").unlink()

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {"name": "abh_doctor", "arguments": {}},
            }
        )

        result = response["result"]
        self.assertTrue(result["isError"])
        envelope = result["structuredContent"]
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["data"]["issues"], ["missing markdown for plan plan-mcp-doctor"])
        self.assertEqual(envelope["errors"][0]["code"], "doctor_issues")
        self.assertEqual(envelope["errors"][0]["category"], "consistency")

    def test_mcp_stdio_processes_newline_delimited_messages(self) -> None:
        from abh.mcp_server import serve_stdio

        input_stream = io.StringIO(
            "\n".join(
                [
                    json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
                    "not-json",
                    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                ]
            )
        )
        output_stream = io.StringIO()

        with Chdir(self.root):
            exit_code = serve_stdio(input_stream=input_stream, output_stream=output_stream)

        self.assertEqual(exit_code, 0)
        lines = [json.loads(line) for line in output_stream.getvalue().splitlines()]
        self.assertEqual(lines[0]["id"], 1)
        self.assertIn("tools", lines[0]["result"])
        self.assertEqual(lines[1]["error"]["code"], -32700)

    def test_mcp_write_tools_require_confirm_and_do_not_write_without_it(self) -> None:
        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_create",
                    "arguments": {
                        "plan_id": "plan-mcp-no-confirm",
                        "title": "No Confirm",
                        "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                        "baseline": "baseline",
                    },
                },
            }
        )

        result = response["result"]
        self.assertTrue(result["isError"])
        envelope = result["structuredContent"]
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["errors"][0]["category"], "business_rule")
        self.assertFalse((self.root / ".abh" / "plans" / "plan-mcp-no-confirm.json").exists())

    def test_mcp_controlled_write_flow_can_create_verify_audit_close_and_write_memory(self) -> None:
        create_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_create",
                    "arguments": {
                        "confirm": True,
                        "plan_id": "plan-mcp-write",
                        "title": "MCP Write Plan",
                        "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                        "baseline": "baseline",
                        "status": "ready",
                        "goals": ["ship controlled writes"],
                        "non_goals": ["skip audit"],
                        "exit_criteria": ["closed through mcp"],
                        "validation_checklist": ["unit tests pass"],
                        "closure_evidence": ["tests/test_mcp_server.py"],
                    },
                },
            }
        )
        plan = create_response["result"]["structuredContent"]["data"]["plan"]
        self.assertEqual(plan["id"], "plan-mcp-write")
        self.assertEqual(plan["status"], "ready")

        verify_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "abh_verify_record",
                    "arguments": {
                        "confirm": True,
                        "plan_id": "plan-mcp-write",
                        "command": "unit tests pass",
                        "result": "pass",
                        "artifacts": ["tests/test_mcp_server.py"],
                    },
                },
            }
        )
        verification = verify_response["result"]["structuredContent"]["data"]["verification"]
        self.assertEqual(verification["plan_id"], "plan-mcp-write")

        transition_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_transition",
                    "arguments": {"confirm": True, "plan_id": "plan-mcp-write", "to": "running"},
                },
            }
        )
        self.assertEqual(transition_response["result"]["structuredContent"]["data"]["plan"]["status"], "running")

        audit_request_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {
                    "name": "abh_audit_request",
                    "arguments": {
                        "confirm": True,
                        "plan_id": "plan-mcp-write",
                        "audit_id": "audit-mcp-write",
                        "auditor": "independent-auditor",
                        "scope": "mcp write close gate",
                        "evidence": ["tests/test_mcp_server.py"],
                    },
                },
            }
        )
        self.assertEqual(audit_request_response["result"]["structuredContent"]["data"]["audit"]["id"], "audit-mcp-write")

        audit_record_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 15,
                "method": "tools/call",
                "params": {
                    "name": "abh_audit_record",
                    "arguments": {
                        "confirm": True,
                        "audit_id": "audit-mcp-write",
                        "result": "pass",
                        "rationale": "mcp write flow verified",
                        "auditor_context": "independent MCP write-flow reviewer",
                        "independence": "independent",
                        "verification_id": verification["id"],
                    },
                },
            }
        )
        self.assertEqual(audit_record_response["result"]["structuredContent"]["data"]["audit"]["result"], "pass")

        closing_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 16,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_transition",
                    "arguments": {"confirm": True, "plan_id": "plan-mcp-write", "to": "closing"},
                },
            }
        )
        self.assertEqual(closing_response["result"]["structuredContent"]["data"]["plan"]["status"], "closing")

        close_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 17,
                "method": "tools/call",
                "params": {
                    "name": "abh_close_plan",
                    "arguments": {"confirm": True, "plan_id": "plan-mcp-write"},
                },
            }
        )
        self.assertEqual(close_response["result"]["structuredContent"]["data"]["plan"]["status"], "closed")

        memory_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 18,
                "method": "tools/call",
                "params": {
                    "name": "abh_memory_add",
                    "arguments": {
                        "confirm": True,
                        "memory_id": "mem-mcp-write",
                        "type": "divergent_pattern",
                        "summary": "controlled mcp write flow",
                        "context": "mcp write tools created ABH records",
                        "implication": "write tools preserve ABH gates",
                        "evidence": ["tests/test_mcp_server.py"],
                        "related": ["plan-mcp-write"],
                        "tags": ["mcp", "quality-signal"],
                        "status": "active",
                        "related_plan_ids": ["plan-mcp-write"],
                        "related_audit_ids": ["audit-mcp-write"],
                        "related_drift_ids": ["drift-mcp-write"],
                        "superseded_by": "mem-mcp-write-v2",
                    },
                },
            }
        )
        memory = memory_response["result"]["structuredContent"]["data"]["memory"]
        self.assertEqual(memory["id"], "mem-mcp-write")
        self.assertEqual(memory["tags"], ["mcp", "quality-signal"])
        self.assertEqual(memory["related_plan_ids"], ["plan-mcp-write"])
        self.assertEqual(memory["related_audit_ids"], ["audit-mcp-write"])
        self.assertEqual(memory["related_drift_ids"], ["drift-mcp-write"])
        self.assertEqual(memory["superseded_by"], "mem-mcp-write-v2")
        self.assertTrue((self.root / ".abh" / "plans" / "plan-mcp-write.json").exists())
        self.assertTrue((self.root / "docs" / "plans" / "plan-mcp-write.md").exists())
        self.assertTrue((self.root / ".abh" / "audits" / "audit-mcp-write.json").exists())
        self.assertTrue((self.root / ".abh" / "memory" / "mem-mcp-write.json").exists())

    def test_mcp_drift_analyze_write_tool_requires_confirm_and_can_write_report(self) -> None:
        drift_source = self.root / "mcp-drift-source.txt"
        drift_source.write_text("Skipped tests and added external dependency.\n", encoding="utf-8")

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 19,
                "method": "tools/call",
                "params": {
                    "name": "abh_drift_analyze",
                    "arguments": {
                        "confirm": True,
                        "drift_id": "drift-mcp-write",
                        "source": str(drift_source),
                        "evidence": ["mcp-drift-source.txt"],
                    },
                },
            }
        )

        envelope = response["result"]["structuredContent"]
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["data"]["drift_report"]["id"], "drift-mcp-write")
        finding = envelope["data"]["drift_report"]["findings"][0]
        self.assertEqual(finding["severity"], "high")
        self.assertEqual(finding["confidence"], "high")
        self.assertIn("source_excerpt", finding)
        self.assertTrue((self.root / ".abh" / "drift" / "drift-mcp-write.json").exists())
