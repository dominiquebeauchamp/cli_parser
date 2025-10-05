#!/usr/bin/env python
from typing import Callable, ParamSpec, TypeVar, Tuple
from functools import wraps, WRAPPER_ASSIGNMENTS
import argparse
import json
from pathlib import Path
import sys
import re
import textwrap
import io
from contextlib import redirect_stdout
import os
import subprocess


P = ParamSpec('P')
R = TypeVar('R')


def _get_orig_func(func: Callable[P, R], 
                   *decorator_args: P.args, 
                   **decorator_kwargs: P.kwargs) -> Callable[P, R]:
    """
    Retrieve the original undecorated function and record CLI argument metadata.

    This function walks through any wrappers (produced by this module's decorators)
    to access the original function. It initializes and appends to the `_cli_arguments`
    attribute, storing information about CLI arguments for later retrieval when
    parsing command line input.

    Args:
        func: The function to unwrap and annotate.
        *decorator_args: Positional CLI argument definitions.
        **decorator_kwargs: Keyword CLI argument definitions.

    Returns:
        The original undecorated function with enriched CLI arguments metadata.
    """
    orig_func = getattr(func, '__wrapped__', func)
    if not hasattr(orig_func, '_cli_arguments'):
        orig_func._cli_arguments = []
    orig_func._cli_arguments.append((decorator_args, decorator_kwargs))

    return orig_func


def _get_arguments_file_path(orig_func: Callable[P, R]) -> Path:
    """
    Construct the file path for saving or loading CLI parameters for a function.

    The path is built based on the function's Python qualified name, and the user's 
    home directory, enabling uniquely identifying each function's parameter set.

    Args:
        orig_func: The function whose settings file location is calculated.
    Returns:
        Path object for the arguments file location.
    """
    func_name = orig_func.__qualname__ if hasattr(orig_func, '__qualname__') else orig_func.__name__
    file_path = (Path('~').expanduser() / '.params' / __package__ / func_name).with_suffix('.par')
    return file_path


def _save_arguments(orig_func: Callable[P, R],
                    arguments: dict):
    """
    Save CLI argument values for a function to a persistent file.

    Serializes the argument dictionary as JSON and writes it to a file
    in the user's home directory, using a path derived from the function's metadata.
    Creates intermediate directories as needed.
    
    Args:
        orig_func: The function for which arguments are stored.
        arguments: Dictionary of parsed/used arguments to persist.
    """
    file_path = _get_arguments_file_path(orig_func)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as args_file:
        json.dump(arguments, args_file, ensure_ascii=False, indent=4)


def _load_arguments(orig_func: Callable[P, R]) -> dict:
    """
    Load previously saved CLI argument values for a function from file.

    If the arguments file exists for the provided function, parses and returns
    its JSON contents as a dictionary. Otherwise, returns an empty dictionary.

    Args:
        orig_func: The function whose arguments to attempt to load.
    Returns:
        Dictionary of arguments if present, else empty dict.
    """
    file_path = _get_arguments_file_path(orig_func)
    if file_path.is_file():
        with open(file_path, 'r', encoding='utf-8') as args_file:
            arguments = json.load(args_file)
        return arguments
    return {}


def _edit_arguments(orig_func: Callable[P, R]):
    """
    Opens the saved CLI arguments file for the specified function in the text editor defined by the EDITOR environment variable.

    This function allows the user to manually edit the parameters file associated with the given function,
    launching the text editor configured via the EDITOR environment variable. The file is only opened for editing
    if it already exists.

    Args:
        orig_func: The function whose saved CLI parameters should be edited.

    Note:
        If the EDITOR environment variable is not set, or if the parameter file does not exist, nothing will be launched.
    """
    default_editor = os.environ.get('EDITOR', default=None)
    if default_editor is not None:
        file_path = _get_arguments_file_path(orig_func)
        if file_path.is_file():
            default_editor_splitted = default_editor.split(' ')
            cmd = default_editor_splitted
            cmd.append(str(file_path))
            proc_result = subprocess.run(cmd)


