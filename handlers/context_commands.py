from rich.console import Console

console = Console()


async def handle_context_command(cmd, args, fs_manager):
    """Handle context management commands"""
    if cmd == '@add':
        if not args:
            console.print("[red]Usage: @add <file_pattern>[/red]")
            return
        fs_manager.add_to_context(args[0])
    
    elif cmd in ['@remove', '@rm']:
        if not args:
            console.print("[red]Usage: @remove <file_pattern>[/red]")
            return
        fs_manager.remove_from_context(args[0])
    
    elif cmd in ['@list', '@ls']:
        fs_manager.list_context()
    
    elif cmd == '@clear':
        fs_manager.context_files.clear()
        console.print("[green]✓ Context cleared[/green]")
    
    else:
        console.print(f"[red]Unknown context command: {cmd}[/red]")
        console.print("[dim]Available: @add, @remove, @list, @clear[/dim]")