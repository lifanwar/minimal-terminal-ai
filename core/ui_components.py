from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from datetime import datetime

console = Console()


def print_header():
    """Print terminal header"""
    title = Text("🤖 Perplexity AI Terminal", style="bold cyan")
    subtitle = Text("Interactive Filesystem + AI Query", style="dim")
    header_panel = Panel(
        Align.center(Text.assemble(title, "\n", subtitle)),
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print(header_panel)
    console.print(Rule(style="dim"))


def print_footer():
    """Print terminal footer"""
    timestamp = Text(
        f"Session ended at {datetime.now().strftime('%H:%M:%S')}", 
        style="dim"
    )
    footer_panel = Panel(
        Align.center(timestamp),
        border_style="dim",
        padding=(0, 1)
    )
    console.print(footer_panel)