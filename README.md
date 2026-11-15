# Amplifier Unified Terminal Client

Work with an AHP host from your terminal. This native Ratatui interface lets you
send messages, inspect agent activity, and reopen conversations alongside web or
other terminal clients. Each client keeps its own drafts and navigation. Closing
the terminal detaches from the conversation; it does not cancel the agent's work.

This is the `amplifier-unified-client-tui` package. The older
[Amplifier app TUI](https://github.com/microsoft/amplifier-app-tui) is a separate
client.

## Install and connect

Use Python 3.11+, Node.js 22+, and [uv](https://docs.astral.sh/uv/) on macOS or
Linux. Windows use is through WSL2; this package does not provide a native Windows
wheel.

To install from source, also install Rust/Cargo and a C linker, then run:

```sh
git clone https://github.com/microsoft/amplifier-unified-client-tui
cd amplifier-unified-client-tui
uv tool install .
amplifier-unified-client-tui --server ws://127.0.0.1:8765/ahp
```

If your distribution already supplies a platform wheel, install that file with
`uv tool install /path/to/the/downloaded-wheel.whl` instead. The wheel includes the
native renderer and bundled AHP SDK, so it does not require Cargo or npm to run.

For a remote host, use WSS with verified TLS and `--token-file /private/token`;
`--ca-file /private/ca.pem` is available for a custom certificate authority. Tokens
are sent in the Authorization header, not in the URL. `AMPLIFIER_UNIFIED_URL`
sets your default host.

## Everyday use

- **Enter** sends; **Alt+Enter** inserts a newline. Pasting never submits.
- **F4** opens Actions. `/new` opens a composer; work starts when you send.
- `/resume` lists conversations. `--session ahp-session:/SESSION_UUID` opens a
  known conversation directly.
- `/messages` lets you inspect saved messages and quote one in a reply.
- `/details` shows the selected agent's identity and failure information.
- `/deliveries` and `/effects` inspect uncertain messages and operations without
  repeating them.

To restore the same local view and drafts, reuse its explicit `--client ID` and
state directory. Different terminals must not claim the same local identity.
Deleting that local state can remove unsent drafts that the host never received.

## Reference

- [Client behavior](docs/VISION.md)
- [Interaction contract](contracts/interaction.v1.md)
- [Connection and recovery contract](contracts/session.v1.md)
- [Package and build configuration](pyproject.toml)

The host determines which agents, settings, and optional actions are available.

## Contributing

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
