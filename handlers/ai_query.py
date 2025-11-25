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
    - Files: Send via 'files' parameter (actual file upload)
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
            
            # Prepare files for upload (only actual files, not pastes)
            files_for_upload = {}
            for display_name, file_path in fs_manager.context_files.items():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    # Gunakan display_name atau basename file sebagai key
                    files_for_upload[display_name] = content
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed to read {display_name}: {e}[/yellow]")

            
            # Prepare query with embedded paste contexts
            final_query = query
            if paste_count > 0:
                paste_parts = []
                for paste_id, data in fs_manager.paste_contexts.items():
                    paste_parts.append(f"--- Context: {paste_id} ---\n{data['content']}\n")
                
                paste_context = "\n".join(paste_parts)
                final_query = f"{paste_context}\n--- User Question ---\n{query}"
                
                console.print(f"[dim]Embedded {paste_count} paste(s) into query[/dim]")
            
            if files_for_upload:
                console.print(f"[dim]Uploading {len(files_for_upload)} file(s): {', '.join(files_for_upload.keys())}[/dim]")
            
            # Build API call parameters
            api_params = {
                'mode': 'pro',
                'model': 'gpt-5.1',
                'sources': ['web'],
                'stream': False,
                'incognito': True
            }
            
            # Only add files parameter if there are actual files (not pastes)
            if files_for_upload:
                api_params['files'] = files_for_upload
            
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
