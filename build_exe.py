#!/usr/bin/env python3
"""
Build standalone Windows executable using PyInstaller

Creates a single .exe file for the Attendance & CSV Converter Tool
that includes all dependencies and can run on Windows without Python.
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")

    required_modules = [
        'tkinter', 'pandas', 'openpyxl', 'yaml', 'xlsxwriter'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"  ❌ {module} - MISSING")

    if missing_modules:
        print(f"\n❌ Missing required modules: {', '.join(missing_modules)}")
        print("Please install them with: pip install " + " ".join(missing_modules))
        return False

    print("✅ All dependencies found")
    return True


def create_icon():
    """Create a simple icon file if it doesn't exist"""
    icon_path = Path("icon.ico")
    if not icon_path.exists():
        print("⚠️  icon.ico not found. Creating placeholder...")

        # Create a simple placeholder using base64 encoded ICO data
        # This is a minimal 32x32 icon
        ico_data = (
            "\x00\x00\x01\x00\x01\x00\x20\x20\x00\x00\x01\x00\x08\x00\x68\x06\x00\x00"
            "\x16\x00\x00\x00\x28\x00\x00\x00\x20\x00\x00\x00\x40\x00\x00\x00\x01\x00"
            "\x08\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )

        with open(icon_path, 'wb') as f:
            import base64
            f.write(base64.b64decode(ico_data + "===="))

        print(f"✅ Created placeholder icon: {icon_path}")
    else:
        print(f"✅ Icon found: {icon_path}")


def build_executable():
    """Build the standalone executable"""
    project_root = Path(__file__).parent
    icon_path = project_root / "icon.ico"
    rule_yaml = project_root / "rule.yaml"

    print("\n" + "=" * 70)
    print("BUILDING EXECUTABLE")
    print("=" * 70)

    # PyInstaller arguments
    args = [
        'main_gui.py',                     # Entry point
        '--name=AttendanceProcessor',      # Executable name
        '--onefile',                       # Single file
        '--windowed',                      # No console window
        '--clean',                         # Clean cache
        '--noconfirm',                     # Overwrite without prompt
        '--distpath=dist',                 # Output directory
        '--workpath=build',                # Build directory
    ]

    # Add icon if available
    if icon_path.exists():
        args.append(f'--icon={icon_path}')
        print(f"✅ Using icon: {icon_path}")
    else:
        print("⚠️  No icon specified")

    # Bundle rule.yaml if available
    if rule_yaml.exists():
        args.append(f'--add-data={rule_yaml};.')
        print(f"✅ Bundling config: {rule_yaml}")
    else:
        print("⚠️  rule.yaml not found - will need to be distributed separately")

    # Hidden imports (ensure all dependencies are included)
    hidden_imports = [
        'pandas',
        'openpyxl',
        'yaml',
        'xlsxwriter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'config',
        'processor',
        'csv_converter',
        'validators',
        'gui.main_window',
        'gui.csv_tab',
        'gui.attendance_tab',
        'gui.utils',
        'gui.styles',
    ]

    for module in hidden_imports:
        args.append(f'--hidden-import={module}')

    print(f"✅ Hidden imports: {len(hidden_imports)} modules")

    # Additional options
    args.extend([
        '--noupx',                         # Don't use UPX compression (can cause issues)
        '--disable-windowed-traceback',   # Disable console traceback
        '--exclude-module=matplotlib',     # Exclude unused heavy modules
        '--exclude-module=scipy',          # Exclude unused heavy modules
        '--exclude-module=numpy.testing',  # Exclude testing modules
    ])

    print("\nRunning PyInstaller...")
    print(f"Command: pyinstaller {' '.join(args)}")

    try:
        PyInstaller.__main__.run(args)

        # Check if executable was created
        exe_path = project_root / "dist" / "AttendanceProcessor.exe"
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"\n✅ Build successful!")
            print(f"📁 Executable: {exe_path}")
            print(f"📏 File size: {file_size:.1f} MB")

            if file_size > 30:
                print("⚠️  File size is larger than expected (>30MB)")
            else:
                print("✅ File size is acceptable")

        else:
            print("❌ Build failed - executable not found")
            return False

    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        return False

    return True


def test_executable():
    """Test the built executable (basic check)"""
    exe_path = Path("dist/AttendanceProcessor.exe")
    if exe_path.exists():
        print(f"\n📋 Executable created: {exe_path}")
        print("✅ Build complete!")
        print("\nNext steps:")
        print("1. Test the executable on your development machine")
        print("2. Test on a clean Windows VM (no Python)")
        print("3. Distribute to users")
    else:
        print("❌ Executable not found - build may have failed")


def main():
    """Main build function"""
    print("Attendance & CSV Converter Tool - Executable Builder")
    print("=" * 70)

    # Check if we're on Windows
    if sys.platform != "win32":
        print("⚠️  Warning: Not running on Windows")
        print("    This will create an executable that may not work properly")
        print("    It's recommended to build on Windows for Windows targets")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Build cancelled")
            return

    # Check dependencies
    if not check_dependencies():
        print("❌ Dependencies check failed")
        return

    # Create icon if needed
    create_icon()

    # Build executable
    if build_executable():
        test_executable()
    else:
        print("❌ Build failed")
        return

    print("\n" + "=" * 70)
    print("BUILD PROCESS COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()