# VGN-Y18C · Tiger 10.4.8 model branch

[Overall VAIO project (main)](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/tree/main) · [Model profile](models/vgn-y18c/README.en.md)

[![Offline checks](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/offline-checks.yml/badge.svg?branch=vgn-y18c)](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/offline-checks.yml)

[简体中文](README.md) · **English**

A Pentium M-era Sony VAIO running Mac OS X Tiger while retaining Windows XP.
This repository records the installation, current compatibility and ongoing driver research on this particular machine. Updated **2026-10-19**.

![Sony VAIO VGN-Y18C running Mac OS X Tiger 10.4.8](github-ph.jpg)

*Hardware photo provided by the project owner. About This Mac text has received cosmetic changes; the photo does not establish complete hardware support.*

## Current progress

**Tiger is installed and reaches the desktop. Reliable built-in keyboard and touchpad support remains unresolved.** An experimental PS/2 controller caused a boot panic; restoring the original controller brought the desktop back. The new candidate remains source for offline research.

| Area | Status |
| --- | --- |
| USB installation and internal-disk boot | Installed on the machine; desktop reached again after recovery |
| Windows XP | Partition retained and previously booted; a full dual-boot round trip after the latest recovery is pending |
| Darwin boot menu | Configured, using Legacy BIOS + MBR |
| USB keyboard and mouse | Working on the machine |
| Built-in keyboard and touchpad | Briefly worked, failed again after a restart; investigation continues |
| Intel 2200BG Wi-Fi | Historical driver researched; successful networking unverified |
| Sleep and lid sleep | Unresolved |
| Graphics, audio and other devices | Graphical desktop works; acceleration, audio and other functions have not been fully validated |

See the [English progress report](docs/PROGRESS.en.md) for the investigation, failures and next steps.

## This machine

| Component | Project record |
| --- | --- |
| Model | Sony VAIO VGN-Y18C |
| Processor | Intel Pentium M 755, 2.00 GHz, 32-bit / SSE2 |
| Memory | 2 GB DDR |
| Chipset / graphics | Intel 855GME / ICH4-M; Intel Extreme Graphics 2 |
| Wireless | Intel PRO/Wireless 2200BG, `8086:4220` |
| Storage | 128 GB Kingston, approximately 38.86 GB for Tiger, XP retained |
| System / boot | Mac OS X 10.4.8, semthex Darwin 8.8.1, BIOS / MBR / Darwin |
| Installation media | 32 GB USB drive; no usable optical drive for this installation |

These describe this machine, not every VGN-Y18C's factory configuration. The storage adapter controller, actual panel resolution and other devices still need verification. This setup uses no EFI, OpenCore or rEFInd.

## Repository contents

```text
README.md / README.en.md          Chinese and English home pages
github-ph.jpg                     Hardware photo, original pixels, capture metadata removed
docs/                             Bilingual progress, offline build and archive notes
drivers/VAIOPS2Controller-r3-offline/
                                  PS/2 source for offline research only
scripts/                          Offline build, loader preflight and protocol simulation
tests/                            Portable tests using handcrafted Mach-O data
tools/Tiger-Input-State/           Read-only input-state collector for Tiger
evidence/                         Status and historical file hashes, without private reports
licenses/                         Complete APSL 1.1 text for the Apple source
```

This is a versionable source and research snapshot. It excludes ISOs, installation images, Apple system binaries, driver binaries, SDKs, compilers, raw diagnostics and personal backups. Keep the full local workspace separately. See [archive scope](docs/ARCHIVE.en.md).

## Offline checks

On a modern development host, Python 3.9+ runs the portable tests without original driver files:

```sh
python3 -B -m unittest discover -s tests -v
```

The host protocol simulation substitutes port operations and does not access hardware:

```sh
c++ -std=c++11 -Wall -Wextra -Werror scripts/ps2_init_protocol_sim.cpp -o /tmp/vaio-ps2-protocol-sim
/tmp/vaio-ps2-protocol-sim
```

Building the complete candidate additionally requires legacy Apple GCC, a Tiger SDK and a suitable linker. See the [English build notes](docs/BUILD.en.md). Passing format, ABI or simulation checks does not establish safe kernel loading.

## PS/2 research status

R2 was withdrawn: five const scattered relocations triggered a null-pointer path in Tiger's old loader. R3-OFFLINE uses `-fno-jump-tables` to remove this known build defect, but inherited unbounded waits and IRQ risks remain. It has not been loaded on the VAIO. This repository provides no driver installation entry point.

The next steps are to confirm post-recovery input state and address runtime deadlines and error propagation offline. An external diagnostic environment isolated from internal system files comes later. Wi-Fi and sleep testing remain behind input reliability.

## Sources and licensing

Apple-derived source retains its copyright and applicable license. See [third-party notices](THIRD_PARTY_NOTICES.md) and [license scope](LICENSE.md). The hardware photo was supplied by the project owner. This independent hardware project is not affiliated with Sony or Apple.
