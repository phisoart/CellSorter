from typing import Dict

def get_default_card_colors() -> Dict[str, str]:
    """
    Get default light theme colors as fallback.
    Returns:
        Dictionary mapping color variable names to their values
    """
    return {
        'card': 'hsl(0, 0%, 100%)',
        'card_foreground': 'hsl(222.2, 84%, 4.9%)',
        'border': 'hsl(214.3, 31.8%, 91.4%)',
        'accent': 'hsl(210, 40%, 96%)',
        'foreground': 'hsl(222.2, 84%, 4.9%)',
        'muted': 'hsl(210, 40%, 96%)',
    } 