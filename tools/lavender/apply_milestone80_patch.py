#!/usr/bin/env python3
"""
apply_milestone80_patch.py

Milestone 80:
1. Preserves Cave 2 hook (hook_m79.bin, 3,072 bytes) and branches:
   - _pmap_enter at 0x418010 -> Cave 2 entry (0xfffffe0007b1b3b0)
   - _exception_triage at 0x2be490 -> hook_exception_triage (0xfffffe0007b1b3b0 + 0x7cc)
2. Preserves sc25_stubs_m70.bin (3,096 bytes) at 0xb20810 (VA 0xfffffe0007b24810) and expected_stubs_va at 0xb20800.
3. Applies Milestone 80 static kernel patches:
   A. Neutralize zone_require_ro panics:
      - 0x334bbc (VA 0xfffffe0007338bbc): b #0xfffffe0007338ba0 (0x17fffff9)
      - 0x334c64 (VA 0xfffffe0007338c64): b #0xfffffe0007338c58 (0x17fffffd)
      - 0xa8fc8c (VA 0xfffffe0007a93c8c): ret (0xd65f03c0)
   B. Neutralize vm_fault protection check (Data/Stack execution not permitted):
      - 0x3a087c (VA 0xfffffe00073a487c): nop (0xd503201f)
      - 0x3a0884 (VA 0xfffffe00073a4884): b #0xfffffe00073a4898 (0x14000005)
"""

import os
import struct
import subprocess

kernel_path = r"C:\Users\Phoenix\Documents\ios-rn7\kernel-armv8\kernel.development.sweet"
scratch_dir = r"C:\Users\Phoenix\.gemini\antigravity-cli\brain\975fb478-007f-42b4-8e6e-effbe6176699\scratch"
hook_bin_path = os.path.join(scratch_dir, "hook_m79.bin")
hook_o_path = "/mnt/c/Users/Phoenix/.gemini/antigravity-cli/brain/975fb478-007f-42b4-8e6e-effbe6176699/scratch/hook_m79.o"
stubs_bin_path = os.path.join(scratch_dir, "sc25_stubs_m70.bin")

# 1. Read hook binary
with open(hook_bin_path, "rb") as f:
    hook_data = f.read()

assert len(hook_data) == 3072, f"Expected 3072 bytes, got {len(hook_data)}"
assert len(hook_data) <= 3152, f"Hook size {len(hook_data)} exceeds Cave 2 capacity (3152 bytes)"

# 2. Read stubs binary
with open(stubs_bin_path, "rb") as f:
    stubs_data = f.read()

assert len(stubs_data) == 3096, f"Expected 3096 bytes, got {len(stubs_data)}"

# 3. Determine triage_offset from ELF symbol table
res = subprocess.run(["wsl", "bash", "-c", f"llvm-nm {hook_o_path} | grep hook_exception_triage"], capture_output=True, text=True)
triage_offset = int(res.stdout.strip().split()[0], 16)
print(f"[*] hook_exception_triage offset in Cave 2: {hex(triage_offset)}")
assert triage_offset == 0x7cc, f"Unexpected triage offset: {hex(triage_offset)}"

# 4. Calculate branches
pmap_enter_src = 0xfffffe000741c010
pmap_enter_dst = 0xfffffe0007b1b3b0
pmap_diff = pmap_enter_dst - pmap_enter_src
pmap_insn = 0x14000000 | ((pmap_diff // 4) & 0x03ffffff)
pmap_bytes = struct.pack("<I", pmap_insn)

triage_src = 0xfffffe00072c2490
triage_dst = 0xfffffe0007b1b3b0 + triage_offset
triage_diff = triage_dst - triage_src
triage_insn = 0x14000000 | ((triage_diff // 4) & 0x03ffffff)
triage_bytes = struct.pack("<I", triage_insn)

print(f"[*] _pmap_enter branch: {pmap_insn:#010x} ({pmap_bytes.hex()})")
print(f"[*] _exception_triage branch: {triage_insn:#010x} ({triage_bytes.hex()})")

# Milestone 80 static kernel patches
m80_patches = [
    # (file_offset, VA, patch_insn, description)
    (0x334bbc, 0xfffffe0007338bbc, 0x17fffff9, "Bypass zone_require_ro caller 1 -> clean return"),
    (0x334c64, 0xfffffe0007338c64, 0x17fffffd, "Bypass zone_require_ro caller 2 -> clean return"),
    (0xa8fc8c, 0xfffffe0007a93c8c, 0xd65f03c0, "zone_require_ro entry -> ret"),
    (0x3a087c, 0xfffffe00073a487c, 0xd503201f, "vm_fault protection check 1 -> nop"),
    (0x3a0884, 0xfffffe00073a4884, 0x14000005, "vm_fault protection check 2 -> b #0xfffffe00073a4898 (always grant exec)"),
]

# 5. Apply patches to kernel
with open(kernel_path, "r+b") as f:
    # A. Write hook_m79.bin to Cave 2 at 0xb173b0 (VA 0xfffffe0007b1b3b0)
    f.seek(0xb173b0)
    f.write(hook_data)
    rem = 3152 - len(hook_data)
    f.write(b"\x00" * rem)
    print(f"[+] Injected {len(hook_data)} bytes of hook into Cave 2 at 0xb173b0, zeroed {rem} trailing bytes")

    # B. Patch _pmap_enter at 0x418010 (VA 0xfffffe000741c010)
    f.seek(0x418010)
    f.write(pmap_bytes)
    print(f"[+] Patched _pmap_enter branch at 0x418010 -> Cave 2 entry ({pmap_insn:#010x})")

    # C. Patch _exception_triage at 0x2be490 (VA 0xfffffe00072c2490)
    f.seek(0x2be490)
    f.write(triage_bytes)
    print(f"[+] Patched _exception_triage branch at 0x2be490 -> hook_exception_triage ({triage_insn:#010x})")

    # D. Clear expected_stubs_va at 0xb20800 (VA 0xfffffe0007b24800, 8 bytes)
    f.seek(0xb20800)
    f.write(b"\x00" * 8)
    print("[+] Initialized expected_stubs_va at 0xb20800 (VA 0xfffffe0007b24800) to 0")

    # E. Inject sc25_stubs_m70.bin into __KLDDATA at 0xb20810 (VA 0xfffffe0007b24810, 3096 bytes)
    f.seek(0xb20810)
    f.write(stubs_data)
    print(f"[+] Injected {len(stubs_data)} bytes of sc25_stubs_m70 into __KLDDATA at 0xb20810")

    # F. Apply Milestone 80 static kernel patches
    for off, va, insn, desc in m80_patches:
        f.seek(off)
        f.write(struct.pack("<I", insn))
        print(f"[+] Patched 0x{off:x} (VA 0x{va:x}) -> {insn:#010x}: {desc}")

print("[+] Milestone 80 patches applied successfully to kernel.development.sweet!")
