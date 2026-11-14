import os, sys, subprocess

DIR = r'C:\Users\Phoenix\Documents\ios-rn7'

def main():
    kernel_path = os.path.join(DIR, 'kernel-armv8', 'kernel.development.sweet')
    adt_path = os.path.join(DIR, 'kernel-armv8', 'adt.bin')
    payload_path = os.path.join(DIR, 'kernel-armv8', 'payload.bin')
    ramdisk_path = os.path.join(DIR, 'kernel-armv8', 'ramdisk.bin')
    boot_img = os.path.join(DIR, 'kernel-armv8', 'shim-boot.img')

    if not os.path.exists(kernel_path):
        print(f"Error: {kernel_path} does not exist!")
        sys.exit(1)

    print("=== Step 1: Scan for LSE instructions ===")
    res = subprocess.run([sys.executable, os.path.join(DIR, 'scan_lse.py'), kernel_path])
    if res.returncode != 0:
        print("Warning: scan_lse failed!")

    print("\n=== Step 2: Generate ADT ===")
    subprocess.run([sys.executable, os.path.join(DIR, 'ios-lavender', 'tools', 'mkadt.py'), adt_path, '--highmem'], check=True)

    print("\n=== Step 3: Create Payload ===")
    cmdline = "debug=0xc serial=3 cpus=1 keepsyms=1 -v -enable_kprintf_spam -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=01 ignition_force_dylib_root=rootfs ignition_live_app_graft=skip wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1 sweetkeys=0 sweettouch=0 sweetusb=0 sweetlog=1 sweetsample=launchd,SpringBoard,backboardd,watchdogd,keybagd,launchd_cache_loader sweetnull=launchd,launchd_cache_loader,keybagd,watchdogd,SpringBoard,backboardd sweetiolog=launchd,SpringBoard,backboardd,watchdogd cs_enforcement_disable=1 cs_system_enforcement=0 shared_region_trace_level=7 LogServiceLifecycle LogIPC"
    subprocess.run([
        sys.executable,
        os.path.join(DIR, 'ios-lavender', 'tools', 'mkpayload.py'),
        kernel_path,
        adt_path,
        payload_path,
        '--cmdline',
        cmdline
    ], check=True)

    print("\n=== Step 4: Create Ramdisk ===")
    subprocess.run([
        sys.executable,
        os.path.join(DIR, 'ios-lavender', 'tools', 'mkramdisk.py'),
        payload_path,
        ramdisk_path
    ], check=True)

    print("\n=== Step 5: Build Shim Boot Image via WSL ===")
    subprocess.run(['wsl', 'bash', '/mnt/c/Users/Phoenix/Documents/ios-rn7/build_shim_armv8.sh'], check=True)

    size = os.path.getsize(boot_img)
    print(f"\nSUCCESS! Generated {boot_img} ({size} bytes, {size / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    main()
