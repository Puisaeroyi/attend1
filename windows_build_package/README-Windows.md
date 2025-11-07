# Attendance & CSV Converter Tool - Windows Build Package

## Overview

This package contains everything you need to build the Windows executable (.exe) for the Attendance & CSV Converter Tool v3.0.0 (GUI Edition).

## Package Contents

### Core Application Files
- `main_gui.py` - GUI application entry point
- `processor.py` - Core attendance processing logic
- `csv_converter.py` - CSV to XLSX conversion logic
- `config.py` - Configuration management
- `validators.py` - Input validation functions
- `utils.py` - Utility functions
- `rule.yaml` - Business rules configuration

### GUI Module
- `gui/` - Complete GUI interface
  - `main_window.py` - Main window with tabs
  - `csv_tab.py` - CSV converter interface
  - `attendance_tab.py` - Attendance processor interface
  - `utils.py` - GUI utilities
  - `styles.py` - Professional styling
  - `__init__.py` - GUI module initialization

### Build Files
- `build_exe.py` - PyInstaller build script
- `icon.ico` - Application icon
- `requirements.txt` - Python dependencies

### Documentation
- `README-GUI.txt` - Quick start guide for users
- `BUILDING.txt` - Detailed build instructions

## Prerequisites

### Windows System
- Windows 10 or Windows 11 (64-bit)
- Python 3.9+ installed
- Command Prompt or PowerShell

### Python Dependencies
The required packages will be installed automatically:
- tkinter (usually included with Python)
- pandas
- openpyxl
- pyyaml
- xlsxwriter
- pyinstaller

## Building the Executable

### Step 1: Install Dependencies
```cmd
pip install pyinstaller pandas openpyxl pyyaml xlsxwriter
```

### Step 2: Build the Executable
```cmd
python build_exe.py
```

The build script will:
- Check all dependencies
- Create the application icon
- Build a standalone executable
- Report the file size

### Step 3: Locate Your Executable
After successful build, the executable will be at:
```
dist/AttendanceProcessor.exe
```

## Testing the Executable

### Basic Tests
1. Double-click `AttendanceProcessor.exe` - should open without errors
2. Verify both tabs (CSV Converter, Attendance Processor) are visible
3. Test file browsers work correctly
4. Verify no console window appears

### Functional Tests
1. **CSV Converter Test:**
   - Browse for a CSV file
   - Choose output location
   - Click Convert - should process without errors

2. **Attendance Processor Test:**
   - Browse for an Excel file
   - Choose output location
   - Use default config (rule.yaml)
   - Click Process - should show real-time logging

## Distribution

The final `AttendanceProcessor.exe` file is all users need:
- ✅ No Python installation required
- ✅ No dependencies needed
- ✅ Single file distribution
- ✅ Professional Windows application

## File Structure After Build

```
AttendanceProcessor/
├── AttendanceProcessor.exe    # Your final application
├── README-GUI.txt             # User instructions
└── BUILDING.txt               # Build documentation (optional)
```

## Troubleshooting

### Build Issues
- **"Module not found"**: Install missing dependencies from requirements.txt
- **"Permission denied"**: Run Command Prompt as Administrator
- **Large file size (>30MB)**: Check for unnecessary dependencies

### Runtime Issues
- **Application won't open**: Check Windows version compatibility
- **File not found errors**: Verify input files exist
- **Permission errors**: Close files in Excel before processing

## Support

For build issues:
1. Check the console output during build for specific errors
2. Verify Python version is 3.9+
3. Ensure all dependencies are installed

For application issues:
1. Review README-GUI.txt for usage instructions
2. Check error messages in the application log
3. Test with sample data files

---

**Version:** 3.0.0 (GUI Edition)
**Platform:** Windows 10/11 (64-bit)
**Build Date:** 2025-11-06