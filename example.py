import pandas as pd
from IPython.display import display

from ambre import Database

# load the famous titanic dataset and add the passengers that survived into our Database
# note: - data does not have to be a pandas dataframe. there is also methods to add non-columnar data with varying
#         transaction sizes such as insert_transactions().
database = Database(["Survived=1"], max_antecedents_length=3)
database.insert_from_pandas_dataframe_rows(
    pd.read_csv("packages/ambre/tests/datasets/titanic.csv"),
    input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
)

# derive frequent itemsets
print("Deriving frequent itemsets...")
derived_itemsets = database.derive_frequent_itemsets_pandas().sort_values(
    by=["occurrences", "itemset_length"], ascending=[False, True]
)
display(derived_itemsets)

# derive rules
print("Deriving rules...")
derived_rules = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7)
derived_rules = derived_rules.sort_values(by=["confidence", "occurrences"], ascending=[False, False])
display(derived_rules)

# common sense rules
# Let's assume for the sake of the demo here that we knew passengers with no parents or children aboard have always
# survived. In that case, we can tell ambre about our common sense knowledge. When ambre knows about it, it will not
# generate rules with knowledge we have already. Btw: we can add as many common sense rules as we like.
print("Consider common sense knowledge...")
database.insert_common_sense_rule(["Parch=0"], ["Survived=1"])
derived_rules = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7)
derived_rules = derived_rules.sort_values(by=["confidence", "occurrences"], ascending=[False, False])
display(derived_rules)