def _get_man_page(orig_func: Callable[P, R]) -> Tuple[str, str, str]:
    """
    Extract a structured manual page (man page) from the special comment sections
    in the provided function's docstring.

    The function will attempt to extract sections such as NAME, DESCRIPTION, EXAMPLES,
    AUTHOR, REPORTING BUGS, COPYRIGHT, and SEE ALSO by searching for specific markers
    in the docstring. These sections are then formatted appropriately for display as
    a help/man page.

    Args:
        orig_func: The function whose docstring is parsed for man page contents.

    Returns:
        Tuple of three strings: prolog (NAME/SYNOPSIS), midlog (DESCRIPTION), epilog (all others).
    """
    # #NAME {{{short description}}}
    res = re.search(r'#NAME\s+{{{(?P<shortdesc>(?:(?!}}}).)+)',
                    orig_func.__doc__,
                    re.MULTILINE)
    prolog = f'NAME\n\t{orig_func.__qualname__} - ' +\
        res.group('shortdesc') if res is not None else '...'
    
    prolog += '\n\nSYNOPSIS\n'

    midlog = f'\t       {orig_func.__qualname__} % \n\t\t# Reuse the previously used arguments.\n'

    # #DESCRIPTION {{{description}}}
    res = re.search(r'#DESCRIPTION\s+{{{(?P<desc>(?:(?!}}}).)+)',
                    orig_func.__doc__,
                    re.MULTILINE | re.DOTALL)
    midlog += '\nDESCRIPTION\n' + textwrap.indent(textwrap.dedent(res.group('desc') + '\n') if res is not None else '...\n', '\t')

    # #EXAMPLES {{{examples}}}
    res = re.search(r'#EXAMPLES\s+{{{(?P<examples>(?:(?!}}}).)+)',
                    orig_func.__doc__,
                    re.MULTILINE | re.DOTALL)
    epilog = 'EXAMPLES\n' + textwrap.indent(textwrap.dedent(res.group('examples' + '\n')) if res is not None else '...\n', '\t')
    
    # #AUTHOR {{{author}}}
    res = re.search(r'#AUTHOR\s+{{{(?P<author>(?:(?!}}}).)+)',
                    orig_func.__doc__,
                    re.MULTILINE | re.DOTALL)
    epilog += '\nAUTHOR\n' + textwrap.indent(textwrap.dedent(res.group('author') + '\n') if res is not None else '...\n', '\t')
    
    # #REPORTING_BUGS {{{reporting_bugs}}}
    res = re.search(r'#REPORTING_BUGS\s+{{{(?P<reporting_bugs>(?:(?!}}}).)+)',
                    orig_func.__doc__,
                    re.MULTILINE | re.DOTALL)
    epilog += '\nREPORTING BUGS\n' + textwrap.indent(textwrap.dedent(res.group('reporting_bugs' + '\n')) if res is not None else '...\n', '\t')
    
    # #COPYRIGHT {{{copyright}}}
    res = re.search(r'#COPYRIGHT\s+{{{(?P<copyright>(?:(?!}}}).)+)',
                    orig_func.__doc__,
                    re.MULTILINE | re.DOTALL)
    epilog += '\nCOPYRIGHT\n' + textwrap.indent(textwrap.dedent(res.group('copyright') + '\n') if res is not None else '...\n', '\t')
    
    # #SEE_ALSO {{{see_also}}}
    res = re.search(r'#SEE_ALSO\s+{{{(?P<see_also>(?:(?!}}}).)+)',
                    orig_func.__doc__,
                    re.MULTILINE | re.DOTALL)
    epilog += '\nSEE ALSO\n' + textwrap.indent(textwrap.dedent(res.group('see_also') + '\n') if res is not None else '...\n', '\t')

    return prolog, midlog, epilog


