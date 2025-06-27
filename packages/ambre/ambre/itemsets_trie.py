"""Everything related to the itemsets trie."""

from collections import deque

from recordclass import dataobject
from tqdm import tqdm

from ambre.strings import compress_string, decompress_string


class ItemsetsTrie:
    """
    A trie that stores the itemsets and corresponding powersets inserted into the database.

    Within the trie, nodes are always sorted such that consequents come first, then followed by antecedents. Consequents
    and antecedents are also sorted within their group.

    For memory optimization, nodes don't store the full item names. Instead, a string compression/decompression is
    applied, based on an alphabet allowing/disallowing characters in item's names. The compression does not impact
    sorting. Nodes are always sorted as if there was no compression at all.

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

        def _print_node_info(node):
            if node.itemset_length != 0:
                current_node_itemset_length = node.itemset_length
                indentation = 2 * (current_node_itemset_length - 1) * " "
                edge = " └ " if current_node_itemset_length > 1 else ""
                itemset_node_as_string = node.with_consequents_highlighted()
                _our_own_print(
                    (
                        f"{node.occurrences}".rjust(11)
                        + " | "
                        + f"{node.support:.2f}".rjust(7)
                        + " | "
                        + f"{node.confidence:.2f}".rjust(10)
                        + " | "
                        + f"{node.lift:.2f}".rjust(6)
                        + " | "
                        + f"{indentation}{edge}{itemset_node_as_string}"
                    )
                )

        self.visit_itemset_nodes_depth_first(_print_node_info)

        _our_own_print(f"\nTotal number of transactions: {self.number_transactions}")
        _our_own_print(f"Total number of nodes (incl. root node): {self.number_nodes}")

        if to_string:
            return "\n".join(result_lines)
        return None

    def get_node_from_compressed(self, compressed_itemset, skip_unknown_items=False, none_if_not_exists=False):
        """Get the itemset node from the trie representing the specified itemset (assuming compressed items)."""
        if not compressed_itemset:
            raise ValueError("Parameter 'compressed_itemset' is None or empty.")
        node = self.root_node
        for compressed_item in compressed_itemset:
            # item is known
            if compressed_item in node.children:
                node = node.children[compressed_item]
            else:
                # item is unknown
                if none_if_not_exists:
                    return None
                if not skip_unknown_items:
                    # skip_unknown_items is false -> raise exception
                    uncompressed_itemset = [
                        decompress_string(item, original_input_alphabet=self.item_alphabet)
                        for item in compressed_itemset
                    ]
                    raise ValueError(
                        (
                            f"Cannot find node for the given itemset (uncompressed: {uncompressed_itemset}). Ensure that "
                            f"the specified node is contained in the trie."
                        )
                    )
                else:
                    # skip_unknown_items is true -> skip item and continue
                    pass
        return node

    def get_node_from_uncompressed(self, uncompressed_itemset, skip_unknown_items=False):
        """Get the itemset node from the trie representing the specified itemset (assuming uncompressed items)."""
        if not uncompressed_itemset:
            raise ValueError("Parameter 'uncompressed_itemset' is None or empty.")
        return self.get_node_from_compressed(
            list(compress_string(item, input_alphabet=self.item_alphabet) for item in uncompressed_itemset),
            skip_unknown_items=skip_unknown_items,
        )

    def visit_itemset_nodes_depth_first(
        self, visitor_function, only_with_consequents=False, show_progress_bar=False, progress_bar_text=None
    ):
        """
        Walk through all itemsets (nodes) and visit them with the given visitor_function, using depth first.

        Visitor functions can control the walk by returning one of the following results:
            - "skip_children" skips the node's children and proceeds with the next node on the right
            - "stop" stops the entire walk
            - "next_node" or any other value continues with the next node.

        For convenience, the root node is not visited.

        By setting only_with_consequents to True, only nodes containing consequents in the itemset are
        visited.
        """
        progress_bar = tqdm(total=self.number_nodes - 1) if show_progress_bar else None
        if progress_bar:
            progress_bar.set_description(progress_bar_text)
        try:
            next_node = self.root_node
            while True:
                # stop if we have reached the nodes starting with antecedents and only_with_consequents is set
                if only_with_consequents and next_node.parent_node == self.root_node and not next_node.is_consequent:
                    if progress_bar:
                        progress_bar.update(progress_bar.total - progress_bar.n)
                    return
                # visit next node
                next_action = "next_node"
                if next_node != self.root_node:
                    next_action = visitor_function(next_node)
                    if progress_bar:
                        progress_bar.update(1)
                # stop on stop request
                if next_action == "stop":
                    if progress_bar:
                        progress_bar.update(progress_bar.total - progress_bar.n)
                    return
                # determine next node
                if next_node.first_child is not None and next_action != "skip_children":
                    # walk down if possible
                    next_node = next_node.first_child
                else:
                    # else walk up (until there is a parent that has a sibling)...
                    while not next_node.next_sibling:
                        if next_node == self.root_node:
                            if progress_bar:
                                progress_bar.update(progress_bar.total - progress_bar.n)
                            return
                        next_node = next_node.parent_node
                    # ...and right
                    next_node = next_node.next_sibling
        finally:
            if progress_bar:
                progress_bar.close()

    def get_all_consequent_nodes_depth_first(self):
        """Return all consequent nodes, using depth-first search."""
        result = []

        def _collect_result(node):
            if node.is_consequent:
                result.append(node)
                return None
            return "skip_children"

        self.visit_itemset_nodes_depth_first(_collect_result, only_with_consequents=True)
        return result

    def get_consequent_root_nodes(self):
        """Return all children from the root node that are a consequent."""
        return [node for node in list(self.root_node.children.values()) if node.is_consequent]

    def get_first_antecedent_after_consequents_nodes(self):
        """Return all nodes which are the first antecedent after the consequent nodes."""
        result = []

        def _append_if_first_antecedent(node):
            """Append the node if it is the antecedent after a consequent node."""
            if not node.is_consequent:
                result.append(node)
                return "skip_children"
            return "next_node"

        self.visit_itemset_nodes_depth_first(_append_if_first_antecedent, only_with_consequents=True)
        return result

    def insert_consequents_antecedents_compressed(self, consequents, antecedents):
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

    def has_consequents_antecedents_compressed(self, itemset):
        """Check if the trie has the given normalized and compression transaction."""
        return self.get_node_from_compressed(itemset, none_if_not_exists=True) is not None

    def remove_consequents_antecedents_compressed(self, consequents, antecedents, silent):
        """Remove the given normalized and compressed transaction from the trie."""
        transaction_normalized_compressed = consequents + antecedents
        # ensure that the trie has transactions
        if self.number_transactions == 0:
            raise ValueError("The database is empty. There are no transactions to remove.")
        # ensure that the transaction exists
        if not self.has_consequents_antecedents_compressed(transaction_normalized_compressed):
            if silent:
                return
            raise ValueError(
                f"The transaction {consequents + antecedents} cannot be removed because it was not inserted before."
            )
        # navigate through and update the trie
        for start_index in range(len(transaction_normalized_compressed)):
            leaf_node = self.get_node_from_compressed(transaction_normalized_compressed[start_index:])
            current_node = leaf_node
            while current_node is not self.root_node:
                current_node.occurrences -= 1
                if current_node.occurrences == 0:
                    del current_node.parent_node.children[current_node.compressed_item]
                    self.number_nodes -= 1
                current_node = current_node.parent_node
        # update the number of transactions
        self.number_transactions -= 1

    def merge(self, itemsets_trie):
        """Merge the given itemsets trie into this itemsets trie."""
        source_itemsets_trie = itemsets_trie
        target_itemsets_trie = self
        stack = deque([(source_itemsets_trie.root_node, target_itemsets_trie.root_node)])
        while len(stack) > 0:
            source_node, target_node = stack.pop()
            for source_child in source_node.children.values():
                target_child, _ = target_node.get_or_create_child(
                    source_child.compressed_item, source_child.is_consequent, item_is_compressed=True
                )
                target_child.occurrences += source_child.occurrences
                stack.append((source_child, target_child))
        return self


class ItemsetNode(dataobject):
    """An itemset within an itemset trie."""

    __fields__ = "compressed_item", "parent_node", "itemsets_trie", "is_consequent", "children", "occurrences"
    __options__ = {"fast_new": True}

    def __init__(self, compressed_item, parent_node, itemsets_trie, is_consequent, children, occurrences):
        """
        Init.

        Parameter 'children' should be a dict with items as keys and values as nodes.
        """
        self.compressed_item: str = compressed_item
        self.children: dict = children
        self.parent_node: ItemsetNode = parent_node
        self.itemsets_trie: ItemsetsTrie = itemsets_trie
        self.is_consequent: bool = is_consequent
        self.occurrences: int = occurrences

    def __repr__(self):
        """More comfortable string representation of the object."""
        return self.itemsets_trie.item_separator_for_string_outputs.join(self.itemset_items_uncompressed_sorted)

    def with_consequents_highlighted(self):
        """Return a string representation of the node with all consequents highlighted."""
        decompressed_items = [
            f"{'(' if node.is_consequent else ''}"
            f"{decompress_string(node.compressed_item, original_input_alphabet=self.itemsets_trie.item_alphabet)}"
            f"{')' if node.is_consequent else ''}"
            for node in self.itemset_items_compressed_sorted
        ]
        return self.itemsets_trie.item_separator_for_string_outputs.join(decompressed_items)

    @property
    def first_child(self):
        """Return the node's first child."""
        if not self.children:
            return None
        try:
            return self.children[next(iter(self.children))]
        except StopIteration:
            return None

    @property
    def next_sibling(self):
        """Return the node's next sibling."""
        if self.parent_node is None:
            return None
        sibling_iterator = iter(self.parent_node.children)
        try:
            while next(sibling_iterator) != self.compressed_item:
                pass
            return self.parent_node.children[next(sibling_iterator)]
        except StopIteration:
            return None

    @property
    def next_node_on_same_level(self):
        """Return the node's next node on the same level."""
        next_sibling = self.next_sibling
        if next_sibling:
            return next_sibling
        if self.parent_node:
            next_right_parent = self.parent_node
            while (next_right_parent := next_right_parent.next_sibling) is not None:
                if next_right_parent is None:
                    return None
                next_parent_first_child = next_right_parent.first_child
                if next_parent_first_child:
                    return next_parent_first_child
        return None

    @property
    def itemset_items_compressed_sorted(self):
        """Return a sorted list of the compressed itemset's nodes (consequents first, items sorted within groups)."""
        result = []
        iterated_node = self
        while iterated_node.parent_node is not None:
            result = [iterated_node] + result
            iterated_node = iterated_node.parent_node
        return result

    @property
    def itemset_items_uncompressed_sorted(self):
        """Return itemset represented by this node, sorted by uncompressed items with consequences first."""
        return [
            decompress_string(node.compressed_item, original_input_alphabet=self.itemsets_trie.item_alphabet)
            for node in self.itemset_items_compressed_sorted
        ]

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
    def antecedents_length(self):
        """Return the length of the itemset's antecedents."""
        result = 0
        iterated_node = self
        while iterated_node is not None:
            if not iterated_node.is_consequent:
                result += 1
            else:
                return result
            iterated_node = iterated_node.parent_node
        return result

    @property
    def has_consequents(self):
        """Check if the itemset contains consequents."""
        iterated_node = self
        while iterated_node is not None:
            if iterated_node.is_consequent:
                return True
            iterated_node = iterated_node.parent_node
        return False

    @property
    def has_antecedents(self):
        """Check if the itemset contains antecedents."""
        return not self.is_consequent

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
        """Return the itemset's consequents and antecedents, compressed."""
        antecedents_compressed = []
        consequents_compressed = []
        iterated_node = self
        while iterated_node.parent_node is not None:
            if iterated_node.is_consequent:
                consequents_compressed.insert(0, iterated_node.compressed_item)
            else:
                antecedents_compressed.insert(0, iterated_node.compressed_item)
            iterated_node = iterated_node.parent_node
        return consequents_compressed, antecedents_compressed

    @property
    def consequents_antecedents_uncompressed(self):
        """Return the itemset's consequents and antecedents, uncompressed."""
        consequents_compressed, antecedents_compressed = self.consequents_antecedents_compressed
        return [
            decompress_string(item, original_input_alphabet=self.itemsets_trie.item_alphabet)
            for item in consequents_compressed
        ], [
            decompress_string(item, original_input_alphabet=self.itemsets_trie.item_alphabet)
            for item in antecedents_compressed
        ]

    @property
    def support(self):
        """Return the itemset's relative support."""
        return self.occurrences / self.itemsets_trie.number_transactions

    @property
    def confidence(self):
        """Return the confidence of the rule antecedents => consequents."""
        antecedents_compressed = self.antecedents_compressed
        if antecedents_compressed:
            return self.support / self.itemsets_trie.get_node_from_compressed(antecedents_compressed).support
        return 1.0

    @property
    def lift(self):
        """Return the lift of the rule antecedents => consequents."""
        consequents_compressed, antecedents_compressed = self.consequents_antecedents_compressed
        if antecedents_compressed and consequents_compressed:
            return self.support / (
                self.itemsets_trie.get_node_from_compressed(antecedents_compressed).support
                * self.itemsets_trie.get_node_from_compressed(consequents_compressed).support
            )
        return 1.0

    def get_or_create_child(self, item, is_consequent, item_is_compressed=False):
        """Get or create a child node."""
        compressed_item = (
            compress_string(item, input_alphabet=self.itemsets_trie.item_alphabet) if not item_is_compressed else item
        )
        child_node = self.children.get(compressed_item, None)
        created_new_child = False
        if child_node is None:
            new_child_node = ItemsetNode(compressed_item, self, self.itemsets_trie, is_consequent, {}, 0)

            # Performance optimization: avoid sorting when possible
            if not self.children:
                # First child - just add it
                self.children[compressed_item] = new_child_node
            elif len(self.children) == 1:
                # Only one existing child - simple comparison is sufficient
                existing_item, existing_node = next(iter(self.children.items()))
                item_alphabet = self.itemsets_trie.item_alphabet

                existing_decompressed = decompress_string(existing_item, original_input_alphabet=item_alphabet)
                new_decompressed = decompress_string(compressed_item, original_input_alphabet=item_alphabet)

                existing_sort_key = (not existing_node.is_consequent, existing_decompressed)
                new_sort_key = (not is_consequent, new_decompressed)

                if new_sort_key < existing_sort_key:
                    # New item comes first
                    self.children = {compressed_item: new_child_node, existing_item: existing_node}
                else:
                    # Existing item comes first
                    self.children[compressed_item] = new_child_node
            else:
                # Multiple children - need to sort
                item_alphabet = self.itemsets_trie.item_alphabet

                # Create list of (sort_key, compressed_item, node) tuples for efficient sorting
                items_with_keys = []
                for existing_compressed, existing_node in self.children.items():
                    existing_decompressed = decompress_string(
                        existing_compressed, original_input_alphabet=item_alphabet
                    )
                    existing_sort_key = (not existing_node.is_consequent, existing_decompressed)
                    items_with_keys.append((existing_sort_key, existing_compressed, existing_node))

                # Add new item
                new_decompressed = decompress_string(compressed_item, original_input_alphabet=item_alphabet)
                new_sort_key = (not is_consequent, new_decompressed)
                items_with_keys.append((new_sort_key, compressed_item, new_child_node))

                # Sort and rebuild dict
                items_with_keys.sort(key=lambda x: x[0])
                self.children = {compressed: node for _, compressed, node in items_with_keys}

            self.itemsets_trie.number_nodes += 1
            child_node = new_child_node
            created_new_child = True
        return child_node, created_new_child
