# Qualified current TUI release assets

The manifest format is `amplifier-unified-client-tui.release`, schema version 1.
[Schema](manifest-v1.schema.json) is the shape contract; the standard-library
[validator/exporter](../scripts/release_manifest.py) applies semantic bindings.
It describes this canonical repository and package, not the older terminal app.

A manifest binds one exact source commit and package version, AHP 0.9.0 and bundled
SDK 0.9.0, Python >=3.11, Node >=22, and at most 16 qualified native wheels. Each
record binds basename, bytes, SHA256, exact wheel tag, OS/architecture, and a
SHA256-bound sanitized qualification evidence asset. Runtime versions are actual
installed qualification inputs. `osFloor` is the macOS compiler/wheel deployment
floor, not a claim of testing every OS above it. Linux `minimumGlibc` conservatively
uses the qualification host's glibc; a lower glibc is not advertised as qualified.
`testedOS` identifies where installed tests ran. No Windows or universal wheel is
advertised. A configured CI runner is not an accepted platform until its entire
independent installation, isolation, privacy and actual PTY job passes.

The manual workflow builds candidates on Linux x86_64/ARM64 and macOS x86_64/ARM64.
It uploads only wheel, manifest and safe qualification summary as CI artifacts.
Publication is a separate reviewed root-owner action after required source merges.
No tags, GitHub releases, package registry writes or live installation occur here.

From a clean exact checkout, qualify with an independently built public host:

```sh
uv run --no-sync python scripts/qualify_current.py
uv run --no-sync python scripts/release_manifest.py export --output .release-assets
uv run --no-sync python scripts/release_manifest.py validate .release-assets/manifest.json --verify-assets
```

Qualification writes its source/version/runtime/bytes binding only after all
required checks pass. Export requires a fresh output directory and refuses tracked changes, changed source, modified
wheel bytes or incomplete evidence. It emits no local paths, tokens, histories,
private drafts, unknown-effect journals or complete test logs. Raw owned evidence
stays private in `.evidence/current`; summary hashes bind each completed check log.

To combine independently passing platform fragments for the same source/version:

```sh
python scripts/release_manifest.py assemble candidates/*/manifest.json --output reviewed-release
python scripts/release_manifest.py validate reviewed-release/manifest.json --verify-assets
```

Assembly rejects mixed sources/versions/compatibility, duplicate targets, wrong
asset hashes and missing/failed evidence. Failed targets are absent; it does not
reuse another source's wheel or substitute a previous release. Installers must
validate the complete manifest and exact selected wheel/evidence before staging
or consuming enrollment. Filenames are safe basenames resolved against a reviewed
release authority; the manifest cannot redirect downloads to arbitrary URLs.
Malformed newest candidates must fail visibly rather than silently downgrade.
There is no evidence of real account access, physical-device use, production
installation or release adoption merely because these artifacts pass.

Installer-facing manifest/evidence reads open regular files with no-follow and
nonblocking flags and refuse size above 128 KiB before parsing or hashing. Wheel
hashes and verified copies stream at most the declared bytes plus one growth
probe, with descriptor and path identity/size/time checks before accepting.
FIFOs, symlinks, replaced files and changed contents refuse rather than blocking.
