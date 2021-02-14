"""Defines the Database class."""

import random

import numpy as np
import pandas as pd
from tqdm import tqdm

from ambre.common_sense_rule import CommonSenseRule
from ambre.itemsets_trie import ItemsetsTrie
from ambre.preprocessor import Preprocessor
from ambre.settings import Settings


class Database:
    """Transaction database for mining association rules."""

    def __init__(
        self,
        consequents=[],
        normalize_whitespace=True,
        case_insensitive=True,
        max_antecedents_length=None,
        item_separator_for_string_outputs=" ∪ ",
    ):
        """Init."""
        self.settings = Settings(
            consequents,
            normalize_whitespace,
            case_insensitive,
            max_antecedents_length,
            item_separator_for_string_outputs,
        )
        self.preprocessor = Preprocessor(self.settings)
        self.itemsets_trie = ItemsetsTrie(
            self.preprocessor.normalized_consequents,
            self.settings.max_antecedents_length,
            self.settings.item_separator_for_string_outputs,
        )
        self.common_sense_rules = []

    def insert_from_pandas_dataframe_rows(self, pandas_df, sampling_ratio=1, input_columns=None, show_progress=True):
        """Interpret each row in the given pandas dataframe as transaction and insert those."""
        if not 0 <= sampling_ratio <= 1:
            raise ValueError(
                f"Parameter 'sampling_ratio' needs to be between 0 and 1. Specified value is: {sampling_ratio}."
            )
        columns = input_columns if input_columns else pandas_df.columns
        self.insert_transactions(
            [[f"{column}:{row[column]}" for column in columns] for _, row in pandas_df.iterrows()],
            sampling_ratio,
            show_progress,
        )

    def insert_transactions(self, transactions, sampling_ratio=1, show_progress=True):
        """Insert the given transactions, optionally sampling to enable larger datasets."""
        if not 0 <= sampling_ratio <= 1:
            raise ValueError(
                f"Parameter 'sampling_ratio' needs to be between 0 and 1. Specified value is: {sampling_ratio}."
            )
        transaction_iterator = tqdm(transactions) if show_progress else transactions
        for transaction in transaction_iterator:
            if sampling_ratio == 1 or (random.random() < sampling_ratio):
                self.insert_transaction(transaction)

    def insert_transaction(self, transaction):
        """Insert the given transaction."""
        self.itemsets_trie.insert_normalized_transaction(self.preprocessor.normalize_itemset(transaction))

    @property
    def number_transactions(self):
        """Return the number of inserted transactions."""
        return self.itemsets_trie.number_transactions

    def insert_common_sense_rule(self, antecedents, consequents, confidence=1):
        """
        Insert a common sense rule which is known already.

        Common sense rules and rules that become redundant by the specified common sense rules are not returned when
        rules are derived. This helps concentrating on rules not known before.
        """
        antecedents = self.preprocessor.normalize_itemset(antecedents)
        consequents = self.preprocessor.normalize_itemset(consequents)
        self.common_sense_rules.append(CommonSenseRule(antecedents, consequents, confidence))

    def clear_common_sense_rules(self):
        """Clear all common sense rules."""
        self.common_sense_rules = []

    def derive_frequent_itemsets(
        self,
        filter_to_consequent_itemsets_only=False,
        min_itemset_length=0,
        max_itemset_length=None,
        min_occurrences=0,
        max_occurrences=None,
        min_support=0,
        max_support=1,
    ):
        """Derive the frequent itemsets from the internally assembled trie and return them as a dict object."""

        def _recursive_trie_walkdown_depth_first(node, level_number):
            result = {"itemset": [], "occurrences": [], "support": [], "itemset_length": []}
            for child_item in self.preprocessor.sort_itemset_consequents_first(node.children.keys()):
                child_node = node.children[child_item]
                if level_number == 0 and filter_to_consequent_itemsets_only and not child_node.consequents:
                    # if we reach here, we have passed all consequents (because consequents are iterated first)
                    # => no need to continue => break the recursion
                    break
                itemset_length = child_node.itemset_length
                occurrences = child_node.occurrences
                support = child_node.support
                if (
                    itemset_length >= min_itemset_length
                    and ((max_itemset_length is None) or (itemset_length <= max_itemset_length))
                    and ((max_occurrences is None) or (occurrences <= max_occurrences))
                    and (occurrences >= min_occurrences)
                    and (min_support <= support <= max_support)
                ):
                    result["itemset"].append(child_node.itemset_sorted_list)
                    result["occurrences"].append(child_node.occurrences)
                    result["support"].append(child_node.support)
                    result["itemset_length"].append(child_node.itemset_length)

                result_from_recursion = _recursive_trie_walkdown_depth_first(child_node, level_number + 1)
                for column in result_from_recursion:
                    result[column].extend(result_from_recursion[column])
            return result

        return _recursive_trie_walkdown_depth_first(self.itemsets_trie.root_node, 0)

    def derive_frequent_itemsets_pandas(self, *args, **kwargs):
        """
        Derive frequent itemsets and return them as pandas dataframe.

        See derive_frequent_itemsets() for parameter descriptions.
        """
        result = pd.DataFrame(self.derive_frequent_itemsets(*args, **kwargs))
        result["itemset"] = result["itemset"].map(self.settings.item_separator_for_string_outputs.join)
        return result

    def derive_frequent_itemsets_excel(self, filename, *args, **kwargs):
        """
        Derive frequent itemsets and save them in an Excel workbook.

        See derive_frequent_itemsets() for parameter descriptions.
        """
        self.derive_frequent_itemsets_pandas(*args, **kwargs).to_excel(filename, header=True, index=False)

    def derive_rules(
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

        rules_temp = {}
        for common_sense_rule in self.common_sense_rules:
            rules_temp[
                self.preprocessor.itemset_to_string(common_sense_rule.consequents + common_sense_rule.antecedents)
            ] = common_sense_rule.confidence

        def any_preexisting_rule_with_antecedents_subset_and_same_confidence(
            rules_temp, antecedents, consequents, confidence, confidence_tolerance
        ):
            for rule_itemset, rule_confidence in rules_temp.items():
                if self.preprocessor.string_to_itemset_set(rule_itemset).issubset(consequents.union(antecedents)) and (
                    (rule_confidence - confidence_tolerance <= confidence <= rule_confidence + confidence_tolerance)
                    or (rule_confidence == 1)
                ):
                    return True
            return False

        def _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(nodes, current_node_antecedent_size):
            next_nodes = []
            for current_node in nodes:
                # add the node as a new rule if certain conditions are met

                # condition: antecedents size is lower or equal than the specified max_occurrences
                antecedents_length_condition_met = (max_antecedents_length is None) or (
                    current_node_antecedent_size <= max_antecedents_length
                )
                if antecedents_length_condition_met:

                    # condition: itemset has a different confidence than its parent or parent is consequent
                    # rationale: an itemset with the same confidence as its parent does not add value, first antecedent
                    #            nodes have no parents with confidence.
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
                            antecedents = current_node.antecedents
                            consequents = current_node.consequents

                            # condition: there is no rule yet which predicts the same consequents with a subset of the
                            #            current rule's antecedents and the same confidence (within tolerances)
                            #            PLUS
                            #            there is no common sense rule yet which matches antecedents and consequents or
                            #            overrules with confidence=1
                            if not any_preexisting_rule_with_antecedents_subset_and_same_confidence(
                                rules_temp,
                                set(antecedents),
                                set(consequents),
                                current_node_confidence,
                                confidence_tolerance,
                            ):
                                # add rule to result
                                consequents, antecedents = current_node.consequents_antecedents
                                result["antecedents"].append(antecedents)
                                result["consequents"].append(consequents)
                                result["confidence"].append(current_node_confidence)
                                result["lift"].append(current_node_lift)
                                result["occurrences"].append(current_node_occurrences)
                                result["support"].append(current_node_support)
                                result["antecedents_length"].append(current_node_antecedent_size)

                                # add rule to temp rules to avoid redundant rules
                                rules_temp[
                                    self.preprocessor.itemset_to_string(consequents + antecedents)
                                ] = current_node_confidence

                    # only continue if the antecedents size is below the allowed maximum (which is the case here anyway,
                    # therefore no additional check) and if the current nodes confidence is different from 1
                    # rationale: if the confidence is 1, any rule generated from this node's children is redundant.
                    #            hence in that case, there is no need to walk down further.
                    if not current_node_confidence == 1:
                        child_nodes = list(current_node.children.values())
                        next_nodes.extend(child_nodes)

            if next_nodes:
                _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
                    next_nodes, current_node_antecedent_size + 1
                )

        # use a recursive function to compile the result, starting at the first antecedent nodes in the itemset trie
        _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(
            self.itemsets_trie.get_first_antecedent_after_consequents_nodes(), 1
        )

        # return result
        return result

    def derive_rules_pandas(self, *args, **kwargs):
        """
        Derive association rules and return them as pandas dataframe.

        See derive_rules() for parameter descriptions.
        """
        result = pd.DataFrame(self.derive_rules(*args, **kwargs))
        for list_column in ["consequents", "antecedents"]:
            result[list_column] = result[list_column].map(self.settings.item_separator_for_string_outputs.join)
        # result = result.sort_values(by=["confidence", "support"], ascending=[False, True])
        return result

    def derive_rules_excel(self, filename, *args, **kwargs):
        """
        Derive association rules and save them in an Excel workbook.

        See derive_rules() for parameter descriptions.
        """
        self.derive_rules_pandas(*args, **kwargs).to_excel(filename, header=True, index=False)

    @staticmethod
    def merge_rules_pandas(ruleset_df_1, ruleset_df_2):
        """
        Merge two pandas dataframes containing rules into a single dataframe (to enable parallelization).

        Note: Metrics for duplicate antecedents => consequents rules are aggregated into single rules by using a
              weighted average function, with using the occurrences as weight.
        """
        concatenated_df = pd.concat([ruleset_df_1, ruleset_df_2], ignore_index=True)

        def weighted_average(weight_column):
            return lambda x: np.ma.average(x, weights=concatenated_df.loc[x.index, weight_column])

        result = concatenated_df.groupby(["antecedents", "consequents"]).agg(
            {
                "confidence": weighted_average("occurrences"),
                "lift": weighted_average("occurrences"),
                "occurrences": "sum",
                "support": weighted_average("occurrences"),
                "antecedents_length": "first",
            }
        )
        result.reset_index(level=result.index.name, inplace=True)
        return result
