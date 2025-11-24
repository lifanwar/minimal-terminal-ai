import asyncio
from perplexity_async import Client
from config.cookies.perplexity import perplexity_cookies
from rich.console import Console

from core.filesystem_manager import FileSystemManager
from core.ui_components import print_header, print_footer
from handlers.fs_commands import handle_fs_command
from handlers.context_commands import handle_context_command
from handlers.ai_query import handle_ai_query

console = Console()


async def main():
    console.print("\n[dim]Initializing Perplexity AI Client...[/dim]")
    
    try:
        perplexity_cli = await Client(perplexity_cookies)
        fs_manager = FileSystemManager()
        
        console.print("[bold green]✓[/bold green] [dim]Client ready![/dim]")
        print_header()
        
        # Main loop
        while True:
            rel_path = fs_manager.get_relative_path()
            console.print(f"\n[dim]{rel_path}[/dim]", end="")
            user_input = console.input(" [bold green]>[/bold green] ").strip()
            
            if not user_input:
                continue
            
            cmd_parts = user_input.split()
            cmd = cmd_parts[0]
            args = cmd_parts[1:] if len(cmd_parts) > 1 else []
            
            if cmd == 'exit':
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                print_footer()
                break
            
            elif cmd in ['ls', 'cd', 'pwd', 'cat', 'tree']:
                await handle_fs_command(cmd, args, fs_manager)
            
            elif cmd.startswith('@'):
                await handle_context_command(cmd, args, fs_manager)
            
            else:
                # AI query
                await handle_ai_query(user_input, fs_manager, perplexity_cli)
                
    except Exception as e:
        console.print(f"[red]❌ Failed: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]👋 Program terminated. Goodbye![/bold yellow]\n")