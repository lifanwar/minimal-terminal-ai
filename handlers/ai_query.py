from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.rule import Rule
from rich.markdown import Markdown

from core.response_handler import extract_answer_from_response, show_search_results_simple

console = Console()


async def handle_ai_query(query, fs_manager, perplexity_cli):
    """Handle AI query dengan file context"""
    files_dict = fs_manager.get_context_for_api()
    
    if files_dict:
        console.print(f"[dim]Sending query with {len(files_dict)} file(s) in context...[/dim]")
    
    try:
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing query...", total=None)
            
            resp = await perplexity_cli.search(
                query,
                mode='pro',
                model='gpt-5.1',
                sources=['web'],
                files=files_dict,
                stream=False,
                incognito=True
            )
            
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