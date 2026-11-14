import struct, sys

def scan(path):
    with open(path, 'rb') as f:
        data = f.read()

    ncmds, sizeofcmds = struct.unpack_from('<II', data, 16)
    off = 32
    sections = []
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', data, off)
        if cmd == 0x19: # LC_SEGMENT_64
            nsects, = struct.unpack_from('<I', data, off + 64)
            s_off = off + 72
            for _ in range(nsects):
                sectname = data[s_off:s_off+16].rstrip(b'\0').decode('latin1')
                s_segname = data[s_off+16:s_off+32].rstrip(b'\0').decode('latin1')
                s_addr, s_size, s_offset = struct.unpack_from('<QQI', data, s_off + 32)
                sections.append((s_segname, sectname, s_addr, s_size, s_offset))
                s_off += 80
        off += cmdsize

    text_segs = [s for s in sections if s[0] == '__TEXT_EXEC' and s[1] == '__text']
    if not text_segs:
        # Try finding __TEXT __text
        text_segs = [s for s in sections if 'text' in s[1].lower()]
    
    total_lse = 0
    for s_segname, sectname, text_va, text_size, text_foff in text_segs:
        print(f"Scanning section {s_segname} {sectname} (VA 0x{text_va:x}, size {text_size} bytes)...")
        all_lse = []
        for i in range(0, text_size, 4):
            word, = struct.unpack_from('<I', data, text_foff + i)
            # LSE atomics: LDADD, LDCLR, LDSET, SWP, etc.
            # CAS, CASP
            if (word & 0x3f200c00) == 0x38200000 or (word & 0x3fe00000) == 0x08a00000:
                all_lse.append((text_va + i, text_foff + i, word))
        if all_lse:
            print(f"  Found {len(all_lse)} LSE instructions in {sectname}:")
            for va, foff, word in all_lse:
                print(f"    VA 0x{va:x} (offset 0x{foff:x}): 0x{word:08x}")
            total_lse += len(all_lse)
        else:
            print(f"  Clean! 0 LSE instructions in {sectname}.")

    print(f"\nTOTAL LSE INSTRUCTIONS: {total_lse}")
    return total_lse

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Phoenix\Documents\ios-rn7\kernel-48bit-l0\kernel.development.sweet'
    scan(target)
