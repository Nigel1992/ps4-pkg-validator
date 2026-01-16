# PS4 PKG Validator - Feature Summary

## What It Does
A Linux desktop application that validates PS4 PKG files and extracts detailed metadata.

## Key Features

### 1. PKG Validation
- Verifies PKG magic number (0x7F434E54)
- Checks header structure integrity
- Validates minimum file size requirements

### 2. Metadata Extraction
The tool now extracts comprehensive information from PKG files:

#### From PKG Header:
- PKG Type (PS4 App, Game, Patch, Addon, Theme, etc.)
- PKG Flags
- File Count and Entry Count
- Body Offset and Body Size
- Content ID (e.g., EP1234-CUSA12345_00-GAMEID00000000)
- Title ID (e.g., CUSA12345)

#### From param.sfo (NEW):
- **Title**: Full game/application name
- **App Version**: Application version (e.g., 01.05)
- **Version**: PKG version (e.g., 1.00)
- **System Version**: Raw firmware requirement
- **Minimum Firmware**: Converted to readable format (e.g., 8.50, 9.00, 11.00)
- **Category**: Package category code

### 3. User Interface
- PyQt6-based modern GUI
- Drag-and-drop support for .pkg files
- Multi-file processing
- Visual status indicators (✓ valid, ✗ invalid)
- Detailed information panel
- File size formatting (GB, MB, KB)

### 4. Firmware Version Detection
Automatically converts PS4 SYSTEM_VER values to firmware versions:
- `0x08500000` → 8.50
- `0x09000000` → 9.00
- `0x0B000000` → 11.00

## Implementation Details

### Technologies Used
- Python 3.8+
- PyQt6 for GUI
- Struct module for binary parsing
- Custom SFO parser based on PS4-PKG-Tool

### Parsing Approach
1. Reads PKG header (first 192 bytes minimum)
2. Validates magic number and structure
3. Locates entry table from header offset
4. Iterates through entries to find:
   - Content ID entry (0x0100)
   - Title ID entry (0x0103)
   - param.sfo entry (0x1000)
5. Extracts and parses param.sfo:
   - Reads SFO header
   - Parses key/value tables
   - Extracts TITLE, SYSTEM_VER, APP_VER, etc.
6. Converts firmware hex values to decimal

### Based On
Code and techniques adapted from:
- **pearlxcore/PS4-PKG-Tool**: C# PKG parser and param.sfo extraction
- **hippie68/ps4-pkg-compatibility-checker**: Java PKG validation

## Use Cases

1. **PKG Library Management**: Quickly check PKG validity before archiving
2. **Firmware Compatibility**: See which firmware version is required
3. **Version Tracking**: Track app versions across updates
4. **Content Verification**: Verify Content ID and Title ID accuracy
5. **Metadata Extraction**: Extract titles and IDs for database/cataloging

## Testing
Includes unit tests with synthetic PKG files to verify:
- Valid PKG parsing
- Invalid magic number detection
- File size validation
- Missing file handling
