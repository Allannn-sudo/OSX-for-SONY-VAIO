#!/usr/bin/env python3
"""Read-only preflight for this project's thin i386 Tiger MH_OBJECT kexts.

This is a deliberately narrow input profile, not a general Mach-O validator and
not a proof that a driver can be loaded or run safely. It models concrete unsafe
assumptions in Apple's IOKitUser-297.10 kext.subproj/kld_patch.c. In particular,
relocateSection() reserves one cache record per relocation but leaves records
uninitialized for scattered, non-VANILLA/non-long and local R_ABS entries;
prepareFileForLink() subsequently dereferences every record's fRInfo. Merely
comparing the resulting vtable function names does not detect that defect.

No subprocesses, driver loading, device access or filesystem writes occur here.
"""
import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import struct
import sys

SOURCE = {
    'url': 'https://github.com/apple-oss-distributions/IOKitUser/blob/'
           'IOKitUser-297.10/kext.subproj/kld_patch.c',
    'sha256': 'bb44601700abee0b686cf9afa68032a0ab8451ac4f3190622be530fc1c83c25d',
    'functions': ['parseSymtab', 'findSymbolByName', 'recordClass',
                  'relocateSection', 'patchVTable', 'prepareFileForLink'],
}
LIMITS = [
    'Static format and selected Tiger kld assumptions only; passing is not '
    'permission to deploy and does not prove loading or hardware safety.',
    'No execution, kernel relocation/link simulation, dependency resolution, '
    'C++ ABI/layout comparison, instruction-set audit, interrupt/locking '
    'analysis or PS/2 protocol validation is performed.',
    'The narrow profile accepts little-endian thin i386/all-subtype MH_OBJECT '
    'with LC_SEGMENT, LC_SYMTAB and bounded legacy LC_UNIXTHREAD only. Other '
    'formats require separate review and are rejected, not declared invalid.',
    'Every section containing a defined C++3 vtable or OSObject superClass '
    'pointer is conservatively treated as pseudo-relocated. The kernel and '
    'already-linked images are outside this profile.',
]
MH_MAGIC, CPU_I386, CPU_ALL, MH_OBJECT = 0xfeedface, 7, 3, 1
LC_SEGMENT, LC_SYMTAB, LC_UNIXTHREAD = 1, 2, 5
N_STAB, N_TYPE, N_EXT, N_UNDF, N_ABS, N_SECT = 0xe0, 0x0e, 1, 0, 2, 14


class AuditError(ValueError):
    """Malformed or unsupported object; fail closed without a Python traceback."""


def require(condition, message):
    if not condition:
        raise AuditError(message)


def region(total, offset, size, label):
    require(0 <= offset <= total and 0 <= size <= total - offset,
            '%s exceeds file bounds' % label)


def fixed_name(raw):
    prefix, separator, tail = raw.partition(b'\0')
    require(not separator or not tail.strip(b'\0'),
            'nonzero data after Mach-O name terminator')
    try:
        return prefix.decode('ascii')
    except UnicodeDecodeError:
        raise AuditError('non-ASCII Mach-O segment/section name')


@dataclass
class Relocation:
    index: int
    address: int
    scattered: bool
    type: int
    length: int
    pcrel: bool
    external: bool
    target: int


@dataclass
class Section:
    index: int
    segment: str
    name: str
    address: int
    size: int
    offset: int
    alignment: int
    relocation_offset: int
    relocation_count: int
    flags: int
    header_offset: int
    relocations: list = field(default_factory=list)

    @property
    def label(self):
        return '%s,%s' % (self.segment, self.name)

    @property
    def zerofill(self):
        return (self.flags & 0xff) == 1


@dataclass
class Symbol:
    index: int
    name: str
    type: int
    section: int
    description: int
    value: int
    file_offset: int

    @property
    def debug(self):
        return bool(self.type & N_STAB)

    @property
    def kind(self):
        return self.type & N_TYPE

    @property
    def external(self):
        return bool(self.type & N_EXT)

    @property
    def defined(self):
        return not self.debug and self.kind in (N_ABS, N_SECT)


