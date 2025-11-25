"""
Handler for multi-line paste with interactive menu
"""

import questionary
from rich.console import Console
from rich.panel import Panel
from lib.paste_detector import create_preview

console = Console()


async def handle_paste(text, fs_manager, stats):
    """
    Handle detected paste with interactive menu
    
    Args:
        text (str): Pasted text content
        fs_manager (FileSystemManager): File system manager instance
        stats (dict): Paste statistics from detector
    
    Returns:
        str: Action taken ('add_and_continue', 'send_as_query', 'discard')
    """
    # Show paste info
    console.print(f"\n[cyan]📋 Detected large text paste ({stats['lines']} lines, {stats['size']})[/cyan]")
    
    # Show preview
    preview = create_preview(text, max_lines=3)
    console.print(Panel(preview, title="Preview", border_style="dim", padding=(0, 1)))
    
    # Interactive menu with arrow navigation (ASYNC VERSION)
    choice = await questionary.select(
        "What would you like to do?",
        choices=[
            "Add to context",
            "Send directly as query",
            "Discard"
        ],
        style=questionary.Style([
            ('selected', 'fg:cyan bold'),
            ('pointer', 'fg:cyan bold'),
            ('highlighted', 'fg:cyan'),
        ])
    ).ask_async()  # CHANGED: use ask_async() instead of ask()
    
    if choice == "Add to context":
        paste_id = fs_manager.add_paste_to_context(text)
        console.print(f"[green]✓ Added as {paste_id} to context[/green]")
        return "add_and_continue"
    
    elif choice == "Send directly as query":
        return "send_as_query"
    
    else:  # Discard
        console.print("[dim]Discarded[/dim]")
        return "discard"