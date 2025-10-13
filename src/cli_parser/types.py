import argparse
from pathlib import Path


def non_negative_int(value):
    """
    Parse and validate that a command-line argument value is a non-negative integer.

    This function is intended for use as a type in argparse argument definitions.
    It converts the given value to int and raises an ArgumentTypeError if the value is negative.

    Args:
        value: The value to be validated and converted (str or int).

    Returns:
        int: The validated non-negative integer.

    Raises:
        argparse.ArgumentTypeError: If the value is negative.
    """
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError('Value must be >= 0')
    return ivalue


def non_negative_float(value):
    """
    Parse and validate that a command-line argument value is a non-negative float.

    This function is intended for use as a type in argparse argument definitions.
    It converts the given value to int and raises an ArgumentTypeError if the value is negative.

    Args:
        value: The value to be validated and converted (str or float).

    Returns:
        float: The validated non-negative integer.

    Raises:
        argparse.ArgumentTypeError: If the value is negative.
    """
    if float(value) < 0:
        raise argparse.ArgumentTypeError('Value must be >= 0.0')
    return float(value)


def existing_fits_file_name(value: str) -> str:
    """
    Validate that the argument is the path to an existing FITS file with a valid header.

    This function checks if the given file path exists and verifies that the file begins
    with the standard FITS header line ("SIMPLE  =                    T"). Intended for
    use as a type or validator in argparse argument definitions for FITS files.

    Args:
        value: The file path to validate as a FITS file (str).

    Returns:
        str: The validated file path.

    Raises:
        argparse.ArgumentTypeError: If the file does not exist or does not appear to be a valid FITS file.
    """
    file_path = Path(value).expanduser()
    if not file_path.is_file():
        raise argparse.ArgumentTypeError('Invalid FITS file name: file not found.')
    with open(value, 'rb') as file:
        first_line = file.read(80)
        if not first_line.startswith(b'SIMPLE  =                    T'):
            raise argparse.ArgumentTypeError('Invalid FITS file name: invalid FITS file.')
    return str(file_path)
