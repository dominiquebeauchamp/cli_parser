try:
    from .cli_arg import cli_arg
    from .types import non_negative_float, non_negative_int
except:
    # package not installed...
    from cli_arg import cli_arg
    from types import non_negative_float, non_negative_int

__version__ = '0.1.0'

__all__ = [
    'cli_arg', 
    'non_negative_int', 
    'non_negative_float'
]
