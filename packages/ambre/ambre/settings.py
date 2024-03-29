"""Everything related to settings."""

import string

class Settings:
    """Holds all settings at a central place."""

    def __init__(
        self,
        consequents=[],
        normalize_whitespace=True,
        case_insensitive=True,
        max_antecedents_length=None,
        item_separator_for_string_outputs=" ∪ ",
        column_value_separator="=",
        omit_column_names=False,
        item_alphabet=string.printable
    ):
        """Init."""
        self.consequents = sorted(set(consequents))
        self.normalize_whitespace = normalize_whitespace
        self.case_insensitive = case_insensitive
        self.max_antecedents_length = max_antecedents_length
        self.item_separator_for_string_outputs = item_separator_for_string_outputs
        self.column_value_separator = column_value_separator
        self.omit_column_names = omit_column_names
        self.item_alphabet = item_alphabet
        if self.case_insensitive and self.item_alphabet is not None:
            self.item_alphabet = "".join(sorted(set((char.casefold() for char in self.item_alphabet))))

    def __eq__(self, other):
        """Check if the given object is equal to this one."""
        if not isinstance(other, Settings):
            return False
        return (
            self.consequents == other.consequents
            and self.normalize_whitespace == other.normalize_whitespace
            and self.case_insensitive == other.case_insensitive
            and self.max_antecedents_length == other.max_antecedents_length
            and self.item_separator_for_string_outputs == other.item_separator_for_string_outputs
            and self.column_value_separator == other.column_value_separator
            and self.omit_column_names == other.omit_column_names
            and self.item_alphabet == other.item_alphabet
        )

    def __hash__(self):
        """Return a hash value for this instance."""
        return hash(
            chr(0).join(self.consequents),
            self.normalize_whitespace,
            self.case_insensitive,
            self.max_antecedents_length,
            self.item_separator_for_string_outputs,
            self.column_value_separator,
            self.omit_column_names,
            self.item_alphabet
        )
