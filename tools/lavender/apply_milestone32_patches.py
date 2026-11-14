import os, sys, shutil, struct

KERNEL_PATH = r'C:\Users\Phoenix\Documents\ios-rn7\kernel-armv8\kernel.development.sweet'
BACKUP_PATH = r'C:\Users\Phoenix\Documents\ios-rn7\kernel-armv8\kernel.development.sweet.pre_m32'

BASE_VM = 0xfffffe000727c000
BASE_FOFF = 0x278000

PATCHES = [
    # (Name, VM address, Expected Original, New Value)
    ("console_ring_try_empty un-mute", 0xfffffe0007405320, 0x35000508, 0xd503201f),
    ("cnputs un-mute",                 0xfffffe0007405700, 0x350004c8, 0xd503201f),
    ("console_write un-mute",          0xfffffe0007913ea4, 0x54000100, 0xd503201f),
    ("mac_check_signature ret 0 (1)",  0xfffffe0007a63e60, 0xd10303ff, 0x52800000), # mov w0, #0
    ("mac_check_signature ret 0 (2)",  0xfffffe0007a63e64, 0xa9066ffc, 0xd65f03c0), # ret
]

def main():
    if not os.path.exists(BACKUP_PATH):
        print(f"Creating backup: {BACKUP_PATH}")
        shutil.copyfile(KERNEL_PATH, BACKUP_PATH)
    else:
        print(f"Backup already exists at: {BACKUP_PATH}")

    with open(KERNEL_PATH, 'rb') as f:
        data = bytearray(f.read())

    print(f"\nApplying {len(PATCHES)} patches to {KERNEL_PATH}...")
    for name, vm_addr, expected, new_val in PATCHES:
        foff = BASE_FOFF + (vm_addr - BASE_VM)
        current = struct.unpack('<I', data[foff:foff+4])[0]
        if current == new_val:
            print(f"  [ALREADY PATCHED] {name} at {hex(vm_addr)} (foff {hex(foff)})")
        elif current == expected:
            data[foff:foff+4] = struct.pack('<I', new_val)
            print(f"  [PATCHED] {name} at {hex(vm_addr)} (foff {hex(foff)}): {hex(expected)} -> {hex(new_val)}")
        else:
            print(f"  [ERROR] {name} at {hex(vm_addr)} (foff {hex(foff)}): current={hex(current)} != expected={hex(expected)}")
            sys.exit(1)

    with open(KERNEL_PATH, 'wb') as f:
        f.write(data)

    print("\nVerifying applied patches...")
    with open(KERNEL_PATH, 'rb') as f:
        verify_data = f.read()

    for name, vm_addr, expected, new_val in PATCHES:
        foff = BASE_FOFF + (vm_addr - BASE_VM)
        val = struct.unpack('<I', verify_data[foff:foff+4])[0]
        assert val == new_val, f"Verification failed for {name}: {hex(val)} != {hex(new_val)}"
        print(f"  [VERIFIED] {name}: {hex(val)}")

    print("\nSUCCESS: All Milestone 32 patches applied and verified!")

if __name__ == '__main__':
    main()
