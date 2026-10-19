#!/usr/bin/env python3
"""Portable, synthetic tests for the narrow Tiger kld format preflight.

Fixtures are assembled here from documented Mach-O fields; they contain no
Apple driver, kernel, or other third-party binary bytes. These tests exercise
static parsing and the selected loader assumptions only. They do not exercise
kernel loading, C++ ABI compatibility, PS/2 hardware, or installation/recovery.
The separate original/R2/R3 artifact regression suite is not redistributed.
"""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'portable_tiger_loader_audit', ROOT / 'scripts/audit_tiger_kext_loader.py')
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def ordinary(address, target, *, external=False, length=2, kind=0, pcrel=False):
    """Encode a generic 32-bit relocation_info record for a synthetic object."""
    bits = (target | (int(pcrel) << 24) | (length << 25) |
            (int(external) << 27) | (kind << 28))
    return struct.pack('<II', address, bits)


def scattered(address, value=0x1000):
    return struct.pack('<II', 0x80000000 | (2 << 28) | address, value)


def synthetic_object(*, include_thread=False, text_scattered=False,
                     extra_const_scattered=False, vtable_external=False):
    """Build a minimal thin-i386 MH_OBJECT with one OSObject-style class.

    __const contains a two-zero-word vtable preamble, one relocated function
    pointer, its unrelocated zero terminator, and a relocated superClass pointer.
    A local method symbol resolves the function pointer exactly. The superclass
    points to an imported gMetaClass symbol. No fixture is an executable driver.
    """
    names = ['__ZN4Demo10superClassE', '__ZTV4Demo', '_demo_method',
             '__ZN8OSObject10gMetaClassE']
    if vtable_external:
        names.append('_demo_import')
    strings = bytearray(b'\0')
    string_indexes = []
    for name in names:
        string_indexes.append(len(strings))
        strings.extend(name.encode('ascii') + b'\0')

    thread = struct.pack('<4I', 5, 16, 0xffffffff, 0) if include_thread else b''
    segment_size = 56 + 2 * 68
    command_size = segment_size + 24 + len(thread)
    header_end = 28 + command_size
    text_offset = header_end
    const_offset = text_offset + 4
    text_data = b'\x90' * 4
    const_data = struct.pack('<5I', 0, 0, 0 if vtable_external else 0x1000, 0, 0)
    text_relocs = scattered(0) if text_scattered else b''
    const_relocs = b''
    if extra_const_scattered:
        const_relocs += b''.join(scattered(pos) for pos in (0, 4, 8, 12, 16))
    const_relocs += (ordinary(8, 4, external=True) if vtable_external else
                     ordinary(8, 1))
    const_relocs += ordinary(16, 3, external=True)
    text_reloc_offset = const_offset + len(const_data)
    const_reloc_offset = text_reloc_offset + len(text_relocs)
    symbol_offset = const_reloc_offset + len(const_relocs)
    string_offset = symbol_offset + len(names) * 12

    header = struct.pack('<7I', 0xfeedface, 7, 3, 1,
                         3 if include_thread else 2, command_size, 0)
    segment = struct.pack('<II16s8I', 1, segment_size, b'',
                          0x1000, 0x1014, header_end, 24, 7, 7, 2, 0)
    text_section = struct.pack('<16s16s9I', b'__text', b'__TEXT',
                               0x1000, 4, text_offset, 2, text_reloc_offset,
                               len(text_relocs) // 8, 0, 0, 0)
    const_section = struct.pack('<16s16s9I', b'__const', b'__TEXT',
                                0x2000, 20, const_offset, 2, const_reloc_offset,
                                len(const_relocs) // 8, 0, 0, 0)
    symtab = struct.pack('<6I', 2, 24, symbol_offset, len(names),
                         string_offset, len(strings))
    symbol_fields = [(0x0f, 2, 0x2010), (0x0f, 2, 0x2000),
                     (0x0f, 1, 0x1000), (1, 0, 0)]
    if vtable_external:
        symbol_fields.append((1, 0, 0))
    symbols = b''.join(struct.pack('<IBBHI', strx, typ, sec, 0, value)
                       for strx, (typ, sec, value)
                       in zip(string_indexes, symbol_fields))
    return (header + segment + text_section + const_section + symtab + thread +
            text_data + const_data + text_relocs + const_relocs + symbols + strings)


class TigerLoaderSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.data = synthetic_object()
        self.image = AUDIT.MachO(self.data)
        self.text, self.const = self.image.sections
        self.vtable = next(s for s in self.image.symbols if s.name == '__ZTV4Demo')
        self.superclass = self.image.symbols[0]

    def altered(self, offset, fmt, *values, source=None):
        data = bytearray(self.data if source is None else source)
        struct.pack_into(fmt, data, offset, *values)
        return bytes(data)

    def assert_code(self, data, code):
        result = AUDIT.audit_bytes(data)
        self.assertFalse(result['passed'], result)
        self.assertIn(code, [error['code'] for error in result['errors']], result)
        return result

    def assert_malformed(self, data, detail):
        result = self.assert_code(data, 'malformed_or_unsupported_object')
        self.assertTrue(any(detail in error['detail'] for error in result['errors']),
                        result)

    def change_const_bits(self, mutate):
        pos = self.const.relocation_offset + 4
        bits = struct.unpack_from('<I', self.data, pos)[0]
        return self.altered(pos, '<I', mutate(bits))

    def test_minimal_object_passes_and_resolves_vtable_and_superclass(self):
        result = AUDIT.audit_bytes(self.data)
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['vtables'], [{'symbol': '__ZTV4Demo',
                         'section': '__TEXT,__const', 'function_words': 1,
                         'terminated': True}])
        self.assertEqual(result['superclasses'][0]['target'],
                         '__ZN8OSObject10gMetaClassE')

    def test_external_imported_vtable_target_is_supported(self):
        result = AUDIT.audit_bytes(synthetic_object(vtable_external=True))
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['undefined_symbols'], 2)

    def test_legacy_thread_command_framing_is_supported(self):
        result = AUDIT.audit_bytes(synthetic_object(include_thread=True))
        self.assertTrue(result['passed'], result)
        self.assertIn('0x5', result['load_commands'])

    def test_scattered_text_relocation_does_not_mark_uncached_text_unsafe(self):
        result = AUDIT.audit_bytes(synthetic_object(text_scattered=True))
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['sections'][0]['scattered_relocations'], 1)
        self.assertFalse(result['sections'][0]['pseudo_relocated'])

    def test_five_scattered_cached_records_reproduce_null_cache_signature(self):
        result = self.assert_code(synthetic_object(extra_const_scattered=True),
                                  'uninitialized_pseudo_relocation')
        self.assertEqual(len(result['errors']), 5, result)
        self.assertEqual({e['address'] for e in result['errors']},
                         {'0x0', '0x4', '0x8', '0xc', '0x10'})

    def test_cached_nonlong_relocation_leaves_uninitialized_record(self):
        self.assert_code(self.change_const_bits(
            lambda bits: (bits & ~(3 << 25)) | (1 << 25)),
            'uninitialized_pseudo_relocation')

    def test_cached_nonvanilla_relocation_leaves_uninitialized_record(self):
        self.assert_code(self.change_const_bits(
            lambda bits: (bits & 0x0fffffff) | (2 << 28)),
            'uninitialized_pseudo_relocation')

    def test_cached_local_absolute_relocation_leaves_uninitialized_record(self):
        self.assert_code(self.change_const_bits(lambda bits: bits & ~0x08ffffff),
                         'uninitialized_pseudo_relocation')

    def test_pc_relative_cached_pointer_is_rejected(self):
        self.assert_code(self.change_const_bits(lambda bits: bits | (1 << 24)),
                         'non_pointer_pseudo_relocation')

    def test_unaligned_cached_pointer_is_rejected(self):
        self.assert_code(self.altered(self.const.relocation_offset, '<I', 9),
                         'non_pointer_pseudo_relocation')

    def test_duplicate_cached_patch_address_is_rejected(self):
        self.assert_code(self.altered(self.const.relocation_offset + 8, '<I', 8),
                         'duplicate_pseudo_relocation')

    def test_external_cached_target_must_be_exact_undefined_type(self):
        self.assert_code(self.change_const_bits(
            lambda bits: (bits & 0xff000000) | (1 << 27) | self.vtable.index),
            'pseudo_external_target')

    def test_local_vtable_target_requires_exact_symbol_address(self):
        self.assert_code(self.altered(self.const.offset + 8, '<I', 0x1001),
                         'vtable_target_missing_symbol')

    def test_vtable_requires_unrelocated_zero_preamble(self):
        self.assert_code(self.altered(self.const.offset, '<I', 1),
                         'vtable_preamble')

    def test_nonzero_unrelocated_vtable_word_is_rejected(self):
        self.assert_code(self.altered(self.const.offset + 12, '<I', 1),
                         'vtable_entry_without_record')

    def test_vtable_without_terminator_is_rejected(self):
        data = self.altered(self.vtable.file_offset + 8, '<I', 0x2008)
        data = self.altered(self.const.offset + 8, '<3I', 0, 0, 1, source=data)
        self.assert_code(data, 'vtable_termination')

    def test_superclass_pointer_must_resolve_to_metaclass_symbol(self):
        data = self.altered(self.const.relocation_offset + 12, '<I',
                            (2 << 25) | 1)
        data = self.altered(self.const.offset + 16, '<I', 0x1000, source=data)
        self.assert_code(data, 'superclass_target')

    def test_export_binary_search_span_must_be_name_sorted(self):
        data = bytearray(self.data)
        first, second = self.image.symbols[:2]
        left = data[first.file_offset:first.file_offset + 12]
        right = data[second.file_offset:second.file_offset + 12]
        data[first.file_offset:first.file_offset + 12] = right
        data[second.file_offset:second.file_offset + 12] = left
        self.assert_code(bytes(data), 'symbol_export_order')

    def test_export_span_cannot_contain_local_symbol(self):
        self.assert_code(self.altered(self.image.symbols[2].file_offset + 4,
                                      '<B', 0x0e), 'symbol_export_span')

    def test_truncated_header_is_rejected(self):
        self.assert_malformed(self.data[:20], 'truncated Mach-O header')

    def test_fat_or_wrong_endian_magic_is_rejected(self):
        self.assert_malformed(self.altered(0, '<I', 0xcafebabe), 'requires thin')

    def test_non_i386_object_is_rejected(self):
        self.assert_malformed(self.altered(4, '<I', 0x01000007), 'requires i386')

    def test_incremental_link_flag_is_rejected(self):
        self.assert_malformed(self.altered(24, '<I', 2), 'Mach-O flags')

    def test_zero_command_size_cannot_stall_parser(self):
        self.assert_malformed(self.altered(32, '<I', 0), 'load-command size')

    def test_truncated_command_region_is_rejected(self):
        self.assert_malformed(self.data[:self.image.header_end - 1],
                              'load-command area')

    def test_command_count_and_size_must_match(self):
        self.assert_malformed(self.altered(16, '<I', 1),
                              'load-command count/size mismatch')

    def test_modern_load_command_is_rejected(self):
        self.assert_malformed(self.altered(28, '<I', 0x32), 'load command 0x32')

    def test_segment_section_count_must_match(self):
        self.assert_malformed(self.altered(28 + 48, '<I', 99),
                              'section-count mismatch')

    def test_legacy_thread_count_cannot_exceed_command(self):
        data = synthetic_object(include_thread=True)
        offset = 28 + (56 + 2 * 68) + 24
        self.assert_malformed(self.altered(offset + 12, '<I', 0xffffffff,
                                           source=data), 'thread-state count')

    def test_symbol_table_must_fit_file(self):
        self.assert_malformed(self.altered(self.image.symtab_command_offset + 8,
                                           '<I', len(self.data) - 1), 'symbol table')

    def test_symbol_string_index_must_fit_string_table(self):
        self.assert_malformed(self.altered(self.vtable.file_offset, '<I',
                                           self.image.strsize), 'symbol string index')

    def test_symbol_name_requires_nul_terminator(self):
        data = self.altered(self.vtable.file_offset, '<I', self.image.strsize - 1)
        data = self.altered(self.image.stroff + self.image.strsize - 1, '<B',
                            ord('x'), source=data)
        self.assert_malformed(data, 'unterminated symbol name')

    def test_defined_symbol_section_index_must_exist(self):
        self.assert_malformed(self.altered(self.vtable.file_offset + 5, '<B', 255),
                              'invalid n_sect')

    def test_relocation_patch_must_fit_wholly_in_section(self):
        self.assert_malformed(self.altered(self.const.relocation_offset, '<I', 18),
                              'patch extends outside section')

    def test_external_relocation_symbol_index_must_exist(self):
        self.assert_malformed(self.change_const_bits(
            lambda bits: (bits & 0xff000000) | (1 << 27) | len(self.image.symbols)),
            'external relocation symbol index')

    def test_post_tiger_relocation_type_is_rejected(self):
        self.assert_malformed(self.change_const_bits(
            lambda bits: (bits & 0x0fffffff) | (5 << 28)),
            'relocation type not defined by Tiger')

    def test_section_file_data_cannot_overlap_commands(self):
        self.assert_malformed(self.altered(self.const.header_offset + 40,
                                           '<I', 28),
                              'section data outside segment file range')

    def test_relocation_table_cannot_overlap_section_data(self):
        self.assert_malformed(self.altered(self.const.header_offset + 48,
                                           '<I', self.const.offset),
                              'overlapping file regions')

    def test_section_vm_ranges_cannot_overlap(self):
        self.assert_malformed(self.altered(self.const.header_offset + 32,
                                           '<I', 0x1000),
                              'overlapping section VM ranges')

    def test_arbitrary_short_inputs_fail_closed(self):
        for length in range(100):
            with self.subTest(length=length):
                result = AUDIT.audit_bytes(bytes([length]) * length)
                self.assertFalse(result['passed'])
                self.assertTrue(result['errors'])

    def test_report_explicitly_limits_static_preflight_assurance(self):
        result = AUDIT.audit_bytes(self.data)
        self.assertTrue(result['passed'], result)
        self.assertIn('does not prove', ' '.join(result['limits']))
        self.assertIn('No execution', ' '.join(result['limits']))


if __name__ == '__main__':
    unittest.main()
