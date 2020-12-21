"""Performance testing."""

import pytest
from ambre import Database
from faker import Faker

# comment line below to run these tests automatically without explicitly starting them
pytestmark = pytest.mark.skip("Performance benchmarks are only run on explicit demand.")


@pytest.mark.parametrize("number_transactions", [100, 1000, 5000])
def test_insert_performance(benchmark, number_transactions):
    """Test the performance of inserting the specified number of transactions."""
    faker = Faker()
    transactions = list([faker.name().replace(" ", "") for i in range(0, number_transactions)])
    database = Database("a")
    benchmark(database.insert_transactions, transactions=transactions, show_progress=False)
