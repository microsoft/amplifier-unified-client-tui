"""The cross-platform observer checks restoration without silently repairing it."""

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terminal_probe  # noqa: E402
from terminal_probe import Probe  # noqa: E402


def test_concurrent_probe_receipts_preserve_every_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(terminal_probe, 'ROOT', tmp_path)
    barrier = threading.Barrier(16)

    def lifecycle(pid):
        barrier.wait(timeout=5)
        terminal_probe.record(pid, 'active')
        terminal_probe.record(pid, 'reaped')

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(lifecycle, range(16)))
    data = json.loads((tmp_path / '.state/WORKSPACE-MANIFEST.json').read_text())
    assert len(data['resources']) == 16
    assert {row['pid'] for row in data['resources']} == set(range(16))
    assert all(row['status'] == 'reaped' and row['reaped_at'] for row in data['resources'])


def test_probe_receipt_readers_see_complete_original_until_replace(tmp_path, monkeypatch):
    monkeypatch.setattr(terminal_probe, 'ROOT', tmp_path)
    terminal_probe.record(1, 'active')
    receipt = tmp_path / '.state/WORKSPACE-MANIFEST.json'
    before = receipt.read_bytes()
    entered, release = threading.Event(), threading.Event()
    replace = terminal_probe.os.replace

    def held_replace(source, destination):
        entered.set()
        assert release.wait(5)
        replace(source, destination)

    monkeypatch.setattr(terminal_probe.os, 'replace', held_replace)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(terminal_probe.record, 1, 'reaped')
        try:
            assert entered.wait(5)
            assert receipt.read_bytes() == before
            assert json.loads(receipt.read_text())['resources'][0]['status'] == 'active'
        finally:
            release.set()
        future.result(timeout=5)
    assert json.loads(receipt.read_text())['resources'][0]['status'] == 'reaped'
    assert not list(receipt.parent.glob('.probe-receipt-*'))


def test_malformed_probe_receipt_fails_without_replacement(tmp_path, monkeypatch):
    monkeypatch.setattr(terminal_probe, 'ROOT', tmp_path)
    receipt = tmp_path / '.state/WORKSPACE-MANIFEST.json'
    receipt.parent.mkdir()
    receipt.write_text('{broken')
    with pytest.raises(json.JSONDecodeError):
        terminal_probe.record(1, 'reaped')
    assert receipt.read_text() == '{broken'


@pytest.mark.parametrize("restore,exit_code", [(True, 0), (False, 0), (True, 7)])
def test_controlling_session_guard_preserves_failure(restore, exit_code):
    code = (
        "import os, sys, termios, tty; "
        "original = termios.tcgetattr(0); tty.setraw(0); "
        "os.write(1, b'guard ready'); os.read(0, 1); "
        + ("termios.tcsetattr(0, termios.TCSANOW, original); " if restore else "")
        + f"sys.exit({exit_code})"
    )
    probe = Probe([sys.executable, "-I", "-c", code], guard_terminal_modes=True)
    try:
        probe.wait("guard ready")
    except BaseException:
        probe.close()
        raise
    if restore and not exit_code:
        probe.close()
    else:
        with pytest.raises(AssertionError):
            probe.close()
