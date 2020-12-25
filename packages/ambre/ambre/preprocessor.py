"""Defines the Preprocessor class."""

import re


class Preprocessor:
    """Preprocesses (mostly) incoming data."""

    def __init__(self, settings):
        """Init."""
        self.settings = settings
        self.normalized_consequents = sorted(
            self.normalize_itemset(self.settings.consequents, sort_result=False)
        )  # need to normalize first before sorting due to dependency on normalized item values in sort function

    def normalize_itemset(self, itemset, sort_result=True):
        """Normalize the given itemset (any iterable)."""
        if self.settings.normalize_whitespace:
            itemset = [re.sub(r"\s+", " ", item).strip() for item in itemset]
        if self.settings.case_insensitive:
            itemset = [item.lower() for item in itemset]
        itemset = set(itemset)
        if sort_result:
            itemset = self.sort_itemset_consequents_first(itemset)
        return itemset

    def sort_itemset_consequents_first(self, itemset):
        """Sort the given itemset so we have the consequents first, followed by the antecedents."""
        consequents, antecedents = self.extract_consequents_antecedents(itemset, sort_result=True)
        return consequents + antecedents

    def extract_consequents_antecedents(self, itemset, sort_result=True):
        """Extract consequents and antecedents from the given itemset."""
        result_consequents, result_antecedents = [], []
        for item in itemset:
            if item in self.normalized_consequents:
                result_consequents.append(item)
            else:
                result_antecedents.append(item)
        if sort_result:
            result_consequents.sort(key=str.casefold)
            result_antecedents.sort(key=str.casefold)
        return result_consequents, result_antecedents

    def is_consequent(self, item, is_normalized=True):
        """Check if the specified item is a consequent."""
        if not is_normalized:
            item = self.normalize_itemset([item], sort_result=False)
        return item in self.normalized_consequents

    def itemset_to_string(self, itemset):
        """Convert the given itemset to a string."""
        return self.settings.item_separator_for_string_outputs.join(itemset)

    def string_to_itemset_set(self, string):
        """Convert the given string to a set of items."""
        return set(string.split(self.settings.item_separator_for_string_outputs))
