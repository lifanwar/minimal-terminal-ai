from rich.console import Console

console = Console()


async def handle_fs_command(cmd, args, fs_manager):
    """Handle filesystem commands"""
    if cmd == 'ls':
        path = args[0] if args else None
        fs_manager.ls(path)
    
    elif cmd == 'cd':
        path = args[0] if args else None
        fs_manager.cd(path)
    
    elif cmd == 'pwd':
        fs_manager.pwd()
    
    elif cmd == 'cat':
        if not args:
            console.print("[red]Usage: cat <filename>[/red]")
            return
        fs_manager.cat(args[0])
    
    elif cmd == 'tree':
        path = args[0] if args else None
        fs_manager.tree(path)