# Return and retained intent Contract — v1 (DRAFT)

Parent: [composition.v1](composition.v1.md).
Desired behavior is distinct from current acceptance evidence.

## Who builds against this

Client-state owners, AHP host implementers and people returning to conversations.
The steward reviews wording independently of implementation progress.

## What it is

```text
private draft + selection + unknown-effect journal -> client-owned storage
AHP resource identity + cursor + server sequence -> derived observation
reconnect -> replay or complete upstream snapshot
explicit submission -> durable host admission
```

The artifact describes a boundary, not a claim of complete implementation.
Receipts live in [acceptance notes](../notes/ACCEPTANCE.md).

## The promises

1. **Retain identity.** Selection uses the same AHP session/chat resources and the host-reported workspace. Native history, writer locks, configuration and engine binding belong to the host/ACP owner; a client never writes those files or substitutes an inferred native identity.
   Broken: Returning to another workspace or silently starting a new session loses the intended target.
   Affected: people returning to saved work.

2. **Retain intent.** Private drafts, selection and uncertain input survive local restart under the same client identity and host scope. Switching saves the source draft; failed selection preserves it. Renderer revisions include unflushed keystrokes and stale agent edits refuse.
   Broken: An unsent input is submitted, retargeted or overwritten during recovery.
   Affected: people editing across concurrent clients.

3. **Replay only observations.** AHP recovery applies ordered upstream actions or replacement snapshots. Lost baselines require fresh subscriptions; paged history never prompts a model or approves a tool. Derived caches may be discarded; private unsent text cannot be recovered from a host that never received it.
   Broken: A repeated side effect or silently truncated mandatory snapshot changes recovery semantics.
   Affected: client authors and people recovering from disconnects.

4. **Keep decisions attributable.** Permission and client-effect receipts retain the source session, turn, tool and command identity. Durable unknown status is written before a device/UI effect; missing replies remain inspectable without automatic retry.
   Private quotes retain their original session and canonical locator across restart. Reaction evidence binds the original command, native message, authenticated host scope and desired state; current counts never prove an unknown request. Inspecting an exact original receipt never repeats the reaction or overwrites a newer observed revision. A selected capability watch coalesces bounded read-only invalidations, releases its old scope on selection/detach, and restores an independent baseline after reconnect; it never settles unknown intent from current counts.
   Broken: A stale decision applies to a newer request or uncertainty is treated as denial of any effect.
   Affected: people reviewing approvals and agent-directed local actions.

5. **Separate stopping and undo.** Cancel follows the standard host action and observed outcome. It never implies rollback, force termination, safe prompt replay or newly admitted follow-up work. Advanced recovery requires an advertised host capability and preserves original evidence.
   Broken: Cancelled work is described as undone or an unknown tool is automatically retried.
   Affected: people trusting interruption and recovery.

6. **Keep viewers independent.** Detach, close, focus and ordinary local editing do not acquire, cancel or prolong a native writer. Any explicit handoff is a negotiated host operation with its own admission and result. Multiple client drafts remain separate.
   Broken: Closing a terminal ends another client’s active execution, or focusing steals ownership.
   Affected: people using several views and independently implemented clients.

7. **Load the requested view.** Ordinary catalogs page root sessions and selected conversations initially request 50 complete turns. Earlier pages are explicit. Reconnect uses upstream semantics; explicit full recovery is disclosed and never silently shortened to a private client limit.
   Broken: Browsing warms every agent or returning requests every project and child transcript.
   Affected: people with large archives and host operators.

## Not in v1

Native history migration, private module-state portability, host process supervision,
or automatic replay of unacknowledged effects.

## How the kit checks it

Use independent host/ACP fixtures, two clients, process loss and erased local caches.
Count side effects, preserve private drafts and inspect original native bytes through
the host owner’s separate integration tests; clients never acquire those stores.
The document checker verifies shape and links, not behavior or ratification.
DRAFT contracts do not seed formal verdict rows.

## Open questions

Which additional host capabilities can safely expose recovery without widening client authority?
What recovery windows best satisfy both upstream semantics and measured client memory?
