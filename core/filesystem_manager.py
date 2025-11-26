from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax    

# Utils
from utils.validators import PathValidator, FileValidator

console = Console()


class FileSystemManager:
    def __init__(self):
        self.home_dir = Path.home()
        self.current_dir = Path.cwd()
        self.prev_dir = self.current_dir

        self.path_validator = PathValidator(self.home_dir)
        self.file_validator = FileValidator(self.home_dir)
        self.context_files = {}  # {display_name: Path_object}
        self.paste_contexts = {}  # NEW: {paste_id: {"content": str, "timestamp": datetime, "lines": int, "size": int}}
        self.paste_counter = 0  # NEW: Counter for paste IDs
        self.ignore_patterns = [
            '*.pyc', '__pycache__', '.git', 
            'node_modules', '.env', '*.so', '*.pyc'
        ]
    
    def cd(self, path=None):
        """Change directory dengan validasi"""
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
        
        if not self.path_validator.is_path_allowed(target):
            console.print("[red]❌ Access denied: outside home directory[/red]")
            return False
            
        if not target.exists():
            console.print(f"[red]❌ Directory not found: {target}[/red]")
            return False
            
        if not target.is_dir():
            console.print(f"[red]❌ Not a directory: {target}[/red]")
            return False
        
        self.prev_dir = self.current_dir
        self.current_dir = target
        console.print(f"[green]✓[/green] [dim]{self.current_dir}[/dim]")
        return True
    
    def ls(self, path=None):
        """List directory contents"""
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
    
    def cat(self, filepath):
        """Read file content"""
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
            # Detect jika file code, syntax highlight
            suffix_to_lexer = {                                                    
             '.py': 'python',                                                   
             '.js': 'javascript',                                               
             '.java': 'java',                                                   
             '.cpp': 'cpp',                                                     
             '.c': 'c',                                                         
             '.h': 'c',                                                         
             '.css': 'css',                                                     
             '.html': 'html'                                                    
         }    
            
            if target.suffix in suffix_to_lexer:                                   
                lexer_name = suffix_to_lexer[target.suffix]                        
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
    
    def pwd(self):
        """Print working directory"""
        console.print(f"[cyan]{self.current_dir}[/cyan]")
        return str(self.current_dir)
    
    def tree(self, path=None, max_depth=3, current_depth=0, prefix=""):
        """Display directory tree structure"""
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
    
    def add_to_context(self, pattern):
        """Add file(s) to AI context"""
        if '*' in pattern or '?' in pattern:
            matches = list(self.current_dir.glob(pattern))
        else:
            target = self.current_dir / pattern
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
                    rel_home = path_obj.relative_to(self.home_dir)
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
                    rel_home = file_path.relative_to(self.home_dir)
                    key = f"~/{rel_home}"
                except ValueError:
                    key = str(file_path)  # absolute fallback
                files_dict[key] = content
            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to read {abs_path}: {e}[/yellow]")
        return files_dict

    
    def get_relative_path(self):
        """Get current path relative to home"""
        try:
            rel = self.current_dir.relative_to(self.home_dir)
            return f"~/{rel}" if str(rel) != '.' else "~"
        except ValueError:
            return str(self.current_dir)
    
    def _show_context_summary(self):
        """Show quick summary of context structure"""
        folders = set()
        for name, path in self.context_files.items():
            try:
                rel = path.relative_to(self.current_dir)
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
