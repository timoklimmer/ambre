"""Everything related to tries."""

from collections import deque

from recordclass import dataobject

from ambre.helpers.strings import compress_string, decompress_string


class ItemsetsTrie:
    """
    A trie that stores information about the itemsets and corresponding powersets inserted into the database.

    Within the trie, nodes are always sorted such that consequents come first, then followed by antecedents. Consequents
    and antecedents are also sorted within their group.

    Use the .print() method to visualize the trie.
    """

    def __init__(
        self,
        normalized_consequents,
        compressed_consequents,
        max_antecedents_length,
        item_separator_for_string_outputs,
        item_alphabet,
    ):
        """Init."""
        self.root_node = ItemsetNode("", None, self, None, {}, 0)
        self.normalized_consequents = normalized_consequents
        self.compressed_consequents = compressed_consequents
        self.max_antecedents_length = max_antecedents_length
        self.item_separator_for_string_outputs = item_separator_for_string_outputs
        self.item_alphabet = item_alphabet
        self.number_transactions = 0
        self.number_nodes = 1

    def insert_normalized_consequents_antecedents_compressed(self, consequents, antecedents):
        """Insert the given normalized and compressed transaction into the trie."""
        # basic approach: for each node, add all items that follow that node in the itemset as children.
        #                 an itemset of size n leads to 2**n-1 nodes.

        itemset_plus_meta = [(consequent, True) for consequent in consequents] + [
            (antecedent, False) for antecedent in antecedents
        ]

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

        self.number_transactions += 1


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
                itemset_node_as_string = current_node.with_consequents_highlighted()
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
                        + f"{indentation}{edge}{itemset_node_as_string}"
                    )
                )
            for source_child in reversed(current_node.children.values()):
                stack.append(source_child)

        _our_own_print(f"\nTotal number of transactions: {self.number_transactions}")
        _our_own_print(f"Total number of nodes (incl. root node): {self.number_nodes}")

        if to_string:
            return "\n".join(result_lines)

    def merge(self, itemsets_trie):
        """Merge the given itemsets trie into this itemsets trie."""
        source_itemsets_trie = itemsets_trie
        target_itemsets_trie = self
        stack = deque([(source_itemsets_trie.root_node, target_itemsets_trie.root_node)])
        while len(stack) > 0:
            source_node, target_node = stack.pop()
            for source_child in source_node.children.values():
                target_child, _ = target_node.get_or_create_child(
                    source_child.item, source_child.is_consequent, item_is_compressed=True
                )
                target_child.occurrences += source_child.occurrences
                stack.append((source_child, target_child))
        return self

    def walk_through_all_consequent_nodes_depth_first(self):
        """Yield all consequent nodes, using depth-first search."""
        result = []
        stack = deque([self.root_node])
        is_root_node = True
        while len(stack) > 0:
            current_node = stack.pop()
            if not is_root_node:
                if current_node.is_consequent:
                    result.append(current_node)
                    next_children = [
                        child_node for child_node in current_node.children.values() if child_node.is_consequent
                    ]
            else:
                next_children = [
                    child_node for child_node in current_node.children.values() if child_node.is_consequent
                ]
            for child in reversed(next_children):
                stack.append(child)
            is_root_node = False
        return result

    def get_itemset_node_from_compressed(self, compressed_itemset):
        """Get the itemset node from the trie representing the specified itemset (assuming compressed items)."""
        if not compressed_itemset:
            raise ValueError("Parameter 'compressed_itemset' is None or empty.")
        node = self.root_node
        for compressed_item in compressed_itemset:
            if compressed_item in node.children:
                node = node.children[compressed_item]
            else:
                uncompressed_itemset = [
                    decompress_string(item, original_input_alphabet=self.item_alphabet) for item in compressed_itemset
                ]
                raise ValueError(
                    (
                        f"Cannot find node for the given itemset (uncompressed: {uncompressed_itemset}). Ensure that "
                        f"the specified node is contained in the trie."
                    )
                )
        return node

    def get_itemset_node_from_uncompressed(self, uncompressed_itemset):
        """Get the itemset node from the trie representing the specified itemset (assuming uncompressed items)."""
        if not uncompressed_itemset:
            raise ValueError("Parameter 'uncompressed_itemset' is None or empty.")
        return self.get_itemset_node_from_compressed(
            list(compress_string(item, input_alphabet=self.item_alphabet) for item in uncompressed_itemset)
        )

    def get_consequent_root_nodes(self):
        """Return all children from the root node that are a consequent."""
        return [node for node in list(self.root_node.children.values()) if node.is_consequent]

    def get_first_antecedent_after_consequents_nodes(self):
        """Return all nodes which are the first antecedent after the consequent nodes."""
        # TODO: refactor to depth-first search
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
        return self.itemsets_trie.item_separator_for_string_outputs.join(self.itemset_sorted_list_uncompressed)

    def with_consequents_highlighted(self):
        """Return a string representation of the node with all consequents highlighted."""
        decompressed_items = [
            f"{'(' if node.is_consequent else ''}"
            f"{decompress_string(node.item, original_input_alphabet=self.itemsets_trie.item_alphabet)}"
            f"{')' if node.is_consequent else ''}"
            for node in self.itemset_nodes
        ]
        return self.itemsets_trie.item_separator_for_string_outputs.join(decompressed_items)

    def get_or_create_child(self, item, is_consequent, item_is_compressed=False):
        """Get or create a child node."""
        compressed_item = (
            compress_string(item, input_alphabet=self.itemsets_trie.item_alphabet) if not item_is_compressed else item
        )
        child_node = self.children.get(compressed_item, None)
        created_new_child = False
        if child_node is None:
            new_child_node = ItemsetNode(compressed_item, self, self.itemsets_trie, is_consequent, {}, 0)
            item_alphabet = self.itemsets_trie.item_alphabet
            self.children = {
                key: value
                for key, value in sorted(
                    list(self.children.items()) + [(compressed_item, new_child_node)],
                    key=lambda t: (
                        not t[1].is_consequent,
                        decompress_string(t[0], original_input_alphabet=item_alphabet),
                    ),
                )
            }
            self.itemsets_trie.number_nodes += 1
            child_node = new_child_node
            created_new_child = True
        return child_node, created_new_child

    @property
    def itemset_sorted_list_uncompressed(self):
        """Return itemset represented by this node, sorted by uncompressed items with consequences first."""
        return [
            decompress_string(node.item, original_input_alphabet=self.itemsets_trie.item_alphabet)
            for node in self.itemset_nodes
        ]

    @property
    def itemset_nodes(self):
        """Return a sorted list of all nodes leading to the itemset (consequents first)."""
        result = []
        iterated_node = self
        while iterated_node.parent_node is not None:
            result = [iterated_node] + result
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
    def consequents_compressed(self):
        """Return the itemset's consequents."""
        result, _ = self.consequents_antecedents_compressed
        return result

    @property
    def antecedents_compressed(self):
        """Return the itemset's antecedents."""
        _, result = self.consequents_antecedents_compressed
        return result

    @property
    def consequents_antecedents_compressed(self):
        """Return the itemset's consequents and antecedents."""
        antecedents_compressed = []
        consequents_compressed = []
        iterated_node = self
        while iterated_node.parent_node is not None:
            if iterated_node.is_consequent:
                consequents_compressed.insert(0, iterated_node.item)
            else:
                antecedents_compressed.insert(0, iterated_node.item)
            iterated_node = iterated_node.parent_node
        return consequents_compressed, antecedents_compressed

    @property
    def support(self):
        """Return the itemset's relative support."""
        return self.occurrences / self.itemsets_trie.number_transactions

    @property
    def confidence(self):
        """Return the itemset's confidence."""
        antecedents_compressed = self.antecedents_compressed
        if antecedents_compressed:
            return self.support / self.itemsets_trie.get_itemset_node_from_compressed(antecedents_compressed).support
        return 1

    @property
    def lift(self):
        """Return the itemset's confidence."""
        consequents_compressed, antecedents_compressed = self.consequents_antecedents_compressed
        if antecedents_compressed and consequents_compressed:
            return self.support / (
                self.itemsets_trie.get_itemset_node_from_compressed(antecedents_compressed).support
                * self.itemsets_trie.get_itemset_node_from_compressed(consequents_compressed).support
            )
        return 1
