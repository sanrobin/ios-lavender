#!/usr/bin/env python3
import os

kernel_path = r"C:\Users\Phoenix\Documents\ios-rn7\kernel-armv8\kernel.development.sweet"
hook_bin_path = r"C:\Users\Phoenix\.gemini\antigravity-cli\brain\975fb478-007f-42b4-8e6e-effbe6176699\scratch\hook_pid1.bin"

with open(hook_bin_path, "rb") as f:
    hook_data = f.read()

assert len(hook_data) == 440, f"Expected 440 bytes, got {len(hook_data)}"

with open(kernel_path, "r+b") as f:
    # 1. Write hook binary to cave at file offset 0x431c60 (VA 0xfffffe0007435c60)
    f.seek(0x431c60)
    f.write(hook_data)
    print(f"[+] Injected {len(hook_data)} bytes of universal open/fcntl hook code into cave at 0x431c60")

    # 2. Patch _open1 epilogue at file offset 0x4d3da0 (VA 0xfffffe00074d7da0)
    f.seek(0x4d3da0)
    # b hook_open1 (-663872 bytes -> 0x17fd77b0)
    f.write(bytes.fromhex("b077fd17"))
    print(f"[+] Patched _open1 epilogue at 0x4d3da0 with 'b hook_open1'")

    # 3. Patch _sys_fcntl_nocancel epilogue at file offset 0x790434 (VA 0xfffffe0007794434)
    f.seek(0x790434)
    # b hook_fcntl (-3532564 bytes -> 0x17f2873b)
    f.write(bytes.fromhex("3b86f217"))
    print(f"[+] Patched _sys_fcntl_nocancel epilogue at 0x790434 with 'b hook_fcntl'")

    # 4. Eliminate nested panic: make _pmap_map_cpu_windows_copy_internal return immediately
    f.seek(0x41b640)
    f.write(bytes.fromhex("c0035fd6")) # ret
    print(f"[+] Patched _pmap_map_cpu_windows_copy_internal at 0x41b640 with 'ret'")

    # 5. Eliminate 60-line paniclog dump: make _SavePanicInfo return immediately so screen never scrolls
    f.seek(0x43dc70)
    old_save = f.read(4)
    assert old_save in (bytes.fromhex("fc6fbaa9"), bytes.fromhex("c0035fd6")), f"Unexpected SavePanicInfo bytes: {old_save.hex()}"
    f.seek(0x43dc70)
    f.write(bytes.fromhex("c0035fd6")) # ret
    print(f"[+] Patched _SavePanicInfo at 0x43dc70 with 'ret' to prevent 60-line paniclog scroll")

print("[*] Successfully applied Milestone 33.2 patches!")
