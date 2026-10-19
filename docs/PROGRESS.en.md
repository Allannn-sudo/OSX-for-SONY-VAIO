# Project progress and validation limits

[简体中文](PROGRESS.zh-CN.md) · [Back to the main page](../README.en.md)

Updated **2026-10-19**. This personal hardware project brings Mac OS X Tiger 10.4.8 to a Sony VAIO VGN-Y18C while retaining Windows XP and investigating device support.

**Tiger has reached the desktop. Reliable built-in keyboard and touchpad support remains unresolved.** An experimental controller caused a boot panic; restoring the original controller subsequently brought the desktop back. The current bootable configuration is being preserved while further driver work stays offline.

## Hardware and installation environment

| Item | Project record |
| --- | --- |
| Computer | Sony VAIO VGN-Y18C |
| CPU | Intel Pentium M 755, 2.00 GHz, SSE2, 32-bit |
| Memory | 2 GB DDR |
| Chipset | Intel 855GME / ICH4-M |
| Graphics | Intel Extreme Graphics 2; graphical desktop reached, hardware acceleration unverified |
| Wireless | Intel PRO/Wireless 2200BG, observed PCI ID `8086:4220` |
| Internal storage | 128 GB Kingston; approximately 38.86 GB for Tiger, XP partition retained; adapter controller unconfirmed |
| Firmware and boot | Legacy BIOS, MBR, Darwin boot menu |
| System | Mac OS X 10.4.8, 32-bit semthex Darwin 8.8.1 kernel |
| Installation media | 32 GB USB drive; no usable optical drive for this installation |

These describe this machine and the project records, rather than every VGN-Y18C's factory specification. Actual panel resolution, audio, other expansion devices and long-term system stability have not been fully validated.

## Current usability

| Feature | Status | Evidence and limits |
| --- | --- | --- |
| USB installation and Tiger desktop | Completed on the machine | USB installer booted and installed to the internal disk; the desktop was reached again after R2 recovery |
| Windows XP retained | Preserved, previously booted successfully | Darwin selection menu configured; a complete XP/Tiger boot round trip after the latest recovery remains pending |
| USB keyboard and mouse | Working | External input was used in the installer and desktop |
| Built-in keyboard and touchpad | Unresolved | Work in BIOS, boot menu and XP; briefly worked in Tiger, then failed again; no valid working-state capture exists |
| Wi-Fi | Connection unverified | 2200BG identified and a Tiger driver researched; no confirmed scan, association or address assignment |
| Sleep and lid sleep | Unresolved | Closed-lid state reaches the system; successful sleep and wake have not been demonstrated |
| Graphics, audio and other devices | Partly unverified | Displaying a desktop does not establish QE/CI acceleration or other hardware support |

## Completed work

1. Analyzed the JaS 10.4.8 media, its SSE2 installation route, 32-bit kernel and BIOS bootstrap; checked installation archives and mkext contents.
2. Built USB media using an active MBR HFS+ partition and wrote it to a 32 GB drive. File-level readback verified 10,171 original installer files and the Darwin bootstrap; the HFS check passed.
3. Kept XP, allocated approximately 38.86 GB to Tiger, completed the installation and configured the Darwin menu. This BIOS/MBR setup does not require an EFI System Partition.
4. Collected and analyzed input, ACPI and power reports. Built-in input works outside Tiger; Tiger PS/2 initialization and driver binding remain unreliable.
5. Preserved the original and tested input files while distinguishing on-disk drivers, caches and runtime state. A backup named “Working” was confirmed by the owner to have been collected after input failed; it is not a verified working driver.
6. Investigated an actual kernel panic, identified a legacy loader incompatibility, and completed separate offline builds, checks and runtime-path reviews.

## R2 failure and recovery

R2 is a withdrawn PS/2 controller experiment. Its build placed five scattered relocations in `__TEXT,__const`, sharing the section with vtables. Tiger's old kernel linker skipped initialization of the corresponding cache entries and later dereferenced empty records. The machine's panic address and disassembly matched this path. The failure occurred during loading, before successful execution of the new hardware initialization could be established.

Earlier ABI checks, protocol simulations and installation-transaction tests did not cover this loader constraint. Passing them did not establish bootability.

Recovery review also found a transaction-design problem: after copying the original controller, a later cache or timestamp error could cause the helper to put the previous R2 back. The complete error output from that incident was not preserved, so its precise failing operation is unknown. Recovery ultimately used a hash-checked native copy of the original controller, after which the owner confirmed returning to the desktop. The R2 installation entry point is disabled; this public collection does not provide its installer package.

## R3-OFFLINE: what changed and what remains unproven

A separate research build uses `-fno-jump-tables` to eliminate the five problematic relocations. The failed R2 artifacts were preserved rather than overwritten or republished.

- All 33 tests for the selected legacy loader-format checks pass. The original passes, R2 is correctly rejected, and the new research object passes this preflight.
- Checks for six original vtables, class sizes, field offsets and related ABI properties pass, together with 11 host protocol simulations.
- The new object has not been loaded or tested on the VAIO and has no installation entry point.
- Review still finds inherited unbounded port waits, cross-channel reads and IRQ data-draining paths. Timeouts, error propagation and interrupt continuation require further work. A compiler-flag correction is not a completed input repair.

Offline checks can reject known bad objects; they cannot establish real hardware timing, boot safety or functional input. Kernel experiments can still panic or hang. New candidates are currently kept outside the internal system's automatic driver-loading path.

## Wireless and power research

The 2200BG candidate is the historical Tiger `iwi2200` r779 release. Its source, dependencies and basic compatibility requirements were reviewed; **real-machine networking remains unverified**. This version supports open networks and legacy Open WEP, rather than WPA/WPA2/WPA3. The available network's security remains unconfirmed, so this is not a solution for joining modern protected Wi-Fi networks.

Power reports show that closed-lid state reaches rootDomain while lid-sleep policy stays disabled. Manual sleep adds a hibernation-preparation error and `System Doze`; a unique causal link has not been established, nor has successful sleep/wake. ACPI drivers are not being replaced as a speculative fix. Hardware changes for Wi-Fi and sleep are paused while input and boot reliability take priority.

## Next steps

1. Obtain a fresh, read-only input-state report after recovery, accompanied by the observed keyboard and touchpad behavior. **This report has not yet been received.**
2. Continue offline work on unbounded runtime paths and error handling, using fault-injection checks that execute the actual shared routines.
3. Once evidence supports a candidate, design an external diagnostic environment isolated from the internal Tiger files. Such test media has not yet been prepared.
4. After input becomes reliable, validate Wi-Fi, sleep and XP/Tiger boot round trips separately and record each result.

This public directory collects documentation, source and checking tools for version control. It is not a complete installable distribution. It excludes ISOs, Apple system/SDK binaries, driver binaries, raw private diagnostics, backups and local toolchains.

## Key technical references

- [Apple IOKitUser-297.10: legacy kld relocation and vtable handling](https://github.com/apple-oss-distributions/IOKitUser/blob/IOKitUser-297.10/kext.subproj/kld_patch.c)
- [Apple boot-132: driver and mkext loading](https://github.com/apple-oss-distributions/boot/blob/boot-132/i386/boot2/drivers.c)
- [Apple xnu-792.13.8: power and lid policy](https://github.com/apple-oss-distributions/xnu/blob/xnu-792.13.8/iokit/Kernel/IOPMrootDomain.cpp)

Original Apple source explains the period's interfaces and code paths. The machine runs a patched kernel, so identical behavior cannot be assumed throughout.
