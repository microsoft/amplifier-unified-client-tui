"""The cross-platform observer checks restoration without silently repairing it."""

import codecs
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terminal_probe  # noqa: E402
from terminal_probe import Probe  # noqa: E402


@contextmanager
def pipe_screen(cols=200, rows=40):
    import pyte
    probe = Probe.__new__(Probe)
    probe.screen = terminal_probe.Screen(cols, rows)
    probe.stream = pyte.Stream(probe.screen)
    probe.decoder = codecs.getincrementaldecoder('utf-8')('replace')
    probe.bytes, probe.raw = 0, bytearray()
    probe.visible_deltas, probe.observer_ns = {}, []
    probe.last_input_ns, probe.idle_transition_ns = time.monotonic_ns(), 0
    probe.saw_work = False
    reader, writer = os.pipe()
    probe.master = reader
    try:
        yield probe, writer
    finally:
        os.close(reader)
        os.close(writer)


def test_complete_geometry_wait_handles_fragmented_draw():
    from test_compact_terminal import complete_pasted_geometry, composer_rows
    with pipe_screen() as (probe, writer):
        os.write(writer, b'\x1b[2J\x1b[HGeometry proof')
        probe.read()
        with pytest.raises(StopIteration):
            composer_rows(probe)
        before = probe.bytes
        os.write(writer, b'\x1b[33;1HMessage ')
        probe.read()
        assert not complete_pasted_geometry(probe, 200)
        os.write(writer, b'\xc2\xb7\x1b[35;1H' + b'x' * 200
                 + b'\x1b[36;1HNEXT\x1b[37;1Hthird\x1b[39;1H[ Actions ]\x1b[40;1HReady')
        probe.wait_screen(lambda p: complete_pasted_geometry(p, 200), after_bytes=before)
        assert complete_pasted_geometry(probe, 200)


def test_complete_response_wait_handles_coalesced_busy_and_ready_without_relaxing_idle():
    from test_reading_terminal import complete_response_screen
    submitted, response = 'Use @context-beta suffix', 'Exact new fixture response'
    with pipe_screen() as (probe, writer):
        os.write(writer, (f'\x1b[40;1HWorking\x1b[1;1H{submitted}\x1b[2;1H{response}'
                         '\x1b[33;1HMessage ·\x1b[39;1H[ Actions ]\x1b[40;1H\x1b[2KReady')
                 .encode())
        probe.read()
        assert probe.idle_transition_ns == 0
        with pytest.raises(AssertionError, match='did not become idle'):
            probe.wait_idle(timeout=0.01)
        probe.wait_screen(lambda p: complete_response_screen(p,
            submitted=submitted, response=response), after_bytes=0)


def test_complete_screen_rejects_stale_output_and_missing_content():
    from test_reading_terminal import complete_response_screen
    with pipe_screen() as (probe, writer):
        os.write(writer, b'\x1b[40;1HReady')
        probe.read()
        with pytest.raises(AssertionError, match='complete screen condition'):
            probe.wait_screen(lambda p: True, after_bytes=probe.bytes, timeout=0.01)
        with pytest.raises(AssertionError, match='complete screen condition'):
            probe.wait_screen(lambda p: complete_response_screen(p,
                submitted='missing submission', response='missing response'),
                after_bytes=0, timeout=0.01)


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
