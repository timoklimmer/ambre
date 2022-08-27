"""Several common helper functions used when working with strings."""

import string

DEFAULT_INPUT_ALPHABET = string.printable


def compress_string(string, input_alphabet=DEFAULT_INPUT_ALPHABET):
    """
    Compress the given string to a shorter string.

    Basic approach: Represent chars in a different system of numeration such that we don't waste space for unused chars.
    """
    if input_alphabet is None:
        return string
    if chr(255) in input_alphabet:
        raise ValueError(
            (
                "chr(255) as input character is invalid. Ensure that the string to be compressed does not include a "
                "char with ASCII code 255."
            )
        )
    input_alphabet = chr(255) + input_alphabet
    input_base = len(input_alphabet)
    cumulated_number = 0
    is_first_char = True
    for char in string:
        position_in_input_alphabet = input_alphabet.find(char)
        if position_in_input_alphabet >= 0:
            cumulated_number = cumulated_number * input_base + position_in_input_alphabet
            if is_first_char and cumulated_number == 0:
                cumulated_number = input_base
        else:
            raise ValueError(
                f"Character '{char}' does not exist in input alphabet '{input_alphabet[1:]}'. Ensure that the string "
                f"'{string}' has only valid characters from the input alphabet or extend the input alphabet."
            )
        is_first_char = False
    result = ""
    output_base = 256
    while cumulated_number > 0:
        result = chr(cumulated_number % output_base) + result
        cumulated_number //= output_base
    return result


def decompress_string(compressed_string, original_input_alphabet=DEFAULT_INPUT_ALPHABET):
    """Decompress the given string to its original value."""
    if original_input_alphabet is None:
        return compressed_string
    original_input_alphabet = chr(255) + original_input_alphabet
    input_base = 256
    cumulated_number = 0
    is_first_char = True
    for char in compressed_string:
        position_in_input_alphabet = ord(char)
        if position_in_input_alphabet >= 0:
            cumulated_number = cumulated_number * input_base + position_in_input_alphabet
            if is_first_char and cumulated_number == 0:
                cumulated_number = input_base
        else:
            raise ValueError(
                f"Character '{char}' does not exist in original input alphabet '{original_input_alphabet[1:]}'. Ensure "
                f"that the string '{string}' contains only valid characters."
            )
        is_first_char = False
    result = ""
    output_base = len(original_input_alphabet)
    while cumulated_number > 0:
        result = original_input_alphabet[cumulated_number % output_base] + result
        cumulated_number //= output_base
    return result
