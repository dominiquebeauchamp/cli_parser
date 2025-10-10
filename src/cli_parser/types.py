import argparse

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