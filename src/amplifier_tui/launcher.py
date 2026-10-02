"""Launch the AHP terminal client. Execution belongs to the host and ACP agent."""
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent

def executable(workspace=None):
    return (Path(workspace) / "frontends/ratatui/target/release/amplifier-ratatui"
            if workspace else PACKAGE / "_bin/amplifier-ratatui")

def main(workspace=None):
    from .connected import main as connected_main
    return connected_main(workspace=workspace)
