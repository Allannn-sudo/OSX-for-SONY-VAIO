# Read-only input state after recovery

Target: installed Mac OS X 10.4.8, i386 Darwin 8.8.1 on the VAIO. No driver is included.

1. Transfer the repository ZIP to the Tiger Desktop and extract it there, preserving executable permissions.
2. Open this folder and double-click `Collect-Input-State.command`. No administrator password or restart is required.
3. Return the new Desktop `Input-Post-Recovery-…zip` to the local research workspace. Say whether the built-in keyboard and touchpad worked when it was collected. If ZIP creation fails, return the matching report folder.

The script reads module/PS2 registry state, existing boot messages and the on-disk controller hash. It writes only its Desktop report and ZIP. It does not load/unload drivers, edit system or boot files, retire caches or access controller ports directly.

The on-disk hash does not prove which binary is already loaded in memory. Command failures are retained rather than reported as success. Reports may contain system identifiers from existing logs; keep them out of the public repository.
