"""Test the frequent itemset features of the ambre package."""

import os

from ambre import Database


def test_save_load_file():
    """Test if we can save and load a database to/from a file."""
    database_filename = "test_save_load_file.ambre.db"

    try:
        # populate an initial database
        database = Database(["bread"])

        # add two common sense rules
        database.insert_common_sense_rule(["milk"], ["bread"])
        database.insert_common_sense_rule(["butter"], ["bread"])

        # add two transactions
        database.insert_transaction(["milk", "bread"])
        database.insert_transaction(["butter"])

        # save and reload the database
        database.save_to_file(database_filename)
        database = Database.load_from_file(database_filename)

        # check if we can add additional transactions
        database.insert_transaction(["milk", "bread", "butter"])
        database.insert_transaction(["bread"])

        # check if the number of transactions is correct
        assert database.number_transactions == 4

        # check if there are still two common sense rules
        assert len(database.get_common_sense_rules()) == 2

        # query frequent itemsets
        frequent_itemsets = database.derive_frequent_itemsets_pandas()
        assert frequent_itemsets.shape[0] > 0

        # query rules
        rules = database.derive_rules_pandas(non_antecedents_rules=True)
        assert rules.shape[0] > 0

    finally:
        if os.path.exists(database_filename):
            os.remove(database_filename)


def test_save_load_memory():
    """Test if we can save and load a database to/from memory."""
    # populate and initial database
    database = Database(["bread"])

    # add some transactions
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    # save and restore the database to/from memory
    database = Database.load_from_bytes(database.as_bytes())

    # query frequent itemsets
    frequent_itemsets = database.derive_frequent_itemsets_pandas()
    assert frequent_itemsets.shape[0] > 0

    # query rules
    rules = database.derive_rules_pandas(non_antecedents_rules=True)
    assert rules.shape[0] > 0
