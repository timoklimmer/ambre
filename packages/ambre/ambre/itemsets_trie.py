"""Everything related to tries."""

from collections import deque

from recordclass import dataobject

from ambre.helpers.strings import decompress_string


class ItemsetsTrie:
    """
    A trie that stores information about the itemsets and corresponding subsets inserted into the database.

    Within the trie, consequents are always at the beginning of a path, with antecedents following. Consequents and
    antecedents are sorted along the path to avoid multiple paths for the same itemset. For performance reasons,
    there is no guarantee however that items are sorted among their siblings.

    Note: Intentionally using duplicate code here to facilitate a port to Rust later.
    """

    def __init__(
        self, normalized_consequents, max_antecedents_length, item_separator_for_string_outputs, item_alphabet
    ):
        """Init."""
        self.root_node = ItemsetNode("", None, self, None, {}, 0)
        self.normalized_consequents = normalized_consequents
        self.max_antecedents_length = max_antecedents_length
        self.item_separator_for_string_outputs = item_separator_for_string_outputs
        self.item_alphabet = item_alphabet
        self.number_transactions = 0
        self.number_nodes = 1

    def insert_normalized_consequents_antecedents(self, consequents, antecedents):
        """Insert the given normalized transaction into the trie."""
        # basic approach: for each node, add all items that follow that node in the itemset as children.
        #                 an itemset of size n leads to 2**n-1 nodes.

        itemset_plus_meta = [(consequent, True) for consequent in consequents] + [
            (antecedent, False) for antecedent in antecedents
        ]

        # option 1: more complex code without recursion
        stack = deque([(self.root_node, 0, 0)])  # node, start_index, antecedents_count

        def _create_or_update_child_node(item_plus_meta):
            nonlocal stack, index
            child_node, _ = node.get_or_create_child(*item_plus_meta)
            child_node.occurrences += 1
            new_antecedents_count = antecedents_count + (child_node.is_consequent is False)
            if (not self.max_antecedents_length) or (new_antecedents_count < self.max_antecedents_length):
                stack.append((child_node, start_index + index + 1, new_antecedents_count))
            index += 1

        while len(stack) > 0:
            node, start_index, antecedents_count = stack.popleft()
            index = 0
            deque(map(_create_or_update_child_node, itemset_plus_meta[start_index:]), maxlen=0)

        # # option 2: easier to understand code but limited by Python recursion limit
        # def _add_itemset_powerset_recursive(self, node, start_index, antecedents_count):
        #     index = 0
        #     for item_plus_meta in itemset_plus_meta[start_index:]:
        #         child_node, _ = node.get_or_create_child(*item_plus_meta)
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

    def get_all_consequent_nodes(self):
        """Return all consequent nodes."""
        result = []

        def _recursive_trie_walkdown_breadth_first(nodes):
            next_nodes = []
            for current_node in nodes:
                if current_node.is_consequent:
                    result.append(current_node)
                    next_nodes.extend(list(current_node.children.values()))
            if next_nodes:
                _recursive_trie_walkdown_breadth_first(next_nodes)

        _recursive_trie_walkdown_breadth_first(self.get_consequent_root_nodes())
        return result

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

    def merge(self, itemsets_trie):
        """Merge the given itemsets trie into this itemsets trie."""
        source_itemsets_trie = itemsets_trie
        target_itemsets_trie = self
        stack = deque([(source_itemsets_trie.root_node, target_itemsets_trie.root_node)])
        while len(stack) > 0:
            source_node, target_node = stack.pop()
            for source_child in source_node.children.values():
                target_child, _ = target_node.get_or_create_child(source_child.item, source_child.is_consequent)
                target_child.occurrences += source_child.occurrences
                stack.append((source_child, target_child))
        return self

    def print(self, to_string=False):
        """
        Print the itemsets trie.

        If to_string is set to True, the function returns a string containing the result instead of printing.
        """
        result_lines = []

        def _our_own_print(message):
            if to_string:
                result_lines.append(message)
            else:
                print(message)

        _our_own_print("Occurrences | Support | Confidence | Lift   | Path")
        _our_own_print("-" * 80)
        stack = deque([self.root_node])
        while len(stack) > 0:
            current_node = stack.pop()
            if current_node.itemset_length != 0:
                current_node_itemset_length = current_node.itemset_length
                indentation = 2 * (current_node_itemset_length - 1) * " "
                edge = " └ " if current_node_itemset_length > 1 else ""
                itemset = f"{'(' if current_node.is_consequent else ''}{current_node}{')' if current_node.is_consequent else ''}"
                _our_own_print(
                    (
                        f"{current_node.occurrences}".rjust(11)
                        + " | "
                        + f"{current_node.support:.2f}".rjust(7)
                        + " | "
                        + f"{current_node.confidence:.2f}".rjust(10)
                        + " | "
                        + f"{current_node.lift:.2f}".rjust(6)
                        + " | "
                        + f"{indentation}{edge}{itemset}"
                    )
                )
            for source_child in sorted(
                current_node.children.values(),
                reverse=True,
            ):
                stack.append(source_child)

        _our_own_print(f"\nTotal number of transactions: {self.number_transactions}")
        _our_own_print(f"Total number of nodes (incl. root node): {self.number_nodes}")

        if to_string:
            return "\n".join(result_lines)


class ItemsetNode(dataobject):
    """An itemset within an itemset trie."""

    __fields__ = "item", "parent_node", "itemsets_trie", "is_consequent", "children", "occurrences"
    __options__ = {"fast_new": True}

    def __init__(self, item, parent_node, itemsets_trie, is_consequent, children, occurrences):
        """
        Init.

        Parameter 'children' should be a dict with items as keys and values as nodes.
        """
        self.item: str = item
        self.children: dict = children
        self.parent_node: ItemsetNode = parent_node
        self.itemsets_trie: ItemsetsTrie = itemsets_trie
        self.is_consequent: bool = is_consequent
        self.occurrences: int = occurrences

    def __repr__(self):
        """More comfortable string representation of the object."""
        return self.itemsets_trie.item_separator_for_string_outputs.join(self.itemset_sorted_list)

    def get_or_create_child(self, item, is_consequent):
        """Get or create a child node."""
        created_new_child = False
        child_node = self.children.get(item, None)
        if child_node is None:
            new_child_node = ItemsetNode(item, self, self.itemsets_trie, is_consequent, {}, 0)
            self.children[item] = new_child_node
            self.itemsets_trie.number_nodes += 1
            child_node = new_child_node
            created_new_child = True
        return child_node, created_new_child

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
        result = 0
        iterated_node = self
        while iterated_node.parent_node is not None:
            result += 1
            iterated_node = iterated_node.parent_node
        return result

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
        # return self.support / self.itemsets_trie.get_itemset_node(self.antecedents).support
        antecedents = self.antecedents
        if self.antecedents:
            return self.support / self.itemsets_trie.get_itemset_node(antecedents).support
        return 1

    @property
    def lift(self):
        """Return the itemset's confidence."""
        consequents, antecedents = self.consequents_antecedents
        if self.antecedents and self.consequents:
            return self.support / (
                self.itemsets_trie.get_itemset_node(antecedents).support
                * self.itemsets_trie.get_itemset_node(consequents).support
            )
        return 1
