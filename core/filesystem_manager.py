from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


class FileSystemManager:
    def __init__(self):
        self.home_dir = Path.home()
        self.current_dir = Path.cwd()
        self.prev_dir = self.current_dir
        self.context_files = {}  # {display_name: Path_object}
        self.ignore_patterns = [
            '*.pyc', '__pycache__', '.git', 
            'node_modules', '.env', '*.so', '*.pyc'
        ]
    
    def is_path_allowed(self, target_path):
        """Cek apakah path masih dalam home directory"""
        try:
            resolved = Path(target_path).resolve()
            return resolved.is_relative_to(self.home_dir)
        except Exception:
            return False
    
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
        
        if not self.is_path_allowed(target):
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
        
        if not self.is_path_allowed(target):
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
        
        if not self.is_path_allowed(target):
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
            if target.suffix in ['.py', '.js', '.java', '.cpp', '.c', '.h', '.css', '.html']:
                console.print(Markdown(f"``````"))
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
        
        if not self.is_path_allowed(target):
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
            if match.is_file() and self.is_path_allowed(match):
                if match.stat().st_size > 500_000:
                    console.print(f"[yellow]⚠️  Skipped (too large): {match.name}[/yellow]")
                    continue
                
                if self._is_binary(match):
                    console.print(f"[yellow]⚠️  Skipped (binary): {match.name}[/yellow]")
                    continue
                    
                self.context_files[match.name] = match
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
    
    def list_context(self):
        """Show current context files"""
        if not self.context_files:
            console.print("[dim]No files in context[/dim]")
            return
        
        total_size = sum(f.stat().st_size for f in self.context_files.values())
        console.print(f"[bold cyan]📋 Context ({len(self.context_files)} files, {self._format_size(total_size)})[/bold cyan]")
        
        # Group by folder
        folders = {}
        for name, path in self.context_files.items():
            try:
                rel = path.relative_to(self.current_dir)
                parent = str(rel.parent) if rel.parent != Path('.') else '.'
                if parent not in folders:
                    folders[parent] = []
                folders[parent].append((name, path))
            except:
                if '.' not in folders:
                    folders['.'] = []
                folders['.'].append((name, path))
        
        for folder in sorted(folders.keys()):
            if folder != '.':
                console.print(f"\n[dim]{folder}/[/dim]")
            for name, path in folders[folder]:
                size = self._format_size(path.stat().st_size)
                console.print(f"  [white]• {name}[/white] [dim]({size})[/dim]")
    
    def get_context_for_api(self):
        """Build dict untuk dikirim ke Perplexity API"""
        files_dict = {}
        
        for display_name, file_path in self.context_files.items():
            try:
                content = file_path.read_text(encoding='utf-8')
                rel_path = file_path.relative_to(self.current_dir)
                files_dict[str(rel_path)] = content
            except Exception as e:
                console.print(f"[yellow]⚠️  Failed to read {display_name}: {e}[/yellow]")
        
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
    
    def _is_binary(self, filepath):
        """Check if file is binary"""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return True
    
    @staticmethod
    def _format_size(size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
