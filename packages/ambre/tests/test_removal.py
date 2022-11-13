"""Test the removal of transactions from the database."""

import pytest

from ambre import Database

from .testing_helpers import get_wikipedia_database_consequent_bread


def test_removal_when_database_is_empty():
    """Test if we get an exception when we try to remove a transaction from an empty database."""
    database = Database(["Dummy"])
    with pytest.raises(
        ValueError,
        match=("The database is empty. There are no transactions to remove."),
    ):
        database.remove_transaction(["I don't exist."])


def test_removal_of_single_transaction():
    """Test if we can remove a single transaction."""
    database = get_wikipedia_database_consequent_bread()
    original_transaction_count = database.number_transactions
    database.remove_transaction(["milk", "bread"])
    assert database.number_transactions == original_transaction_count - 1
    assert database.predict_consequents_list(["milk", "bread"])[0]["probability"] is None


def test_removal_of_non_existing_transaction_exception():
    """Test if we get an exception when removing a non-existing transaction."""
    database = get_wikipedia_database_consequent_bread()
    with pytest.raises(
        ValueError,
        match=(".* cannot be removed because it was not inserted before."),
    ):
        database.remove_transaction(["toothbrush"])


def test_removal_of_non_existing_transaction_silent():
    """Test if we get no exception when a non-existing transaction is removed and silent mode is switched on."""
    database = get_wikipedia_database_consequent_bread()
    database.remove_transaction(["toothbrush"], silent=True)


def test_removal_of_one_of_two_equal_transactions():
    """Test if we can remove a transaction if it is one of two equal transactions."""
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])
    original_transaction_count = database.number_transactions
    database.remove_transaction(["milk", "bread", "butter"])
    assert database.number_transactions == original_transaction_count - 1
    assert database.has_itemset(["milk", "bread"]) is True
    assert database.has_itemset(["milk", "bread", "butter"]) is True


def test_removal_of_multiple_transactions():
    """Test if we can remove multiple transactions."""
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])
    original_transaction_count = database.number_transactions
    database.remove_transaction(["milk", "bread", "butter"])
    database.remove_transaction(["milk", "bread", "butter"])
    assert database.number_transactions == original_transaction_count - 2
    assert database.get_itemset(["milk", "bread", "butter"], none_if_not_exists=True) is None
    assert database.has_itemset(["milk", "bread"]) is True
    assert database.has_itemset(["milk", "bread", "butter"]) is False
