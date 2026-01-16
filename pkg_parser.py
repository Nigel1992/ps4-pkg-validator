"""PS4 PKG file parser and validator."""

import struct
from pathlib import Path
from typing import Dict
from io import BytesIO


class SFOParser:
    """Parse param.sfo file format."""
    
    @staticmethod
    def parse(data: bytes) -> Dict[str, str]:
        """Parse param.sfo binary data and return key-value pairs."""
        result = {}
        try:
            if len(data) < 20:
                return result
            
            # Read SFO header
            magic = struct.unpack('<I', data[0:4])[0]
            if magic != 0x46535000:  # '\x00PSF'
                return result
            
            version = struct.unpack('<I', data[4:8])[0]
            key_table_offset = struct.unpack('<I', data[8:12])[0]
            data_table_offset = struct.unpack('<I', data[12:16])[0]
            entry_count = struct.unpack('<I', data[16:20])[0]
            
            # Read entries
            for i in range(entry_count):
                entry_offset = 20 + (i * 16)
                if entry_offset + 16 > len(data):
                    break
                
                key_offset = struct.unpack('<H', data[entry_offset:entry_offset+2])[0]
                param_fmt = struct.unpack('<H', data[entry_offset+2:entry_offset+4])[0]
                param_len = struct.unpack('<I', data[entry_offset+4:entry_offset+8])[0]
                param_max_len = struct.unpack('<I', data[entry_offset+8:entry_offset+12])[0]
                data_offset = struct.unpack('<I', data[entry_offset+12:entry_offset+16])[0]
                
                # Read key name
                key_pos = key_table_offset + key_offset
                key_end = data.find(b'\x00', key_pos)
                if key_end == -1:
                    continue
                key_name = data[key_pos:key_end].decode('utf-8', errors='ignore')
                
                # Read value
                value_pos = data_table_offset + data_offset
                if param_fmt == 0x0004:  # UTF-8 string
                    value_end = data.find(b'\x00', value_pos)
                    if value_end == -1:
                        value_end = value_pos + param_len
                    value = data[value_pos:value_end].decode('utf-8', errors='ignore')
                elif param_fmt == 0x0404:  # Integer
                    if value_pos + 4 <= len(data):
                        value = str(struct.unpack('<I', data[value_pos:value_pos+4])[0])
                    else:
                        value = '0'
                else:
                    value = ''
                
                if key_name and value:
                    result[key_name] = value
        except Exception:
            pass
        
        return result


