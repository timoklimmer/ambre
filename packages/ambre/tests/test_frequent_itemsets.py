"""
Test the frequent itemset features of the ambre package.
"""

from ambre import Database

from .testing_helpers import (
    get_wikipedia_database_consequent_bread,
    get_wikipedia_database_no_consequents,
    load_pandas_dataframe_from_csv,
    save_and_ensure_actual_result_vs_expected,
)


def test_frequent_itemsets_wikipedia_no_consequent(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Condition: No consequents are specified when the database is instantiated.
    """
    actual_result = get_wikipedia_database_no_consequents().derive_frequent_itemsets_pandas()
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_frequent_itemsets_wikipedia_dirty_items(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Condition: Transaction items are not normalized, eg. use different casing and whitespacing or have duplicate items.
    """
    actual_result = get_wikipedia_database_no_consequents().derive_frequent_itemsets_pandas()
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_frequent_itemsets_wikipedia_consequent_bread(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Condition: "Bread" is specified as consequent when the database is instantiated.
    """
    actual_result = get_wikipedia_database_consequent_bread().derive_frequent_itemsets_pandas()
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_frequent_itemsets_wikipedia_consequent_bread_consequents_only(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Conditions:
    - "Bread" is specified as consequent when the database is instantiated.
    - Only itemsets containing a consequent shall be generated.
    """
    actual_result = get_wikipedia_database_consequent_bread().derive_frequent_itemsets_pandas(
        filter_to_consequent_itemsets_only=True
    )

    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_frequent_itemsets_wikipedia_consequent_bread_several_minmax_conditions(request):
    """
    Test the frequent itemset generation against data and numbers from Wikipedia (see module docstring for link).

    Conditions:
    - Consequent = "bread"
    - Minimum occurrences = 2
    - Support >= 0.6
    - Itemset length >= 2
    """
    actual_result = get_wikipedia_database_consequent_bread().derive_frequent_itemsets_pandas(
        min_occurrences=2, min_support=0.6, max_itemset_length=2
    )
    save_and_ensure_actual_result_vs_expected(actual_result, request)


def test_frequent_itemsets_titanic_no_consequents_min_occurences(request):
    """Test the frequent itemset generation against the Titanic dataset with no consequents specified."""
    database = Database()
    database.insert_from_pandas_dataframe_rows(
        load_pandas_dataframe_from_csv("datasets/titanic.csv"),
        input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
    )
    actual_result = database.derive_frequent_itemsets_pandas(min_occurrences=10).sort_values(by="itemset")
    save_and_ensure_actual_result_vs_expected(actual_result, request)
