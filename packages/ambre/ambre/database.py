"""Defines the Database class."""

import random

import pandas as pd
from tqdm import tqdm

from ambre.itemsets_trie import ItemsetsTrie
from ambre.manual_rule import ManualRule
from ambre.preprocessor import Preprocessor
from ambre.settings import Settings


class Database:
    """Transaction database for mining association rules."""

    def __init__(
        self, consequents=[], normalize_whitespace=True, case_insensitive=True, item_separator_for_string_outputs=" ∪ "
    ):
        """Init."""
        self.settings = Settings(consequents, normalize_whitespace, case_insensitive, item_separator_for_string_outputs)
        self.preprocessor = Preprocessor(self.settings)
        self.itemsets_trie = ItemsetsTrie(
            self.preprocessor.normalized_consequents, self.settings.item_separator_for_string_outputs
        )
        self.manual_rules = []

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

    def insert_manual_rule(self, antecedents, consequents, confidence=1):
        """
        Insert a manual rule which is known already.

        Manual rules and rules that become redundant by the manual specified rule are not returned when rules are
        derived. This helps concentrating on rules not known before.
        """
        antecedents = self.preprocessor.normalize_itemset(antecedents)
        consequents = self.preprocessor.normalize_itemset(consequents)
        self.manual_rules.append(ManualRule(antecedents, consequents, confidence))

    def clear_manual_rules(self):
        """Clear all manual rules."""
        self.manual_rules = []

    def derive_frequent_itemsets(
        self,
        filter_to_consequent_itemsets_only=False,
        minimum_itemset_length=0,
        maximum_itemset_length=None,
        minimum_occurences=0,
        maximum_occurences=None,
        minimum_support=0,
        maximum_support=1,
    ):
        """Derive the frequent itemsets from the internally assembled trie and return them as a dict object."""

        def _recursive_trie_walkdown_depth_first(node, level_number):
            result = {"itemset": [], "occurences": [], "support": [], "itemset_length": []}
            for child_item in self.preprocessor.sort_itemset_consequents_first(node.children.keys()):
                child_node = node.children[child_item]
                if level_number == 0 and filter_to_consequent_itemsets_only and not child_node.consequents:
                    # if we reach here, we have passed all consequents (because consequents are iterated first)
                    # => no need to continue => break the recursion
                    break
                itemset_length = child_node.itemset_length
                occurences = child_node.occurences
                support = child_node.support
                if (
                    itemset_length >= minimum_itemset_length
                    and ((maximum_itemset_length is None) or (itemset_length <= maximum_itemset_length))
                    and ((maximum_occurences is None) or (occurences <= maximum_occurences))
                    and (occurences >= minimum_occurences)
                    and (minimum_support <= support <= maximum_support)
                ):
                    result["itemset"].append(child_node.itemset_sorted_list)
                    result["occurences"].append(child_node.occurences)
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
        minimum_confidence=0,
        maximum_confidence=1,
        minimum_lift=0,
        maximum_lift=None,
        minimum_support=0,
        maximum_support=1,
        minimum_occurences=0,
        maximum_occurences=None,
        maximum_antecedent_size=None,
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
                    f"Cannot extract rules because no consequents are defined. To use this function, you need to pass "
                    f"the consequent(s) of interest to the constructor when instantiating this class."
                )
            )

        result = {
            "antecedents": [],
            "consequents": [],
            "confidence": [],
            "lift": [],
            "occurences": [],
            "support": [],
            "antecedents_length": [],
        }

        rules_temp = {}
        for manual_rule in self.manual_rules:
            rules_temp[
                self.preprocessor.itemset_to_string(manual_rule.consequents + manual_rule.antecedents)
            ] = manual_rule.confidence

        def any_preexisting_rule_with_antecedents_subset_and_same_confidence(
            rules_temp, antecedents, consequents, confidence
        ):
            new_itemset = consequents.union(antecedents)
            for rule_itemset, rule_confidence in rules_temp.items():
                if (
                    self.preprocessor.string_to_itemset_set(rule_itemset).issubset(new_itemset)
                    and rule_confidence == confidence
                ):
                    return True
            return False

        def _recursive_trie_walkdown_antecedents_with_consequent_breadth_first(nodes, current_node_antecedent_size):
            next_nodes = []
            for current_node in nodes:
                # add the node as a new rule if certain conditions are met

                # condition: antecedents size is lower or equal than the specified maximum_occurences
                antecedents_length_condition_met = (maximum_antecedent_size is None) or (
                    current_node_antecedent_size <= maximum_antecedent_size
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
                        current_node_occurences = current_node.occurences
                        current_node_lift = current_node.lift
                        current_node_support = current_node.support
                        if (
                            (minimum_confidence <= current_node_confidence <= maximum_confidence)
                            and (minimum_support <= current_node_support <= maximum_support)
                            and (current_node_lift >= minimum_lift)
                            and ((maximum_lift is None) or (current_node_lift <= maximum_lift))
                            and ((maximum_occurences is None) or (current_node_occurences <= maximum_occurences))
                            and (current_node_occurences >= minimum_occurences)
                        ):
                            antecedents = current_node.antecedents
                            consequents = current_node.consequents

                            # condition: there is no rule yet which predicts the same consequents with a subset of the
                            #            current rule's antecedents and the same confidence PLUS there is no manual rule
                            #            yet which matches antecedents and consequents
                            if not any_preexisting_rule_with_antecedents_subset_and_same_confidence(
                                rules_temp, set(antecedents), set(consequents), current_node_confidence
                            ):
                                # add rule to result
                                consequents, antecedents = current_node.consequents_antecedents
                                result["antecedents"].append(antecedents)
                                result["consequents"].append(consequents)
                                result["confidence"].append(current_node_confidence)
                                result["lift"].append(current_node_lift)
                                result["occurences"].append(current_node_occurences)
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
        result = result.sort_values(by=["confidence", "support"], ascending=[False, True])
        return result

    def derive_rules_excel(self, filename, *args, **kwargs):
        """
        Derive association rules and save them in an Excel workbook.

        See derive_rules() for parameter descriptions.
        """
        self.derive_rules_pandas(*args, **kwargs).to_excel(filename, header=True, index=False)
