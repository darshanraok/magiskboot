#!/usr/bin/env python3
import os
import platform
import multiprocessing
import subprocess
from pathlib import Path

cpu_count = multiprocessing.cpu_count()
os_name = platform.system().lower()
is_windows = os_name == "windows"
EXE_EXT = ".exe" if is_windows else ""

# Build architectures
build_abis = {
    "armeabi-v7a": "thumbv7neon-linux-androideabi",
    "arm64-v8a": "aarch64-linux-android",
    "x86": "i686-linux-android",
    "x86_64": "x86_64-linux-android",
    "win32": "i686-pc-windows-gnu",
    "win64": "x86_64-pc-windows-gnu",
    "linux32": "i686-unknown-linux-gnu",
    "linux64": "x86_64-unknown-linux-gnu",
}

def execv(cmds: list):
    return subprocess.run(cmds, check=True)

def collect_ndk_build():
    for arch in build_abis.keys():
        arch_dir = Path("native/libs", arch)
        out_dir = Path("native/out", arch)
        out_dir.mkdir(parents=True, exist_ok=True)
        for source in arch_dir.iterdir():
            target = out_dir / source.name
            source.rename(target)

def run_ndk_build(cmds: list):
    os.chdir("native")
    cmds.append("NDK_PROJECT_PATH=.")
    cmds.append("NDK_APPLICATION_MK=src/Application.mk")
    cmds.append(f"APP_ABI={' '.join(build_abis.keys())}")
    cmds.append(f"-j{cpu_count}")
    subprocess.run([ndk_build := "ndk-build"] + cmds, check=True)
    os.chdir("..")

def build_cpp_src():
    # Only build magiskboot
    cmds = ["B_BOOT=1", "B_CRT0=1"]
    run_ndk_build(cmds)
    collect_ndk_build()

def build_native():
    print("* Building: magiskboot")
    build_cpp_src()

if __name__ == "__main__":
    build_native()
