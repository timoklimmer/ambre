"""Defines the Database class."""

from __future__ import annotations

import itertools
import re
import sys
import warnings
from io import BytesIO
from typing import Iterable, Union

import joblib
import numpy as np
import pandas as pd
from ambre.common_sense_rule import CommonSenseRule
from ambre.itemsets_trie import ItemsetsTrie
from ambre.prepostprocessing import PrePostProcessor
from ambre.settings import Settings
from ambre.strings import decompress_string
from ambre.versions import AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION, AMBRE_PACKAGE_VERSION
from tqdm import tqdm


class Database:
    """Transaction database for mining association rules."""

    AMBRE_PACKAGE_VERSION = AMBRE_PACKAGE_VERSION
    DATABASE_SCHEMA_VERSION = AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION

    @property
    def number_transactions(self):
        """Return the number of inserted transactions."""
        return self.itemsets_trie.number_transactions

    @property
    def number_nodes(self):
        """Return the number of nodes in the underlying itemset trie."""
        return self.itemsets_trie.number_nodes

    def __init__(
        self,
        consequents=[],
        normalize_whitespace=True,
        case_insensitive=True,
        max_antecedents_length=None,
        item_separator_for_string_outputs=" ∪ ",
        column_value_separator="=",
        omit_column_names=False,
        disable_string_consequent_warning=False,
        item_alphabet=None,
    ):
        """Init."""
        if not disable_string_consequent_warning and isinstance(consequents, str):
            warnings.warn(
                (
                    "Parameter 'consequents' is a string, which means that each char in the string is treated as a "
                    "consequence. If you want to treat the entire string as consequent, you need to pass it within a "
                    "list. To disable this warning, set parameter 'disable_string_consequent_warning' to True."
                )
            )
        self.settings = Settings(
            consequents,
            normalize_whitespace,
            case_insensitive,
            max_antecedents_length,
            item_separator_for_string_outputs,
            column_value_separator,
            omit_column_names,
            item_alphabet=item_alphabet,
        )
        self.prepostprocessor = PrePostProcessor(self.settings)
        self.itemsets_trie = ItemsetsTrie(
            self.prepostprocessor.normalized_consequents,
            self.prepostprocessor.compressed_consequents,
            self.settings.max_antecedents_length,
            self.settings.item_separator_for_string_outputs,
            self.settings.item_alphabet,
        )
        self.common_sense_rules = []

    def insert_from_pandas_dataframe_rows(self, pandas_df, input_columns=None, show_progress=True):
        """Interpret each row in the given pandas dataframe as transaction and insert those."""
        columns = input_columns if input_columns else pandas_df.columns
        transaction_iterator = (
            tqdm(pandas_df[columns].iterrows(), total=pandas_df.shape[0])
            if show_progress
            else pandas_df[columns].iterrows()
        )
        if self.settings.omit_column_names:
            for _, row in transaction_iterator:
                self.insert_transaction(frozenset(f"{value}" for value in row.values))
        else:
            column_value_separator = self.settings.column_value_separator
            for _, row in transaction_iterator:
                self.insert_transaction(
                    frozenset(f"{column}{column_value_separator}{row[column]}" for column in columns)
                )

    def insert_transaction(self, transaction):
        """Insert the given transaction."""
        consequents = []
        antecedents = []

        normalized_consequents_set = set(self.prepostprocessor.normalized_consequents)

        normalize_whitespace_setting = self.settings.normalize_whitespace
        case_insensitive_setting = self.settings.case_insensitive
        for item in transaction:
            normalized_item = item
            if normalize_whitespace_setting:
                normalized_item = normalized_item.strip()
                if "  " in normalized_item or "\t" in normalized_item or "\n" in normalized_item:
                    normalized_item = re.sub(r"\s+", " ", normalized_item)
            if case_insensitive_setting:
                normalized_item = normalized_item.lower()

            if normalized_item in normalized_consequents_set:
                consequents.append(normalized_item)
            else:
                antecedents.append(normalized_item)

        consequents.sort(key=str.casefold)
        antecedents.sort(key=str.casefold)

        self.itemsets_trie.insert_consequents_antecedents_compressed(consequents, antecedents)

    def insert_transactions(self, transactions, show_progress=True):
        """Insert the given transactions."""
        transaction_iterator = tqdm(transactions, total=len(transactions)) if show_progress else transactions
        for transaction in transaction_iterator:
            self.insert_transaction(transaction)

    def has_itemset(self, transaction):
        """Check if the given itemset is contained in the database."""
        consequents, antecedents = self.prepostprocessor.extract_consequents_antecedents_compressed_from_uncompressed(
            self.prepostprocessor.normalize_uncompressed_itemset(transaction, sort_result=False), sort_result=True
        )
        transaction = consequents + antecedents
        return self.itemsets_trie.has_consequents_antecedents_compressed(transaction)

    def get_itemset(self, itemset, skip_unknown_items=False, none_if_not_exists=False):
        """Return the given itemset and related information."""
        normalized_itemset = self.prepostprocessor.normalize_uncompressed_itemset(itemset, sort_result=True)
        consequents, antecedents = self.prepostprocessor.extract_consequents_antecedents_compressed_from_uncompressed(
            normalized_itemset, sort_result=True
        )
        trie_node = self.itemsets_trie.get_node_from_compressed(
            consequents + antecedents, skip_unknown_items, none_if_not_exists
        )
        if trie_node:
            consequents_uncompressed, antecedents_uncompressed = trie_node.consequents_antecedents_uncompressed
            result = {
                "itemset": trie_node.itemset_items_uncompressed_sorted,
                "consequents": consequents_uncompressed,
                "antecedents": antecedents_uncompressed,
                "occurrences": trie_node.occurrences,
                "support": trie_node.support,
            }
            if consequents_uncompressed:
                result.update({"confidence": trie_node.confidence, "lift": trie_node.lift})
            return result
        return None

    def remove_transaction(self, transaction, silent=False):
        """Remove the given transaction."""
        self.itemsets_trie.remove_consequents_antecedents_compressed(
            *self.prepostprocessor.extract_consequents_antecedents_compressed_from_uncompressed(
                self.prepostprocessor.normalize_uncompressed_itemset(transaction, sort_result=False), sort_result=True
            ),
            silent,
        )

    def insert_common_sense_rules(self, common_sense_rules_to_insert):
        """
        Insert a batch of common sense rules.

        Common sense rules and rules that become redundant by the specified common sense rules are not returned when
        rules are derived. This helps concentrating on rules not known before.
        """
        # update database in given rules
        for common_sense_rule_to_insert in common_sense_rules_to_insert:
            common_sense_rule_to_insert.database = self
        # add the updated rules to the existing ones and sort the result
        self.common_sense_rules = sorted(
            list(set((item for item in self.common_sense_rules + common_sense_rules_to_insert)))
        )
        # discard all rules where we have another rule with same antecedents and consequents but higher confidence
        # note: assumes that self.common_sense_rules is sorted
        self.common_sense_rules = sorted(
            list(
                list(group)[-1]
                for _, group in itertools.groupby(
                    self.common_sense_rules,
                    lambda common_sense_rule: (
                        common_sense_rule.antecedents_compressed,
                        common_sense_rule.consequents_compressed,
                    ),
                )
            )
        )
        # discard all redundant rules where we have another rule with the same confidence and consequents but
        # antecedents are are a superset. a, b => x (1) == a => x (1). Hence, we can/should remove a, b => x (1).
        # note: assumes that self.common_sense_rules is sorted
        new_common_sense_rules = []
        for index, common_sense_rule in enumerate(self.common_sense_rules):
            if not any(
                (
                    lower_common_sense_rule.confidence == common_sense_rule.confidence
                    and lower_common_sense_rule.consequents_compressed == common_sense_rule.consequents_compressed
                    and set(lower_common_sense_rule.antecedents_compressed).issubset(
                        common_sense_rule.antecedents_compressed
                    )
                    for lower_common_sense_rule in self.common_sense_rules[:index]
                )
            ):
                new_common_sense_rules.append(common_sense_rule)
        self.common_sense_rules = new_common_sense_rules

    def insert_common_sense_rule(self, antecedents, consequents, confidence=1):
        """
        Insert a common sense rule.

        Common sense rules and rules that become redundant by the specified common sense rules are not returned when
        rules are derived. This helps concentrating on unknown rules.
        """
        self.insert_common_sense_rules([CommonSenseRule(self, antecedents, consequents, confidence)])

    def get_common_sense_rules(self):
        """Return the common sense rules."""
        return self.common_sense_rules

    def remove_common_sense_rule(self, antecedents, consequents, confidence):
        """Remove the given common sense rule."""
        common_sense_rule_to_delete = CommonSenseRule(self, antecedents, consequents, confidence)
        self.common_sense_rules = [
            common_sense_rule
            for common_sense_rule in self.common_sense_rules
            if common_sense_rule != common_sense_rule_to_delete
        ]

    def clear_common_sense_rules(self):
        """Clear all common sense rules."""
        self.common_sense_rules = []

    def as_bytes(self):
        """Return a byte array representing the database."""
        with BytesIO() as byte_buffer:
            joblib.dump(
                {
                    "metadata": {
                        "AMBRE_PACKAGE_VERSION": AMBRE_PACKAGE_VERSION,
                        "AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION": AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION,
                        "PYTHON_VERSION": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                        "PYTHON_VERSION_LONG": f"{sys.version}",
                    },
                    "database": self,
                },
                byte_buffer,
                compress="lz4",
            )
            return byte_buffer.getvalue()

    def save_to_file(self, filepath):
        """Save the database into the given file."""
        with open(filepath, "wb") as target_file:
            target_file.write(self.as_bytes())

    @staticmethod
    def load_from_bytes(bytes_array) -> Database:
        """Load the database from the specified bytes."""
        loaded_data_structure = joblib.load(BytesIO(bytes_array))
        package_version_from_file = loaded_data_structure["metadata"]["AMBRE_PACKAGE_VERSION"]
        database_schema_version_from_file = loaded_data_structure["metadata"]["AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION"]
        if database_schema_version_from_file != AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION:
            raise Exception(
                (
                    f"Cannot load database due to incompatible database schema versions. The currently installed ambre "
                    f"package version '{AMBRE_PACKAGE_VERSION}' expects database schema version "
                    f"'{AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION}', but your database uses database schema "
                    f"version '{database_schema_version_from_file}', created by ambre version "
                    f"'{package_version_from_file}'. Ensure that you are saving and loading databases with compatible "
                    f"versions."
                )
            )
        database: Database = loaded_data_structure["database"]
        database.ambre_package_version = package_version_from_file
        database.database_schema_version = database_schema_version_from_file
        return database

    @staticmethod
    def load_from_file(filepath) -> Database:
        """Load the database from the specified file."""
        with open(filepath, "rb") as source_file:
            return Database.load_from_bytes(source_file.read())

    def derive_frequent_itemsets_columns_dict(
        self,
        filter_to_consequent_itemsets_only=False,
        min_itemset_length=0,
        max_itemset_length=None,
        min_occurrences=0,
        max_occurrences=None,
        min_support=0,
        max_support=1,
        omit_column_names_in_output=False,
        show_progress_bar=False,
        progress_bar_text=None,
    ):
        """Derive the frequent itemsets from the internally assembled trie and return them in a dict object."""
        # Performance optimization: pre-calculate static values and cache settings
        number_transactions = self.itemsets_trie.number_transactions
        should_remove_column_names = not self.settings.omit_column_names and omit_column_names_in_output
        item_alphabet = self.itemsets_trie.item_alphabet

        # Pre-allocate result lists with estimated capacity for better performance
        result = {"itemset": [], "occurrences": [], "support": [], "itemset_length": []}

        def _collect_frequent_itemset_data(current_node):
            # Cache node properties to avoid repeated property access
            occurrences = current_node.occurrences

            # Early filtering on occurrences (cheapest check first)
            if occurrences < min_occurrences or (max_occurrences is not None and occurrences > max_occurrences):
                return

            # Calculate itemset length efficiently by traversing tree only once
            itemset_length = 0
            temp_node = current_node
            while temp_node.parent_node is not None:
                itemset_length += 1
                temp_node = temp_node.parent_node

            # Filter on itemset length
            if itemset_length < min_itemset_length or (
                max_itemset_length is not None and itemset_length > max_itemset_length
            ):
                return

            # Calculate support (avoid repeated division)
            support = occurrences / number_transactions

            # Filter on support
            if not min_support <= support <= max_support:
                return

            # Build itemset efficiently - collect compressed items during single traversal
            compressed_items = []
            temp_node = current_node
            while temp_node.parent_node is not None:
                compressed_items.insert(0, temp_node.compressed_item)
                temp_node = temp_node.parent_node

            # Decompress items in batch for better cache locality
            if should_remove_column_names:
                # Optimize: decompress and remove column names in single pass
                column_separator = self.settings.column_value_separator
                itemset = [
                    re.sub(
                        f"^.+?{re.escape(column_separator)}",
                        "",
                        decompress_string(item, original_input_alphabet=item_alphabet),
                    )
                    for item in compressed_items
                ]
            else:
                # Standard decompression
                itemset = [decompress_string(item, original_input_alphabet=item_alphabet) for item in compressed_items]

            # Append to results in batch (avoid repeated dictionary access)
            result["itemset"].append(itemset)
            result["occurrences"].append(occurrences)
            result["support"].append(support)
            result["itemset_length"].append(itemset_length)

        self.itemsets_trie.visit_itemset_nodes_depth_first(
            _collect_frequent_itemset_data,
            only_with_consequents=filter_to_consequent_itemsets_only,
            show_progress_bar=show_progress_bar,
            progress_bar_text=progress_bar_text,
        )
        # return result
        return result

    def derive_frequent_itemsets_pandas(self, *args, **kwargs):
        """
        Derive frequent itemsets and return them as pandas dataframe.

        See derive_frequent_itemsets_columns_dict() for parameter descriptions.
        """
        result = pd.DataFrame(self.derive_frequent_itemsets_columns_dict(*args, **kwargs))
        result["itemset"] = result["itemset"].map(self.settings.item_separator_for_string_outputs.join)
        return result

    def derive_frequent_itemsets_excel(self, filename, *args, **kwargs):
        """
        Derive frequent itemsets and save them in an Excel workbook.

        See derive_frequent_itemsets_columns_dict() for parameter descriptions.
        """
        self.derive_frequent_itemsets_pandas(*args, **kwargs).to_excel(filename, header=True, index=False)

    def derive_frequent_itemsets_csv(self, filename, *args, **kwargs):
        """
        Derive frequent itemsets and save them in a CSV file.

        See derive_frequent_itemsets_columns_dict() for parameter descriptions.
        """
        self.derive_frequent_itemsets_pandas(*args, **kwargs).to_csv(filename, header=True, index=False)

    def derive_rules_columns_dict(
        self,
        min_confidence=0,
        max_confidence=1,
        confidence_tolerance=0,
        min_lift=0,
        max_lift=None,
        min_support=0,
        max_support=1,
        min_occurrences=0,
        max_occurrences=None,
        max_antecedents_length=None,
        non_antecedents_rules=False,
        omit_column_names_in_output=False,
        show_progress_bar=False,
    ):
        """
        Derive antecedents => consequents rules from the internal itemsets trie and return them as a dict object.

        Redundant rules are removed from the result. A rule is redundant if it predicts the same consequents with the
        same confidence as a rule with a subset of its antecedents.

        If specified, known rules are also removed from the result.
        """
        if not self.settings.consequents:
            raise ValueError(
                (
                    "Cannot extract rules because no consequents are defined. To use this function, you need to pass "
                    "the consequent(s) of interest to the constructor when instantiating this class."
                )
            )

        # Pre-allocate result lists for better performance
        result = {
            "antecedents": [],
            "consequents": [],
            "confidence": [],
            "lift": [],
            "occurrences": [],
            "support": [],
            "antecedents_length": [],
            "consequents_length": [],
        }

        # Cache frequently accessed settings for performance
        should_remove_column_names = not self.settings.omit_column_names and omit_column_names_in_output

        # Pre-compute common sense rules lookup with optimized structure
        # Use a nested dict for faster O(1) lookups instead of O(n) iteration
        rules_temp = {}
        common_sense_rules_by_itemset = {}

        for common_sense_rule in self.common_sense_rules:
            itemset_key = frozenset(common_sense_rule.consequents_compressed + common_sense_rule.antecedents_compressed)
            rules_temp[itemset_key] = common_sense_rule.confidence

            # Create lookup by consequents for faster subset checking
            consequents_key = frozenset(common_sense_rule.consequents_compressed)
            if consequents_key not in common_sense_rules_by_itemset:
                common_sense_rules_by_itemset[consequents_key] = []
            common_sense_rules_by_itemset[consequents_key].append(
                (frozenset(common_sense_rule.antecedents_compressed), common_sense_rule.confidence)
            )

        def _any_preexisting_rule_with_antecedents_subset_and_same_confidence(
            antecedents_compressed, consequents_compressed, confidence
        ):
            """Optimized version with faster lookup and early termination."""
            # Create sets once for reuse
            antecedents_set = frozenset(antecedents_compressed)
            consequents_set = frozenset(consequents_compressed)
            combined_set = antecedents_set | consequents_set

            # Check rules_temp with direct lookup first (fastest path)
            for rule_itemset, rule_confidence in rules_temp.items():
                if rule_itemset.issubset(combined_set):
                    if rule_confidence == 1 or abs(rule_confidence - confidence) <= confidence_tolerance:
                        return True

            return False

        def _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
            nodes, current_node_antecedent_size, recursion_level
        ):
            next_nodes = []
            if show_progress_bar and recursion_level == 0:
                nodes = tqdm(nodes)

            for current_node in nodes:
                # Early exit if antecedents length exceeds maximum
                if max_antecedents_length is not None and current_node_antecedent_size > max_antecedents_length:
                    continue

                # Cache node properties to avoid repeated attribute access
                current_node_confidence = current_node.confidence
                current_node_parent = current_node.parent_node

                # Check if this node represents a valid rule candidate
                if current_node_parent.is_consequent or current_node_confidence != current_node_parent.confidence:
                    # Cache remaining node properties for filtering
                    current_node_occurrences = current_node.occurrences
                    current_node_lift = current_node.lift
                    current_node_support = current_node.support

                    # Apply all numeric filters in one compound condition for early exit
                    if (
                        min_confidence <= current_node_confidence <= max_confidence
                        and min_support <= current_node_support <= max_support
                        and current_node_lift >= min_lift
                        and (max_lift is None or current_node_lift <= max_lift)
                        and (max_occurrences is None or current_node_occurrences <= max_occurrences)
                        and current_node_occurrences >= min_occurrences
                    ):
                        antecedents_compressed = current_node.antecedents_compressed
                        consequents_compressed = current_node.consequents_compressed

                        # Check for redundant rules using optimized function
                        if not _any_preexisting_rule_with_antecedents_subset_and_same_confidence(
                            antecedents_compressed,
                            consequents_compressed,
                            current_node_confidence,
                        ):
                            # Decompress items efficiently
                            if should_remove_column_names:
                                # Optimize: decompress and remove column names in single pass
                                column_separator = self.settings.column_value_separator
                                consequents_to_append = [
                                    re.sub(
                                        f"^.+?{re.escape(column_separator)}",
                                        "",
                                        self.prepostprocessor.decompress_item(item),
                                    )
                                    for item in consequents_compressed
                                ]
                                antecedents_to_append = [
                                    re.sub(
                                        f"^.+?{re.escape(column_separator)}",
                                        "",
                                        self.prepostprocessor.decompress_item(item),
                                    )
                                    for item in antecedents_compressed
                                ]
                            else:
                                # Standard decompression
                                consequents_to_append = self.prepostprocessor.decompress_itemset(consequents_compressed)
                                antecedents_to_append = self.prepostprocessor.decompress_itemset(antecedents_compressed)

                            # Batch append to result lists for better performance
                            result["antecedents"].append(antecedents_to_append)
                            result["consequents"].append(consequents_to_append)
                            result["confidence"].append(current_node_confidence)
                            result["lift"].append(current_node_lift)
                            result["occurrences"].append(current_node_occurrences)
                            result["support"].append(current_node_support)
                            result["antecedents_length"].append(current_node_antecedent_size)
                            result["consequents_length"].append(len(consequents_to_append))

                            # Add to rules_temp to prevent future redundant rules
                            rules_temp[frozenset(consequents_compressed + antecedents_compressed)] = (
                                current_node_confidence
                            )

                # Continue tree traversal if confidence is not 1 (optimization from original)
                if current_node_confidence != 1:
                    # Optimize: get children as list in one operation
                    child_nodes = list(current_node.children.values())
                    next_nodes.extend(child_nodes)

            # Continue recursion if there are more nodes to process
            if next_nodes:
                _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
                    next_nodes, current_node_antecedent_size + 1, recursion_level + 1
                )

        # Handle non-antecedent rules with optimized processing
        if non_antecedents_rules:
            for consequent_node in self.itemsets_trie.get_all_consequent_nodes_depth_first():
                # Cache node properties
                confidence = consequent_node.confidence
                lift = consequent_node.lift
                occurrences = consequent_node.occurrences
                support = consequent_node.support

                # Apply filters in compound condition
                if (
                    min_confidence <= confidence <= max_confidence
                    and min_support <= support <= max_support
                    and lift >= min_lift
                    and (max_lift is None or lift <= max_lift)
                    and (max_occurrences is None or occurrences <= max_occurrences)
                    and occurrences >= min_occurrences
                ):
                    # Batch append for performance
                    result["antecedents"].append([""])
                    result["consequents"].append(consequent_node.itemset_items_uncompressed_sorted)
                    result["confidence"].append(confidence)
                    result["lift"].append(lift)
                    result["occurrences"].append(occurrences)
                    result["support"].append(support)
                    result["antecedents_length"].append(0)
                    result["consequents_length"].append(len(consequent_node.consequents_compressed))

        # Start the recursive tree traversal
        _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
            self.itemsets_trie.get_first_antecedent_after_consequents_nodes(), 1, 0
        )

        return result

    def derive_rules_pandas(self, *args, **kwargs):
        """
        Derive association rules and return them as pandas dataframe.

        See derive_rules_columns_dict() for parameter descriptions.
        """
        result = pd.DataFrame(self.derive_rules_columns_dict(*args, **kwargs))
        for list_column in ["consequents", "antecedents"]:
            result[list_column] = result[list_column].map(self.settings.item_separator_for_string_outputs.join)
        return result

    def derive_rules_excel(self, filename, *args, **kwargs):
        """
        Derive association rules and save them in an Excel workbook.

        See derive_rules_columns_dict() for parameter descriptions.
        """
        self.derive_rules_pandas(*args, **kwargs).to_excel(filename, header=True, index=False)

    def derive_rules_csv(self, filename, *args, **kwargs):
        """
        Derive association rules and save them in a CSV file.

        See derive_rules_columns_dict() for parameter descriptions.
        """
        self.derive_rules_pandas(*args, **kwargs).to_csv(filename, header=True, index=False)

    def predict_consequents_list(
        self,
        antecedents: Union[Iterable[str], None] = None,
        consequents: Union[Iterable[str], None] = None,
        skip_unknown_antecedents=False,
    ) -> list:
        """
        Return the probabilities for all or only for the given consequents, assuming the given antecedents hold true.

        Unknown antecedents can be skipped if skip_unknown_antecedents is set to True.
        If no antecedents are given, prior probabilities are returned.
        If no explicit consequents are specified, probabilities for all consequents are computed.
        Common-sense rules are considered.
        """
        total_result = []
        normalized_antecedents = (
            self.prepostprocessor.normalize_uncompressed_itemset(antecedents) if antecedents else []
        )
        compressed_antecedents = self.prepostprocessor.compress_itemset(normalized_antecedents)
        compressed_consequents_to_iterate = self.prepostprocessor.compressed_consequents
        if consequents:
            normalized_consequents = self.prepostprocessor.normalize_uncompressed_itemset(consequents)
            for normalized_consequent in normalized_consequents:
                if normalized_consequent not in self.prepostprocessor.normalized_consequents:
                    raise ValueError(
                        (
                            f"The specified consequent '{normalized_consequent}' has not been specified as a consequent "
                            f"for the database. Ensure you pass only valid consequents."
                        )
                    )
            compressed_consequents_to_iterate = self.prepostprocessor.compress_itemset(normalized_consequents)

        for compressed_consequent in compressed_consequents_to_iterate:
            probability = None
            # common-sense rule first
            for common_sense_rule in self.common_sense_rules:
                if compressed_consequent in common_sense_rule.consequents_compressed and (
                    (
                        not skip_unknown_antecedents
                        and compressed_antecedents == common_sense_rule.antecedents_compressed
                    )
                    or (
                        skip_unknown_antecedents
                        # faster expression of compressed_antecedents.issuperset(common_sense_rule.antecedents_compressed)
                        and all(
                            antecedent_compressed in compressed_antecedents
                            for antecedent_compressed in common_sense_rule.antecedents_compressed
                        )
                    )
                ):
                    probability = common_sense_rule.confidence

            # else try to get the result from the itemset trie
            if probability is None:
                try:
                    if len(compressed_antecedents) > 0:
                        # posterior probability requested
                        # Bayes' Theorem
                        # P(consequent | antecedents) = P(consequent ∩ antecedents) / P(antecedents)
                        p_consequent_intersect_antecedents = self.itemsets_trie.get_node_from_compressed(
                            [compressed_consequent] + compressed_antecedents, skip_unknown_antecedents
                        ).support
                        p_antecedents = self.itemsets_trie.get_node_from_compressed(
                            compressed_antecedents, skip_unknown_antecedents
                        ).support
                        probability = p_consequent_intersect_antecedents / p_antecedents if p_antecedents else None
                    else:
                        # prior probability requested
                        # P(consequent) is a simple lookup from the trie
                        probability = self.itemsets_trie.get_node_from_compressed(
                            [compressed_consequent], skip_unknown_antecedents
                        ).support
                except ValueError:
                    pass

            # add to result
            total_result.append(
                {
                    "antecedents": normalized_antecedents,
                    "consequent": self.prepostprocessor.decompress_item(compressed_consequent),
                    "probability": probability,
                }
            )
        total_result = sorted(
            total_result, key=lambda item: item["probability"] if item["probability"] else 0, reverse=True
        )
        return total_result

    def predict_consequents_pandas(self, *args, **kwargs):
        """
        Determine consequent probabilities given certain antecedents and return result as pandas dataframe.

        See predict_consequents_list() for parameter descriptions.
        """
        result = pd.DataFrame(self.predict_consequents_list(*args, **kwargs)).replace([np.nan], [None])
        for list_column in ["antecedents"]:
            result[list_column] = result[list_column].map(self.settings.item_separator_for_string_outputs.join)
        return result

    def copy(self):
        """Return a copy of the database."""
        # note: not using copy.deepcopy() here because it does not copy deep sometimes...
        return Database.load_from_bytes(self.as_bytes())

    @staticmethod
    def merge_databases(database1: Database, database2: Database, *further_databases) -> Database:
        """
        Merge the given database into a single database.

        Note: For performance/memory reasons, the merge operation is performed "in-place", means: specified databases
            might be modified. If you need to keep the specified databases, pass copies of your databases by using
            the <database>.copy() method.
        """
        databases_to_merge = sorted(
            [database1, database2, *further_databases], key=lambda database: database.number_nodes
        )
        largest_database = databases_to_merge[-1]
        for database in databases_to_merge[:-1]:
            largest_database = Database.merge_database_pair(largest_database, database)
        return largest_database

    @staticmethod
    def merge_database_pair(database1: Database, database2: Database, inplace=True) -> Database:
        """
        Merge the given databases into a single database and return the result.

        Note: For performance/memory reasons, the merge operation is performed "in-place", means: specified databases
              might be modified. If you need to keep the specified databases, pass copies of your databases by using
              the <database>.copy() method.
        """
        # -- ensure that database schema versions are supported
        if (
            database1.DATABASE_SCHEMA_VERSION != AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION
            or database2.DATABASE_SCHEMA_VERSION != AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION
        ):
            raise Exception(
                (
                    f"Cannot merge databases because database schema versions are incompatible. Ensure that you only "
                    f"merge databases that use data schema versions supported by this package. With the installed "
                    f"version of the ambre package ('{AMBRE_PACKAGE_VERSION}'), you can only merge databases with "
                    f"database schema version '{AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION}'."
                )
            )

        # -- ensure that the settings of both databases are equal
        if database1.settings != database2.settings:
            raise Exception(
                (
                    "Cannot merge databases because they use different settings. Ensure that both databases "
                    "use the same settings."
                )
            )

        # -- identify source and target database by selecting the larger database as target
        if database1.number_nodes >= database2.number_nodes:
            target_database = database1
            source_database = database2
        else:
            source_database = database2
            target_database = database1

        # -- get a copy of the target database if inplace is False
        if not inplace:
            target_database = target_database.copy()

        # udpate package version in target database
        target_database.AMBRE_PACKAGE_VERSION = AMBRE_PACKAGE_VERSION

        # -- merge the smaller source database into the bigger target database
        # update number of transactions
        target_database.itemsets_trie.number_transactions += source_database.itemsets_trie.number_transactions

        # do NOT update number of nodes
        # note: - this will be done automatically by itemsets_trie.get_or_create_child()

        # merge itemsets trie from source database into target database
        target_database.itemsets_trie.merge(source_database.itemsets_trie)

        # adopt common sense rules
        target_database.insert_common_sense_rules(source_database.get_common_sense_rules())

        # return the result
        return target_database
