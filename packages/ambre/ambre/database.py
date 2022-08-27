"""Defines the Database class."""

from __future__ import annotations

import copy
import itertools
import random
import string
import sys
import warnings
from collections import deque
from io import BytesIO

import joblib
import pandas as pd
from tqdm import tqdm

from ambre.common_sense_rule import CommonSenseRule
from ambre.itemsets_trie import ItemsetsTrie
from ambre.prepostprocessing import PrePostProcessor
from ambre.settings import Settings
from ambre.versions import AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION, AMBRE_PACKAGE_VERSION


class Database:
    """Transaction database for mining association rules."""

    AMBRE_PACKAGE_VERSION = AMBRE_PACKAGE_VERSION
    DATABASE_SCHEMA_VERSION = AMBRE_PACKAGE_DATABASE_SCHEMA_VERSION

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
        item_alphabet=string.printable,
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

    def insert_from_pandas_dataframe_rows(self, pandas_df, sampling_ratio=1, input_columns=None, show_progress=True):
        """Interpret each row in the given pandas dataframe as transaction and insert those."""
        columns = input_columns if input_columns else pandas_df.columns
        self.insert_transactions(
            (
                [
                    (
                        f"{row[column]}"
                        if self.settings.omit_column_names
                        else f"{column}{self.settings.column_value_separator}{row[column]}"
                    )
                    for column in columns
                ]
                for _, row in pandas_df.iterrows()
            ),
            sampling_ratio,
            show_progress,
        )

    def insert_transactions(self, transactions, sampling_ratio=1, show_progress=True):
        """Insert the given transactions, optionally sampling to enable larger datasets."""
        if not 0 <= sampling_ratio <= 1:
            raise ValueError(
                f"Parameter 'sampling_ratio' must be between 0 and 1. Specified value is: {sampling_ratio}."
            )
        transaction_iterator = tqdm(transactions) if show_progress else transactions
        if sampling_ratio == 1:
            deque([self.insert_transaction(transaction) for transaction in transaction_iterator], maxlen=0)
        else:
            deque(
                [
                    self.insert_transaction(transaction)
                    for transaction in transaction_iterator
                    if (random.random() < sampling_ratio)
                ],
                maxlen=0,
            )

    def insert_transaction(self, transaction):
        """Insert the given transaction."""
        self.itemsets_trie.insert_normalized_consequents_antecedents_compressed(
            *self.prepostprocessor.extract_consequents_antecedents_compressed_from_uncompressed(
                self.prepostprocessor.normalize_uncompressed_itemset(transaction, sort_result=False), sort_result=True
            )
        )

    @property
    def number_transactions(self):
        """Return the number of inserted transactions."""
        return self.itemsets_trie.number_transactions

    @property
    def number_nodes(self):
        """Return the number of nodes in the underlying itemset trie."""
        return self.itemsets_trie.number_nodes

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
        rules are derived. This helps concentrating on rules not known before.
        """
        self.insert_common_sense_rules([CommonSenseRule(self, antecedents, consequents, confidence)])

    def get_common_sense_rules(self):
        """Return the common sense rules."""
        return self.common_sense_rules

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
    ):
        """Derive the frequent itemsets from the internally assembled trie and return them in a dict object."""
        # walk down the tree (depth-first) and collect the result
        result = {"itemset": [], "occurrences": [], "support": [], "itemset_length": []}
        root_node = self.itemsets_trie.root_node
        consequent_root_nodes = self.itemsets_trie.get_consequent_root_nodes()
        iterations = len(consequent_root_nodes) if filter_to_consequent_itemsets_only else len(root_node.children)
        progress_bar = tqdm(total=iterations) if show_progress_bar else None
        stack = deque([root_node])
        is_root_node = True
        while len(stack) > 0:
            current_node = stack.pop()
            if not is_root_node:
                itemset_length = current_node.itemset_length
                occurrences = current_node.occurrences
                support = current_node.support
                if (
                    itemset_length >= min_itemset_length
                    and ((max_itemset_length is None) or (itemset_length <= max_itemset_length))
                    and ((max_occurrences is None) or (occurrences <= max_occurrences))
                    and (occurrences >= min_occurrences)
                    and (min_support <= support <= max_support)
                ):
                    itemset = current_node.itemset_uncompressed_items_sorted
                    if not self.settings.omit_column_names and omit_column_names_in_output:
                        itemset = self.prepostprocessor.remove_column_names_from_uncompressed_itemset(itemset)
                    result["itemset"].append(itemset)
                    result["occurrences"].append(current_node.occurrences)
                    result["support"].append(current_node.support)
                    result["itemset_length"].append(current_node.itemset_length)
                if progress_bar and current_node.parent_node == root_node:
                    progress_bar.update(1)
            next_children = (
                current_node.children.values()
                if not (is_root_node and filter_to_consequent_itemsets_only)
                else consequent_root_nodes
            )
            for child in reversed(next_children):
                stack.append(child)
            is_root_node = False
        if progress_bar:
            progress_bar.close()
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

        result = {
            "antecedents": [],
            "consequents": [],
            "confidence": [],
            "lift": [],
            "occurrences": [],
            "support": [],
            "antecedents_length": [],
        }

        rules_temp = {
            frozenset(
                common_sense_rule.consequents_compressed + common_sense_rule.antecedents_compressed
            ): common_sense_rule.confidence
            for common_sense_rule in self.common_sense_rules
        }

        def _any_preexisting_rule_with_antecedents_subset_and_same_confidence(
            rules_temp, antecedents, consequents, confidence, confidence_tolerance
        ):
            for rule_itemset, rule_confidence in rules_temp.items():
                if (
                    (rule_confidence - confidence_tolerance <= confidence <= rule_confidence + confidence_tolerance)
                    or (rule_confidence == 1)
                ) and rule_itemset.issubset(consequents.union(antecedents)):
                    return True
            return False

        def _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
            nodes, current_node_antecedent_size, recursion_level
        ):
            next_nodes = []
            if show_progress_bar and recursion_level == 0:
                nodes = tqdm(nodes)
            for current_node in nodes:
                # add the node as a new rule if certain conditions are met

                # condition: antecedents size is lower or equal than the specified max_antecedents_length
                antecedents_length_condition_met = (max_antecedents_length is None) or (
                    current_node_antecedent_size <= max_antecedents_length
                )
                if antecedents_length_condition_met:

                    # condition: itemset has a different confidence than its parent or parent is consequent
                    # rationale: an itemset with the same confidence as its parent does not add value, first antecedent
                    #            nodes should be considered in any case
                    current_node_confidence = current_node.confidence
                    if (
                        current_node.parent_node.is_consequent
                        or current_node_confidence != current_node.parent_node.confidence
                    ):

                        # condition: minimum/maximum criteria from configuration are met
                        # rationale: filter defined by user
                        current_node_occurrences = current_node.occurrences
                        current_node_lift = current_node.lift
                        current_node_support = current_node.support
                        if (
                            (min_confidence <= current_node_confidence <= max_confidence)
                            and (min_support <= current_node_support <= max_support)
                            and (current_node_lift >= min_lift)
                            and ((max_lift is None) or (current_node_lift <= max_lift))
                            and ((max_occurrences is None) or (current_node_occurrences <= max_occurrences))
                            and (current_node_occurrences >= min_occurrences)
                        ):
                            antecedents = current_node.antecedents_compressed
                            consequents = current_node.consequents_compressed

                            # condition: there is no rule yet which predicts the same consequents with a subset of the
                            #            current rule's antecedents and the same confidence (within tolerances)
                            #            PLUS
                            #            there is no common sense rule yet which matches antecedents and consequents or
                            #            overrules with confidence=1
                            if not _any_preexisting_rule_with_antecedents_subset_and_same_confidence(
                                rules_temp,
                                set(antecedents),
                                set(consequents),
                                current_node_confidence,
                                confidence_tolerance,
                            ):
                                # add rule to result
                                consequents, antecedents = current_node.consequents_antecedents_compressed
                                consequents_to_append, antecedents_to_append = self.prepostprocessor.decompress_itemset(
                                    consequents
                                ), self.prepostprocessor.decompress_itemset(antecedents)
                                if not self.settings.omit_column_names and omit_column_names_in_output:
                                    consequents_to_append = (
                                        self.prepostprocessor.remove_column_names_from_uncompressed_itemset(
                                            consequents_to_append
                                        )
                                    )
                                    antecedents_to_append = (
                                        self.prepostprocessor.remove_column_names_from_uncompressed_itemset(
                                            antecedents_to_append
                                        )
                                    )
                                result["antecedents"].append(antecedents_to_append)
                                result["consequents"].append(consequents_to_append)
                                result["confidence"].append(current_node_confidence)
                                result["lift"].append(current_node_lift)
                                result["occurrences"].append(current_node_occurrences)
                                result["support"].append(current_node_support)
                                result["antecedents_length"].append(current_node_antecedent_size)

                                # add rule to temp rules to avoid redundant rules
                                rules_temp[frozenset(consequents + antecedents)] = current_node_confidence

                    # only continue if the antecedents size is below the allowed maximum (which is the case here anyway,
                    # therefore no additional check) and if the current nodes confidence is different from 1
                    # rationale: if the confidence is 1, any rule generated from this node's children is redundant.
                    #            hence in that case, there is no need to walk down further.
                    if not current_node_confidence == 1:
                        child_nodes = list(current_node.children.values())
                        next_nodes.extend(child_nodes)

            if next_nodes:
                _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
                    next_nodes, current_node_antecedent_size + 1, recursion_level + 1
                )

        # add the non-antecedent consequences to the result if desired (also considering several config settings)
        if non_antecedents_rules:
            for consequent_node in self.itemsets_trie.walk_through_all_consequent_nodes_depth_first():
                confidence = consequent_node.confidence
                lift = consequent_node.lift
                occurrences = consequent_node.occurrences
                support = consequent_node.support
                if (
                    (min_confidence <= confidence <= max_confidence)
                    and (min_support <= support <= max_support)
                    and (lift >= min_lift)
                    and ((max_lift is None) or (lift <= max_lift))
                    and ((max_occurrences is None) or (occurrences <= max_occurrences))
                    and (occurrences >= min_occurrences)
                ):
                    result["antecedents"].append("")
                    result["consequents"].append(consequent_node.itemset_uncompressed_items_sorted)
                    result["confidence"].append(consequent_node.confidence)
                    result["lift"].append(consequent_node.lift)
                    result["occurrences"].append(consequent_node.occurrences)
                    result["support"].append(consequent_node.support)
                    result["antecedents_length"].append(0)

        # use a recursive function to compile the result, starting at the first antecedent nodes in the itemset trie
        _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
            self.itemsets_trie.get_first_antecedent_after_consequents_nodes(), 1, 0
        )

        # return result
        return result

    def derive_rules_pandas(self, *args, **kwargs):
        """
        Derive association rules and return them as pandas dataframe.

        See derive_rules_columns_dict() for parameter descriptions.
        """
        result = pd.DataFrame(self.derive_rules_columns_dict(*args, **kwargs))
        for list_column in ["consequents", "antecedents"]:
            result[list_column] = result[list_column].map(self.settings.item_separator_for_string_outputs.join)
        # result = result.sort_values(by=["confidence", "support"], ascending=[False, True])
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

    def copy(self):
        """Return a copy of the database."""
        return copy.deepcopy(self)

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
