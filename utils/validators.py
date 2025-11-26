# utils/validators.py
from pathlib import Path
from typing import Optional


class PathValidator:
    """Validator for filesystem paths with context"""
    
    def __init__(self, home_dir: Path):
        """
        Initialize validator with home directory
        
        Args:
            home_dir: Home directory boundary for path validation
        """
        self.home_dir = home_dir
    
    def is_path_allowed(self, target_path: Path) -> bool:
        """
        Check if path is within home directory boundaries
        
        Args:
            target_path: Path to validate
            
        Returns:
            True if path is within home_dir
        """
        try:
            resolved = Path(target_path).resolve()
            return resolved.is_relative_to(self.home_dir)
        except Exception:
            return False
    
    def validate_path_exists(self, target_path: Path) -> Optional[str]:
        """Validate path existence"""
        if not target_path.exists():
            return f"Path not found: {target_path}"
        return None
    
    def validate_is_directory(self, target_path: Path) -> Optional[str]:
        """Validate path is a directory"""
        if not target_path.is_dir():
            return f"Not a directory: {target_path}"
        return None
    
    def validate_is_file(self, target_path: Path) -> Optional[str]:
        """Validate path is a file"""
        if not target_path.is_file():
            return f"Not a file: {target_path}"
        return None


class FileValidator:
    """Validator for file properties (stateless)"""
    
    @staticmethod
    def is_binary(filepath: Path, chunk_size: int = 1024) -> bool:
        """Check if file is binary"""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(chunk_size)
                return b'\x00' in chunk
        except Exception:
            return True
    
    @staticmethod
    def is_too_large(filepath: Path, max_size: int = 500_000) -> bool:
        """Check if file exceeds size limit"""
        try:
            return filepath.stat().st_size > max_size
        except Exception:
            return True
    
    @staticmethod
    def validate_file_for_context(filepath: Path, max_size: int = 500_000) -> Optional[str]:
        """Comprehensive validation for adding file to context"""
        if not filepath.is_file():
            return "Not a file"
        
        if FileValidator.is_too_large(filepath, max_size):
            return f"File too large (max {max_size / 1000}KB)"
        
        if FileValidator.is_binary(filepath):
            return "Binary file not supported"
        
        return None
