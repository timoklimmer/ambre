"""Testpad for ambre.py."""

# # #from ipython.display import display
# from faker import Faker

# from ambre import Database

# database = Database(["A", "C"])
# database.insert_transaction(["H", "B", "C"])
# database.insert_transaction(["H", "X", "C"])
# database.insert_transaction("aBC")
# database.insert_transaction("AaBBC")
# database.insert_transaction("BXYZA")
# database.insert_transaction("BCD")
# database.insert_transaction("DCX")
# database.insert_transaction("ZDCX")
# database.insert_transaction("ZCX")

# # faker = Faker()
# # database = Database(["c"])
# # # transactions = [faker.name().replace(" ", "") for i in range(0, 10)]
# # transactions = [
# #     "ScottKlein",
# #     "SarahWolf",
# #     "CharlesWhite",
# #     "KarenBrown",
# #     "ValerieJames",
# #     "JoshuaLewis",
# #     "EricaCosta",
# #     "RobertHenry",
# #     "KeithBurgess",
# #     "NicoleHernandez",
# # ]
# # for transaction in transactions:
# #     print(transaction)
# # database.insert_transactions(transactions, show_progress=False)

# derived_itemsets = database.derive_frequent_itemsets_pandas()
# display(derived_itemsets)

# rules = database.derive_rules_pandas()
# display(rules)


# -------

import pandas as pd

from ambre import Database

print("Loading data...", flush=True)
database = Database(["Survived:0"], max_antecedents_length=2)
database.insert_from_pandas_dataframe_rows(
    pd.read_csv("titanic.csv"), input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]
)
print("")

print("Deriving frequent itemsets...")
derived_itemsets = database.derive_frequent_itemsets_pandas().sort_values(
    by=["occurrences", "itemset_length"], ascending=[False, True]
)
display(derived_itemsets)
print("")

a = database.derive_frequent_itemsets_pandas()
a[a["itemset_length"] == 3]

# print("Deriving rules...")
# derived_rules = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7)
# derived_rules["relevance"] = (derived_rules["confidence"] * derived_rules["support"]) ** (1/2)
# derived_rules = derived_rules.sort_values(
#    by=["confidence", "occurrences"], ascending=[False, False]
# )
# display(derived_rules)

# # database.insert_manual_rule(["sex:female"], ["survived:1"])
# print("Deriving rules with manual rules...")
# derived_rules = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7, confidence_tolerance=0.05)
# derived_rules["relevance"] = (derived_rules["confidence"] * derived_rules["support"]) ** (1 / 2)
# #derived_rules = derived_rules.sort_values(by=["confidence", "occurrences"], ascending=[False, False])
# derived_rules = derived_rules.sort_values(by=["relevance"], ascending=[False])
# #display(derived_rules)