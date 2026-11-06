#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) < 2:
        path = "dxb/build.sh"
    else:
        path = sys.argv[1]

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Target arm64 only for libfirehose_kernel
    old_arch = 'ARCHS="x86_64 arm64e" VALID_ARCHS="x86_64 arm64e"'
    new_arch = 'ARCHS="arm64" VALID_ARCHS="arm64"'
    if old_arch in content:
        content = content.replace(old_arch, new_arch)
        print(f"Patched ARCHS: {old_arch} -> {new_arch}")
    else:
        print("Note: old_arch not found, check if already patched")

    # 2. Append Cortex-A73 CFLAGS into libfirehose_kernel.xcconfig
    target_needle = 'sed -i \'\' \'s|$(SDKROOT)/usr/local/include|$(FAKEROOT_DIR)/usr/local/include|g\' "${SRCROOT}/xcodeconfig/libfirehose_kernel.xcconfig"'
    replacement = target_needle + '\n        sed -i \'\' \'s|-Wno-packed|-Wno-packed -mcpu=cortex-a73+crypto|g\' "${SRCROOT}/xcodeconfig/libfirehose_kernel.xcconfig"'

    if target_needle in content:
        content = content.replace(target_needle, replacement)
        print("Patched libfirehose_kernel.xcconfig sed rule to include -mcpu=cortex-a73+crypto")
    else:
        raise RuntimeError("Could not find libfirehose_kernel xcconfig sed target in build.sh!")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {path}")

if __name__ == "__main__":
    main()
