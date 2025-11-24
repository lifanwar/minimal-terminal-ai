"""
System command executor with user shell environment
"""

import subprocess
import os
from rich.console import Console

console = Console()


def execute_system_command(command):
    """
    Execute system command in user's configured shell environment
    """
    try:
        # Show command being executed
        console.print(f"[dim]$ {command}[/dim]")
        
        # Detect user's shell
        user_shell = os.environ.get('SHELL', '/bin/bash')
        
        # Build command that sources shell config
        # For interactive-like behavior, use -i flag or source config
        if 'zsh' in user_shell:
            # For zsh: source .zshrc
            wrapped_cmd = f'source ~/.zshrc 2>/dev/null; {command}'
        elif 'bash' in user_shell:
            # For bash: source .bashrc
            wrapped_cmd = f'source ~/.bashrc 2>/dev/null; {command}'
        else:
            # Fallback: just run command
            wrapped_cmd = command
        
        # Execute command
        result = subprocess.run(
            wrapped_cmd,
            shell=True,
            executable=user_shell,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Display output
        if result.stdout:
            console.print(result.stdout, end='')
        
        # Display errors
        if result.stderr:
            # Some commands write to stderr even on success
            if result.returncode == 0:
                # Success but has stderr (warnings, etc)
                console.print(f"[yellow]{result.stderr}[/yellow]", end='')
            else:
                # Actual error
                console.print(f"[red]{result.stderr}[/red]", end='')
        
        # Show return code if non-zero
        if result.returncode != 0:
            console.print(f"[yellow]⚠️  Exit code: {result.returncode}[/yellow]")
            
    except subprocess.TimeoutExpired:
        console.print("[red]❌ Command timeout (30s limit)[/red]")
    except FileNotFoundError:
        console.print(f"[red]❌ Command not found: {command.split()[0]}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")