def _get_cli_arg_wrapper(func: Callable[P, R], 
                         orig_func: Callable[P, R]) -> Callable[P, R]:
    """
    Build a callable wrapper that enables CLI argument parsing and invocation.

    The wrapper sets up argument parsing from collected metadata, manages help display
    or error reporting, supports manual page rendering, loads and saves parameter files, and
    finally dispatches all parsed inputs to the decorated function.
    
    Args:
        func: The function currently being wrapped (may already be decorated).
        orig_func: The underlying, undecorated function with argument metadata.
    Returns:
        A callable wrapping the original which provides CLI support.
    """
    @wraps(func, assigned=WRAPPER_ASSIGNMENTS)
    def wrapper():
        prolog, midlog, epilog = _get_man_page(orig_func)

        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         formatter_class=argparse.RawDescriptionHelpFormatter)

        if len(sys.argv) == 2 and sys.argv[1] == '%':
            # Edit the arguments in a text editor prior to loading them here.
            _edit_arguments(orig_func)
            
            # Load arguments from ~/.params... file when there is only one argument: "#"
            parsed = _load_arguments(orig_func)
        else:
            # Get the arguments from the original function attribute _cli_arguments
            cli_arguments = orig_func._cli_arguments

            # Iterate over the arguments in the order decorators are stacked.
            for args, kwargs in cli_arguments:
                parser.add_argument(*args, **kwargs)

            # Redirect stdout to buffer to prevent help to be written by parse_args().
            buffer = io.StringIO()
            try:
                with redirect_stdout(buffer):
                    # Actual CLI arguments parsing.
                    parsed = vars(parser.parse_args())
            except SystemExit:
                #Print help when parse_args() raise a SystemExit.
                print(prolog)
                print(textwrap.indent(parser.format_usage(), '\t'))
                print(midlog)
                print(textwrap.indent(parser.format_help(), '\t'))
                print(epilog)
                sys.exit()

        # Save the arguments to ~/.params...
        _save_arguments(orig_func, parsed)

        # Actual original function call and return.
        return orig_func(**parsed)

    return wrapper


def cli_arg(*decorator_args: P.args,
            **decorator_kwargs: P.kwargs) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator factory for attaching CLI (command-line) arguments to a Python function.

    This decorator can be stacked multiple times to assign several CLI parameters and
    their parsing rules to the same function. It stores all CLI argument metadata so that,
    when the function is executed, arguments are parsed, injected as keyword arguments, and
    optionally loaded or saved to disk for repeatability.
    
    Args:
        *decorator_args: Positional CLI argument definitions as accepted by argparse.
        **decorator_kwargs: Keyword CLI argument definitions as accepted by argparse.
    Returns:
        A decorator which wraps the function to add CLI-parsing behavior.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        Inner decorator that attaches and manages CLI arguments metadata, wrapping with CLI support only if needed.

        If the function is already wrapped (by this decorator), it is not re-wrapped, otherwise the
        CLI argument parsing wrapper is applied, using all accumulated CLI argument data.

        Args:
            func: Function to decorate for CLI usage.
        Returns:
            The wrapped function, now supporting CLI parsing and argument injection.
        """
        orig_func = _get_orig_func(func, *decorator_args, **decorator_kwargs)

        # Wrap only once.
        if getattr(func, '_is_cli_wrapper', False):
            return func

        wrapper = _get_cli_arg_wrapper(func, orig_func)

        wrapper._is_cli_wrapper = True  # Flag that indicates it is already wrapped.

        # The wrapped function is the original function.
        wrapper.__wrapped__ = orig_func

        return wrapper
    
    return decorator

#%% Rest of the code = demo
#
@cli_arg('--foo', type=int, required=True, help='Le nombre foo')
@cli_arg('--bar', default='abc', help='La chaîne bar')
@cli_arg('names', type=str, nargs='*')
def my_function(bar, foo, names):
    """Exemple de fonction principale utilisant des arguments CLI.
    
    #NAME {{{Exemple de fonction principale utilisant des arguments CLI.}}}

    #DESCRIPTION
    {{{
    Test function
    }}}
    
    
Beauchamp"""
    print(f'foo = {foo}, bar = {bar}')
    for name in names:
        print(name)


if __name__ == '__main__':
    my_function()
