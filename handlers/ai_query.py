"""
AI query handler with context support
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.rule import Rule
from rich.markdown import Markdown

from core.response_handler import extract_answer_from_response, show_search_results_simple

console = Console()

async def handle_ai_query(query, fs_manager, perplexity_cli):
    """
    Handle AI query dengan file context dan paste context
    
    Strategy:
    - Files: Embed sebagai context di query (seperti paste)
    - Pastes: Embed directly into query text
    
    Args:
        query (str): User query
        fs_manager (FileSystemManager): Filesystem manager instance
        perplexity_cli (Client): Perplexity API client
    """
    # Get context
    file_count = len(fs_manager.context_files)
    paste_count = len(fs_manager.paste_contexts)
    total_items = file_count + paste_count
    
    # Show what's being sent
    if total_items > 0:
        console.print(f"[dim]Sending query with {total_items} item(s) in context ({file_count} files, {paste_count} pastes)...[/dim]")
    
    try:
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing query...", total=None)
            
            # ✅ BUILD CONTEXT dari files + pastes
            context_parts = []
            
            if fs_manager.context_files:
                for abs_path, file_path in fs_manager.context_files.items():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        # Display dengan path yang jelas
                        display_name = abs_path.replace(str(fs_manager.home_dir), '~')
                        context_parts.append(f"```{display_name}\n{content}\n```")
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Failed to read {abs_path}: {e}[/yellow]")

            
            # Add paste contexts
            if fs_manager.paste_contexts:
                for paste_id, data in fs_manager.paste_contexts.items():
                    content = data['content']
                    lines = data['lines']
                    context_parts.append(f"```{paste_id} ({lines} lines)\n{content}\n```")
            
            # Build final query dengan context
            if context_parts:
                context_block = "\n\n".join(context_parts)
                final_query = f"{context_block}\n\n---\n\n{query}"
                console.print(f"[dim]Embedded {total_items} item(s) into query[/dim]")
            else:
                final_query = query
            
            # Build API call parameters (NO files parameter)
            api_params = {
                'mode': 'pro',
                'model': 'gpt-5.1',
                'sources': ['web'],
                'stream': True,
                'incognito': True
            }
            
            # Send query
            resp = await perplexity_cli.search(final_query, **api_params)
            
            # Process response
            all_steps = []
            if hasattr(resp, '__aiter__'):
                async for chunk in resp:
                    if isinstance(chunk, dict) and 'text' in chunk:
                        if isinstance(chunk['text'], list):
                            all_steps.extend(chunk['text'])
            elif isinstance(resp, dict):
                if 'text' in resp and isinstance(resp['text'], list):
                    all_steps.extend(resp['text'])
            
            progress.remove_task(task)
        
        # Show results
        show_search_results_simple(all_steps, console)
        answer = extract_answer_from_response({'text': all_steps})
        
        console.print(Rule(title="Answer", style="bright_green"))
        if isinstance(answer, str) and '```':
            console.print(Markdown(answer))
        else:
            console.print(Panel(answer, border_style="bright_blue", padding=(1,2)))
        console.print(Rule(style="bright_green"))
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
