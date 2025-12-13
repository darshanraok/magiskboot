#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import multiprocessing
from pathlib import Path

cpu_count = multiprocessing.cpu_count()
os_name = os.name

# Android ABIs (NDK)
android_abis = {
    "armeabi-v7a": "thumbv7neon-linux-androideabi",
    "arm64-v8a": "aarch64-linux-android",
    "x86": "i686-linux-android",
    "x86_64": "x86_64-linux-android",
}

# Host Rust targets
host_targets = {
    "linux32": "i686-unknown-linux-gnu",
    "linux64": "x86_64-unknown-linux-gnu",
    "win32": "i686-pc-windows-gnu",
    "win64": "x86_64-pc-windows-gnu",
}

def execv(cmds, env=None):
    print("Running:", " ".join(cmds))
    subprocess.run(cmds, check=True, env=env)

def run_ndk_build(app_abis):
    os.chdir("native")
    cmds = ["ndk-build", f"APP_ABI={' '.join(app_abis)}", f"-j{cpu_count}"]
    subprocess.run(cmds, check=True)
    os.chdir("..")

def build_cpp_src():
    # Only build magiskboot for Android ABIs
    print("* Building Android magiskboot (NDK)...")
    run_ndk_build(android_abis.keys())

def run_cargo(target):
    env = os.environ.copy()
    env["CARGO_BUILD_RUSTFLAGS"] = f"-Z threads={min(8, cpu_count)}"
    return subprocess.run(["cargo", "build", "--release", "--target", target], env=env, check=True)

def build_rust_src():
    # Only build magiskboot for host platforms
    print("* Building host magiskboot (Rust)...")
    os.chdir("native/src")
    for tgt in host_targets.values():
        run_cargo(tgt)
        # move binary to native/out/<arch>
        bin_name = "magiskboot"
        if "windows" in tgt:
            bin_name += ".exe"
        target_dir = Path("..","..","out", tgt.split('-')[0])
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path("target") / tgt / "release" / bin_name, target_dir / bin_name)
    os.chdir("../..")

if __name__ == "__main__":
    build_cpp_src()
    build_rust_src()
    print("✅ magiskboot build finished")
