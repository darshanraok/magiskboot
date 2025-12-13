#!/usr/bin/env python3
import argparse
import glob
import multiprocessing
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path

# -----------------------------
# Helper functions
# -----------------------------

def color_print(code, str_):
    if no_color:
        print(str_)
    else:
        str_ = str_.replace("\n", f"\033[0m\n{code}")
        print(f"{code}{str_}\033[0m")

def error(str_):
    color_print("\033[41;39m", f"\n! {str_}\n")
    sys.exit(1)

def header(str_):
    color_print("\033[44;39m", f"\n{str_}\n")

def vprint(str_):
    if args.verbose > 0:
        print(str_)

def execv(cmds: list, env=None):
    out = None if force_out or args.verbose > 0 else subprocess.DEVNULL
    return subprocess.run(cmds, stdout=out, env=env)

def mv(source: Path, target: Path):
    try:
        shutil.move(source, target)
        vprint(f"mv {source} -> {target}")
    except:
        pass

def collect_ndk_build():
    for arch in build_abis.keys():
        arch_dir = Path("native", "libs", arch)
        out_dir = Path("native", "out", arch)
        for source in arch_dir.iterdir():
            target = out_dir / source.name
            mv(source, target)

def run_ndk_build(cmds: list[str]):
    os.chdir("native")
    cmds.append("NDK_PROJECT_PATH=.")
    cmds.append("NDK_APPLICATION_MK=src/Application.mk")
    cmds.append(f"APP_ABI={' '.join(build_abis.keys())}")
    cmds.append(f"-j{cpu_count}")
    if args.verbose > 1:
        cmds.append("V=1")
    if not args.release:
        cmds.append("MAGISK_DEBUG=1")
    proc = execv([str(ndk_build), *cmds])
    if proc.returncode != 0:
        error("Build binary failed!")
    os.chdir("..")

def build_cpp_src():
    # Only build magiskboot
    cmds = []
    cmds.append("B_BOOT=1")
    cmds.append("B_CRT0=1")
    run_ndk_build(cmds)
    collect_ndk_build()

def ensure_toolchain():
    # Verify NDK install
    if not ndk_build.exists():
        error(f"NDK not found at {ndk_build}")

# -----------------------------
# Global settings
# -----------------------------
args = argparse.Namespace()
args.verbose = 0
args.release = True

force_out = False
cpu_count = multiprocessing.cpu_count()
no_color = False

support_abis = {
    "armeabi-v7a": "thumbv7neon-linux-androideabi",
    "x86": "i686-linux-android",
    "arm64-v8a": "aarch64-linux-android",
    "x86_64": "x86_64-linux-android",
}
build_abis = support_abis.copy()

# Detect NDK path automatically from environment
ndk_path = os.environ.get("NDK_PATH") or os.environ.get("ANDROID_NDK_HOME")
if not ndk_path or not Path(ndk_path).exists():
    error("NDK path not found! Please set NDK_PATH or ANDROID_NDK_HOME environment variable.")
ndk_build = Path(ndk_path) / "ndk-build"

# -----------------------------
# Build
# -----------------------------
def build_native():
    ensure_toolchain()
    header("* Building: magiskboot")
    build_cpp_src()

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    build_native()
