"""Test ambre's prediction capabilities."""

import pytest

from .testing_helpers import (
    get_wikipedia_database_consequent_bread,
    get_wikipedia_database_consequent_bread_and_milk,
    get_wikipedia_database_no_consequents,
)


def test_predict_correct_probability_when_single_antecedent_is_given():
    """Test if ambre can predict the correct probability when a single antecedent is given."""
    database = get_wikipedia_database_consequent_bread()
    bread_consequent_result = database.predict_consequents_list(["butter"])[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["antecedents"] == ["butter"]
    assert bread_consequent_result["probability"] == 0.5


def test_predict_correct_probability_when_multiple_antecedents_are_given():
    """Test if ambre can predict the correct probability when multiple antecedents are given."""
    database = get_wikipedia_database_consequent_bread()
    bread_consequent_result = database.predict_consequents_list(["butter", "milk"])[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["antecedents"] == ["butter", "milk"]
    assert bread_consequent_result["probability"] == 1


def test_predict_none_when_antecedent_does_not_exist():
    """Test if ambre predicts none if a specified antecedent does not exist."""
    database = get_wikipedia_database_consequent_bread()
    assert database.predict_consequents_list(["i_dont_exist"])[0]["probability"] is None
    assert database.predict_consequents_list(["butter", "i_dont_exist"])[0]["probability"] is None


def test_predict_skips_unknown_antecedents_when_desired():
    """Test if ambre prediction skips unknown antecedents when desired."""
    database = get_wikipedia_database_consequent_bread()
    assert database.predict_consequents_list(["butter", "coke"], skip_unknown_antecedents=True)[0]["probability"] == 0.5
    assert database.predict_consequents_list(["i_dont_exist"], skip_unknown_antecedents=True)[0]["probability"] is None


def test_predict_priors_when_no_antecedents():
    """Test if ambre predicts prior probabilities when no antecedents are given."""
    database = get_wikipedia_database_consequent_bread()
    bread_consequent_result = database.predict_consequents_list()[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["probability"] == 0.6


def test_predict_empty_list_when_no_consequents():
    """Test if ambre predicts an empty list when the database has no consequents defined."""
    database = get_wikipedia_database_no_consequents()
    assert database.predict_consequents_list() == []


def test_predict_specified_consequents_only():
    """Test if ambre predicts only the specified consequents when consequents are passed."""
    database = get_wikipedia_database_consequent_bread_and_milk()
    assert len(database.predict_consequents_list(consequents=["bread"])) == 1


def test_predict_throws_when_specified_consequent_does_not_exist():
    """Test if ambre raises an exception when the probability for a non-existing consequent is requested."""
    with pytest.raises(
        ValueError,
        match=("The specified consequent '.+?' has not been specified as a consequent"),
    ):
        database = get_wikipedia_database_consequent_bread_and_milk()
        assert database.predict_consequents_list(consequents=["pasta"])


def test_predict_correct_when_common_sense_rule_is_set():
    """Test if ambre still predicts correct when common sense rules are defined."""
    database = get_wikipedia_database_consequent_bread()
    database.insert_common_sense_rule(["butter"], ["bread"], 1)

    # no antecedents skip, all antecedents known
    bread_consequent_result = database.predict_consequents_list(["butter"])[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["antecedents"] == ["butter"]
    assert bread_consequent_result["probability"] == 1

    # no antecedents skip, not all antecedents known
    bread_consequent_result = database.predict_consequents_list(["butter", "soda"])[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["antecedents"] == ["butter", "soda"]
    assert bread_consequent_result["probability"] is None

    # antecedents skip, all antecedents known
    bread_consequent_result = database.predict_consequents_list(["butter"], skip_unknown_antecedents=True)[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["antecedents"] == ["butter"]
    assert bread_consequent_result["probability"] == 1

    # no antecedents skip, not all antecedents known
    bread_consequent_result = database.predict_consequents_list(["butter", "soda"], skip_unknown_antecedents=True)[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["antecedents"] == ["butter", "soda"]
    assert bread_consequent_result["probability"] == 1

    # antecedent not covered by common sense rule
    bread_consequent_result = database.predict_consequents_list(["beer"])[0]
    assert bread_consequent_result["consequent"] == "bread"
    assert bread_consequent_result["antecedents"] == ["beer"]
    assert bread_consequent_result["probability"] is None


def test_predict_to_pandas():
    """Test if ambre can return prediction results in a pandas dataframe."""
    database = get_wikipedia_database_consequent_bread()
    result = database.predict_consequents_pandas(["butter", "milk"])
    assert result.shape[0] == 1
    assert result.loc[0]["probability"] == 1
