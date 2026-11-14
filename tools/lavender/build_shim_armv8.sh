#!/bin/bash
set -e
cd /mnt/c/Users/Phoenix/Documents/ios-rn7

(cd ios-lavender/shim && ./build.sh)

mkbootimg --header_version 0 \
    --kernel ios-lavender/shim/out/Image.gz-dtb \
    --ramdisk kernel-armv8/ramdisk.bin \
    --base 0 --kernel_offset 0x8000 --ramdisk_offset 0x1000000 \
    --tags_offset 0x100 --pagesize 4096 \
    --cmdline "console=null" \
    -o kernel-armv8/shim-boot.img

python3 -c "import struct; f = open('kernel-armv8/shim-boot.img', 'r+b'); f.seek(28); f.write(struct.pack('<I', 0xf00000)); f.seek(44); f.write(struct.pack('<I', 0x2004063c))"

ls -l kernel-armv8/shim-boot.img
