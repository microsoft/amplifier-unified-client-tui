# Connected TUI parity inventory

This lane implements the ratified shared CS/CX/CD/CB contracts without ratifying
this repository's DRAFT platform contracts. Baseline: main `512bacb47c79e3abe44638f39ad5b7e7b62501b9`.
The older amplifier-app-tui repository is untouched. No source, CI or package
receipt establishes deployment, real-account or physical-terminal acceptance.

| Contract / feature | Existing baseline | Remaining slice and public seam |
| --- | --- | --- |
| CS1–2 / CX1 | Private per-client session selection and drafts; separate local identity locks | Persist workspace selection locally; workspace.list and workspace.sessions negotiated v1 actions provide bounded existing-directory/root pages |
| CS3 / HP / working set | Official AHP reducer, selected session/chat subscriptions, 50-turn history window, linear local stream delivery | Read only selected capability reviews; no app-wide snapshot or native filesystem bypass |
| CS4 / CX2 | Original stable turn/creation IDs saved before dispatch; unknown input recovery only reads receipts | Append original intent/outcome journal survives clearing optimistic outbox; retain exact managed launch choices and creation receipt |
| CS9 / CD3 | Core conversation available with absent runtime/device controls | Optional active-client tool registration failure retains selected core resources; unsupported capabilities refuse explicitly |
| F21.04 / CS5–6 | No native launch override flags | --new --managed --agent --bundle --provider --model [--effort]; passive configured alias/revision lookup and typed native selection; explicit Send alone allocates/submits |
| F15.10/.12/.14/.15 / CX5 | Native details/fork unavailable | /details and /recovery use advertised preserve-history sessionLifecycle v1; exact inspected revision and command ID; recovery result proof precedes explicit optional navigation; no draft/model replay |
| Managed files / CX6–7 | No managed disposal control | /managed-files displays bounded exact native review; confirmation captures session, review identity/hash/revision; host retains family and dependent-owner authority; /effects only reads original receipts |
| CX3 / CS8 | Standard cancel and exact approval IDs; unsupported controls visibly refuse | Queue, steer, force stop, takeover, rich/device effects, generic native settings/editor parity remain unavailable |

## Public contract delta

No change to core AHP/ACP or shared extension schemas. Consumers use negotiated
capabilityAction v1 and the existing workspace owner action mapping. Standard
listSessions keeps its upstream fields. Optional lifecycle and managedCreation
methods are used only after their advertised version/method checks; native
recoveryCopy is checked through selected passive inspection. Missing producer
support never invokes a private runtime or guesses a substitute operation.

Workspace pages and session pages are 50 rows with opaque cursors. Query/scope
changes and reconnect invalidate client cursor maps. A standard-only host exposes
honestly labelled per-page local workspace/search filtering; it cannot claim root
filtering or bounded workspace discovery. The legacy CLI workflow in F21.01–.03/.05
belongs to client-kit; this repository adds interactive TUI flags for managed
creation only. Existing-workspace/resumed native overrides refuse.

Original prompt/creation requests and host effects stay in private 0600 append-only
intent journals, distinct from derived protocol cache and optimistic outbox.
Unknown commands are never resent, including after a completed creation receipt:
the original unsent input still requires deliberate inspection and a new action.
Current journals intentionally have no automatic pruning or replay mechanism.

## Reproduction and evidence boundaries

Run the canonical gate with independently installed AHP_HOST_ENTRY and
AHP_HOST_MODULE. `tests/test_connected_parity.py` additionally uses installed
TUI_NATIVE_PYTHON, TUI_NATIVE_PROVIDER, TUI_CATALOG_PYTHON, TUI_OWNERS_PYTHON and
TUI_WORKSPACES_MODULE; TUI_TEST_CANDIDATES=1 enables actual native PTYs.
TUI_CONNECTED_EXECUTABLE repeats terminal cases against the installed wheel.
Every run creates owned homes, app homes, catalogs, managed roots and ephemeral
ports. Shared executables are read-only with PYTHONDONTWRITEBYTECODE=1.

The native provider is synthetic, but actual Core/Foundation/loop-live and native
canonical persistence run behind the installed ACP package. The managed-files
interface fixture supplies one explicitly labelled protection participant. It is
not proof of complete production dependent-owner protection; distribution owns
that separate composition. Tests record refusal and missing family coverage
rather than bypassing them. Large production catalogs, paid accounts, physical
terminals, Spark deployment and rich-device support remain separate acceptance.
Exact package/source hashes, passing tests and any failing/skipped peer scenarios
are reported in the owner handoff receipt, not inferred from this inventory.
