<p>
    <img src="logo/logo_small.png"/>
</p>

# ambre

> TL;DR -- **Give ambre your data and tell it what outcomes in your data you are interested in. It then tells you when
those outcomes occur.**

ambre is a package for association mining-based rules extraction -- it extracts rules from your data in the form of
*factors (named "antecedents")* --lead to--> *outcomes (named "consequents")*. In contrast to other approaches like
deriving feature importances, it tells you more than just columns. It tells you exactly which *combinations* of
*concrete* values lead to your outcomes of interest most frequently and at which confidence.

For instance, imagine you had to manage a production line. By using traditional approaches, you would learn for example
that your vendors or the used machine models are a critical factor for defects. In contrast, ambre will tell you that a
defect occurs most likely when the vendor is *"ABC"*, and when machine model *"XYZ"* is used. Because it's more
detailed, the information we get from ambre can be more valuable than pure importance of factors.

ambre can even work with non-columnar data. It's no problem if the "transactions" (see below) consist of different
numbers of items.

To increase usability, there is also a feature to specify common sense knowledge. Let's assume you know already that
machine model *XYZ* produces one defect after another. With the common sense feature, you can tell ambre, and it will
not create boring and confusing rules for things you already know.

The ultimate goal of ambre is to deliver actionable insights. As detailed as necessary but not more.


## Installation

### pip

The package is not available on PyPI yet but can be installed from GitHub via *pip*.

To install, either run

`pip install --upgrade git+https://github.com/timoklimmer/ambre.git#subdirectory=packages/ambre`

OR

clone the repo and install the package by running `pip install -e .` in folder `packages/ambre`.

You can also add the package to your `requirements.txt` file by adding a
`git+https://github.com/timoklimmer/ambre.git#subdirectory=packages/ambre` line.

### Azure Databricks
If you are on Databricks, run

`%pip install --upgrade git+https://github.com/timoklimmer/ambre.git#subdirectory=packages/ambre`

within a cell for a quick install. For production-ready installation, install the package via your init script.


## Usage Example

### Non-Tabular Data
```python
from IPython.display import display

from ambre import Database

# populate database
# using "bread" as consequence -> under which conditions do people buy bread?
database = Database(["bread"])
database.insert_transaction(["milk", "bread"])
database.insert_transaction(["butter"])
database.insert_transaction(["beer", "diapers"])
database.insert_transaction(["milk", "bread", "butter"])
database.insert_transaction(["bread"])

# query frequent itemsets
frequent_itemsets = database.derive_frequent_itemsets_pandas()
display(frequent_itemsets)

# query rules
rules = database.derive_rules_pandas(non_antecedents_rules=True)
display(rules)
```

### Tabular Data + Common Sense Rules
```python
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
```

### Distributed Training
```python
from IPython.display import display

from ambre import Database

# populate database 1 in a fictive process 1
database1 = Database(["bread", "milk"])
database1.insert_transaction(["milk", "bread"])
database1.insert_transaction(["butter"])
# optionally save the database either to a file or byte array as needed
# file       : database1.save_to_file("database1.ambre.db")
# byte array : database1_as_byte_array = database1.as_bytes()

# populate database 2 in fictive process 2
database2 = Database(["bread", "milk"])
database2.insert_transaction(["bread", "coke"])
database2.insert_transaction(["milk", "honey"])
# optionally save database, similar to above

# populate database 3 in fictive process 3
database3 = Database(["bread", "milk"])
database3.insert_transaction(["candy"])
database3.insert_transaction(["mustard", "salad"])
# optionally save database, similar to above

# make sure we have the database objects again (if saved before)
# file       : database1 = Database.load_from_file("database1.ambre.db")
# byte array : database1 = Database.load_from_bytes(database1_as_byte_array)

# merge all databases into a single database
merged_database = Database.merge_databases(database1, database2, database3)

# query frequent itemsets
frequent_itemsets = merged_database.derive_frequent_itemsets_pandas()
display(frequent_itemsets)

# query rules
rules = merged_database.derive_rules_pandas(non_antecedents_rules=True)
display(rules)
```


## Glossary
|Term|Meaning|
|----|-------|
|Itemset|A set of items or states.|
|Transaction|A set of items that occur together, eg. a basket at a supermarket or all infos around a specific defect instance.|
|Database|Set of all transactions.|
|Frequent Itemset|A set of items that occurs frequently across all transactions.|
|Antecedent|Antecedents are items that lead to/are correlated with one or more consequents.|
|Consequent|An item which occurs because of/together with one or more antecedents.|
|Rule|Describes how well a certain set of antecedents leads to certain consequents.|
|Support|The proportion of transactions in the dataset which contain the respective itemset.|
|Confidence|Estimates the probability of finding a certain consequence under the condition that certain antecedents have been observed.|
|Lift|The support of the whole rule divided by the support expected under independence. Greater lift values indicate stronger assumptions.|


## Performance
ambre can lead to valuable results but its performance might not be as you expect. Compared to other machine learning
algorithms, it has to create a lot of combinations and store them in a trie data structure. This can take a lot of time,
and it seems there is no workaround or smarter method yet.

The good news is that ambre's performance is highly dependent on its configuration. To improve ambre's performance, you
can set a couple of parameters when creating the database and when using the *derive_...()* methods.

Whenever possible, you should prefer to set the parameters at the database, because this will help filter data as early
as possible, avoiding unnecessary workload in the derive..() methods.

- `max_antecedents_length` controls how many antecedents you are returned at maximum when frequent itemsets or rules are
generated. In most of the cases, you are only interested in maybe 3 or 5 antecedents anyway because results with more
antecedents get confusing. It is recommendeded to set the parameter to a reasonable value when creating the Database
object. This should lead to dramatic performance improvements (and memory savings). Note that you can safely use a low
parameter value. Results will still be correct even if transactions have more than *max_antecedents_length* items.

- `min_occurrences` controls how many occurences are needed at minimum for consideration. In many cases, you would
filter out results with too few occurences anyway. Setting a min_occurences value can speed up things because less data
is generated.

- `min_confidence` (and other min... settings) are similar to min_occurences. It's just another way to filter results.
You are likely not interested in rules with low confidences anyway. So filtering them out will reduce data that needs to
be processed and hence speed up things.

Besides, it is always a good idea not to pass irrelevant data to ambre. You are probably not interested in data coming
from technical fields such as "created_at", "is_deleted" etc. Removing/not passing such data will improve ambre's
performance.

In some cases you may also be able to group individual items to a group. Grouped items mean less items, and the less
items you have, the faster is ambre because it needs to deal with less data then.

If performance is still not sufficient, you can also try distributing the training, as suggested above.


## Disclaimer
As always - feel free to use but don't blame me if things go wrong.