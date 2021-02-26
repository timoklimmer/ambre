"""
Test the rule merging features of the ambre package.

Some data and numbers are taken from the Wikipedia article at https://en.wikipedia.org/wiki/Association_rule_learning.
"""

from ambre import Database

from .testing_helpers import (
    load_pandas_dataframe_from_csv,
    save_and_ensure_actual_result_vs_expected,
)


def test_rule_merge(request):
    """Test the rule merging on two rulesets derived from the Titanic dataset."""
    database = Database(["Survived=1"])
    database.insert_from_pandas_dataframe_rows(
        load_pandas_dataframe_from_csv("datasets/titanic.csv"),
        input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
    )
    ruleset1 = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7).sort_values(
        by=["confidence", "occurrences"], ascending=[False, False]
    )
    ruleset2 = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7).sort_values(
        by=["confidence", "occurrences"], ascending=[False, False]
    )
    merge_result = Database.merge_rules_pandas(ruleset1, ruleset2)
    merge_result = merge_result.sort_values(by="confidence", ascending=False)
    actual_result = merge_result
    save_and_ensure_actual_result_vs_expected(actual_result, request)