class PKGParser:
    """Parse and validate PS4 PKG files."""
    
    # PS4 PKG magic number (0x7F434E54 = "\x7FCNT")
    PKG_MAGIC = 0x7F434E54
    
    # Entry types in PKG header table
    ENTRY_DIGEST_TABLE = 0x0001
    ENTRY_CONTENT_ID = 0x0100
    ENTRY_TITLE_ID = 0x0103
    ENTRY_PARAM_SFO = 0x1000
    
    def __init__(self, file_path: str):
        """Initialize parser with PKG file path."""
        self.file_path = Path(file_path)
        self.is_valid = False
        self.info: Dict[str, str] = {}
        self.error_message = ""
        
    def validate(self) -> bool:
        """Validate PKG file and extract information."""
        try:
            if not self.file_path.exists():
                self.error_message = "File does not exist"
                return False
                
            if self.file_path.stat().st_size < 0xC0:  # Minimum header size
                self.error_message = "File too small to be a valid PKG"
                return False
                
            with open(self.file_path, 'rb') as f:
                # Read and validate magic number
                magic = struct.unpack('>I', f.read(4))[0]
                if magic != self.PKG_MAGIC:
                    self.error_message = f"Invalid PKG magic: 0x{magic:08X} (expected 0x{self.PKG_MAGIC:08X})"
                    return False
                
                # Read PKG type and flags
                pkg_type = struct.unpack('>I', f.read(4))[0]
                pkg_flags = struct.unpack('>I', f.read(4))[0]
                
                # Read file offset values
                f.seek(0x10)
                file_count = struct.unpack('>I', f.read(4))[0]
                entry_count = struct.unpack('>I', f.read(4))[0]
                
                f.seek(0x18)
                table_offset = struct.unpack('>I', f.read(4))[0]
                
                f.seek(0x20)
                body_offset = struct.unpack('>Q', f.read(8))[0]
                body_size = struct.unpack('>Q', f.read(8))[0]

                # Read content type / flags (based on community tools)
                f.seek(0x70)
                content_type = struct.unpack('>I', f.read(4))[0]
                content_flags = struct.unpack('>I', f.read(4))[0]
                
                # Store basic info
                self.info['PKG Type'] = self._get_pkg_type_name(pkg_type)
                self.info['PKG Flags'] = f"0x{pkg_flags:08X}"
                self.info['File Count'] = str(file_count)
                self.info['Entry Count'] = str(entry_count)
                self.info['Body Offset'] = f"0x{body_offset:08X}"
                self.info['Body Size'] = self._format_size(body_size)
                self.info['Content Type'] = f"0x{content_type:08X}"
                self.info['Content Flags'] = f"0x{content_flags:08X}"
                
                # Parse entry table for content ID and other metadata
                self._parse_entry_table(f, table_offset, entry_count)
                
                # Extract firmware version from param.sfo if available
                if 'SYSTEM_VER' in self.info:
                    try:
                        sys_ver = int(self.info['SYSTEM_VER'])
                        if sys_ver > 0:
                            hex_ver = f"{sys_ver:X}"
                            if len(hex_ver) >= 3:
                                fw_ver = f"{hex_ver[0]}.{hex_ver[1:3]}"
                                self.info['Minimum Firmware'] = fw_ver
                    except Exception:
                        pass

                # Trophy presence heuristic (scan small portion for TRP markers)
                try:
                    self.info['Trophies Present'] = 'Yes' if self._has_trophy_files() else 'No'
                except Exception:
                    self.info['Trophies Present'] = 'Unknown'

                # Backport heuristic: filename contains backport/backported
                name_lower = self.file_path.name.lower()
                if 'backport' in name_lower or 'backported' in name_lower:
                    self.info['Backport'] = 'Likely (filename hint)'
                else:
                    self.info['Backport'] = 'Unknown'
                
                self.is_valid = True
                return True
                
        except Exception as e:
            self.error_message = f"Parse error: {str(e)}"
            return False
    
    def _parse_entry_table(self, f, table_offset: int, entry_count: int):
        """Parse the PKG entry table to extract metadata."""
        try:
            f.seek(table_offset)
            param_sfo_offset = None
            param_sfo_size = None
            
            for _ in range(entry_count):
                entry_id = struct.unpack('>I', f.read(4))[0]
                entry_flags = struct.unpack('>I', f.read(4))[0]
                entry_offset = struct.unpack('>I', f.read(4))[0]
                entry_size = struct.unpack('>I', f.read(4))[0]
                f.read(16)  # Skip padding
                
                current_pos = f.tell()
                
                # Extract Content ID
                if entry_id == self.ENTRY_CONTENT_ID:
                    f.seek(entry_offset)
                    content_id = f.read(min(entry_size, 64)).decode('utf-8', errors='ignore').rstrip('\x00')
                    self.info['Content ID'] = content_id
                
                # Extract Title ID  
                elif entry_id == self.ENTRY_TITLE_ID:
                    f.seek(entry_offset)
                    title_id = f.read(min(entry_size, 16)).decode('utf-8', errors='ignore').rstrip('\x00')
                    self.info['Title ID'] = title_id
                
                # Extract param.sfo
                elif entry_id == self.ENTRY_PARAM_SFO:
                    param_sfo_offset = entry_offset
                    param_sfo_size = entry_size
                
                f.seek(current_pos)
            
            # Parse param.sfo if found
            if param_sfo_offset and param_sfo_size:
                f.seek(param_sfo_offset)
                sfo_data = f.read(min(param_sfo_size, 65536))  # Max 64KB
                sfo_params = SFOParser.parse(sfo_data)
                
                # Extract useful parameters
                if 'TITLE' in sfo_params:
                    self.info['Title'] = sfo_params['TITLE']
                if 'TITLE_ID' in sfo_params:
                    self.info['Title ID'] = sfo_params['TITLE_ID']
                if 'APP_VER' in sfo_params:
                    app_ver = sfo_params['APP_VER'].lstrip('0')
                    self.info['App Version'] = app_ver if app_ver else '0'
                if 'VERSION' in sfo_params:
                    ver = sfo_params['VERSION'].lstrip('0')
                    self.info['Version'] = ver if ver else '0'
                if 'SYSTEM_VER' in sfo_params:
                    self.info['SYSTEM_VER'] = sfo_params['SYSTEM_VER']
                if 'CATEGORY' in sfo_params:
                    self.info['Category'] = sfo_params['CATEGORY']
                
        except Exception:
            # Non-fatal, just skip metadata extraction
            pass

    def _has_trophy_files(self) -> bool:
        """Heuristic scan for trophy/TRP markers without full extraction."""
        max_scan = 8 * 1024 * 1024  # scan first 8MB for markers
        patterns = [b'.trp', b'TROPHY', b'TROPHY.TRP']
        try:
            with open(self.file_path, 'rb') as fh:
                chunk = fh.read(max_scan)
                data_lower = chunk.lower()
                return any(pat.lower() in data_lower for pat in patterns)
        except Exception:
            return False
    
    def _get_pkg_type_name(self, pkg_type: int) -> str:
        """Convert PKG type to human-readable name."""
        types = {
            0x1: "PS4 App",
            0x2: "PS4 Patch",
            0x3: "PS4 Remaster",
            0x4: "PS4 Theme",
            0x5: "PS4 Widget",
            0x6: "PS4 License",
            0x7: "PS Vita App",
            0x8: "PS Vita DLC",
            0x9: "PS Vita Theme",
        }
        return types.get(pkg_type, f"Unknown (0x{pkg_type:X})")
    
    def _format_size(self, size: int) -> str:
        """Format byte size as human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
