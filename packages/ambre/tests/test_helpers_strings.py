"""Test the helper functions provided by the strings helper module."""

import pytest
from ambre.strings import compress_string, decompress_string


def test_roundtrip_no_custom_alphabet():
    """Test if a string is correctly compressed and decompressed, without custom alphabet."""
    string_to_compress = "Hello world!"
    assert decompress_string(compress_string(string_to_compress)) == string_to_compress


def test_roundtrip_custom_input_alphabet():
    """Test if a string is correctly compressed and decompressed, using a custom alphabet."""
    string_to_compress = "A123456789"
    custom_input_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    compressed_string = compress_string(string_to_compress, input_alphabet=custom_input_alphabet)
    decompressed_string = decompress_string(compressed_string, original_input_alphabet=custom_input_alphabet)
    assert decompressed_string == string_to_compress
    assert len(compressed_string) <= len(string_to_compress)

def test_roundtrip_begins_with_first_char_in_alphabet():
    """Test if the roundtrip works when the first char is the first char from the alphabet."""
    string_to_compress = "0A"
    custom_input_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    compressed_string = compress_string(string_to_compress, input_alphabet=custom_input_alphabet)
    decompressed_string = decompress_string(compressed_string, original_input_alphabet=custom_input_alphabet)
    assert decompressed_string == string_to_compress

def test_if_throws_when_input_char_out_of_alphabet():
    """Test if a ValueError is thrown when a char shall be compressed that is not included in the input alphabet."""
    with pytest.raises(
        ValueError,
        match=("Character 'e' does not exist in input alphabet '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'."),
    ):
        string_to_compress = "Hello world!"
        custom_input_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        compress_string(string_to_compress, input_alphabet=custom_input_alphabet)


def test_none_input_alphabet():
    """Test if compression works when input alphabet = None is specified."""
    string_to_compress = "A01"
    custom_input_alphabet = None
    compressed_string = compress_string(string_to_compress, input_alphabet=custom_input_alphabet)
    decompressed_string = decompress_string(compressed_string, original_input_alphabet=custom_input_alphabet)
    assert compressed_string == decompressed_string
