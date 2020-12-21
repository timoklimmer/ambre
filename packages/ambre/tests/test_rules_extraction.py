"""
Test the rule extraction features of the ambre package.

Some data and numbers are taken from the Wikipedia article at https://en.wikipedia.org/wiki/Association_rule_learning.
"""

# TODO: add manual rule tests

import pytest
from ambre import Database
from pandas._testing import assert_frame_equal

from .testing_helpers import load_expected_result, save_actual_result


def test_rule_extraction_wikipedia_consequent_bread(request):
    """
    Test the rule generation against data and numbers from a Wikipedia article.

    Condition: Bread is the consequent we are interested in.
    """
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["beer", "diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    actual_result = database.derive_rules_pandas()

    save_actual_result(actual_result, request)
    expected_result = load_expected_result(request)
    assert_frame_equal(actual_result, expected_result, check_dtype=False)


def test_rule_extraction_wikipedia_consequent_bread_minmax_conditions(request):
    """
    Test the rule generation against data and numbers from a Wikipedia article.

    Condition: Bread is the consequent we are interested in, and there is some min/max filter values.
    """
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["beer", "diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    actual_result = database.derive_rules_pandas(minimum_confidence=0.8, maximum_antecedent_size=4)
    save_actual_result(actual_result, request)

    expected_result = load_expected_result(request)

    assert_frame_equal(actual_result, expected_result, check_dtype=False)


def test_rule_extraction_throws_exception_without_consequent():
    """Test if the rule generation throws an exception if no consequent was specified before inserting transactions."""
    database = Database()
    with pytest.raises(ValueError, match=r"Cannot extract rules because no consequents are defined."):
        database.derive_rules_pandas()


def test_rule_extraction_wikipedia_manual_rule(request):
    """
    Test the rule generation against data and numbers from a Wikipedia article.

    Condition: A manual rule is specified.
    """
    database = Database(["bread"])
    database.insert_transaction(["milk", "bread"])
    database.insert_transaction(["butter"])
    database.insert_transaction(["beer", "diapers"])
    database.insert_transaction(["milk", "bread", "butter"])
    database.insert_transaction(["bread"])

    database.insert_manual_rule(["milk"], ["bread"])
    database.insert_manual_rule(["diapers"], ["beer"])

    actual_result = database.derive_rules_pandas()

    save_actual_result(actual_result, request)
    expected_result = load_expected_result(request)

    assert_frame_equal(actual_result, expected_result, check_dtype=False)
