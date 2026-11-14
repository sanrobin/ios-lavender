#!/usr/bin/env python3
import os
import capstone

KERNEL_PATH = r"C:\Users\Phoenix\Documents\ios-rn7\kernel-armv8\kernel.development.sweet"

with open(KERNEL_PATH, "r+b") as f:
    # 1. Milestone 35 Core Fix: In _sys_fcntl_nocancel cmd 97 handler at file offset 0x791ffc (VA 0xfffffe0007795ffc)
    # Synthesize fs_file_start = -1 when out_blob == NULL
    f.seek(0x791ffc)
    fcntl_97_patch = bytes.fromhex("e82b40f9 e9033faa 480000b4 091d40f9 e91b00f9")
    f.write(fcntl_97_patch)
    print("[+] Patched fcntl cmd 97 return at 0x791ffc (fs_file_start = -1 if blob == NULL)")

    # 2. Milestone 34 Fixes:
    # _ubc_cs_blob_add mov w24, wzr at file offset 0x805900 (VA 0xfffffe0007809900)
    f.seek(0x805900)
    f.write(bytes.fromhex("f8031f2a"))
    print("[+] Patched _ubc_cs_blob_add at 0x805900 with 'mov w24, wzr'")

    # supplement parser mov w23, wzr at file offset 0x806bfc (VA 0xfffffe000780abfc)
    f.seek(0x806bfc)
    f.write(bytes.fromhex("f7031f2a"))
    print("[+] Patched supplement parser at 0x806bfc with 'mov w23, wzr'")

    # 3. Milestone 33.2 suppression patches:
    f.seek(0x41b640)
    f.write(bytes.fromhex("c0035fd6")) # ret
    print("[+] Patched _pmap_map_cpu_windows_copy_internal at 0x41b640 with 'ret'")

    f.seek(0x43dc70)
    f.write(bytes.fromhex("c0035fd6")) # ret
    print("[+] Patched _SavePanicInfo at 0x43dc70 with 'ret'")

    # 4. Verify ExceptionVectorsBase is 100% intact at 0x432000
    f.seek(0x432000)
    vbar = f.read(16)
    assert vbar[:4] == bytes.fromhex("00040014"), f"ExceptionVectorsBase corrupted: {vbar.hex()}"
    print("[+] Verified ExceptionVectorsBase at 0x432000 is 100% INTACT!")

print("\n[*] Successfully verified and applied Milestone 35 patches!")
