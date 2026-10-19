#!/usr/bin/env python3
"""Build a Tiger i386 research object outside the checkout; never install/load it.

Requires separately obtained Apple GCC 4.2 frontends, a Tiger SDK and an
i386-capable classic linker. Modern clang is used as an assembler only.
Outputs and local tool paths remain in the explicit external output directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / 'drivers' / 'VAIOPS2Controller-r3-offline'
AUDITOR = Path(__file__).resolve().with_name('audit_tiger_kext_loader.py')
MARKER = b'VAIO-Y18C-PS2-R3-OFFLINE-20261019'
SOURCE_NAMES = (
    'ApplePS2Controller.cpp', 'ApplePS2Controller.h', 'ApplePS2Device.h',
    'ApplePS2KeyboardDevice.cpp', 'ApplePS2KeyboardDevice.h',
    'ApplePS2MouseDevice.cpp', 'ApplePS2MouseDevice.h', 'VAIOPS2Init.h',
    'NOTICE',
)
MODULE_INFO = '''#include <mach/mach_types.h>
extern kern_return_t _start(kmod_info_t *ki, void *data);
extern kern_return_t _stop(kmod_info_t *ki, void *data);
KMOD_EXPLICIT_DECL(com.apple.driver.ApplePS2Controller, "1.1.0", _start, _stop)
__private_extern__ kmod_start_func_t *_realmain = 0;
__private_extern__ kmod_stop_func_t *_antimain = 0;
__private_extern__ int _kext_apple_cc = __APPLE_CC__;
'''
PROTECTED = (
    '/System', '/Library', '/Applications', '/usr', '/bin', '/sbin',
    '/dev', '/etc', '/private/etc', '/private/var', '/Volumes',
)
WARNING = '''OFFLINE RESEARCH ONLY. DO NOT INSTALL OR LOAD.

This object is not a .kext installation package. Passing a selected static
loader-format check does not prove bootability, hardware safety, ABI identity,
dependency resolution or keyboard/touchpad operation. Known runtime waits still
require work. This builder does not load drivers or change the installed system.
'''


class BuildError(RuntimeError):
    pass


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within(path, parent):
    return path == parent or parent in path.parents


def regular_file(value, label, executable=False):
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file() or executable and not os.access(path, os.X_OK):
        raise BuildError('%s must be a regular%s file: %s' %
                         (label, ' executable' if executable else '', path))
    return path


def output_path(value, sdk, tools):
    requested = Path(value).expanduser()
    if requested.is_symlink() or requested.exists():
        raise BuildError('--output must be a new, nonexistent directory')
    output = requested.resolve()
    if within(output, REPO):
        raise BuildError('--output must be outside this source checkout')
    if within(output, sdk):
        raise BuildError('--output must not be inside the SDK')
    if any(within(output, Path(p).resolve()) for p in PROTECTED):
        raise BuildError('--output must not be inside a protected system path')
    if output == Path('/') or any(within(tool, output) for tool in tools):
        raise BuildError('--output must not contain system roots or input tools')
    return output


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def run_command(command, output, index):
    result = subprocess.run(
        [str(arg) for arg in command], cwd=str(output), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
    )
    (output / ('command-%02d.log' % index)).write_bytes(result.stdout)
    if result.returncode:
        raise BuildError('command %d failed (exit %d); see command-%02d.log' %
                         (index, result.returncode, index))
    return result.stdout


def build(args):
    if sys.platform != 'darwin':
        raise BuildError('this recipe requires macOS-hosted tools')
    tools = {name: regular_file(getattr(args, name), name, executable=True)
             for name in ('cc1plus', 'cc1', 'clang', 'ld')}
    sdk = Path(args.sdk).expanduser().resolve(strict=True)
    if not sdk.is_dir():
        raise BuildError('--sdk must be an SDK directory')
    kernel_headers = sdk / 'System/Library/Frameworks/Kernel.framework/Headers'
    user_headers = sdk / 'usr/include'
    for directory in (kernel_headers, user_headers):
        if not directory.is_dir():
            raise BuildError('required SDK headers missing: %s' % directory)
    libraries = [regular_file(sdk / name, 'SDK library') for name in (
        'usr/lib/libkmodc++.a', 'usr/lib/libkmod.a',
        'usr/lib/gcc/i686-apple-darwin9/4.0.1/libcc_kext.a',
    )]
    regular_file(AUDITOR, 'sibling loader auditor')
    source_files = [regular_file(SOURCE / name, 'source') for name in SOURCE_NAMES]
    before = {name: sha256(SOURCE / name) for name in SOURCE_NAMES}
    if MARKER not in (SOURCE / 'VAIOPS2Init.h').read_bytes():
        raise BuildError('unexpected source marker; this recipe targets R3-OFFLINE')
    output = output_path(args.output, sdk, tools.values())
    output.mkdir(parents=True, exist_ok=False)
    (output / 'OFFLINE-ONLY.txt').write_text(WARNING, encoding='utf-8')
    src = output / 'src'
    src.mkdir()
    include = output / 'include'
    ps2_headers = include / 'IOKit/ps2'
    ps2_headers.mkdir(parents=True)
    for source_file in source_files:
        shutil.copy2(source_file, src / source_file.name)
    for name in ('ApplePS2Device.h', 'ApplePS2KeyboardDevice.h', 'ApplePS2MouseDevice.h'):
        shutil.copy2(src / name, ps2_headers / name)
    (src / 'module_info.c').write_text(MODULE_INFO, encoding='utf-8')
    write_json(output / 'source-sha256.json', before)

    # These flags reproduce the reviewed legacy recipe. clang sees .s only.
    common = [
        '-fno-jump-tables', '-quiet', '-m32', '-mkernel',
        '-mmacosx-version-min=10.4', '-DKERNEL', '-DKERNEL_PRIVATE',
        '-DDRIVER_PRIVATE', '-DAPPLE', '-DNeXT', '-fno-common',
        '-fno-stack-protector', '-fno-pic', '-fno-builtin', '-finline',
        '-fno-keep-inline-functions', '-msoft-float', '-mno-sse', '-mno-sse2',
        '-mno-mmx', '-nostdinc', '-Os', '-isystem', str(kernel_headers),
        '-isystem', str(user_headers), '-I', str(include), '-I', str(src),
    ]
    cpp_flags = common.copy()
    cpp_flags.insert(cpp_flags.index('-mmacosx-version-min=10.4'), '-fapple-kext')
    cpp_flags.insert(cpp_flags.index('-fno-common'), '-fno-exceptions')
    cpp_flags += ['-fno-rtti', '-fno-threadsafe-statics', '-fno-use-cxa-atexit',
                  '-nostdinc++', '-fdump-class-hierarchy']
    commands = []
    object_files = []
    units = [('ApplePS2Controller', 'cpp'), ('ApplePS2KeyboardDevice', 'cpp'),
             ('ApplePS2MouseDevice', 'cpp'), ('module_info', 'c')]
    for stem, language in units:
        asm, obj = output / (stem + '.s'), output / (stem + '.o')
        compiler = tools['cc1plus' if language == 'cpp' else 'cc1']
        flags = cpp_flags if language == 'cpp' else common
        commands.append([str(compiler)] + flags +
                        [str(src / (stem + '.' + language)), '-o', str(asm)])
        commands.append([str(tools['clang']), '-target', 'i386-apple-macosx10.4',
                         '-c', str(asm), '-o', str(obj)])
        object_files.append(str(obj))
    result_path = output / 'ApplePS2Controller'
    commands.append([str(tools['ld']), '-no_data_in_code_info', '-r', '-arch',
                     'i386', '-keep_private_externs', '-o', str(result_path)] +
                    object_files + [str(p) for p in libraries])
    commands.append([sys.executable, str(AUDITOR), str(result_path)])
    write_json(output / 'commands.json', commands)
    write_json(output / 'build-inputs.json', {
        'offline_only': True, 'sdk': str(sdk),
        'tools': {name: {'path': str(path), 'sha256': sha256(path)}
                  for name, path in tools.items()},
        'sdk_libraries': {str(path.relative_to(sdk)): sha256(path) for path in libraries},
        'module_info_sha256': sha256(src / 'module_info.c'),
    })
    try:
        audit_stdout = b''
        for index, command in enumerate(commands):
            audit_stdout = run_command(command, output, index)
            print('command %d/%d passed' % (index + 1, len(commands)))
        audit_result = json.loads(audit_stdout)
        write_json(output / 'loader-preflight.json', audit_result)
        if len(audit_result) != 1 or not audit_result[0].get('passed'):
            raise BuildError('loader preflight did not confirm this object')
        raw = result_path.read_bytes()
        if MARKER not in raw:
            raise BuildError('built object lacks the expected OFFLINE marker')
        if before != {name: sha256(SOURCE / name) for name in SOURCE_NAMES}:
            raise BuildError('source files changed during the build')
        summary = {
            'offline_only': True, 'build_succeeded': True,
            'loader_preflight_passed': True, 'marker': MARKER.decode('ascii'),
            'object_bytes': len(raw), 'object_sha256': sha256(result_path),
            'hardware_tested': False, 'safe_to_install': False,
            'source_unchanged': True,
            'limits': ['Selected static loader profile only; no hardware execution, '
                       'full ABI/layout comparison or dependency validation.',
                       'Inherited unbounded runtime waits remain unresolved.'],
        }
        write_json(output / 'build-result.json', summary)
    except (BuildError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        write_json(output / 'build-result.json', {
            'offline_only': True, 'build_succeeded': False,
            'safe_to_install': False, 'error': str(exc),
        })
        raise
    print('OFFLINE build and selected loader preflight passed: %s' % output)
    print('SHA-256: %s' % summary['object_sha256'])
    print('DO NOT INSTALL OR LOAD; hardware operation and runtime safety are unverified.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc1plus', required=True, help='Apple GCC 4.2 C++ frontend')
    parser.add_argument('--cc1', required=True, help='matching Apple GCC C frontend')
    parser.add_argument('--sdk', required=True, help='separately obtained MacOSX10.4u.sdk')
    parser.add_argument('--ld', required=True, help='i386-capable ld-classic')
    parser.add_argument('--clang', default='/usr/bin/clang', help='assembler frontend only')
    parser.add_argument('--output', required=True, help='new directory outside this checkout')
    args = parser.parse_args(argv)
    try:
        build(args)
    except (BuildError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, 'STOPPED: %s\n' % exc)
    return 0


if __name__ == '__main__':
    sys.exit(main())
