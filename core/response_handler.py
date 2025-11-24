import json


def extract_answer_from_response(resp):
    """Extract answer dari Perplexity response"""
    if not resp or 'text' not in resp:
        return "Error: No response from API"
    
    text_content = resp['text']
    
    if isinstance(text_content, list):
        try:
            final_step = next((step for step in text_content 
                             if isinstance(step, dict) and step.get('step_type') == 'FINAL'), None)
            
            if final_step and 'content' in final_step:
                content = final_step['content']
                if isinstance(content, dict) and 'answer' in content:
                    answer_content = content['answer']
                    if isinstance(answer_content, str):
                        try:
                            answer_json = json.loads(answer_content)
                            return answer_json.get('answer', str(answer_json))
                        except:
                            return answer_content
                    elif isinstance(answer_content, dict):
                        return answer_content.get('answer', str(answer_content))
                    else:
                        return str(answer_content)
                return str(content)
            
            elif text_content:
                last_step = text_content[-1]
                if isinstance(last_step, dict) and 'content' in last_step:
                    return str(last_step['content'])
                return str(last_step)
            
            return "Error: Empty steps list"
        except Exception as e:
            return f"Error parsing steps: {str(e)}"
    
    elif isinstance(text_content, str):
        return text_content
    elif isinstance(text_content, dict):
        return str(text_content)
    
    return f"Error: Unknown text format: {type(text_content)}"


def show_search_results_simple(steps, console):
    """Show web sources used"""
    for step in steps:
        if step.get('step_type') == 'SEARCH_RESULTS':
            web_results = []
            if 'content' in step and 'web_results' in step['content']:
                web_results = step['content']['web_results']
            
            if web_results:
                console.print("\n[bold magenta]Web Sources Used:[/bold magenta]")
                for i, r in enumerate(web_results, 1):
                    name = r.get('name', '-')
                    url = r.get('url', '-')
                    domain = url.split('//')[-1].split('/')[0]
                    console.print(f"[bold cyan]{i}.[/bold cyan] [white]{name}[/white] [dim]-[/dim] [yellow]{domain}[/yellow]")
            break