"""Defines the common sense rule class."""


class CommonSenseRule:
    """
    A rule brought in from a domain expert.

    Common sense rules can be used to bring in expert knowledge and avoid that common sense rules are generated. Goal is
    to facilitate more focus on rules not known before.
    """

    def __init__(self, antecedents, consequents, confidence=1, database=None):
        """Init."""
        self.antecedents = database.preprocessor.normalize_itemset(antecedents)
        self.consequents = database.preprocessor.normalize_itemset(consequents)
        self.confidence = confidence
        self.database = database

    def __repr__(self):
        """Return a human-friendly string representing the object."""
        if self.database is None:
            item_separator_for_string_outputs = " ∪ "
        else:
            item_separator_for_string_outputs = self.database.settings.item_separator_for_string_outputs
        return (
            f"{item_separator_for_string_outputs.join(self.antecedents)} => "
            f"{item_separator_for_string_outputs.join(self.consequents)} "
            f"({self.confidence})"
        )

    def __eq__(self, other):
        """Check if the given object is equal to this one."""
        if not isinstance(other, CommonSenseRule):
            return False
        return (
            self.antecedents == other.antecedents
            and self.consequents == other.consequents
            and self.confidence == other.confidence
        )

    def __ne__(self, other):
        """Check if the given object is not equal to this one."""
        return not self.__eq__(other)

    def __lt__(self, other):
        """Check if the object is lower than the given object."""
        return (self.antecedents, self.confidence) < (other.antecedents, other.confidence)

    def __le__(self, other):
        """Check if the object is lower than or equal to the given object."""
        return (self.antecedents, self.confidence) <= (other.antecedents, other.confidence)

    def __gt__(self, other):
        """Check if the object is greater than the given object."""
        return (self.antecedents, self.confidence) > (other.antecedents, other.confidence)

    def __ge__(self, other):
        """Check if the object is greater than or equal to the given object."""
        return (self.antecedents, self.confidence) >= (other.antecedents, other.confidence)

    def __hash__(self):
        """Return a hash value for this instance."""
        return hash((chr(0).join(self.antecedents), chr(0).join(self.consequents), self.confidence))
