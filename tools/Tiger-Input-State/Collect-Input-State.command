#!/bin/bash
# Tiger 10.4.8 / Darwin 8.8.1: observation only; no driver operations.
set -u
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
umask 077

case "$(/usr/bin/sw_vers -productVersion 2>/dev/null):$(/usr/bin/uname -m):$(/usr/bin/uname -r)" in
    10.4.8:i386:8.8.1) ;;
    *) echo "Run this on the VAIO running Tiger 10.4.8 / i386 Darwin 8.8.1."; exit 1 ;;
esac

if [ ! -d "$HOME/Desktop" ] || [ ! -w "$HOME/Desktop" ]; then
    echo "Desktop is unavailable; nothing was changed."
    exit 1
fi
stamp=$(/bin/date +%Y%m%d-%H%M%S)
report=$(/usr/bin/mktemp -d "$HOME/Desktop/Input-Post-Recovery-$stamp-XXXXXX") || exit 1
name=$(/usr/bin/basename "$report")

capture() {
    file=$1
    shift
    "$@" > "$report/$file" 2>&1
    result=$?
    printf '%s\t%s\n' "$file" "$result" >> "$report/command-exit-codes.txt"
    return 0
}

echo "Reading the recovered input-driver state. No administrator password needed."
echo "No drivers are loaded, unloaded, replaced or deleted by this tool."

capture system-version.txt /usr/bin/sw_vers
capture kernel.txt /usr/bin/uname -a
capture boot-time.txt /usr/sbin/sysctl kern.boottime
capture kextstat.txt /usr/sbin/kextstat
# Tiger's ioreg has no -r; -c prints matching properties, with tree context.
# Do not add -l: on Tiger that would print unrelated devices' properties too.
capture ps2-controller.txt /usr/sbin/ioreg -c ApplePS2Controller -w 0
capture ps2-keyboard-nub.txt /usr/sbin/ioreg -c ApplePS2KeyboardDevice -w 0
capture ps2-mouse-nub.txt /usr/sbin/ioreg -c ApplePS2MouseDevice -w 0
capture ps2-keyboard.txt /usr/sbin/ioreg -c ApplePS2Keyboard -w 0
capture ps2-mouse.txt /usr/sbin/ioreg -c ApplePS2Mouse -w 0
capture ps2-trackpad.txt /usr/sbin/ioreg -c ApplePS2Trackpad -w 0
capture boot-messages.txt /sbin/dmesg

controller=/System/Library/Extensions/ApplePS2Controller.kext/Contents/MacOS/ApplePS2Controller
capture controller-sha1.txt /usr/bin/openssl sha1 "$controller"
capture controller-metadata.txt /usr/bin/stat -f '%N | bytes=%z | mode=%Sp | uid=%u | gid=%g | mtime=%m' "$controller"
capture cache-metadata.txt /bin/ls -ldT /System/Library/Extensions /System/Library/Extensions.mkext /System/Library/Extensions.kextcache

state=UNKNOWN
if [ -r "$controller" ]; then
    digest=$(/usr/bin/openssl sha1 "$controller" 2>/dev/null | /usr/bin/awk '{print $NF}')
    case "$digest" in
        434fc5bc5377ec28fd955c5435e047e7a18fe8a8) state=ORIGINAL_ON_DISK ;;
        6008cc46aa6c66f3aebe6db6f7bd1d4b1dfe9ad0) state=OLD_CC_TRIAL_ON_DISK ;;
        62d92df7f2310bbee7fd537b1be4f0af41357ece) state=WITHDRAWN_R2_ON_DISK ;;
    esac
fi

cat > "$report/READ-ME.txt" <<EOF
Sony VAIO Tiger input state after recovery
Collected: $stamp
Controller executable state: $state

This label describes the executable on disk only. It does not prove the hash
of code already loaded in memory, whether a cached driver was used, or that
the keyboard/touchpad works. Compare kextstat, registry children and boot logs.
Command failures are retained in command-exit-codes.txt; they are not successes.

This collector does not use sudo, load/unload drivers, edit system files,
retire caches, write controller ports, install anything, or request a reboot.
It creates only this Desktop report and its ZIP archive. It does not monitor
live keyboard input. The boot-messages file contains existing driver logs.

When returning the report, say whether the built-in keyboard and touchpad
worked at the moment it was collected. USB input working is a separate fact.
EOF

archive="$report.zip"
if [ -x /usr/bin/zip ] && [ -x /usr/bin/unzip ]; then
    (
        cd "$HOME/Desktop" || exit 1
        /usr/bin/zip -q -r "$archive" "$name"
    )
    packed=$?
    if [ "$packed" -eq 0 ] && /usr/bin/unzip -tq "$archive" >/dev/null 2>&1; then
        echo "Saved and checked: $archive"
    else
        echo "Archive creation/check failed. Return this report folder: $report"
    fi
else
    echo "Return this report folder: $report"
fi
echo "Controller on disk: $state"
echo "Done. You can close this window. No restart is needed."
