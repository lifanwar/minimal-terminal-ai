from pathlib import Path
from rich.console import Console
from typing import Optional

# Core
from core.filesystem import FileSystemNavigator

# Utils
from utils.validators import PathValidator, FileValidator

console = Console()


class FileSystemManager:
    def __init__(self):
        # filesystem operations
        self.navigator = FileSystemNavigator()

        # validators
        self.path_validator = PathValidator(self.home_dir)
        self.file_validator = FileValidator(self.home_dir)

        self.context_files = {}  # {display_name: Path_object}
        self.paste_contexts = {}  # NEW: {paste_id: {"content": str, "timestamp": datetime, "lines": int, "size": int}}
        self.paste_counter = 0  # NEW: Counter for paste IDs
        self.ignore_patterns = [
            '*.pyc', '__pycache__', '.git', 
            'node_modules', '.env', '*.so', '*.pyc'
        ]
    
    @property
    def home_dir(self):
        """Get home directory from navigator"""
        return self.navigator.home_dir
    
    @property
    def current_dir(self):
        """Get current directory from navigator"""
        return self.navigator.current_dir
    
    def cd(self, path: Optional[str] = None) -> bool:
        """Change directory - delegates to navigator"""
        return self.navigator.cd(path)
    
    def ls(self, path: Optional[str] = None) -> None:
        """List directory - delegates to navigator"""
        self.navigator.ls(path)
    
    def pwd(self) -> str:
        """Print working directory - delegates to navigator"""
        return self.navigator.pwd()
    
    def cat(self, filepath: str) -> Optional[str]:
        """Read file - delegates to navigator"""
        return self.navigator.cat(filepath)
    
    def tree(self, path: Optional[str] = None, max_depth: int = 3) -> None:
        """Display tree - delegates to navigator"""
        self.navigator.tree(path, max_depth)
    
    def get_relative_path(self) -> str:
        """Get relative path - delegates to navigator"""
        return self.navigator.get_relative_path()
    
    
    def add_to_context(self, pattern):
        """Add file(s) to AI context"""
        if '*' in pattern or '?' in pattern:
            matches = list(self.navigator.current_dir.glob(pattern))
        else:
            target = self.navigator.current_dir / pattern
            if target.is_dir():
                matches = list(target.glob('*'))
            else:
                matches = [target] if target.exists() else []

        added = 0
        for match in matches:
            if match.is_file() and self.path_validator.is_path_allowed(match):
                if match.stat().st_size > 500_000:
                    console.print(f"[yellow]⚠️  Skipped (too large): {match.name}[/yellow]")
                    continue
                
                if self.file_validator._is_binary(match):
                    console.print(f"[yellow]⚠️  Skipped (binary): {match.name}[/yellow]")
                    continue
                
                # ✅ Simpan dengan absolute path sebagai key
                abs_path = str(match.resolve())
                self.context_files[abs_path] = match
                added += 1

        if added:
            console.print(f"[green]✓ Added {added} file(s) to context[/green]")
            self._show_context_summary()
        else:
            console.print("[yellow]⚠️  No files added[/yellow]")

    
    def remove_from_context(self, pattern):
        """Remove file(s) from context"""
        import fnmatch
        removed = 0
        
        if pattern == '*':
            removed = len(self.context_files)
            self.context_files.clear()
        else:
            to_remove = [k for k in self.context_files.keys() 
                        if fnmatch.fnmatch(k, pattern)]
            for key in to_remove:
                del self.context_files[key]
                removed += 1
        
        console.print(f"[green]✓ Removed {removed} file(s) from context[/green]")

    def add_paste_to_context(self, text):
        """
        Add pasted text to context with auto-generated ID

        Args:
            text (str): Pasted text content

        Returns:
            str: Generated paste ID (e.g., "paste_001")
        """
        from datetime import datetime

        self.paste_counter += 1
        paste_id = f"paste_{self.paste_counter:03d}"

        self.paste_contexts[paste_id] = {
            'content': text,
            'timestamp': datetime.now(),
            'lines': text.count('\n') + 1,
            'size': len(text)
        }

        return paste_id


    def remove_paste_from_context(self, paste_id):
        """
        Remove specific paste from context by ID

        Args:
            paste_id (str): Paste ID to remove

        Returns:
            bool: True if removed, False if not found
        """
        if paste_id in self.paste_contexts:
            del self.paste_contexts[paste_id]
            return True
        return False


    def clear_paste_contexts(self):
        """
        Clear all paste contexts

        Returns:
            int: Number of pastes cleared
        """
        count = len(self.paste_contexts)
        self.paste_contexts.clear()
        return count


    def _format_time_ago(self, timestamp):
        """
        Format timestamp to relative time string

        Args:
            timestamp (datetime): Timestamp to format

        Returns:
            str: Relative time (e.g., "2m ago", "1h ago")
        """
        from datetime import datetime

        now = datetime.now()
        diff = now - timestamp
        seconds = diff.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"

    
    def list_context(self):
        """Show current context files and pastes"""
        has_files = len(self.context_files) > 0
        has_pastes = len(self.paste_contexts) > 0
        
        if not has_files and not has_pastes:
            console.print("[dim]No files or pastes in context[/dim]")
            return
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in self.context_files.values())
        total_size += sum(p['size'] for p in self.paste_contexts.values())
        
        total_items = len(self.context_files) + len(self.paste_contexts)
        console.print(f"[bold cyan]📋 Context ({total_items} items, {self._format_size(total_size)})[/bold cyan]")
        
        # Show files
        if has_files:
            console.print("\n[bold]Files:[/bold]")
            for abs_path, path_obj in self.context_files.items():
                size = self._format_size(path_obj.stat().st_size)
                # Show relative to home for readability
                try:
                    rel_home = path_obj.relative_to(self.navigator.home_dir)
                    display_path = f"~/{rel_home}"
                except ValueError:
                    display_path = abs_path
                
                console.print(f"  [white]• {display_path}[/white] [dim]({size})[/dim]")
            
            # Show pastes
            if has_pastes:
                console.print("\n[bold]Pasted Content:[/bold]")
                for paste_id, data in sorted(self.paste_contexts.items()):
                    size = self._format_size(data['size'])
                    lines = data['lines']
                    time_ago = self._format_time_ago(data['timestamp'])
                    console.print(f"  [yellow]• {paste_id}[/yellow] [dim]({lines} lines, {size}) - {time_ago}[/dim]")
    
    
    def get_context_for_api(self):
        files_dict = {}
        for abs_path, file_path in self.context_files.items():
            try:
                content = file_path.read_text(encoding='utf-8')
                # Stabil: relatif ke home_dir, fallback ke absolute
                try:
                    rel_home = file_path.relative_to(self.navigator.home_dir)
                    key = f"~/{rel_home}"
                except ValueError:
                    key = str(file_path)  # absolute fallback
                files_dict[key] = content
            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to read {abs_path}: {e}[/yellow]")
        return files_dict
    
    def _show_context_summary(self):
        """Show quick summary of context structure"""
        folders = set()
        for name, path in self.context_files.items():
            try:
                rel = path.relative_to(self.navigator.current_dir)
                if rel.parent != Path('.'):
                    folders.add(str(rel.parent))
            except:
                pass
        
        if folders:
            console.print(f"[dim]Folders: {', '.join(sorted(folders))}[/dim]")
    
    @staticmethod
    def _format_size(size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
