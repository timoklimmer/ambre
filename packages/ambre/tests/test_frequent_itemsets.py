"""
Test the frequent itemset features of the ambre package.

Some data and numbers are taken from the Wikipedia article at https://en.wikipedia.org/wiki/Association_rule_learning.
"""

from ambre import Database
from pandas._testing import assert_frame_equal

from .testing_helpers import load_expected_result, save_actual_result


def test_frequent_itemsets_wikipedia_no_consequent(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Condition: No consequents are specified when the database is instantiated.
    """
    database = Database()
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["beer", "diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    actual_result = database.derive_frequent_itemsets_pandas()

    save_actual_result(actual_result, request)
    expected_result = load_expected_result(request)
    assert_frame_equal(actual_result, expected_result)


def test_frequent_itemsets_wikipedia_dirty_items(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Condition: Transaction items are not normalized, eg. use different casing and whitespacing or have duplicate items.
    """
    database = Database()
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["Butter", "butter"])
    database.insert_transaction(["\tbEEr\t", " Diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["Bread "])

    actual_result = database.derive_frequent_itemsets_pandas()

    save_actual_result(actual_result, request)
    expected_result = load_expected_result(request)
    assert_frame_equal(actual_result, expected_result)


def test_frequent_itemsets_wikipedia_consequent_bread(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Condition: "Bread" is specified as consequent when the database is instantiated.
    """
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["beer", "diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    actual_result = database.derive_frequent_itemsets_pandas()

    save_actual_result(actual_result, request)
    expected_result = load_expected_result(request)
    assert_frame_equal(actual_result, expected_result)


def test_frequent_itemsets_wikipedia_consequent_bread_consequents_only(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Conditions:
    - "Bread" is specified as consequent when the database is instantiated.
    - Only itemsets containing a consequent shall be generated.
    """
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["beer", "diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    actual_result = database.derive_frequent_itemsets_pandas(filter_to_consequent_itemsets_only=True)

    save_actual_result(actual_result, request)
    expected_result = load_expected_result(request)
    assert_frame_equal(actual_result, expected_result)


def test_frequent_itemsets_wikipedia_consequent_bread_several_minmax_conditions(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Conditions:
    - Consequent = "bread"
    - Minimum occurences = 2
    - Support >= 0.6
    - Itemset length >= 2
    """
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["beer", "diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    actual_result = database.derive_frequent_itemsets_pandas(
        minimum_occurences=2, minimum_support=0.6, maximum_itemset_length=2
    )

    save_actual_result(actual_result, request)
    expected_result = load_expected_result(request)
    assert_frame_equal(actual_result, expected_result)
