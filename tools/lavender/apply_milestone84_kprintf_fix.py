#!/usr/bin/env python3
"""
apply_milestone84_kprintf_fix.py

Milestone 84: Accurate kprintf Routing for On-Glass Telemetry & Fast Process Sampler
Fixes the kprintf destination address:
- Real kprintf is located at VA 0xfffffe0007a55c60 (file offset 0xa51c60)
- Expects arguments via Darwin ARM64 variadic stack conventions (str xN, [sp])
"""

import os
import struct
import capstone

KERNEL_PATH = r"C:\Users\Phoenix\Documents\ios-rn7\kernel-armv8\kernel.development.sweet"

with open(KERNEL_PATH, "r+b") as f:
    # 1. Verify Cave 2 and ExceptionVectorsBase integrity
    f.seek(0x432000)
    vbar = f.read(16)
    assert vbar[:4] == bytes.fromhex("00040014"), f"ExceptionVectorsBase corrupted: {vbar.hex()}"
    print("[+] ExceptionVectorsBase verified intact at 0x432000")

    # 2. Sampler: Bypass initial delay -> Sample 0 immediately
    # VA 0xfffffe000749aa80, file offset 0x496a80: b #0xfffffe000749aab4 (0x1400000d)
    f.seek(0x496a80)
    f.write(bytes.fromhex("0d000014"))
    print("[+] Patched sweet_sample_thread: initial delay bypassed -> immediate Sample 0 at 0x496a80")

    # 3. Sampler: Route 'SMP --- sample %d' to REAL kprintf (0xfffffe0007a55c60)
    # VA 0xfffffe000749aad0, file offset 0x496ad0: str x24, [sp] (0xf90003f8 -> f80300f9)
    # VA 0xfffffe000749aad8, file offset 0x496ad8: bl #0xfffffe0007a55c60 (0x9416ec62 -> 62ec1694)
    f.seek(0x496ad0)
    f.write(bytes.fromhex("f80300f9"))
    f.seek(0x496ad8)
    f.write(bytes.fromhex("62ec1694"))
    print("[+] Patched sweet_sample_thread: sample header routed to real kprintf at 0x496ad8")

    # 4. Sampler: Recurring interval -> 2s
    # VA 0xfffffe000749aaf8, file offset 0x496af8: mov w9, #2 (0x52800049 -> 49008052)
    f.seek(0x496af8)
    f.write(bytes.fromhex("49008052"))
    print("[+] Patched sweet_sample_thread: interval -> 2s at 0x496af8")

    # 5. Sampler: Sample EVERY process unconditionally
    # VA 0xfffffe000749ab90, file offset 0x496b90: b #0xfffffe000749ac14 (0x14000021 -> 21000014)
    f.seek(0x496b90)
    f.write(bytes.fromhex("21000014"))
    print("[+] Patched sweet_sample_proc: universal process sampling at 0x496b90")

    # 6. Sampler Task Header: Route 'SMP %s[%d] slide 0x%llx mh 0x%llx\n' to REAL kprintf
    # VA 0xfffffe00072c2d8c, file offset 0x2bed8c: bl #0xfffffe0007a55c60 (0x941e4bb5 -> b54b1e94)
    f.seek(0x2bed8c)
    f.write(bytes.fromhex("b54b1e94"))
    print("[+] Patched sweet_sample_task: task header routed to real kprintf at 0x2bed8c")

    # 7. Sampler Thread Line: Route thread backtrace line to REAL kprintf
    # VA 0xfffffe00072c2dc8, file offset 0x2bedc8: str x19, [sp] (0xf90003f3 -> f30300f9)
    # VA 0xfffffe00072c2dd4, file offset 0x2bedd4: bl #0xfffffe0007a55c60 (0x941e4ba3 -> a34b1e94)
    f.seek(0x2bedc8)
    f.write(bytes.fromhex("f30300f9"))
    f.seek(0x2bedd4)
    f.write(bytes.fromhex("a34b1e94"))
    print("[+] Patched sweet_sample_task: thread backtraces routed to real kprintf at 0x2bedd4")

    # 8. Exec logger: Route 'exec %s\n' to REAL kprintf
    # VA 0xfffffe00077ac9ac, file offset 0x7a89ac: b #0xfffffe00077ac9f0 (0x14000011 -> 11000014)
    # VA 0xfffffe00077acbc8, file offset 0x7a8bc8: str x8, [sp] (0xf90003e8 -> e80300f9)
    # VA 0xfffffe00077acbcc, file offset 0x7a8bcc: bl #0xfffffe0007a55c60 (0x940aa425 -> 25a40a94)
    f.seek(0x7a89ac)
    f.write(bytes.fromhex("11000014"))
    f.seek(0x7a8bc8)
    f.write(bytes.fromhex("e80300f9"))
    f.seek(0x7a8bcc)
    f.write(bytes.fromhex("25a40a94"))
    print("[+] Patched kern_exec: universal execve/spawn routed to real kprintf at 0x7a8bcc")

# Disassemble all patches to verify
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
with open(KERNEL_PATH, "rb") as f:
    checks = [
        (0x496a80, 0xfffffe000749aa80, 4),
        (0x496ad0, 0xfffffe000749aad0, 12),
        (0x496af8, 0xfffffe000749aaf8, 4),
        (0x496b90, 0xfffffe000749ab90, 4),
        (0x2bed8c, 0xfffffe00072c2d8c, 4),
        (0x2bedc8, 0xfffffe00072c2dc8, 16),
        (0x7a89ac, 0xfffffe00077ac9ac, 4),
        (0x7a8bc8, 0xfffffe00077acbc8, 8),
    ]
    print("\n--- Disassembly Verification ---")
    for off, va, size in checks:
        f.seek(off)
        data = f.read(size)
        for ins in md.disasm(data, va):
            print(f"  0x{ins.address:x}: {ins.mnemonic} {ins.op_str}")

print("\n[*] Milestone 84 accurate kprintf telemetry successfully applied!")
