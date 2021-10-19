"""Everything related to tries."""

import sys
from itertools import chain, combinations


class ItemsetsTrie:
    """
    A trie that stores information about the itemsets and corresponding subsets inserted into the database.

    Within the trie, consequents are always at the beginning of a path, with antecedents following. Consequents and
    antecedents are sorted along the path to avoid multiple paths for the same itemset. For performance reasons,
    there is no guarantee however that items are sorted among their siblings.

    Note: Intentionally using duplicate code here to facilitate a port to Rust later.
    """

    def __init__(self, normalized_consequents, max_antecedents_length, item_separator_for_string_outputs):
        """Init."""
        self.root_node = ItemsetNode("", None, self, None)
        self.normalized_consequents = normalized_consequents
        self.max_antecedents_length = max_antecedents_length
        self.item_separator_for_string_outputs = item_separator_for_string_outputs
        self.number_transactions = 0

    def insert_normalized_consequents_antecedents_tuple(self, normalized_consequents_antecedents_tuple):
        """Insert the given normalized transaction."""
        consequents, antecedents = (
            normalized_consequents_antecedents_tuple[0],
            normalized_consequents_antecedents_tuple[1],
        )
        if not self.max_antecedents_length:
            for itemset in ItemsetsTrie._powerset(consequents + antecedents):
                self.insert_subset(itemset)
        else:
            for consequent_subset in ItemsetsTrie._powerset(consequents):
                for antecedent_subset in ItemsetsTrie._powerset(antecedents, self.max_antecedents_length):
                    self.insert_subset(consequent_subset + antecedent_subset)
        self.number_transactions += 1

    def insert_subset(self, itemset):
        """Insert the given subset into the trie."""
        # note: this function is called very often. if changes are made ensure that the performance does not decrease
        #       accidentially.
        node = self.root_node
        items = len(itemset) - 1
        for i, item in enumerate(itemset):
            is_last_item = i == items
            try:
                node = node.children[item]
            except KeyError:
                is_consequent = item in self.normalized_consequents
                new_node = ItemsetNode(item, node, self, is_consequent)
                node.children[item] = new_node
                node = new_node
            if is_last_item:
                node.occurrences += 1

    def get_itemset_node(self, itemset):
        """Get the itemset node from the trie which represents the specified itemset."""
        if not itemset:
            raise ValueError("Parameter 'itemset' is None or empty.")
        node = self.root_node
        for item in itemset:
            if item in node.children:
                node = node.children[item]
            else:
                raise ValueError(
                    (
                        f"Itemset '{itemset}' could not be found. Ensure that a corresponding itemset was inserted "
                        f"before and that evtl. preprocessing transformations are considered."
                    )
                )
        return node

    def get_consequent_root_nodes(self):
        """Return all children from the root node that are a consequent."""
        return [node for node in list(self.root_node.children.values()) if node.is_consequent]

    def get_first_antecedent_after_consequents_nodes(self):
        """Return all nodes which are the first antecedent after the consequent nodes."""
        result = []

        def _recursive_trie_walkdown_breadth_first(nodes):
            next_nodes = []
            for current_node in nodes:
                if current_node.is_consequent:
                    next_nodes.extend(list(current_node.children.values()))
                else:
                    result.append(current_node)
            if next_nodes:
                _recursive_trie_walkdown_breadth_first(next_nodes)

        _recursive_trie_walkdown_breadth_first(self.get_consequent_root_nodes())
        return result

    @staticmethod
    def _powerset(iterable, max_subset_length=sys.maxsize):
        """Return the powerset of the items in the given iterable."""
        items = list(iterable)
        return chain.from_iterable(
            combinations(items, subset_length) for subset_length in range(min(max_subset_length, len(items)) + 1)
        )


class ItemsetNode:
    """An itemset within an itemset trie."""

    # note: some properties are intentionally not using singleton patterns to save memory and to enable online updates
    #       without the need to clear caches

    def __init__(self, item, parent_node, itemsets_trie, is_consequent):
        """Init."""
        self.item = item
        self.children = {}  # keys are items, values are nodes
        self.parent_node = parent_node
        self.itemsets_trie = itemsets_trie
        self.is_consequent = is_consequent
        self.occurrences = 0

    def __repr__(self):
        """More comfortable string representation of the object."""
        return self.itemsets_trie.item_separator_for_string_outputs.join(self.itemset_sorted_list)

    @property
    def itemset_unsorted_set(self):
        """Return itemset as unsorted set."""
        result = set()
        iterated_node = self
        while iterated_node.parent_node is not None:
            result = result.union({iterated_node.item})
            iterated_node = iterated_node.parent_node
        return result

    @property
    def itemset_sorted_list(self):
        """Return itemset as sorted list."""
        result = []
        iterated_node = self
        while iterated_node.parent_node is not None:
            result = [iterated_node.item] + result
            iterated_node = iterated_node.parent_node
        return result

    @property
    def itemset_length(self):
        """Return the number of items in the itemset."""
        return len(self.itemset_unsorted_set)

    @property
    def consequents(self):
        """Return the itemset's consequents."""
        consequents, _ = self.consequents_antecedents
        return consequents

    @property
    def antecedents(self):
        """Return the itemset's antecedents."""
        _, antecedents = self.consequents_antecedents
        return antecedents

    @property
    def consequents_antecedents(self):
        """Return the itemset's consequents and antecedents."""
        antecedents = []
        consequents = []
        iterated_node = self
        while iterated_node.parent_node is not None:
            if iterated_node.is_consequent:
                consequents.insert(0, iterated_node.item)
            else:
                antecedents.insert(0, iterated_node.item)
            iterated_node = iterated_node.parent_node
        return consequents, antecedents

    @property
    def support(self):
        """Return the itemset's relative support."""
        return self.occurrences / self.itemsets_trie.number_transactions

    @property
    def confidence(self):
        """Return the itemset's confidence."""
        return self.support / self.itemsets_trie.get_itemset_node(self.antecedents).support

    @property
    def lift(self):
        """Return the itemset's confidence."""
        consequents, antecedents = self.consequents_antecedents
        return self.support / (
            self.itemsets_trie.get_itemset_node(antecedents).support
            * self.itemsets_trie.get_itemset_node(consequents).support
        )
