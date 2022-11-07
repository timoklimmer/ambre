"""
Test some of the common sense features.

There may be more common sense tests in the other test scripts.
"""

from ambre import Database
from ambre.common_sense_rule import CommonSenseRule


def test_common_sense_insert_rule():
    """Test if a common sense rule can be added."""
    database = Database(["dummy"])
    database.insert_common_sense_rule(["a"], ["b"], 0.8)
    database.insert_common_sense_rule(["a"], ["c"], 0.2)
    database.insert_common_sense_rule(["x"], ["z"], 1)
    database.insert_common_sense_rule(["x", "y"], ["z"], 1)
    database.insert_common_sense_rule(["d"], ["e"], 0.5)
    assert len(database.get_common_sense_rules()) == 4


def test_common_sense_insert_rules_batch():
    """Test if redundant common sense rules are consolidated when inserting a batch of rules."""
    database = Database(["dummy"])
    common_sense_rules = [
        CommonSenseRule(database, ["a"], ["b"], 0.8),
        CommonSenseRule(database, ["a"], ["c"], 0.2),
        CommonSenseRule(database, ["x"], ["z"], 1),
        CommonSenseRule(database, ["x", "y"], ["z"], 1),
        CommonSenseRule(database, ["d"], ["e"], 0.5),
    ]
    database.insert_common_sense_rules(common_sense_rules)
    assert len(database.get_common_sense_rules()) == 4
    assert database.get_common_sense_rules()[0] == CommonSenseRule(database, ["a"], ["b"], 0.8)
    assert database.get_common_sense_rules()[1] == CommonSenseRule(database, ["a"], ["c"], 0.2)
    assert database.get_common_sense_rules()[2] == CommonSenseRule(database, ["d"], ["e"], 0.5)
    assert database.get_common_sense_rules()[3] == CommonSenseRule(database, ["x"], ["z"], 1)


def test_common_sense_rule_consolidation():
    """Test if redundant common sense rules are consolidated."""
    database = Database(["dummy"])
    database.insert_common_sense_rule(["x"], ["y"], 0.7)
    assert database.get_common_sense_rules()[0] == CommonSenseRule(database, ["x"], ["y"], 0.7)

    database.insert_common_sense_rule(["x"], ["y"], 1)
    assert len(database.get_common_sense_rules()) == 1
    assert database.get_common_sense_rules()[0] == CommonSenseRule(database, ["x"], ["y"], 1)

    database.insert_common_sense_rule(["a", "b"], ["c"], 0.2)
    assert len(database.get_common_sense_rules()) == 2
    assert database.get_common_sense_rules()[0] == CommonSenseRule(database, ["a", "b"], ["c"], 0.2)

    database.insert_common_sense_rule(["a", "b"], ["c"], 1)
    assert len(database.get_common_sense_rules()) == 2
    assert database.get_common_sense_rules()[0] == CommonSenseRule(database, ["a", "b"], ["c"], 1)

    database.insert_common_sense_rule(["a"], ["c"], 1)
    assert len(database.get_common_sense_rules()) == 2
    assert database.get_common_sense_rules()[0] == CommonSenseRule(database, ["a"], ["c"], 1)


def test_common_sense_remove_rule():
    """Test if a common sense rule can be deleted."""
    database = Database(["dummy"])
    database.insert_common_sense_rule(["a"], ["b"], 0.8)
    assert len(database.get_common_sense_rules()) == 1
    database.remove_common_sense_rule(["a"], ["b"], 0.8)
    assert len(database.get_common_sense_rules()) == 0
