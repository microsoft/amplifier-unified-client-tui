# Work derived from current direction

Authority: [VISION](../docs/VISION.md) and the referenced DRAFT contracts.
Desired behavior is distinct from current [acceptance](ACCEPTANCE.md).

| Item | Source promises | Work | Observable completion / falsifier | State |
|---|---|---|---|---|
| AHP-01 | composition.v1:1, continuity.v1:2, session.v1:2 | Independent AHP client, durable local intent, paged selected resources | Official reducer plus independent host and installed Ratatui PTYs; no command replay | Implemented; source qualification recorded in ACCEPTANCE |
| STREAM-01 | performance.v1:5, presentation.v1:3 | Append active text without copying growing responses through local IPC | Long stream preserves exact bytes and responsive draft input; IPC instrumentation | Implemented; bounded append instrumentation and real PTY regression |
| PARITY-01 | interaction.v1:1, session.v1:6 | Bind remaining optional host controls through negotiated capabilities | Same supported action for person and agent; explicit unsupported inventory | Remaining surfaces listed in README; no private runtime bypass |
| PEERS-01 | ecosystem.v1:6 | Independently qualify other AHP hosts and ACP-backed implementations | Separate source, handshake, tool/approval, model and real-account receipts | Independent host fixture passes; external account qualification remains |

| FLAGS-01 | composition.v1:1, session.v1:6 | F21.04 configured managed launch choices | Passive options resolve exact bundle revision; first installed native model audit matches explicit selection; resumed/unsupported overrides refuse | Implemented; acceptance tracked in CONNECTED-PARITY |
| REVIEW-01 | continuity.v1:2, presentation.v1:7 | Recovery and managed allocation reviews | Exact source/revision confirmation, durable original receipt, stale target refuses, source history preserved | Implemented; acceptance tracked in CONNECTED-PARITY |
| CATALOG-01 | composition.v1:1, interaction.v1:1 | Negotiated workspace/root-session discovery | 50-row host-filtered pages; cursor binds query/workspace/connection; no dormant runtime | Implemented; acceptance tracked in CONNECTED-PARITY |

| WHEEL-01 | composition.v1:1, ecosystem.v1:6 | Reproducible native wheel build and installed client | Compiler deployment floor and isolated host proc-macro artifacts; installed helper/native isolation and actual connected PTYs | Implemented; causal evidence in WHEEL-BUILD |

| CONFIG-01 | session.v1:6, ecosystem.v1:2, continuity.v1:2 | Standard connected model/settings selection and truthful optional controls | Advertised mutable schema choices, readback confirmation, refusal/unknown distinction, local draft preservation and receipt-only inspection | Implemented; standard installed host and actual terminal picker/refusal qualified; fresh native schema boundary reported separately |
| MESSAGE-01 | interaction.v1:3, continuity.v1:4, ecosystem.v1:2 | Private canonical quotes and authenticated shared reactions | Reload and selection preserve drafts; no RPC on quote selection; bounded metadata reads, exact reaction receipts, missing refs and unknown outcomes never replay | Implemented; exact installed public-host/native and PTY evidence in MESSAGE-PARITY; selected metadata watch qualified in MESSAGE-WATCH-01 |

| QUOTE-RECOVERY-01 | interaction.v1:3, continuity.v1:2, continuity.v1:4 | Original frozen quoted submission survives native refusal after host admission | Stale digest/native unknown execution retains exact private text/quote/command through reload, read-only inspection and newer draft/quote without any replay | Implemented; stale-digest native refusal, exact original reload and installed terminal inspection/copy passed; independent review required |

| MESSAGE-WATCH-01 | continuity.v1:3, continuity.v1:4, ecosystem.v1:2 | Selected shared reaction updates via public resource watches | Other-client changes update current projection; stale scope/revision refuses, one coalesced read, detach/reconnect never repeat effects | Implemented; other-client live updates, reconnect and exact original uncertainty tested in installed public-host/native PTYs |

Selection watch repair: retain at most one latest validated metadata packet for
an in-flight selected scope and connection generation. Commit it only after the
matching selection snapshot; discard on cancellation, replacement or reconnect.
Serialize selections so a late snapshot cannot replace a newer view. This keeps
public selected-resource projection and private unknown receipts independent.

Pending selection reconnect: a validated watch packet explicitly stamped with
the current transport generation may replace the pending selection's old-generation
buffer. Keep its same selection token/scope, discard the old packet, and compare
revisions only within that generation. Reject old-generation packets and keep
cancellation/replacement cleanup. No additional read or input replay is needed.
