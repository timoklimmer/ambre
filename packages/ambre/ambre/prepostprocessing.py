"""Defines the PrePostProcessor class."""

import re
from ambre.settings import Settings
from .helpers.strings import compress_string, decompress_string


class PrePostProcessor:
    """Pre- and post-processes in- and outgoing data."""

    def __init__(self, settings: Settings):
        """Init."""
        self.settings = settings
        # note: need to sort here on our own here because other provided sorting functions rely on the list computed
        #       here
        self.normalized_consequents = sorted(
            self.normalize_uncompressed_itemset(self.settings.consequents, sort_result=False)
        )
        self.compressed_consequents = self.compress_itemset(self.normalized_consequents)

    def normalize_uncompressed_itemset(self, itemset, sort_result=True):
        """Normalize the given itemset (any iterable)."""
        if self.settings.normalize_whitespace:
            itemset = (re.sub(r"\s+", " ", item).strip() for item in itemset)
        if self.settings.case_insensitive:
            itemset = (item.lower() for item in itemset)
        itemset = set(itemset)
        if sort_result:
            itemset = self.sort_and_move_consequents_first(itemset)
        return itemset

    def sort_and_move_consequents_first(self, itemset):
        """Sort the given itemset so we have the consequents first, followed by the antecedents."""
        consequents, antecedents = self.extract_consequents_antecedents_compressed_from_uncompressed(
            itemset, sort_result=True
        )
        return consequents + antecedents

    def extract_consequents_antecedents_compressed_from_uncompressed(self, itemset, sort_result=True):
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

    def remove_column_names_from_uncompressed_itemset(self, uncompressed_itemset):
        """Remove column names from items in given uncompressed itemset."""
        return [
            re.sub(f"^.+?{re.escape(self.settings.column_value_separator)}", "", item) for item in uncompressed_itemset
        ]

    def compress_item(self, decompressed_item):
        """Compress the given item string."""
        return compress_string(decompressed_item, input_alphabet=self.settings.item_alphabet)

    def compress_itemset(self, decompressed_items):
        """Compress the given itemset."""
        return list(self.compress_item(uncompressed_item) for uncompressed_item in decompressed_items)

    def decompress_item(self, compressed_item):
        """Uncompress the given compressed item string."""
        return decompress_string(compressed_item, original_input_alphabet=self.settings.item_alphabet)

    def decompress_itemset(self, compressed_items):
        """Decompress the given compressed itemset."""
        return list(
            decompress_string(compressed_item, original_input_alphabet=self.settings.item_alphabet)
            for compressed_item in compressed_items
        )
