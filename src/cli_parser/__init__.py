try:
    from .cli_arg import cli_arg
except:
    # package not installed...
    from cli_arg import cli_arg

__version__ = '0.1.0'

__all__ = ['cli_arg']
