# Ecosystem replacement Contract — v1 (DRAFT)

Parent: [composition.v1](composition.v1.md).
Desired behavior is distinct from current acceptance evidence.

## Who builds against this

Independent client, host, ACP adapter and capability-provider authors.
The steward reviews wording independently of implementation progress.

## What it is

```text
native Ratatui client -> standard AHP 0.9 host
host -> stable ACP agent boundary
negotiated extension -> independently owned optional capability
source review / handshake / fixture / live account -> distinct evidence
```

The artifact describes a boundary, not a claim of complete implementation.
Receipts live in [acceptance notes](../notes/ACCEPTANCE.md).

## The promises

1. **Use public protocol boundaries.** The client consumes standard AHP resources/actions and official reducers. Host implementations and ACP-backed engines are independently replaceable; agent selection binds at session creation and mid-session engine switching is not promised.
   Broken: A sibling private import or vendor assumption is required for ordinary chat.
   Affected: people choosing their host and agent implementations.

2. **Honor declared capability.** Configuration and optional controls appear only through advertised, versioned capabilities. Unknown required configuration is not guessed or reset. Credential/authentication ownership remains outside private client drafts and transcripts.
   Broken: The client offers a control whose semantics it cannot honor or copies provider credentials.
   Affected: operators and independent capability owners.

3. **Preserve module freedom.** Native Amplifier bundles, orchestrators, context, providers, tools and hooks remain agent-owned and replaceable without frontend changes. The client renders effective configuration only through supported public host representations.
   Broken: An ordinary native module imports terminal widgets or demands a client-specific runtime fork.
   Affected: module authors and people assembling custom runtimes.

4. **Keep generic tools useful.** Unrecognized tools retain structured input, output, status and errors through generic rendering. Rich views are optional; no custom widget is required to observe or approve an ordinary tool.
   Broken: A tool disappears, loses its failure or treats output as a new executable instruction.
   Affected: authors adding tools independently.

5. **Preserve authority across replacements.** Approvals use the actual offered IDs; cancellation retains host semantics; origins and local-effect revisions remain checked. Protocol compatibility never authorizes an unknown extension or private device inspection.
   Broken: A faster replacement bypasses approval or grants an agent access to another client’s draft.
   Affected: people trusting mixed implementations.

6. **Qualify the actual peer.** Source review, protocol handshake, deterministic execution, installed package and real-account behavior are separate receipts. Each supported swap uses independently built public artifacts and states untested vendor features explicitly.
   Broken: Import success is called full compatibility or a fixture is presented as an external account.
   Affected: maintainers choosing combinations to support.

## Not in v1

Universal historical extension compatibility, provider account configuration,
identical vendor-specific controls, or client ownership of Core/Foundation policy.

## How the kit checks it

Run ordinary AHP actions against independent host builds and ACP fixtures.
Add public vendor adapter tests without bypassing authentication or billing boundaries.
Record known gaps and unsupported negotiation instead of converting them to passes.
The document checker verifies shape and links, not behavior or ratification.
DRAFT contracts do not seed formal verdict rows.

## Open questions

Which independently implemented AHP hosts provide the next useful conformance test?
Which optional controls justify reusable shared schemas rather than vendor-specific UI?
