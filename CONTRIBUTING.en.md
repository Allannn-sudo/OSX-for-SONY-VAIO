# Contributing

[简体中文](CONTRIBUTING.md) · [Project home](README.en.md)

Contributions can include actual VAIO hardware reports, historical sources, reproducible issues, documentation and source improvements. VGN-Y18C is currently the only physically documented model; other machines need their own evidence.

## Reports and questions

Use the hardware form to record the exact model, actual CPU/chipset, system, boot method and separately verified or unverified features. A regression report should explain recent changes, observed behavior, reproduction steps and whether the machine still boots.

Publish only the relevant, sanitized excerpts. Keep full disk backups, personal files, serial numbers, network credentials and complete raw logs local. Support conclusions with sources or observations, and distinguish inference from testing.

Once Discussions is enabled, use Q&A for real questions and let the questioner confirm the result. Be respectful; different models can behave differently.

## Changes and pull requests

1. Create a focused `feature/…`, `fix/…` or `docs/…` branch from the intended target.
2. Make the change and update relevant Chinese/English records. Retain upstream notices and provenance.
3. Run appropriate offline checks and record both results and untested areas.
4. Open a PR explaining the problem, affected models, verification and remaining limits.

`main` maintains the whole project and model index. `vgn-y18c` maintains that model's stage snapshot. The branches have different home pages; avoid accidentally replacing the project overview with a model page.

```sh
python3 -B -m unittest discover -s tests -v
```

See the [build notes](docs/BUILD.en.md) for protocol simulations and complete research-object builds. CI checks portable source and simulations; it does not prove safe driver installation. R3-OFFLINE remains untested on the machine.

For actual coauthorship, obtain agreement on public attribution and use GitHub's `Co-authored-by` format. Commit history should reflect work that was actually performed.

## Scope

Keep installation ISOs, Apple system binaries, SDKs, compilers and personal diagnostic backups out of the repository. See [third-party notices](THIRD_PARTY_NOTICES.md) for provenance and applicable licenses. This collection assigns no additional blanket open-source license to all project materials.
