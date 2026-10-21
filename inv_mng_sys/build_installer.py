"""Automated build script for Inventory Management System.

Pipelines:
1. Generates multi-resolution application icons (app_icon.ico, app_icon.png).
2. Runs PyInstaller to package the offline CustomTkinter application into dist/InventoryManagementSystem/.
3. Compiles Inno Setup script (installer.iss) via ISCC.exe into a standalone setup.exe installer.
4. Verifies the integrity and size of the output installer.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_DIR = Path(__file__).resolve().parent


def find_iscc() -> Path:
    """Locate Inno Setup Compiler (ISCC.exe)."""
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    # Try finding in PATH
    which_iscc = shutil.which("iscc")
    if which_iscc:
        return Path(which_iscc)
    raise FileNotFoundError("Could not find ISCC.exe. Please ensure Inno Setup 6 is installed.")


def build() -> int:
    os.chdir(PROJECT_DIR)
    print("=" * 60)
    print("  IMS Installer Build Pipeline")
    print("=" * 60)

    # Step 1: Ensure icons exist
    ico_path = PROJECT_DIR / "app_icon.ico"
    if not ico_path.is_file():
        print("[1/3] Generating application icon...")
        from generate_icon import create_app_icon
        create_app_icon(PROJECT_DIR)
    else:
        print("[1/3] Application icon already present.")

    # Step 2: PyInstaller packaging
    print("[2/3] Running PyInstaller build with ims.spec...")
    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "-y",
        "ims.spec",
    ]
    res = subprocess.run(pyinstaller_cmd)
    if res.returncode != 0:
        print(f"ERROR: PyInstaller failed with code {res.returncode}")
        return res.returncode

    dist_exe = PROJECT_DIR / "dist" / "InventoryManagementSystem" / "InventoryManagementSystem.exe"
    if not dist_exe.is_file():
        print("ERROR: Packaged executable not found at expected location.")
        return 1
    print(f"SUCCESS: Packaged application built ({dist_exe})")

    # Step 3: Inno Setup compilation
    print("[3/3] Compiling installer with Inno Setup...")
    iscc_path = find_iscc()
    print(f"Using ISCC at: {iscc_path}")

    iss_file = PROJECT_DIR / "installer.iss"
    iscc_cmd = [str(iscc_path), str(iss_file)]
    res = subprocess.run(iscc_cmd)
    if res.returncode != 0:
        print(f"ERROR: ISCC failed with code {res.returncode}")
        return res.returncode

    installer_exe = PROJECT_DIR / "dist_installer" / "setup.exe"
    if not installer_exe.is_file():
        print("ERROR: Output installer not found.")
        return 1

    # Also copy setup.exe to project root for convenience
    root_setup = PROJECT_DIR / "setup.exe"
    shutil.copy2(installer_exe, root_setup)

    size_mb = installer_exe.stat().st_size / (1024 * 1024)
    print("=" * 60)
    print(f"  BUILD COMPLETE!")
    print(f"  Installer: {installer_exe}")
    print(f"  Root Copy: {root_setup}")
    print(f"  Size:      {size_mb:.2f} MB")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(build())