class MachO:
    def __init__(self, data):
        self.data = data
        require(isinstance(data, bytes), 'input must be bytes')
        require(len(data) >= 28, 'truncated Mach-O header')
        h = struct.unpack_from('<7I', data)
        self.magic, self.cpu, self.subtype, self.filetype, self.ncmds, \
            self.sizeofcmds, self.flags = h
        require(self.magic == MH_MAGIC, 'requires thin little-endian 32-bit Mach-O')
        require((self.cpu, self.subtype, self.filetype) ==
                (CPU_I386, CPU_ALL, MH_OBJECT),
                'requires i386/all-subtype MH_OBJECT (narrow Tiger profile)')
        require(not self.flags & ~0x2000,
                'Mach-O flags outside plain MH_OBJECT/subsections profile')
        region(len(data), 28, self.sizeofcmds, 'load-command area')
        require(self.ncmds > 0 and self.ncmds <= self.sizeofcmds // 8,
                'invalid load-command count')
        self.header_end = 28 + self.sizeofcmds
        self.sections, self.symbols, self.commands = [], [], []
        self.segments = []
        ranges = [(0, self.header_end, 'header/load commands')]
        symtab = None
        offset = 28
        for command_index in range(self.ncmds):
            require(offset + 8 <= self.header_end, 'truncated load command')
            cmd, size = struct.unpack_from('<II', data, offset)
            require(size >= 8 and size % 4 == 0 and
                    size <= self.header_end - offset, 'invalid load-command size')
            self.commands.append(cmd)
            if cmd == LC_SEGMENT:
                require(size >= 56, 'truncated LC_SEGMENT')
                s = struct.unpack_from('<II16s8I', data, offset)
                _, _, rawname, address, vmsize, fileoff, filesize, maxprot, \
                    initprot, nsects, segflags = s
                require(size == 56 + nsects * 68, 'LC_SEGMENT section-count mismatch')
                require(address + vmsize <= 0x100000000, 'segment VM range overflows')
                region(len(data), fileoff, filesize, 'segment data')
                require(not (maxprot | initprot) & ~7 and
                        not initprot & ~maxprot, 'invalid segment protection')
                require(segflags == 0, 'segment flags outside narrow Tiger object profile')
                self.segments.append({'name': fixed_name(rawname), 'address': address,
                                      'size': vmsize, 'offset': fileoff,
                                      'file_size': filesize, 'flags': segflags})
                for i in range(nsects):
                    shoff = offset + 56 + i * 68
                    sh = struct.unpack_from('<16s16s9I', data, shoff)
                    rawsec, rawseg, addr, length, pos, alignment, reloff, nreloc, \
                        flags, reserved1, reserved2 = sh
                    require(len(self.sections) < 255, 'more sections than n_sect can address')
                    sec = Section(len(self.sections) + 1, fixed_name(rawseg),
                                  fixed_name(rawsec), addr, length, pos, alignment,
                                  reloff, nreloc, flags, shoff)
                    require(sec.name and sec.segment, 'empty section/segment name')
                    require(alignment <= 31, 'invalid section alignment exponent')
                    require(addr % (1 << alignment) == 0, 'unaligned section VM address')
                    require(addr + length <= 0x100000000 and address <= addr and
                            length <= address + vmsize - addr,
                            'section outside segment VM range')
                    require(flags & 0xff in (0, 1, 2) and
                            not flags & ~0x800004ff,
                            'section flags outside narrow Tiger object profile')
                    require(reserved1 == 0 and reserved2 == 0,
                            'unsupported section reserved fields')
                    if not sec.zerofill:
                        region(len(data), pos, length, 'section data ' + sec.label)
                        require(fileoff <= pos and length <= fileoff + filesize - pos,
                                'section data outside segment file range')
                        if length:
                            ranges.append((pos, pos + length, 'data ' + sec.label))
                    else:
                        require(nreloc == 0, 'relocations in zerofill section unsupported')
                    region(len(data), reloff, nreloc * 8, 'relocations ' + sec.label)
                    require(not nreloc or reloff % 4 == 0, 'unaligned relocation table')
                    if nreloc:
                        ranges.append((reloff, reloff + nreloc * 8,
                                       'relocations ' + sec.label))
                    self.sections.append(sec)
            elif cmd == LC_SYMTAB:
                require(size == 24 and symtab is None, 'invalid/duplicate LC_SYMTAB')
                symtab = struct.unpack_from('<4I', data, offset + 8)
                self.symtab_command_offset = offset
            elif cmd == LC_UNIXTHREAD:
                # The JaS original has Apple's legacy -r pseudo-thread flavor
                # 0xffffffff. kld ignores thread state; validate its framing only.
                cursor = offset + 8
                require(cursor < offset + size, 'empty LC_UNIXTHREAD')
                while cursor < offset + size:
                    require(cursor + 8 <= offset + size, 'truncated thread-state header')
                    flavor, count = struct.unpack_from('<II', data, cursor)
                    cursor += 8
                    require(count <= (offset + size - cursor) // 4,
                            'thread-state count exceeds command')
                    cursor += count * 4
                require(cursor == offset + size, 'thread-state framing mismatch')
            else:
                raise AuditError('load command 0x%x outside narrow Tiger profile' % cmd)
            offset += size
        require(offset == self.header_end, 'load-command count/size mismatch')
        require(self.sections, 'no sections')
        require(symtab is not None, 'missing LC_SYMTAB')
        vm_ranges = sorted((s.address, s.address + s.size, s.label)
                           for s in self.sections if s.size)
        self._disjoint(vm_ranges, 'overlapping section VM ranges')
        symoff, nsyms, stroff, strsize = symtab
        require(nsyms > 0, 'empty symbol table')
        region(len(data), symoff, nsyms * 12, 'symbol table')
        region(len(data), stroff, strsize, 'string table')
        require(strsize > 0, 'empty string table')
        require(symoff % 4 == 0, 'unaligned symbol table')
        ranges += [(symoff, symoff + nsyms * 12, 'symbols'),
                   (stroff, stroff + strsize, 'strings')]
        self._disjoint(sorted(ranges), 'overlapping file regions')
        self.symoff, self.stroff, self.strsize = symoff, stroff, strsize
        strings = data[stroff:stroff + strsize]
        for index in range(nsyms):
            pos = symoff + index * 12
            strx, typ, sect, desc, value = struct.unpack_from('<IBBHI', data, pos)
            require(strx < strsize, 'symbol string index outside string table')
            end = strings.find(b'\0', strx)
            require(end >= 0, 'unterminated symbol name')
            name = strings[strx:end].decode('latin1')
            symbol = Symbol(index, name, typ, sect, desc, value, pos)
            if not symbol.debug:
                require(symbol.kind in (N_UNDF, N_ABS, N_SECT),
                        'symbol kind outside narrow Tiger profile')
                if symbol.kind == N_SECT:
                    require(1 <= sect <= len(self.sections), 'invalid n_sect symbol reference')
                    section = self.sections[sect - 1]
                    require(section.address <= value <= section.address + section.size,
                            'defined symbol outside its section')
                else:
                    require(sect == 0, 'non-section symbol has nonzero n_sect')
                if symbol.kind == N_UNDF:
                    require(symbol.external and value == 0,
                            'common/local undefined symbol outside linked-object profile')
            self.symbols.append(symbol)
        for section in self.sections:
            for index in range(section.relocation_count):
                address, bits = struct.unpack_from('<II', data,
                                                   section.relocation_offset + index * 8)
                scattered = bool(address & 0x80000000)
                if scattered:
                    reloc = Relocation(index, address & 0xffffff, True,
                                       (address >> 24) & 15, (address >> 28) & 3,
                                       bool(address & 0x40000000), False, bits)
                else:
                    reloc = Relocation(index, address, False, (bits >> 28) & 15,
                                       (bits >> 25) & 3, bool(bits & 0x1000000),
                                       bool(bits & 0x8000000), bits & 0xffffff)
                require(reloc.address < 0x80000000, 'negative ordinary relocation address')
                require(reloc.type <= 4, 'relocation type not defined by Tiger generic ABI')
                # PAIR records encode operands rather than patch locations. They
                # are parsed, then explicitly rejected in cached sections below.
                if reloc.type != 1:
                    require(reloc.address <= section.size and
                            (1 << reloc.length) <= section.size - reloc.address,
                            'relocation patch extends outside section')
                if not scattered and reloc.external:
                    require(reloc.target < len(self.symbols),
                            'external relocation symbol index outside table')
                elif not scattered:
                    require(reloc.target <= len(self.sections),
                            'local relocation section index outside table')
                section.relocations.append(reloc)

    @staticmethod
    def _disjoint(ranges, message):
        for left, right in zip(ranges, ranges[1:]):
            require(left[1] <= right[0], '%s: %s / %s' % (message, left[2], right[2]))

    def pointer(self, section, address):
        require(not section.zerofill and 0 <= address <= section.size - 4,
                'pointer outside file-backed section')
        return struct.unpack_from('<I', self.data, section.offset + address)[0]

    def symbol_for_relocation(self, section, reloc):
        if reloc.external:
            return self.symbols[reloc.target]
        value = self.pointer(section, reloc.address)
        # Match findSymbolByAddress: globals first, then preceding locals.
        ordered = [s for s in self.symbols if s.external and s.defined]
        ordered += [s for s in self.symbols if not s.external and not s.debug]
        return next((s for s in ordered if s.value == value), None)


