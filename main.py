import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from perplexity_async import Client
from config.cookies.perplexity import perplexity_cookies
from rich.console import Console

from core.filesystem_manager import FileSystemManager
from ui.components import print_header, print_footer
from lib.paste_detector import detect_multiline_paste

# handlers
from handlers.fs_commands import handle_fs_command
from handlers.context_commands import handle_context_command
from handlers.ai_query import handle_ai_query
from handlers.system_commands import execute_system_command
from handlers.paste_handler import handle_paste

console = Console()


async def main():
    console.print("\n[dim]Initializing Perplexity AI Client...[/dim]")
    
    try:
        perplexity_cli = await Client(perplexity_cookies)
        fs_manager = FileSystemManager()
        session = PromptSession(enable_open_in_editor=False)
        
        console.print("[bold green]✓[/bold green] [dim]Client ready![/dim]")
        print_header()
        
        # Main loop
        while True:
            try:
                rel_path = fs_manager.get_relative_path()
                
                # Use prompt_toolkit for better paste handling
                with patch_stdout():
                    user_input = await session.prompt_async(
                        f"\n{rel_path} > ",
                        multiline=False,
                        enable_history_search=False
                    )
                
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                # Detect multi-line paste
                is_paste, stats = detect_multiline_paste(user_input)
                if is_paste:
                    action = await handle_paste(user_input, fs_manager, stats)
                    
                    if action == "add_and_continue":
                        continue
                    elif action == "discard":
                        continue
                    elif action == "send_as_query":
                        await handle_ai_query(user_input, fs_manager, perplexity_cli)
                        continue

                # Check if AI query (starts with .)
                if user_input.startswith('.'):
                    query = user_input[1:].strip()
                    if query:
                        await handle_ai_query(query, fs_manager, perplexity_cli)
                    else:
                        console.print("[yellow]⚠️  Empty AI query[/yellow]")
                    continue
                
                # Parse command
                cmd_parts = user_input.split()
                cmd = cmd_parts[0]
                args = cmd_parts[1:] if len(cmd_parts) > 1 else []
                
                # Handle exit
                if cmd == 'exit':
                    console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                    print_footer()
                    break
                
                # Handle filesystem commands
                elif cmd in ['ls', 'cd', 'pwd', 'cat', 'tree']:
                    await handle_fs_command(cmd, args, fs_manager)
                
                # Handle context commands
                elif cmd.startswith('@'):
                    await handle_context_command(cmd, args, fs_manager)
                
                # Handle system commands (fallback)
                else:
                    execute_system_command(user_input)
                    
            except (EOFError, KeyboardInterrupt):
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                print_footer()
                break
                
    except Exception as e:
        console.print(f"[red]❌ Failed: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]👋 Program terminated. Goodbye![/bold yellow]\n")