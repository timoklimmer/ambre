"""Helper methods for running tests."""
import os

import pandas as pd

def get_test_name(request):
    """Get the name of the test from the given request object."""
    return request.node.name.replace("test_", "")


def save_actual_result(actual_result, request):
    """Save actual result to Excel worksheet."""
    dataset_name = get_test_name(request)
    actual_result.to_excel(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data",
            f"{dataset_name}.actual_result.xlsx",
        ),
        header=True,
        index=False,
    )


def load_expected_result(request):
    """Load expected result from Excel worksheet."""
    dataset_name = get_test_name(request)
    return pd.read_excel(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data",
            f"{dataset_name}.expected_result.xlsx",
        ),
        engine="openpyxl",
    )
