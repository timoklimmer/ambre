"""
Test the rule extraction features of the ambre package.

Some data and numbers are taken from the Wikipedia article at https://en.wikipedia.org/wiki/Association_rule_learning.
"""

import pytest
from ambre import Database

from .testing_helpers import (
    get_titanic_survived_1_database, get_wikipedia_database_consequent_bread,
    get_wikipedia_database_consequent_bread_and_milk,
    get_wikipedia_database_consequent_bread_custom_input_alphabet,
    get_wikipedia_database_no_consequents, load_pandas_dataframe_from_csv,
    save_and_ensure_actual_result_vs_expected)


def test_rule_extraction_wikipedia_consequent_bread(request):
    """
    Test the rule generation against data and numbers from a Wikipedia article.

    Condition: Bread is the consequent we are interested in.
    """
    save_and_ensure_actual_result_vs_expected(get_wikipedia_database_consequent_bread().derive_rules_pandas(), request)


def test_rule_extraction_wikipedia_consequent_bread_minmax_conditions(request):
    """
    Test the rule generation against data and numbers from a Wikipedia article.

    Condition: Bread is the consequent we are interested in, and there is some min/max filter values.
    """
    actual_result = get_wikipedia_database_consequent_bread().derive_rules_pandas(
        min_confidence=0.8, max_antecedents_length=4
    )
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_rule_extraction_wikipedia_consequent_bread_non_antecedents_rules(request):
    """
    Test the rule generation against data and numbers from a Wikipedia article.

    Condition: Bread and milk are the consequents we are interested in, and we also want to extract the non-antecedents
               rules.
    """
    actual_result = get_wikipedia_database_consequent_bread_and_milk().derive_rules_pandas(non_antecedents_rules=True)
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_rule_extraction_wikipedia_throws_exception_without_consequent():
    """Test if the rule generation throws an exception if no consequent was specified before inserting transactions."""
    database = get_wikipedia_database_no_consequents()
    with pytest.raises(ValueError, match=r"Cannot extract rules because no consequents are defined."):
        database.derive_rules_pandas()


def test_rule_extraction_wikipedia_common_sense_rule(request):
    """
    Test the rule generation against data and numbers from a Wikipedia article.

    Condition: A common sense rule is specified.
    """
    database = get_wikipedia_database_consequent_bread()
    database.insert_common_sense_rule(["milk"], ["bread"])
    database.insert_common_sense_rule(["diapers"], ["beer"])

    actual_result = database.derive_rules_pandas()
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_rule_extraction_wikipedia_custom_item_alphabet(request):
    """Test the rule extraction with custom item alphabet."""
    database = get_wikipedia_database_consequent_bread_custom_input_alphabet()
    actual_result = database.derive_rules_pandas()
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_rule_extraction_titanic(request):
    """Test the rule extraction on the Titanic dataset."""
    database = Database(["Survived=1"])
    database.insert_from_pandas_dataframe_rows(
        load_pandas_dataframe_from_csv("datasets/titanic.csv"),
        input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
    )
    actual_result = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7).sort_values(
        by=["confidence", "occurrences"], ascending=[False, False]
    )
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_rule_extraction_titanic_omit_column_names_in_result(request):
    """Test the rule extraction on the Titanic dataset, omitting column names in the result."""
    database = Database(["Survived=1"])
    database.insert_from_pandas_dataframe_rows(
        load_pandas_dataframe_from_csv("datasets/titanic.csv"),
        input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
    )
    actual_result = database.derive_rules_pandas(
        min_occurrences=30, min_confidence=0.7, omit_column_names_in_output=True
    ).sort_values(by=["confidence", "occurrences"], ascending=[False, False])
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_rule_extraction_titanic_max_antecedents_length(request):
    """Test the rule extraction on the Titanic dataset."""
    actual_result = (
        get_titanic_survived_1_database(max_antecedents_length=2)
        .derive_rules_pandas(min_occurrences=30, min_confidence=0.7)
        .sort_values(by=["confidence", "occurrences"], ascending=[False, False])
    )
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_rule_extraction_titanic_confidence_tolerance(request):
    """Test the rule extraction on the Titanic dataset."""
    actual_result = (
        get_titanic_survived_1_database()
        .derive_rules_pandas(min_occurrences=30, min_confidence=0.7, confidence_tolerance=0.05)
        .sort_values(by=["confidence", "occurrences"], ascending=[False, False])
    )
    save_and_ensure_actual_result_vs_expected(actual_result, request)