def audit_bytes(data, path='<bytes>'):
    result = {'path': str(path), 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'passed': False,
              'source': SOURCE, 'limits': LIMITS, 'errors': [], 'sections': [],
              'vtables': [], 'superclasses': []}
    def error(code, detail, **context):
        result['errors'].append(dict(code=code, detail=detail, **context))
    try:
        image = MachO(data)
    except AuditError as exc:
        error('malformed_or_unsupported_object', str(exc))
        return result
    result['load_commands'] = ['0x%x' % c for c in image.commands]
    exported = [s for s in image.symbols if s.external and not s.debug]
    definitions = [s for s in exported if s.defined]
    imports = [s for s in exported if s.kind == N_UNDF]
    result['defined_external_symbols'] = len(definitions)
    result['undefined_symbols'] = len(imports)
    # parseSymtab records one contiguous, alphabetically sorted export span;
    # findSymbolByName binary-searches it. Reject layouts that break that model.
    if not exported or not definitions:
        error('symbol_export_span', 'requires a nonempty defined export span')
    else:
        first = exported[0].index
        end = imports[0].index if imports else len(image.symbols)
        span = image.symbols[first:end]
        if any(not s.external or s.debug or not s.defined for s in span) or \
                any(not s.external or s.debug or s.kind != N_UNDF
                    for s in image.symbols[end:]):
            error('symbol_export_span', 'defined exports and imports must occupy contiguous spans')
        names = [s.name for s in span]
        if names != sorted(names) or len(names) != len(set(names)):
            error('symbol_export_order', 'defined exports must be uniquely name-sorted for bsearch')
    all_vtables = [s for s in definitions if s.name.startswith('__ZTV')]
    superclasses = [s for s in definitions
                    if s.name.startswith('__ZN') and s.name.endswith('10superClassE')]
    if not all_vtables or not superclasses:
        error('osobject_profile', 'requires C++3 vtables and OSObject superClass symbols')
    cached = {s.section for s in all_vtables + superclasses if s.kind == N_SECT}
    by_name = {s.name: s for s in definitions}
    for section in image.sections:
        summary = {'index': section.index, 'name': section.label,
                   'relocations': section.relocation_count,
                   'scattered_relocations': sum(r.scattered for r in section.relocations),
                   'pseudo_relocated': section.index in cached}
        result['sections'].append(summary)
        if section.index not in cached:
            continue
        seen = set()
        for reloc in section.relocations:
            context = {'section': section.label, 'relocation_index': reloc.index,
                       'address': '0x%x' % reloc.address}
            skipped = (reloc.scattered or reloc.type != 0 or reloc.length != 2 or
                       (not reloc.external and reloc.target == 0))
            if skipped:
                error('uninitialized_pseudo_relocation',
                      'relocateSection skips this cache record, but '
                      'prepareFileForLink unconditionally dereferences fRInfo', **context)
                continue
            if reloc.address in seen:
                error('duplicate_pseudo_relocation',
                      'same pointer is pseudo-relocated more than once', **context)
            seen.add(reloc.address)
            if reloc.address % 4 or reloc.pcrel:
                error('non_pointer_pseudo_relocation',
                      'cached relocation must address an aligned absolute 32-bit pointer', **context)
            if reloc.external and image.symbols[reloc.target].type != (N_EXT | N_UNDF):
                error('pseudo_external_target',
                      'Tiger requires external relocation target type exactly N_EXT|N_UNDF', **context)
    usable = {}
    for section in image.sections:
        if section.index in cached:
            usable[section.index] = {r.address: r for r in section.relocations
                                     if not r.scattered and r.type == 0 and r.length == 2
                                     and (r.external or r.target != 0)}
    for symbol in all_vtables:
        context = {'symbol': symbol.name}
        if symbol.kind != N_SECT:
            error('vtable_section', 'relocatable vtable must be an N_SECT symbol', **context)
            continue
        section = image.sections[symbol.section - 1]
        start = symbol.value - section.address
        if section.zerofill or start % 4 or start > section.size - 12:
            error('vtable_bounds', 'vtable preamble/terminator outside file-backed section', **context)
            continue
        relocs = usable.get(section.index, {})
        if any(image.pointer(section, start + i * 4) != 0 or
               start + i * 4 in relocs for i in range(2)):
            error('vtable_preamble', 'requires two unrelocated zero preamble words', **context)
        cursor, entries, terminated = start + 8, 0, False
        while cursor <= section.size - 4:
            reloc = relocs.get(cursor)
            value = image.pointer(section, cursor)
            if reloc is None and value == 0:
                terminated = True
                break
            if reloc is None:
                error('vtable_entry_without_record',
                      'nonzero vtable entry is not a valid pseudo-relocation record',
                      offset='0x%x' % (cursor - start), **context)
                break
            target = image.symbol_for_relocation(section, reloc)
            if target is None or not target.name:
                error('vtable_target_missing_symbol',
                      'Tiger dereferences the vtable record symbol; local addend has no exact symbol',
                      offset='0x%x' % (cursor - start), **context)
            entries += 1
            cursor += 4
        if not terminated:
            error('vtable_termination', 'no unrelocated zero terminator before section end', **context)
        result['vtables'].append({'symbol': symbol.name, 'section': section.label,
                                  'function_words': entries, 'terminated': terminated})
    for symbol in superclasses:
        context = {'symbol': symbol.name}
        token = symbol.name[len('__ZN'):-len('10superClassE')]
        expected_vtable = '__ZTV' + token
        if expected_vtable not in by_name:
            error('superclass_vtable_missing', 'recordClass cannot find matching ' + expected_vtable,
                  **context)
        if symbol.kind != N_SECT:
            error('superclass_section', 'superClass pointer must be file-backed N_SECT', **context)
            continue
        section = image.sections[symbol.section - 1]
        start = symbol.value - section.address
        if section.zerofill or start % 4 or start > section.size - 4:
            error('superclass_bounds', 'superClass pointer outside/aligned incorrectly', **context)
            continue
        reloc = usable.get(section.index, {}).get(start)
        target = image.symbol_for_relocation(section, reloc) if reloc else None
        if target is None or not target.name.endswith('10gMetaClassE'):
            error('superclass_target', 'cannot resolve superClass pointer to gMetaClass symbol', **context)
        result['superclasses'].append({'symbol': symbol.name,
                                       'target': target.name if target else None})
    result['passed'] = not result['errors']
    return result


def audit_path(path):
    return audit_bytes(Path(path).read_bytes(), str(path))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('objects', nargs='+', type=Path)
    args = parser.parse_args(argv)
    results = []
    for path in args.objects:
        try:
            results.append(audit_path(path))
        except OSError as exc:
            results.append({'path': str(path), 'passed': False,
                            'errors': [{'code': 'read_failed', 'detail': str(exc)}],
                            'limits': LIMITS})
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0 if all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
