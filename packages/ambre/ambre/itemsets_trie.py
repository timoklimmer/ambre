"""Everything related to tries."""

from collections import deque

from recordclass import dataobject


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

    def insert_normalized_consequents_antecedents(self, consequents, antecedents):
        """Insert the given normalized transaction to the trie."""
        # basic approach: for each node, add all items that follow that node in the itemset as children.
        #                 an itemset of size n leads to 2**n-1 nodes.
        itemset_plus_meta = [(consequent, True) for consequent in consequents] + [
            (antecedent, False) for antecedent in antecedents
        ]
        # more complex code without recursion
        stack = deque([(self.root_node, 0, 0)])  # node, start_index, antecedents_count
        stack_height = 1

        def _update_child_item(item_plus_meta):
            nonlocal stack_height, index
            child_node = node.get_or_create_child(*item_plus_meta)
            child_node.occurrences += 1
            new_antecedents_count = antecedents_count + (child_node.is_consequent is False)
            if (not self.max_antecedents_length) or (new_antecedents_count < self.max_antecedents_length):
                stack.append((child_node, start_index + index + 1, new_antecedents_count))
                stack_height += 1
            index += 1

        while stack_height > 0:
            node, start_index, antecedents_count = stack.popleft()
            stack_height -= 1
            index = 0
            deque(map(_update_child_item, itemset_plus_meta[start_index:]), maxlen=0)

        # # easier to understand code but limited by Python recursion limit
        # def _add_itemset_powerset_recursive(self, node, start_index, antecedents_count):
        #     index = 0
        #     for item_plus_meta in itemset_plus_meta[start_index:]:
        #         child_node = node.get_or_create_child(*item_plus_meta)
        #         child_node.occurrences += 1
        #         new_antecedents_count = antecedents_count + (child_node.is_consequent is False)
        #         if (not self.max_antecedents_length) or (new_antecedents_count < self.max_antecedents_length):
        #             _add_itemset_powerset_recursive(
        #                 self,
        #                 child_node,
        #                 start_index + index + 1,
        #                 new_antecedents_count,
        #             )
        #         index += 1

        # _add_itemset_powerset_recursive(self, self.root_node, 0, 0)

        self.number_transactions += 1

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


class ItemsetNode(dataobject):
    """An itemset within an itemset trie."""

    __fields__ = "item", "children", "parent_node", "itemsets_trie", "is_consequent", "occurrences"
    __options__ = {"fast_new": True}

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

    def get_or_create_child(self, item, is_consequent):
        """Get or create a child node."""
        try:
            child_node = self.children[item]
        except KeyError:
            new_child_node = ItemsetNode(item, self, self.itemsets_trie, is_consequent)
            self.children[item] = new_child_node
            child_node = new_child_node
        return child_node

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
