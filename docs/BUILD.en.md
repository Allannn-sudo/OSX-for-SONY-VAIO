# Build the offline research object

[简体中文](BUILD.zh-CN.md) · [Project progress](PROGRESS.en.md) · [Main page](../README.md)

This process builds the 32-bit `R3-OFFLINE` research object only. **It is not an installation or driver-loading procedure.** It fixes one confirmed legacy Tiger loader-format problem but retains unresolved runtime waits and has not been validated on the VAIO.

## Separately supplied dependencies

The repository does not include Apple SDKs, legacy toolchains or driver binaries. On a macOS host, supply:

| Dependency | Purpose and tested version |
| --- | --- |
| Python 3 | Runs the builder and read-only format check, using the standard library only |
| Apple GCC `cc1plus` / `cc1` | Tested with Apple GCC 4.2.1, Apple build 5666.3; matching C++ and C frontends |
| `MacOSX10.4u.sdk` | Tiger kernel headers, user headers and the static libraries listed below |
| i386-capable `ld-classic` | Combines objects with the Tiger libraries into a relocatable `MH_OBJECT`; must support this recipe's options |
| `clang` | **Assembles `.s` files emitted by legacy GCC only**; defaults to `/usr/bin/clang` |

The SDK must contain:

```text
System/Library/Frameworks/Kernel.framework/Headers/
usr/include/
usr/lib/libkmodc++.a
usr/lib/libkmod.a
usr/lib/gcc/i686-apple-darwin9/4.0.1/libcc_kext.a
```

The legacy GCC used here is an x86_64-host executable capable of running on the modern host. Apple Silicon requires an environment that can execute it. The script neither installs that environment nor downloads dependencies or changes system tools.

Modern clang is used solely as an assembler in this project. Using it as the C++ compiler with `-fapple-kext` does not substitute for the reviewed legacy GCC kernel C++ ABI.

## Build command

Run from the repository root, replacing the placeholder paths with your own tools. `--output` must name a **new, nonexistent directory outside the checkout**. Choose another directory name for a subsequent build.

```sh
python3 scripts/build_ps2_offline.py \
  --cc1plus "/path/to/apple-gcc42/cc1plus" \
  --cc1 "/path/to/apple-gcc42/cc1" \
  --sdk "/path/to/MacOSX10.4u.sdk" \
  --ld "/path/to/ld-classic" \
  --output "/private/tmp/vaio-ps2-research-001"
```

Use `--clang` to select another assembler frontend. The builder rejects output inside this checkout, the SDK, an existing directory or a protected system path. It writes into the new output directory only; it does not load kernel extensions, access hardware ports, write disk devices, or change boot files or caches.

The recipe:

1. Copies an explicit source/header allowlist into the output directory and generates a self-contained `module_info.c`.
2. Uses legacy GCC to emit i386 assembly. Key options include `-mkernel`, `-fapple-kext`, `-fno-jump-tables` and options disabling SSE/MMX/FPU use.
3. Assembles with clang and combines with `ld-classic`. The original module name and `1.1.0` version remain; the research marker is `VAIO-Y18C-PS2-R3-OFFLINE-20261019`.
4. Invokes the sibling `audit_tiger_kext_loader.py` for selected legacy loader constraints, then verifies unchanged source hashes and the expected marker.

## Outputs and evidence

The external output directory contains copied source, assembly, objects, intermediate logs, `commands.json`, input hashes, `loader-preflight.json` and `build-result.json`. `ApplePS2Controller` is an offline object, and the directory is not a deployable `.kext` package. Do not copy it into Tiger's Extensions or caches.

During this repository preparation, the actual local tools and SDK successfully built outside the checkout. The format preflight passed, the 340 undefined symbols matched the prior offline R3, the marker was present and source hashes stayed unchanged. This particular output also matched the prior offline object byte for byte. Byte equality does not replace semantic checks when changing tools or paths.

This builder does not repeat every historical ABI, layout, instruction or real-machine dependency review. `loader_preflight_passed` covers the selected format constraints only; `safe_to_install` remains `false`. Building successfully does not establish working input, successful kernel loading or runtime safety.

Keep source and checking tools in Git while leaving build output outside the checkout. Logs contain local tool paths; inspect them for private information before sharing.
