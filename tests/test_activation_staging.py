"""Integration tests for workflow activation validation against staging.

These tests run against the real staging server using:
- The publicly installed kestrel-workflows SDK (pip install kestrel-workflows)
- The publicly installed kestrel CLI (brew install kestrelai/tap/kestrel)

They verify the end-to-end flow for both SDK and CLI:
- Create a workflow with missing fields → save succeeds → activate fails
- Create a workflow with all fields → save succeeds → activate succeeds
- CLI: generate with missing fields → prompts user → collects values → saves

Run::

    pip install kestrel-workflows
    brew install kestrelai/tap/kestrel
    python tests/test_activation_staging.py

Environment:
    KESTREL_STAGING_API_KEY  — API key with Full Access scope for staging
    KESTREL_STAGING_URL      — (optional) defaults to https://staging-platform.usekestrel.ai
    KESTREL_BIN              — (optional) path to kestrel binary, defaults to /opt/homebrew/bin/kestrel
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import importlib.util

import pytest

# This file is a manual integration harness against the real staging server,
# not a pytest unit-test module. It hits a live URL with a real API key, exits
# via `sys.exit`, and uses `test_*` function names with positional args that
# pytest cannot fixture-inject. Skip the entire module during normal
# `pytest tests` runs; set KESTREL_RUN_STAGING=1 to opt in (or just invoke
# `python tests/test_activation_staging.py` directly, which bypasses this
# guard because pytest is not involved).
if os.environ.get("KESTREL_RUN_STAGING") != "1":
    pytest.skip(
        "Staging integration tests skipped. Set KESTREL_RUN_STAGING=1 to run.",
        allow_module_level=True,
    )

_spec = importlib.util.find_spec("kestrel")
assert _spec is not None, "kestrel-workflows not installed. Run: pip install kestrel-workflows"
if os.environ.get("KESTREL_REQUIRE_INSTALLED") == "1":
    assert "site-packages" in str(_spec.origin) or "dist-packages" in str(_spec.origin), (
        f"KESTREL_REQUIRE_INSTALLED=1 but kestrel resolves to local source: {_spec.origin}"
    )

from kestrel import KestrelClient, ValidationError, KestrelError


STAGING_URL = os.environ.get("KESTREL_STAGING_URL", "https://staging-platform.usekestrel.ai")
API_KEY = os.environ.get("KESTREL_STAGING_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "KESTREL_STAGING_API_KEY must be set to run the staging integration harness. "
        "Export it from your local secrets store; no hard-coded fallback is provided."
    )
KESTREL_BIN = os.environ.get("KESTREL_BIN", "/opt/homebrew/bin/kestrel")

INCOMPLETE_DEFINITION = {
    "nodes": [
        {
            "id": "trigger-1", "type": "trigger",
            "data": {"source": "kubernetes", "signal_id": "k8s.pod_status"},
            "position": {"x": 250, "y": 0},
        },
        {
            "id": "action-1", "type": "action",
            "data": {
                "action": "kestrel-generate-k8s-manifest",
                "label": "Generate Manifest",
                "integration": "kestrel",
                "config": {"resource_type": "Deployment"},
            },
            "position": {"x": 250, "y": 150},
        },
    ],
    "edges": [{"id": "e1", "source": "trigger-1", "target": "action-1"}],
}

COMPLETE_DEFINITION = {
    "nodes": [
        {
            "id": "trigger-1", "type": "trigger",
            "data": {"source": "kubernetes", "signal_id": "k8s.pod_status"},
            "position": {"x": 250, "y": 0},
        },
        {
            "id": "action-1", "type": "action",
            "data": {
                "action": "kestrel-generate-k8s-manifest",
                "label": "Generate Manifest",
                "integration": "kestrel",
                "config": {"resource_type": "Deployment", "name": "test-app"},
            },
            "position": {"x": 250, "y": 150},
        },
    ],
    "edges": [{"id": "e1", "source": "trigger-1", "target": "action-1"}],
}

TRIGGER_CONFIG = {
    "source": "kubernetes",
    "signals": [{"signal_id": "k8s.pod_status", "filters": {"reasons": ["CrashLoopBackOff"]}}],
}


def test_save_allowed_with_missing_fields(client: KestrelClient) -> str:
    """Create a workflow with missing required fields — should succeed (saved as draft)."""
    wf = client.workflows.create(
        name=f"[Integration Test] Incomplete WF {int(time.time())}",
        definition=INCOMPLETE_DEFINITION,
        trigger_config=TRIGGER_CONFIG,
    )
    assert wf.id, "Expected workflow ID"
    assert wf.status == "draft", f"Expected draft status, got {wf.status}"
    print(f"  PASS: save allowed with missing fields (id={wf.id})")
    return wf.id


def test_activate_blocked_with_missing_fields(client: KestrelClient, workflow_id: str):
    """Activate the incomplete workflow — should fail with ValidationError."""
    try:
        client.workflows.activate(workflow_id)
        assert False, "Expected ValidationError but activate succeeded!"
    except ValidationError as e:
        assert e.status_code == 400, f"Expected 400, got {e.status_code}"
        assert len(e.missing_fields) > 0, "Expected at least one missing field"
        found_name = any(f["field_name"] == "name" for f in e.missing_fields)
        assert found_name, f"Expected 'name' in missing_fields, got: {e.missing_fields}"
        print(f"  PASS: activate blocked — ValidationError with {len(e.missing_fields)} missing field(s)")
        print(f"        missing: {[f['field_label'] for f in e.missing_fields]}")
    except KestrelError as e:
        # If the server doesn't have the new validation yet, it might return a different error
        print(f"  FAIL: Got KestrelError instead of ValidationError: {e}")
        sys.exit(1)


def test_save_allowed_with_complete_fields(client: KestrelClient) -> str:
    """Create a workflow with all required fields — should succeed."""
    wf = client.workflows.create(
        name=f"[Integration Test] Complete WF {int(time.time())}",
        definition=COMPLETE_DEFINITION,
        trigger_config=TRIGGER_CONFIG,
    )
    assert wf.id, "Expected workflow ID"
    assert wf.status == "draft", f"Expected draft status, got {wf.status}"
    print(f"  PASS: save allowed with complete fields (id={wf.id})")
    return wf.id


def test_activate_allowed_with_complete_fields(client: KestrelClient, workflow_id: str):
    """Activate the complete workflow — should succeed."""
    client.workflows.activate(workflow_id)
    wf = client.workflows.get(workflow_id)
    assert wf.status == "active", f"Expected active status, got {wf.status}"
    print(f"  PASS: activate succeeded for complete workflow")


def cleanup(client: KestrelClient, workflow_ids: list[str]):
    """Delete test workflows to keep staging clean."""
    for wid in workflow_ids:
        try:
            try:
                client.workflows.pause(wid)
            except Exception:
                pass
            client.workflows.delete(wid)
        except Exception:
            pass
    print(f"  Cleaned up {len(workflow_ids)} test workflow(s)")


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def _find_kestrel_bin() -> str:
    """Find the installed kestrel binary or fail."""
    if os.path.isfile(KESTREL_BIN):
        return KESTREL_BIN
    found = shutil.which("kestrel")
    if found:
        return found
    print("  SKIP (CLI): kestrel binary not found. Install with: brew install kestrelai/tap/kestrel")
    return ""


def _run_cli(bin_path: str, args: list[str], stdin_text: str = "") -> tuple[str, int]:
    """Run the kestrel CLI with a temp config pointing to staging. Returns (output, exit_code)."""
    tmp_home = tempfile.mkdtemp(prefix="kestrel-test-")
    try:
        kestrel_dir = os.path.join(tmp_home, ".kestrel")
        os.makedirs(kestrel_dir)
        config = {
            "server_url": STAGING_URL,
            "api_key": API_KEY,
            "session_token": "",
            "user_id": "integration-test",
            "email": "test@usekestrel.ai",
        }
        with open(os.path.join(kestrel_dir, "config.json"), "w") as f:
            json.dump(config, f)

        env = os.environ.copy()
        env["HOME"] = tmp_home

        result = subprocess.run(
            [bin_path] + args,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        output = result.stdout + result.stderr
        return output, result.returncode
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_activate_blocked_with_missing_fields(bin_path: str, workflow_id: str):
    """CLI: `kestrel workflows activate` on incomplete workflow shows validation error."""
    output, _ = _run_cli(bin_path, ["workflows", "activate", workflow_id])
    assert "Cannot activate" in output or "required field" in output, (
        f"Expected validation error message, got:\n{output}"
    )
    assert "Resource Name" in output, (
        f"Expected 'Resource Name' in error output, got:\n{output}"
    )
    print(f"  PASS: CLI activate blocked with friendly error message")


def test_cli_activate_succeeds_with_complete_fields(bin_path: str, workflow_id: str):
    """CLI: `kestrel workflows activate` on complete workflow succeeds."""
    output, code = _run_cli(bin_path, ["workflows", "activate", workflow_id])
    assert code == 0, f"Expected exit 0, got {code}. Output:\n{output}"
    assert "activated" in output, f"Expected 'activated' in output, got:\n{output}"
    print(f"  PASS: CLI activate succeeded for complete workflow")


def test_cli_generate_prompts_for_missing_fields(bin_path: str):
    """CLI: `kestrel workflows generate --save` prompts for missing required fields.

    Uses a prompt that should generate a workflow with at least one action
    that has required fields. We provide answers via stdin to fill them in.
    """
    prompt = "when a pod crashloops, generate a kubernetes deployment manifest"
    # Provide multiple newline-separated answers for any missing fields
    # The most likely missing field is "Resource Name" for kestrel-generate-k8s-manifest
    stdin_answers = "test-deployment\ndefault\nmy-app\n"

    output, code = _run_cli(
        bin_path,
        ["workflows", "generate", prompt, "--save"],
        stdin_text=stdin_answers,
    )

    # The generate command should either:
    # (a) Prompt for missing fields (shows "required fields" or field labels), OR
    # (b) Complete successfully without prompting (if AI filled all fields)
    if "required fields" in output or "Resource Name" in output:
        # It prompted — verify it then saved
        assert "Saved" in output or "wf-" in output or "Created" in output, (
            f"Expected save confirmation after prompting, got:\n{output}"
        )
        print(f"  PASS: CLI generate prompted for missing fields and saved")
    elif "Saved" in output or code == 0:
        # AI happened to fill all fields — still a pass (no missing fields to prompt for)
        print(f"  PASS: CLI generate completed (AI filled all required fields, no prompting needed)")
    else:
        # Something went wrong
        assert False, f"CLI generate failed unexpectedly (exit={code}):\n{output}"


def main():
    print(f"\n  Workflow Activation Validation — Integration Tests")
    print(f"  Target: {STAGING_URL}")
    print(f"  SDK: kestrel-workflows (installed at {_spec.origin})")

    bin_path = _find_kestrel_bin()
    if bin_path:
        print(f"  CLI: {bin_path}")
    print()

    client = KestrelClient(server=STAGING_URL, api_key=API_KEY)
    created_ids: list[str] = []

    try:
        # --- SDK Tests ---
        print("  === SDK Tests ===")

        # Test 1: Save with missing fields
        wf_id_incomplete = test_save_allowed_with_missing_fields(client)
        created_ids.append(wf_id_incomplete)

        # Test 2: Activate blocked with missing fields
        test_activate_blocked_with_missing_fields(client, wf_id_incomplete)

        # Test 3: Save with complete fields
        wf_id_complete = test_save_allowed_with_complete_fields(client)
        created_ids.append(wf_id_complete)

        # Test 4: Activate allowed with complete fields
        test_activate_allowed_with_complete_fields(client, wf_id_complete)

        # --- CLI Tests ---
        if bin_path:
            print("\n  === CLI Tests ===")

            # Create fresh workflows for CLI tests
            wf_id_incomplete_cli = test_save_allowed_with_missing_fields(client)
            created_ids.append(wf_id_incomplete_cli)

            wf_id_complete_cli = client.workflows.create(
                name=f"[Integration Test] CLI Complete {int(time.time())}",
                definition=COMPLETE_DEFINITION,
                trigger_config=TRIGGER_CONFIG,
            ).id
            created_ids.append(wf_id_complete_cli)

            # Test 5: CLI activate blocked
            test_cli_activate_blocked_with_missing_fields(bin_path, wf_id_incomplete_cli)

            # Test 6: CLI activate succeeds
            test_cli_activate_succeeds_with_complete_fields(bin_path, wf_id_complete_cli)

            # Test 7: CLI generate prompts for missing fields
            test_cli_generate_prompts_for_missing_fields(bin_path)

            print(f"\n  All 7 tests PASSED\n")
        else:
            print(f"\n  All 4 SDK tests PASSED (CLI tests skipped)\n")

    except AssertionError as e:
        print(f"\n  FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n  FAILED: {type(e).__name__}: {e}\n")
        sys.exit(1)
    finally:
        cleanup(client, created_ids)
        client.close()


if __name__ == "__main__":
    main()
