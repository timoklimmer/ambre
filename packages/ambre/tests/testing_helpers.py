"""Helper methods for running tests."""
import os

import pandas as pd
from ambre import Database
from pandas._testing import assert_frame_equal


def get_test_name(request):
    """Get the name of the test from the given request object."""
    return request.node.name.replace("test_", "")


def load_pandas_dataframe_from_csv(filename):
    """Load the given CSV file and return it as pandas dataframe."""
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
    return pd.read_csv(filename)


def load_pandas_dataframe_from_excel(filename):
    """Load the given Excel workbook and return it as pandas dataframe."""
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
    return pd.read_excel(filename, engine="openpyxl")


def save_actual_result(actual_result, request):
    """Save actual result to Excel worksheet."""
    dataset_name = get_test_name(request)
    actual_result.to_excel(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "actual_expected",
            f"{dataset_name}.actual.xlsx",
        ),
        header=True,
        index=False,
    )


def load_actual_result(request):
    """Load actual result from Excel workbook."""
    dataset_name = get_test_name(request)
    return load_pandas_dataframe_from_excel(os.path.join("actual_expected", f"{dataset_name}.actual.xlsx"))


def load_expected_result(request):
    """Load expected result from Excel workbook."""
    dataset_name = get_test_name(request)
    return load_pandas_dataframe_from_excel(os.path.join("actual_expected", f"{dataset_name}.expected.xlsx"))


def save_and_ensure_actual_result_vs_expected(actual_result_dataframe, request):
    """
    Compare the given actual result dataframe against the expected result dataframe.

    The expected result is automatically loaded from the Excel workbook which has the same name as the test without
    the "test_" prefix and an ".expected.xlsx" extension in folder "actual_expected".
    """
    save_actual_result(actual_result_dataframe, request)
    actual_result_dataframe = load_actual_result(request)
    expected_result_dataframe = load_expected_result(request)
    assert_frame_equal(actual_result_dataframe, expected_result_dataframe)


def get_wikipedia_database_no_consequents():
    """
    Return a database populated with transactions from Wikipedia, no consequent set.

    See https://en.wikipedia.org/wiki/Association_rule_learning for details.
    """
    result = Database()
    result.insert_transaction(["milk", "bread"])
    result.insert_transaction(["butter"])
    result.insert_transaction(["beer", "diapers"])
    result.insert_transaction(["milk", "bread", "butter"])
    result.insert_transaction(["bread"])
    return result


def get_wikipedia_database_consequent_bread():
    """
    Return a database populated with transactions from Wikipedia, using bread as consequent.

    See https://en.wikipedia.org/wiki/Association_rule_learning for details.
    """
    result = Database(["bread"])
    result.insert_transaction(["milk", "bread"])
    result.insert_transaction(["butter"])
    result.insert_transaction(["beer", "diapers"])
    result.insert_transaction(["milk", "bread", "butter"])
    result.insert_transaction(["bread"])
    return result


def get_titanic_survived_1_database(max_antecedents_length=None):
    """Return a database with transactions from the Titanic dataset, consequent = Survived:0."""
    result = Database(["Survived:1"], max_antecedents_length=max_antecedents_length)
    result.insert_from_pandas_dataframe_rows(
        load_pandas_dataframe_from_csv("datasets/titanic.csv"),
        input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
    )
    return result