# Message interaction implementation review

Scope is the independent AHP terminal client. The class audit covered selected
implementations and public boundary owners before implementation:

| Implementation | Revision | Contract and disposition |
| --- | --- | --- |
| Connected TUI | f7bb1ac base | Private drafts and original effects existed; no message reply/reaction mapping. This change adds that mapping. |
| Web client | ed9596ea8dcca9c6e20dd22dda7cf12a1cda1be3 | Private reply/clear, canonical history locators, account-bound shared reaction state and exact original receipts supplied the interaction contract. |
| Native ACP | ab35c1ca1a55a70657d7c9be63e47e2081318eb7 | Native owner validates reference epoch/digest/position and freezes quote source. Unchanged dependency. |
| AHP host | 5d46901ca16a3c119ec6635cba1b732ac4c3c4d7 | Public negotiated capabilities, selected bounded history refresh and settled-turn marker. Unchanged dependency. |
| Native capability bridge | 86bdb4ac1d327cc6e3146b07899838f2b9b99246 | Public message metadata/read/reaction/receipt adapters. Unchanged dependency. |
| Distribution | fbb7046904bdf97688b461b62bbe9722078e561b | Gateway injects authenticated account; caller never supplies actor identity. Exact local public package exercised. |
| Previous standalone TUI | Separate amplifier-app-tui | Different execution boundary; no import, edits or migration. |

Reply/Clear retain private intent with zero RPC. Send carries only the original
canonical locator through standard message metadata. Reactions retain the original
session, reference, desired state and command before dispatch. Unknown acknowledgement
never permits replay; exact receipt lookup preserves newer observed counts.

Missing markers on older saved sessions are a web/native history publication owner
follow-up; this client offers explicit selected history refresh and never invents
canonical references. Standard-only hosts retain existing send/cancel/config behavior
and explicitly refuse optional message operations. Drafts and quotes are independent
per client and selected host/session. Archive references, missing references, stale
renderer revisions, late reads after selection changes and malformed private evidence
must preserve intent and refuse unsafe action.

Coverage boundary: local deterministic installed native/provider fixtures establish
protocol and terminal behavior. They do not establish live Spark, release adoption,
physical devices or real provider/account acceptance. Shared counts update through explicit reads, confirmed changes and one selected
public capability watch; watches never settle original uncertain requests. Managed bundle/provider/model/effort launch flags and the
standard mutable settings picker already shipped and are not new work in this change.

Independent review found host admission could precede native stale-digest refusal,
while the optimistic composer and outbox were already cleared. The repair saves a
complete private frozen quoted submission before dispatch under its exact command.
Admission updates that original record independently of execution; no native success
is inferred. Selected Deliveries exposes read-only inspection, including after reload
and offline. Original text/quote remain recoverable as private evidence; neither
inspection nor subsequent host observations overwrites newer drafts/quotes or resends
work. The stale digest fixture asserts native refusal and no provider execution, while
the frozen original retains its source excerpt and deliberately stale locator.

Follow-on watch audit: the web implementation uses public `createResourceWatch`,
standard `resourceWatch/changed`, and scoped capability `resourceRead`. The upstream
SDK owns resource-watch state/recovery. The native capability owner publishes only
bounded changed-message metadata. The follow-on maps one selected watch, coalesces reads, validates original scope and
monotonic revisions, and releases/re-establishes subscriptions without replay.
