"""Defines the common sense rule class."""

class CommonSenseRule:
    """
    A rule brought in from a domain expert.

    Common sense rules can be used to bring in expert knowledge and avoid that common sense rules are generated. Goal is
    to facilitate more focus on rules not known before.
    """

    def __init__(self, antecedents, consequents, confidence):
        """Init."""
        self.antecedents = antecedents
        self.consequents = consequents
        self.confidence = confidence
