"""Several common helper functions used when working with strings."""

import string

def compress_string(
    string,
    input_alphabet=string.printable,
    output_alphabet="".join((chr(char_number) for char_number in range(0, 256))),
):
    """Compress the given string to a shorter string, using a longer output alphabet than the input alphabet."""
    if input_alphabet is None or output_alphabet is None:
        return string
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
                f"Character '{char}' does not exist in input alphabet '{input_alphabet}'. Ensure that the string "
                f"'{string}' has only valid characters from the input alphabet or extend the input alphabet."
            )
        is_first_char = False
    result = ""
    output_base = len(output_alphabet)
    while cumulated_number > 0:
        result = output_alphabet[cumulated_number % output_base] + result
        cumulated_number //= output_base

    return result


def decompress_string(
    compressed_string,
    original_input_alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    original_output_alphabet="".join((chr(char_number) for char_number in range(0, 256))),
):
    """Decompress the given string to its original value."""
    if original_input_alphabet is None or original_output_alphabet is None:
        return string
    return compress_string(compressed_string, original_output_alphabet, original_input_alphabet)
