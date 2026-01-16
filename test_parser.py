"""Unit tests for PKG parser."""

import struct
import tempfile
from pathlib import Path
from pkg_parser import PKGParser


def create_test_pkg(file_path: str, magic: int = 0x7F434E54, valid: bool = True):
    """Create a minimal test PKG file with synthetic header."""
    with open(file_path, 'wb') as f:
        # Magic number
        f.write(struct.pack('>I', magic))
        
        # PKG type (0x1 = PS4 App)
        f.write(struct.pack('>I', 0x1))
        
        # PKG flags
        f.write(struct.pack('>I', 0x00000000))
        
        # File offset (0x0C)
        f.write(struct.pack('>I', 0x00000000))
        
        # File count and entry count (0x10)
        f.write(struct.pack('>I', 5))  # file_count
        f.write(struct.pack('>I', 3))  # entry_count (includes param.sfo)
        
        # Table offset (0x18)
        f.write(struct.pack('>I', 0xC0))  # table_offset
        
        # Reserved (0x1C)
        f.write(struct.pack('>I', 0x00000000))
        
        # Body offset and size (0x20)
        f.write(struct.pack('>Q', 0x1000))  # body_offset
        f.write(struct.pack('>Q', 0x100000))  # body_size
        
        # Pad to minimum size
        f.write(b'\x00' * (0xC0 - f.tell()))
        
        if valid:
            # Entry 1: Content ID
            f.write(struct.pack('>I', 0x0100))  # entry_id (ENTRY_CONTENT_ID)
            f.write(struct.pack('>I', 0x00))    # flags
            f.write(struct.pack('>I', 0x200))   # offset
            f.write(struct.pack('>I', 48))      # size
            f.write(b'\x00' * 16)                # padding
            
            # Entry 2: Title ID
            f.write(struct.pack('>I', 0x0103))  # entry_id (ENTRY_TITLE_ID)
            f.write(struct.pack('>I', 0x00))    # flags
            f.write(struct.pack('>I', 0x250))   # offset
            f.write(struct.pack('>I', 16))      # size
            f.write(b'\x00' * 16)                # padding
            
            # Entry 3: param.sfo
            f.write(struct.pack('>I', 0x1000))  # entry_id (ENTRY_PARAM_SFO)
            f.write(struct.pack('>I', 0x00))    # flags
            f.write(struct.pack('>I', 0x300))   # offset
            f.write(struct.pack('>I', 0x200))   # size
            f.write(b'\x00' * 16)                # padding
            
            # Add content at offset 0x200
            f.seek(0x200)
            f.write(b'EP1234-CUSA12345_00-TESTGAME00000000\x00')
            
            # Add title at offset 0x250
            f.seek(0x250)
            f.write(b'CUSA12345\x00')
            
            # Add minimal param.sfo at offset 0x300
            f.seek(0x300)
            # SFO header: magic, version, key_table_offset, data_table_offset, entry_count
            f.write(struct.pack('<I', 0x46535000))  # PSF magic
            f.write(struct.pack('<I', 0x00000101))  # version
            f.write(struct.pack('<I', 0x54))        # key_table_offset
            f.write(struct.pack('<I', 0x80))        # data_table_offset
            f.write(struct.pack('<I', 0x03))        # entry_count
            
            # Entry 1: TITLE
            f.write(struct.pack('<H', 0x00))        # key_offset
            f.write(struct.pack('<H', 0x0004))      # format (UTF-8)
            f.write(struct.pack('<I', 20))          # length
            f.write(struct.pack('<I', 128))         # max_length
            f.write(struct.pack('<I', 0x00))        # data_offset
            
            # Entry 2: SYSTEM_VER
            f.write(struct.pack('<H', 0x06))        # key_offset (after "TITLE\0")
            f.write(struct.pack('<H', 0x0404))      # format (uint32)
            f.write(struct.pack('<I', 4))           # length
            f.write(struct.pack('<I', 4))           # max_length
            f.write(struct.pack('<I', 0x80))        # data_offset
            
            # Entry 3: APP_VER
            f.write(struct.pack('<H', 0x11))        # key_offset (after "SYSTEM_VER\0")
            f.write(struct.pack('<H', 0x0004))      # format (UTF-8)
            f.write(struct.pack('<I', 8))           # length
            f.write(struct.pack('<I', 8))           # max_length
            f.write(struct.pack('<I', 0x84))        # data_offset
            
            # Key table at 0x54
            f.seek(0x354)
            f.write(b'TITLE\x00SYSTEM_VER\x00APP_VER\x00')
            
            # Data table at 0x80
            f.seek(0x380)
            f.write(b'Test PKG Game\x00')  # TITLE
            f.seek(0x380 + 0x80)
            f.write(struct.pack('<I', 0x08500000))  # SYSTEM_VER = 8.50
            f.seek(0x380 + 0x84)
            f.write(b'01.05\x00')  # APP_VER


def test_valid_pkg():
    """Test parsing a valid PKG file."""
    with tempfile.NamedTemporaryFile(suffix='.pkg', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        create_test_pkg(tmp_path, valid=True)
        
        parser = PKGParser(tmp_path)
        assert parser.validate() is True
        assert parser.is_valid is True
        assert parser.error_message == ""
        assert parser.info.get('PKG Type') == 'PS4 App'
        assert 'Content ID' in parser.info
        assert 'EP1234-CUSA12345' in parser.info['Content ID']
        assert parser.info.get('Title') == 'Test PKG Game'
        assert parser.info.get('App Version') == '1.05'
        assert parser.info.get('Minimum Firmware') == '8.50'
        print("✓ Valid PKG test passed")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_invalid_magic():
    """Test parsing a PKG with invalid magic number."""
    with tempfile.NamedTemporaryFile(suffix='.pkg', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        create_test_pkg(tmp_path, magic=0xDEADBEEF, valid=False)
        
        parser = PKGParser(tmp_path)
        assert parser.validate() is False
        assert parser.is_valid is False
        assert "Invalid PKG magic" in parser.error_message
        print("✓ Invalid magic test passed")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_file_too_small():
    """Test parsing a file that's too small."""
    with tempfile.NamedTemporaryFile(suffix='.pkg', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'TINY')
    
    try:
        parser = PKGParser(tmp_path)
        assert parser.validate() is False
        assert "too small" in parser.error_message
        print("✓ File too small test passed")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_nonexistent_file():
    """Test parsing a file that doesn't exist."""
    parser = PKGParser('/tmp/nonexistent_file.pkg')
    assert parser.validate() is False
    assert "does not exist" in parser.error_message
    print("✓ Nonexistent file test passed")


if __name__ == '__main__':
    print("Running PKG parser tests...\n")
    test_valid_pkg()
    test_invalid_magic()
    test_file_too_small()
    test_nonexistent_file()
    print("\n✓ All tests passed!")
