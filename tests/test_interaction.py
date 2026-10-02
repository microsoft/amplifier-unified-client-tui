"""Real-terminal ordinary interactions, not source-layout or successful-engine mocks."""

import json
import os
import signal
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from terminal_probe import Probe  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("TUI_TEST_CANDIDATES") != "1", reason="Build Ratatui first"
)


def click(probe, label):
    probe.wait(label)
    for y, row in enumerate(probe.screen.display):
        if label in row:
            x = row.index(label) + 1
            probe.send(f"\x1b[<0;{x + 1};{y + 1}M\x1b[<0;{x + 1};{y + 1}m".encode())
            return
    raise AssertionError(label)


def action(probe, query, expected):
    click(probe, "[ Actions ]")
    probe.wait("Search:")
    probe.send(query.encode())
    probe.wait(f"Search: {query}")
    probe.send(b"\r")
    probe.wait(expected)


def test_actions_cancel_preserves_selection_and_paste_is_local():
    probe = Probe([sys.executable, str(ROOT / "scripts/compare.py"), "ratatui"])
    try:
        probe.wait("Waiting for your decision")
        probe.send(b"\x1b[1;2D")  # select final draft character
        click(probe, "[ Actions ]")
        probe.wait("Search:")
        probe.send(b"\x1b[200~quit\n\x1b[201~")
        probe.wait("Search: quit")
        assert probe.process.poll() is None
        probe.send(b"\x1b")
        probe.wait("Search:", absent=True)
        probe.send(b"!")
        probe.wait("are not retried!")
        # Tab visits Actions in the compact footer; Enter discovers, never submits.
        probe.send(b"\t\r")
        probe.wait("Search:")
        assert "Busy" not in probe.text
        probe.send(b"\x1b")
        probe.wait("Search:", absent=True)
        click(probe, "Review decision")
        probe.wait("Options (exact runtime scope)")
        probe.send(b"deny\r")
        probe.wait("command denied")
        probe.wait("are not retried!")
        click(probe, "[ Actions ]")
        probe.wait("Search:")
        probe.send(b"quit\r")
        probe.wait_exit(timeout=4)
    finally:
        probe.close()






def test_menu_resize_keeps_draft_and_keyboard_access():
    probe = Probe([sys.executable, str(ROOT / "scripts/compare.py"), "ratatui"], cols=160)
    try:
        probe.wait("Waiting for your decision")
        click(probe, "[ Actions ]")
        probe.wait("Search:")
        for cols, rows in [(60, 20), (80, 24), (200, 40)]:
            probe.resize(cols, rows)
            probe.wait("Search:")
            probe.send(b"x")
            probe.wait("Search: x")
            probe.send(b"\x7f")
            probe.wait("Search: x", absent=True)
        probe.send(b"\x1b")
        probe.wait("Search:", absent=True)
        probe.wait("Also check that permanent failures are not retried.")
    finally:
        probe.close()






def test_open_decision_keeps_identity_when_backend_replaces_it(tmp_path):
    # Controlled event fixture for the stale-focus race; separate from real-module tests.
    record = tmp_path / "requests.jsonl"
    backend = """
import json, os, signal, sys
open(sys.argv[1] + ".pid", "w").write(str(os.getpid()))
def emit(value):
    print(json.dumps({"version": 1, **value}), flush=True)
def state(identity, status):
    emit({"type":"state", "status":status, "approval":{"id":identity,"prompt":"Scoped choice", "command":identity,"options":["once","deny"]}})
signal.signal(signal.SIGUSR1, lambda *_: state("second", "replacement pending"))
emit({"type":"snapshot", "mode":"EVENT FIXTURE", "title":"Stale focus test", "context":"test", "draft":"Keep draft", "items":[],"system":[]})
state("first", "first pending")
for line in sys.stdin:
    request=json.loads(line)
    with open(sys.argv[1], "a") as output:
        output.write(json.dumps(request)+"\\n")
    if request["op"] == "shutdown": break
    emit({"type":"state", "status":"second answered", "approval":None})
"""
    command = [
        str(ROOT / "frontends/ratatui/target/release/amplifier-ratatui"),
        "--host-json",
        json.dumps([sys.executable, "-u", "-c", backend, str(record)]),
    ]
    probe = Probe(command)
    try:
        probe.wait("first pending")
        click(probe, "Review decision")
        probe.wait("Options (exact runtime scope)")
        # The controlled backend reports its own PID; no Linux /proc dependency
        # or assumption that a terminal guard is absent from the process tree.
        backend_pid = int(Path(str(record) + ".pid").read_text())
        os.kill(backend_pid, signal.SIGUSR1)
        probe.wait("replacement pending")
        probe.send(b"once\r")
        probe.wait("Decision no longer pending")
        assert not record.exists(), "Stale focus emitted a request"
        probe.wait("Keep draft")
        click(probe, "Review decision")
        probe.wait("Options (exact runtime scope)")
        probe.send(b"deny\r")
        probe.wait("second answered")
        request = json.loads(record.read_text().splitlines()[0])
        assert request["approval_id"] == "second" and request["option"] == "deny"
    finally:
        probe.close()
