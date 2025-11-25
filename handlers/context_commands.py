"""
Context management commands handler
"""

from rich.console import Console

console = Console()


async def handle_context_command(cmd, args, fs_manager):
    """
    Handle @-prefixed context commands
    
    Commands:
        @add <pattern>   - Add files to context
        @remove <pattern> - Remove files/pastes from context
        @list            - List all context items
        @clear           - Clear all context (files + pastes)
    """
    
    if cmd == '@add':
        if not args:
            console.print("[yellow]Usage: @add <pattern>[/yellow]")
            console.print("[dim]Example: @add *.py[/dim]")
            return
        pattern = ' '.join(args)
        fs_manager.add_to_context(pattern)
    
    elif cmd == '@remove':
        if not args:
            console.print("[yellow]Usage: @remove <pattern>[/yellow]")
            console.print("[dim]Example: @remove *.py or @remove paste_001[/dim]")
            return
        pattern = ' '.join(args)
        
        # Check if removing paste by ID
        if pattern.startswith('paste_'):
            if fs_manager.remove_paste_from_context(pattern):
                console.print(f"[green]✓ Removed {pattern} from context[/green]")
            else:
                console.print(f"[yellow]⚠️  Paste not found: {pattern}[/yellow]")
        else:
            # Remove file pattern
            fs_manager.remove_from_context(pattern)
    
    elif cmd in ['@list', '@ls']:
        fs_manager.list_context()
    
    elif cmd == '@clear':
        # Clear both files and pastes
        file_count = len(fs_manager.context_files)
        paste_count = len(fs_manager.paste_contexts)
        
        fs_manager.context_files.clear()
        fs_manager.paste_contexts.clear()
        
        total = file_count + paste_count
        console.print(f"[green]✓ Cleared {total} item(s) from context ({file_count} files, {paste_count} pastes)[/green]")
    
    else:
        console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
        console.print("[dim]Available: @add, @remove, @list/@ls, @clear[/dim]")
