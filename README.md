# cli_parser

A Python framework that lets you define CLI argument parsers with simple, composable decorators.

## Overview

This project allows you to declare command-line arguments directly on functions using the `@cli_arg` decorator. Argument metadata is attached and later used to generate an argparse-powered CLI automatically, while supporting persistent parameter files and nicely formatted help/man pages generated from docstrings.

## Features

- **Declarative CLI**: Stack multiple `@cli_arg` decorators to define positional and optional arguments.
- **Automatic Help/Man Pages**: Extracts help sections from docstrings for rich manual pages.
- **Parameter Persistence**: Arguments can be saved and re-used transparently via parameter files.
- **No boilerplate**: Skip repetitive argparse setup—focus on your business logic.

## Installation

You can install it as a package (instructions to be added once published).

## Usage

### Example

```python
from cli_parser import cli_arg

@cli_arg('--foo', type=int, required=True, help='The foo number')
@cli_arg('--bar', default='abc', help='The bar string')
@cli_arg('names', type=str, nargs='*')
def my_function(bar, foo, names):
    """
    #NAME {{{Main function example using CLI arguments}}}

    #DESCRIPTION
    {{{
    Test function that prints given arguments.
    }}}
    """
    print(f'foo = {foo}, bar = {bar}')
    for name in names:
        print(name)

if __name__ == '__main__':
    my_function()
```

#### Example CLI Usages

```bash
python my_script.py --foo 42 --bar hello Alice Bob Charlie
python my_script.py --foo 99
```

## How It Works

- Decorate your main function (or any function) with `@cli_arg(...)` for each CLI argument or option.
- The decorator attaches metadata about arguments; when your function is called, arguments are parsed and injected automatically.
- Docstrings with special sections (e.g., `#NAME`, `#DESCRIPTION`, etc.) are parsed to generate rich help and man pages.
- Arguments are persisted in a per-function file inside your home directory for reusability.

## Docstring Man Page Sections

In your function docstring, you can use special blocks to define man page sections:

```
#NAME {{{Short description}}}
#DESCRIPTION {{{Detailed description}}}
#EXAMPLES {{{Usage examples}}}
#AUTHOR {{{Author(s)}}}
#REPORTING_BUGS {{{Contact or link for bug reports}}}
#COPYRIGHT {{{Copyright information}}}
#SEE_ALSO {{{Related tools}}}