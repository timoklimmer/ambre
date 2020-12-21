"""Testpad for ambre.py."""

# #from ipython.display import display
from faker import Faker
from ambre import Database

database = Database(["A", "C"])
database.insert_transaction(["H", "B", "C"])
database.insert_transaction(["H", "X", "C"])
database.insert_transaction("aBC")
database.insert_transaction("AaBBC")
database.insert_transaction("BXYZA")
database.insert_transaction("BCD")
database.insert_transaction("DCX")
database.insert_transaction("ZDCX")
database.insert_transaction("ZCX")

# faker = Faker()
# database = Database(["c"])
# # transactions = [faker.name().replace(" ", "") for i in range(0, 10)]
# transactions = [
#     "ScottKlein",
#     "SarahWolf",
#     "CharlesWhite",
#     "KarenBrown",
#     "ValerieJames",
#     "JoshuaLewis",
#     "EricaCosta",
#     "RobertHenry",
#     "KeithBurgess",
#     "NicoleHernandez",
# ]
# for transaction in transactions:
#     print(transaction)
# database.insert_transactions(transactions, show_progress=False)

derived_itemsets = database.derive_frequent_itemsets_pandas()
display(derived_itemsets)

rules = database.derive_rules_pandas()
display(rules)
