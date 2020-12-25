"""Everything related to settings."""

class Settings:
    """Holds all settings at a central place."""

    def __init__(
        self,
        consequents=[],
        normalize_whitespace=True,
        case_insensitive=True,
        max_antecedents_length=None,
        item_separator_for_string_outputs=" ∪ ",
    ):
        """Init."""
        self.consequents = consequents
        self.normalize_whitespace = normalize_whitespace
        self.case_insensitive = case_insensitive
        self.max_antecedents_length = max_antecedents_length
        self.item_separator_for_string_outputs = item_separator_for_string_outputs
