# Composition and ownership Contract — v1 (DRAFT)

Proposed platform boundary derived from the implementation handoff. Ratified shared CS/CX/CD/CB client-family contracts remain parent obligations; this platform wording remains DRAFT and implementation evidence does not ratify it.
Parent: [vision](../docs/VISION.md).

## Who builds against this

Terminal client, presentation bridge and independent host/capability authors.
The steward reviews this wording independently of implementation progress.

## What it is

```text
client -> standard AHP host -> ACP agent -> native runtime
conversation -> presentation boundary -> terminal
client -> local continuity boundary -> private intent and effect receipts
same public behavior -> replaceable frontend, host, transport and modules
```

The example describes a boundary, not a claim that every feature is implemented.
Acceptance evidence lives in [the acceptance notes](../notes/ACCEPTANCE.md).

## The promises

1. **Respect the seam.** The connected product consumes standard AHP 0.9 resources/actions through upstream SDK reducers. Execution reaches the host’s ACP boundary; clients import no Core, Foundation or host internals. A packaged protocol sidecar is permitted to reuse the official reducer implementation.
   Broken: Changing a widget changes tool authority, or a language boundary becomes mandatory without evidence.
   Affected: client builders and people relying on predictable execution.

2. **Keep policy replaceable.** Execution and context policy stay in the chosen modules. The negotiated host and ACP agent own runtime ownership, lease policy, release and reacquisition. Private typing, navigation and inspection make zero backend writes and cannot acquire or prolong a native writer. Agents start on demand; the host alone manages automatic bounded reuse without client pool-size or Ready conversations controls. Opening retained work does not request agent preparation, and reuse preserves canonical history and active execution.
   Broken: An independent tool needing a TUI import breaks ecosystem compatibility.
   Affected: the boundary's clients and the person relying on them.

3. **Name composition changes.** Every host exclusion or overlay is visible with the effective composition.
   Broken: A missing authored hook with no recorded explanation misleads the operator.
   Affected: the boundary's clients and the person relying on them.

4. **Give each rule one home.** [Session](session.v1.md), [presentation](presentation.v1.md), [continuity](continuity.v1.md), [ecosystem](ecosystem.v1.md) and [performance](performance.v1.md) own their details.
   Broken: A second conflicting definition makes a client's obligations ambiguous.
   Affected: the boundary's clients and the person relying on them.

5. **Bound the responsibility.** This project has at most 600 contract lines and 58 production source files, regardless of language. The [cutover inventory](../notes/AHP-CUTOVER.md) records the retired embedded host and current standard protocol/client-only boundary.
   Broken: Exceeding either or gaining a second domain with its own vocabulary and kit requires a split proposal.
   Affected: the boundary's clients and the person relying on them.

6. **Replace implementations, preserve obligations.** Frontend, host, adapters and policy modules may change without preserving their language or topology.
   Broken: A faster replacement silently removes a promised behavior or moves product policy into the thin kernel.
   Affected: ecosystem authors and people depending on the session contract.

## Not in v1

Remote agent process supervision and an operating-system sandbox. The connected product wire is upstream AHP; its packaged sidecar is an implementation choice, not a private protocol requirement.

## How the kit checks it

Inspect imports, composition reports, document links and file counts.
The document check validates shape and links; runtime tests supply behavior evidence.
Draft contracts do not seed formal Converge ledger rows.

## Open questions

Does a long-lived child process, in-process bridge or another host best satisfy the measured obligations?
Which optional client surfaces should move to independent capability packages?
