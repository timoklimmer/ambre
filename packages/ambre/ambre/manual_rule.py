"""Defines the manual rule class."""

class ManualRule:
    """
    A rule brought in from a domain expert.

    Manual rules can be used to bring in expert knowledge and hide common sense knowledge, enabling more focus on
    rules not known before.
    """

    def __init__(self, antecedents, consequents, confidence):
        """Init."""
        self.antecedents = antecedents
        self.consequents = consequents
        self.confidence = confidence