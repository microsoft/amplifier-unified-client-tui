# Native wheel build qualification

The earlier wheel hook used the build machine's macOS release as
MACOSX_DEPLOYMENT_TARGET for both the terminal and host proc macros. On the
qualified macOS 27 ARM64 toolchain, rustversion's dylib was rejected by dlopen
with `mis-aligned LINKEDIT string pool`; rustc surfaced E0463 in castaway.
An ordinary source-build dylib loaded. Setting deployment target 27 alone
reproduced the failure without path remapping, ruling out remapping as the
necessary trigger. Both installed Rust compiler distributions reproduced it.

The hook now asks the selected compiler for its deployment floor and uses that
floor for the native artifact and wheel tag. Here the compiler reports 11.0;
LC_BUILD_VERSION in the installed binary also reports minos 11.0. All original
path-remapping, explicit native target, architecture and client-only safeguards
remain. Cargo reused the invalid proc macro after an environment-only floor
change; target directories now include compiler triple and deployment floor.
A clean floor-11 build and repeat keyed build both passed.

The installed wheel includes the native renderer and bundled official AHP
helper, excludes engine dependencies and builder-home paths, and passes four
actual connected AHP terminal cases against an independently installed host.
The native lifecycle terminal qualification passed in a fresh owned session,
covering managed launch choices, details, recovery, reviewed file disposal,
canonical-history preservation and a private draft. A prior installed attempt
received a host refusal for stale indexed family coverage; its original effect
remains unknown and was never resent. Both receipts are retained.

The native lifecycle terminal qualification uses the installed console entry,
a synthetic provider behind actual Core/Foundation/loop-live, and one labelled
managed-file protection participant. This is distinct from distribution's full
production dependent-owner protection qualification.

The wheel tag describes its compiled deployment floor; this run does not prove
execution on older macOS versions, x86-64 or Linux. No paid-account, physical
terminal, release or deployment acceptance is inferred. Original failure receipts
and source qualification remain preserved in the owner handoff.
