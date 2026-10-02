"""Reusable current-client observer helpers; no execution harness."""


import copy
import time
from types import SimpleNamespace

from terminal_probe import ROOT


def click(probe, label):
    probe.wait(label)
    for y, row in enumerate(probe.screen.display):
        if label in row:
            x = row.index(label) + 1
            probe.send(f"\x1b[<0;{x + 1};{y + 1}M\x1b[<0;{x + 1};{y + 1}m".encode())
            return
    raise AssertionError(label)


def action(probe, query, expected):
    # Native output can move footer coordinates between capture and injection.
    # The normal terminal does not capture physical mouse clicks; use its actual
    # keyboard action entry point. Explicit menu mouse tests remain separate.
    # Wait for the previous dialog's closing frame; otherwise its stale Search
    # label can satisfy the next wait and adjacent ESC sequences can coalesce.
    probe.wait("Actions / choices", absent=True)
    probe.send(b"\x1bOS")
    probe.wait("Search:")
    probe.send(query.encode())
    probe.wait(f"Search: {query}")
    probe.send(b"\r")
    probe.wait(expected)


def capture(probe, name):
    # Reuse terminal-tester's renderer with the existing local observer fixes.
    # No screenshot delay is interpreted as an interaction timing.
    from terminal_raster import render_terminal as render_visible_cursor

    # A menu closing can precede the next native journal paint. Wait for a quiet
    # frame, bounded during streaming; this is never a latency measurement.
    deadline = time.monotonic() + 0.25
    quiet = time.monotonic()
    while time.monotonic() < deadline:
        before = probe.bytes
        probe.read(0.01)
        if probe.bytes != before:
            quiet = time.monotonic()
        elif time.monotonic() - quiet >= 0.04:
            break
    screen = copy.deepcopy(probe.screen)
    ordered = screen.buffer.copy()
    ordered.clear()
    for row in range(probe.rows):
        ordered[row] = screen.buffer[row]
    screen.buffer = ordered
    display = SimpleNamespace(screen=screen, cols=probe.cols, rows=probe.rows, font_size=14)
    path = ROOT / ".evidence/interaction" / f"{name}.png"
    render_visible_cursor(display, path)
    return path

