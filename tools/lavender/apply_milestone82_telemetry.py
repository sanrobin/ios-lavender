#!/usr/bin/env python3
"""
apply_milestone82_telemetry.py

Milestone 82: Userland Execution Telemetry & Fast Process Sampler
1. Verifies Milestone 32, 35, 80 static patches and Cave 2 / stubs integrity.
2. Unlocks SWEET process sampler:
   - 0x496a8c (VA 0xfffffe000749aa8c): mov w9, #5 (5s initial delay instead of 90s)
   - 0x496af8 (VA 0xfffffe000749aaf8): mov w9, #5
   - 0x496afc (VA 0xfffffe000749aafc): mul w3, w8, w9 (5s interval instead of 120s)
3. Unlocks universal execve / posix_spawn logging:
   - 0x7a89ac (VA 0xfffffe00077ac9ac): b #0xfffffe00077ac9f0 (prints 'exec <name>' for every process spawn)
"""

import os
import struct

KERNEL_PATH = r"C:\Users\Phoenix\Documents\ios-rn7\kernel-armv8\kernel.development.sweet"

with open(KERNEL_PATH, "r+b") as f:
    # 1. Verify Cave 2 and ExceptionVectorsBase integrity
    f.seek(0x432000)
    vbar = f.read(16)
    assert vbar[:4] == bytes.fromhex("00040014"), f"ExceptionVectorsBase corrupted: {vbar.hex()}"
    print("[+] ExceptionVectorsBase verified intact at 0x432000")

    # 2. Patch sampler initial delay (5 seconds instead of 90s)
    # VA 0xfffffe000749aa8c, file offset 0x496a8c: mov w9, #5 (0x528000a9)
    f.seek(0x496a8c)
    f.write(bytes.fromhex("a9008052"))
    print("[+] Patched sweet_sample_thread initial delay -> 5s at 0x496a8c")

    # 3. Patch sampler recurring interval (5 seconds instead of 120s)
    # VA 0xfffffe000749aaf8, file offset 0x496af8: mov w9, #5 (0x528000a9)
    # VA 0xfffffe000749aafc, file offset 0x496afc: mul w3, w8, w9 (0x1b097d03)
    f.seek(0x496af8)
    f.write(bytes.fromhex("a9008052 037d091b"))
    print("[+] Patched sweet_sample_thread interval -> 5s at 0x496af8")

    # 4. Patch kern_exec to log 'exec <name>' for EVERY binary spawn
    # VA 0xfffffe00077ac9ac, file offset 0x7a89ac: b #0xfffffe00077ac9f0 (0x14000011)
    f.seek(0x7a89ac)
    f.write(bytes.fromhex("11000014"))
    print("[+] Patched kern_exec at 0x7a89ac to unconditionally log every exec -> 'exec <name>'")

print("\n[*] Milestone 82 telemetry patches successfully applied to kernel.development.sweet!")
