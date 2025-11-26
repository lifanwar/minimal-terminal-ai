"""Filesystem navigation and operations"""
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from utils.validators import PathValidator


console = Console()


class FileSystemNavigator:
    """Handles filesystem navigation and file operations"""
    
    def __init__(self, home_dir: Optional[Path] = None):
        """
        Initialize filesystem navigator
        
        Args:
            home_dir: Home directory boundary (default: user's home)
        """
        self.home_dir = home_dir or Path.home()
        self.current_dir = Path.cwd()
        self.prev_dir = self.current_dir
        
        # Validators
        self.path_validator = PathValidator(self.home_dir)
        
        # Ignore patterns for tree view
        self.ignore_patterns = [
            '*.pyc', '__pycache__', '.git', 
            'node_modules', '.env', '*.so', '*.pyc'
        ]
        
        # Lexer mapping for syntax highlighting
        self.suffix_to_lexer = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.css': 'css',
            '.html': 'html',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'bash',
            '.ts': 'typescript'
        }
    
    def cd(self, path: Optional[str] = None) -> bool:
        """
        Change directory with validation
        
        Args:
            path: Target directory path (None=home, '..'=parent, '-'=previous)
            
        Returns:
            True if successful, False otherwise
        """
        if path is None:
            target = self.home_dir
        elif path == '..':
            target = self.current_dir.parent
        elif path == '-':
            target = self.prev_dir
        else:
            if Path(path).is_absolute():
                target = Path(path)
            else:
                target = self.current_dir / path
        
        target = target.resolve()
        
        # Validations
        if not self.path_validator.is_path_allowed(target):
            console.print("[red]❌ Access denied: outside home directory[/red]")
            return False
            
        if not target.exists():
            console.print(f"[red]❌ Directory not found: {target}[/red]")
            return False
            
        if not target.is_dir():
            console.print(f"[red]❌ Not a directory: {target}[/red]")
            return False
        
        # Update state
        self.prev_dir = self.current_dir
        self.current_dir = target
        console.print(f"[green]✓[/green] [dim]{self.current_dir}[/dim]")
        return True
    
    def ls(self, path: Optional[str] = None) -> None:
        """
        List directory contents
        
        Args:
            path: Directory to list (default: current directory)
        """
        target = self.current_dir if path is None else self.current_dir / path
        target = target.resolve()
        
        if not self.path_validator.is_path_allowed(target):
            console.print("[red]❌ Access denied[/red]")
            return
            
        if not target.exists():
            console.print(f"[red]❌ Path not found: {target}[/red]")
            return
        
        try:
            items = sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for item in items:
                if item.is_dir():
                    console.print(f"[bold blue]📁 {item.name}/[/bold blue]")
                else:
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    console.print(f"[white]📄 {item.name}[/white] [dim]({size_str})[/dim]")
        except PermissionError:
            console.print("[red]❌ Permission denied[/red]")
    
    def pwd(self) -> str:
        """
        Print working directory
        
        Returns:
            Current directory path as string
        """
        console.print(f"[cyan]{self.current_dir}[/cyan]")
        return str(self.current_dir)
    
    def cat(self, filepath: str) -> Optional[str]:
        """
        Read and display file content with syntax highlighting
        
        Args:
            filepath: Path to file (relative to current directory)
            
        Returns:
            File content as string, or None if error
        """
        target = self.current_dir / filepath
        target = target.resolve()
        
        if not self.path_validator.is_path_allowed(target):
            console.print("[red]❌ Access denied[/red]")
            return None
            
        if not target.exists():
            console.print(f"[red]❌ File not found: {filepath}[/red]")
            return None
            
        if not target.is_file():
            console.print(f"[red]❌ Not a file: {filepath}[/red]")
            return None
        
        try:
            content = target.read_text(encoding='utf-8')
            
            # Syntax highlighting if code file
            if target.suffix in self.suffix_to_lexer:
                lexer_name = self.suffix_to_lexer[target.suffix]
                syntax = Syntax(content, lexer_name, theme="monokai", line_numbers=True)
                console.print(syntax)
            else:
                console.print(Panel(content, title=str(filepath), border_style="cyan"))
            
            return content
        except UnicodeDecodeError:
            console.print("[red]❌ Binary file or encoding error[/red]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Error reading file: {e}[/red]")
            return None
    
    def tree(self, path: Optional[str] = None, max_depth: int = 3, 
             current_depth: int = 0, prefix: str = "") -> None:
        """
        Display directory tree structure
        
        Args:
            path: Starting directory (default: current)
            max_depth: Maximum recursion depth
            current_depth: Internal recursion tracker
            prefix: Internal tree prefix for formatting
        """
        target = self.current_dir if path is None else self.current_dir / path
        target = target.resolve()
        
        if not self.path_validator.is_path_allowed(target):
            console.print("[red]❌ Access denied[/red]")
            return
            
        if not target.exists():
            console.print(f"[red]❌ Path not found[/red]")
            return
        
        if current_depth == 0:
            console.print(f"[bold cyan]{target.name or target}/[/bold cyan]")
        
        if not target.is_dir() or current_depth >= max_depth:
            return
        
        try:
            items = sorted(target.iterdir(), 
                          key=lambda x: (not x.is_dir(), x.name.lower()))
            
            # Filter ignored patterns
            items = [item for item in items 
                    if not any(item.match(pattern) for pattern in self.ignore_patterns)]
            
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                current_prefix = "└── " if is_last else "├── "
                child_prefix = "    " if is_last else "│   "
                
                if item.is_dir():
                    console.print(f"[dim]{prefix}{current_prefix}[/dim][blue]📁 {item.name}/[/blue]")
                    self.tree(item, max_depth, current_depth + 1, prefix + child_prefix)
                else:
                    size = self._format_size(item.stat().st_size)
                    console.print(f"[dim]{prefix}{current_prefix}[/dim][white]{item.name}[/white] [dim]({size})[/dim]")
                    
        except PermissionError:
            console.print(f"[dim]{prefix}[/dim][red]❌ Permission denied[/red]")
    
    def get_relative_path(self) -> str:
        """
        Get current path relative to home directory
        
        Returns:
            Relative path with ~ prefix, or absolute path
        """
        try:
            rel = self.current_dir.relative_to(self.home_dir)
            return f"~/{rel}" if str(rel) != '.' else "~"
        except ValueError:
            return str(self.current_dir)
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
