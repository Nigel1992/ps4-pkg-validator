# Changelog

## Version 1.1.0 - Enhanced PKG Parsing

### Added
- **Title Extraction**: Now extracts game/app title from param.sfo
- **Firmware Detection**: Displays minimum required PS4 firmware version
- **App Version**: Shows the application version from param.sfo
- **Category Detection**: Identifies PKG category (game, patch, addon, app)
- **param.sfo Parser**: Complete SFO file format parser

### Improved
- Enhanced metadata display with more detailed PKG information
- Better error handling for corrupted or incomplete PKG files
- More comprehensive PKG validation

### Technical
- Implemented SFOParser class for param.sfo parsing
- Added firmware version conversion (hex to decimal format)
- Extracts SYSTEM_VER, TITLE, APP_VER, VERSION, CATEGORY from param.sfo
- Based on parsing techniques from PS4-PKG-Tool and ps4-pkg-compatibility-checker

### Example Output
Valid PKG files now display:
- **Title**: The actual game/app name
- **Content ID**: EP1234-CUSA12345_00-GAMEID00000000
- **Title ID**: CUSA12345
- **PKG Type**: PS4 App/Game/Patch/Addon
- **Category**: gd, gp, ac, etc.
- **App Version**: 01.05
- **Version**: 1.00
- **Minimum Firmware**: 8.50 (converted from SYSTEM_VER)
- **File Count**: Number of files in PKG
- **Body Size**: Actual content size in GB/MB
