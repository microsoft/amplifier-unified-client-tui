# Verification guide

The supported product is the AHP client. `scripts/qualify_current.py` is the canonical
local/CI gate: it requires an independent host package, builds the official SDK
bundle and Ratatui renderer, runs all explicitly current Python tests and Rust tests,
builds a wheel, installs it into a fresh environment with no runtime dependencies,
and repeats actual terminal PTYs against the installed executable. It refuses missing
host inputs. No paid account/model, publication or deployment is implied.

```sh
AHP_HOST_ENTRY=/independent/host/dist/cli.js \
AHP_HOST_MODULE=file:///independent/host/dist/index.js \
uv run --no-sync python scripts/qualify_current.py
```

The supported test manifest is explicit in `pyproject.toml`; see
[the complete cutover classification](notes/AHP-CUTOVER.md). Renderer cases use real
PTYs and clearly labelled controlled events. AHP cases use an independent ACP fixture.
The terminal restoration observer preserves failure codes and application termios
flags; it ignores the kernel's transient PENDIN retype flag, never ICANON/ECHO/ISIG.
Installed PTYs clear checkout import paths. Evidence includes ANSI output, terminal
cells and reconstructed screenshots with actual font names and stated limitations.

