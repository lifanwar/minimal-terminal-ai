"""
Multi-line paste detection module
"""

def detect_multiline_paste(text):
    """
    Detect if input is a multi-line paste
    
    Args:
        text (str): Input text to check
    
    Returns:
        tuple: (is_paste: bool, stats: dict)
        
    Example:
        >>> is_paste, stats = detect_multiline_paste("line1\\nline2\\nline3")
        >>> print(is_paste)  # True
        >>> print(stats)     # {'lines': 3, 'chars': 18, 'size': '18B'}
    """
    if not text:
        return False, {}
    
    line_count = text.count('\n') + 1
    char_count = len(text)
    
    # Threshold: 3+ lines OR 200+ characters
    is_paste = line_count >= 3 or char_count >= 200
    
    stats = {
        'lines': line_count,
        'chars': char_count,
        'size': format_size(char_count)
    }
    
    return is_paste, stats


def format_size(size):
    """
    Format byte size to human readable string
    
    Args:
        size (int): Size in bytes
    
    Returns:
        str: Formatted size (e.g., "1.5KB", "2.3MB")
    """
    for unit in ['B', 'KB', 'MB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def create_preview(text, max_lines=3):
    """
    Create preview of pasted text with line limit
    
    Args:
        text (str): Full text content
        max_lines (int): Maximum lines to show in preview
    
    Returns:
        str: Preview text with indication of remaining lines
    """
    lines = text.split('\n')
    if len(lines) <= max_lines:
        return text
    
    preview_lines = lines[:max_lines]
    remaining = len(lines) - max_lines
    preview = '\n'.join(preview_lines)
    preview += f"\n... ({remaining} more lines)"
    
    return preview
