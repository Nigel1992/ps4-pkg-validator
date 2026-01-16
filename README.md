# PS4 PKG Validator

A Linux desktop application for validating PS4 PKG files through drag-and-drop.

## Features

- **Drag & Drop Interface**: Simply drag .pkg files into the window
- **PKG Validation**: Checks magic number and header structure
- **Metadata Extraction**: Displays:
  - Title (from param.sfo)
  - Content ID and Title ID
  - PKG type and category
  - App Version and Version
  - Minimum Firmware Required
  - Content Type / Content Flags
  - Trophy presence (heuristic)
  - Backport hint (filename heuristic)
  - File counts and body size
- **Visual Feedback**: Green checkmark for valid files, red X for invalid

## Requirements

- Python 3.8+
- PyQt6

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

1. Launch the application
2. Drag and drop one or more `.pkg` files into the window
3. Select a file from the list to view detailed information
4. Valid files show a green ✓, invalid files show a red ✗

## PKG File Structure

The validator checks:
- **Magic Number**: `0x7F434E54` ("\x7FCNT")
- **Header Structure**: Minimum 192 bytes
- **Entry Table**: Parses metadata entries for Content ID, Title ID, and param.sfo
- **param.sfo Parsing**: Extracts title, firmware version, app version, category, raw SYSTEM_VER
- **File Metadata**: Extracts PKG type, flags, content type/flags, body offset/size, and file counts
- **Firmware Detection**: Converts SYSTEM_VER to human-readable firmware version (e.g., 8.50)
- **Trophy Check (Heuristic)**: Scans PKG for TRP markers
- **Backport Hint (Heuristic)**: Flags filenames containing "backport"/"backported"

## Credits

Based on PKG parsing techniques from:
- [pearlxcore/PS4-PKG-Tool](https://github.com/pearlxcore/PS4-PKG-Tool)
- [hippie68/ps4-pkg-compatibility-checker](https://github.com/hippie68/ps4-pkg-compatibility-checker)

## Limitations

- Does not decrypt encrypted PKG content
- Does not verify digital signatures
- Does not extract embedded files (e.g., param.sfo details beyond the fields parsed)
- Basic validation only - checks structure, not content integrity

## Development

### Project Structure

```
ps4-pkg-validator/
├── main.py              # GUI application
├── pkg_parser.py        # PKG parsing logic
├── test_parser.py       # Unit tests
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

### Testing

Create a test with synthetic PKG header bytes to verify parsing logic without requiring actual PKG files.

## License

MIT License - feel free to use and modify.
