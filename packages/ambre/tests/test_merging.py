"""Test the database merging."""

import pytest
from ambre import Database


def test_merging_can_merge_database_pair():
    """Test if we can correctly merge two databases."""
    # set up two databases
    database1 = Database(["bread", "milk"])
    database1.insert_transaction(["milk", "bread"])
    database1.insert_transaction(["butter"])
    database2 = database1.copy()
    database2.insert_transaction(["beer", "diapers"])
    database2.insert_transaction(["milk", "bread", "butter"])
    database2.insert_transaction(["bread"])

    # merge the databases
    # note: as the inplace parameter is set to true by default, this will modify the bigger of the two databases
    merged_database = Database.merge_databases(database1, database2)

    # assert that the merge was successful
    expected_itemsets_trie_string = (
        """
Occurrences | Support | Confidence | Lift   | Path
--------------------------------------------------------------------------------
          1 |    0.14 |       1.00 |   1.00 | beer
          1 |    0.14 |       1.00 |   1.00 |    └ beer ∪ diapers
          4 |    0.57 |       1.00 |   1.00 | (bread)
          1 |    0.14 |       0.33 |   0.58 |    └ bread ∪ butter
          3 |    0.43 |       1.00 |   1.00 |    └ (bread ∪ milk)
          1 |    0.14 |       0.33 |   0.78 |      └ bread ∪ milk ∪ butter
          3 |    0.43 |       1.00 |   1.00 | butter
          1 |    0.14 |       1.00 |   1.00 | diapers
          3 |    0.43 |       1.00 |   1.00 | (milk)
          1 |    0.14 |       0.33 |   0.78 |    └ milk ∪ butter
""".strip()
        + "\n" * 2
        + """
Total number of transactions: 7
Total number of nodes (incl. root node): 11
""".strip()
    )

    assert merged_database.itemsets_trie.print(to_string=True) == expected_itemsets_trie_string


def test_merging_can_merge_multiple_databases():
    """Test if ambre can merge multiple databases at once."""
    # populate database 1 in a fictive process 1
    database1 = Database(["bread", "milk"])
    database1.insert_transaction(["milk", "bread"])
    database1.insert_transaction(["butter"])

    # populate database 2 in fictive process 2
    database2 = Database(["bread", "milk"])
    database2.insert_transaction(["bread", "coke"])
    database2.insert_transaction(["milk", "honey"])

    # populate database 3 in fictive process 3
    database3 = Database(["bread", "milk"])
    database3.insert_transaction(["candy"])
    database3.insert_transaction(["mustard", "salad"])

    # merge all databases into a single database
    merged_database = Database.merge_databases(database1, database2, database3)

    # assert right number of transactions and nodes
    assert merged_database.number_transactions == 6
    assert merged_database.number_nodes == 13

    # query frequent itemsets
    frequent_itemsets = merged_database.derive_frequent_itemsets_pandas()
    assert frequent_itemsets.shape[0] == 12

    # query rules
    rules = merged_database.derive_rules_pandas(non_antecedents_rules=True)
    assert rules.shape[0] == 5


def test_merging_cannot_merge_different_settings_databases():
    """Test if we cannot merge two databases with different settings."""
    # set up two databases with different settings
    database1 = Database(["milk"])
    database2 = Database(["bread"])
    with pytest.raises(
        Exception,
        match=(
            "Cannot merge databases because they use different settings. "
            "Ensure that both databases use the same settings."
        ),
    ):
        Database.merge_databases(database1, database2)


def test_merging_cannot_merge_different_database_schema_version_databases():
    """Test if we cannot merge two databases with different database schema versions."""
    # set up two databases with different database schema versions
    database1 = Database(["milk"])
    database1.DATABASE_SCHEMA_VERSION = "0.0"
    database2 = Database(["bread"])
    with pytest.raises(
        Exception,
        match=("Cannot merge databases because database schema versions are incompatible. " ".*"),
    ):
        Database.merge_databases(database1, database2)
