# Archive scope and use

[简体中文](ARCHIVE.zh-CN.md) · [Home](../README.en.md)

This public snapshot records the project as of **2026-10-19**. Upload the contents of this directory as the repository root. No GitHub account, remote URL or commit identity is embedded, and nothing has been pushed.

## Included

- Chinese and English home pages, the hardware photo, and matching progress/build notes.
- R3-OFFLINE research source, Apple notices and the complete APSL 1.1 text.
- An offline builder with explicit external toolchain paths, read-only loader-format preflight and host protocol simulation.
- 41 portable tests that require no original or experimental driver binaries.
- A read-only input-state collector and status/historical-file-hash summaries without raw logs.

`MANIFEST.sha256` records the other snapshot files for transfer and preservation checks. It is a content manifest, not a digital signature. Regenerate it after changing files.

## Kept local

- The JaS ISO, generated USB images, Apple kernels/system files and driver binaries.
- The Tiger SDK, historical compilers and other downloads.
- Raw diagnostics, system logs, full IORegistry dumps, machine/volume identifiers and personal backups.
- The withdrawn R2 package and unsafe historical installation/rollback entry points.
- Historical cosmetic assets and binary NIB patches.

This directory is therefore not a disaster-recovery copy of the complete workspace. Keep local installation media, the actual original drivers and backups separately if you need to recover the machine or rebuild its installation media. This repository provides no installation-media download.

## Tool boundaries

Portable tests, protocol simulation and format preflight run on a modern development host without loading kernel code. The full source build needs separately supplied legacy tools and SDK files; its result remains unsuitable for deployment.

`tools/Tiger-Input-State/Collect-Input-State.command` targets installed i386 Tiger 10.4.8 / Darwin 8.8.1. It needs no administrator password, reads state and saves a Desktop report without changing drivers, boot settings or caches. This export corrects the earlier unsupported `ioreg -r` option: Tiger uses supported `-c` and `-w` options, without `-l`, which would expose unrelated device properties. New reports can still contain existing boot logs and device identifiers; use them for diagnosis rather than committing them publicly. Results from this revised collector remain pending.

The previous 33 local loader tests used original/R2/R3 objects. This repository's 41 tests use independently synthesized data; these are distinct suites. The 11 protocol simulations do not replace hardware timing, interrupt, binding or wake testing.

## Maintenance

Keep Chinese and English progress notes aligned. Distinguish source checks, module loading, device binding and observed usability. `.gitignore` excludes common generated files, images and private reports; it cannot remove files already committed into Git history.
