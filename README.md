# <table><tr><td><img src="logo/logo_small.png"/><td>ambre</td></tr></table>

ambre is a package for association mining-based rules extraction. Long story short: **Give it your data, tell it what
consequents you are interested in, and it will tell you under which circumstances these consequents occur.**

The difference to traditional approaches is that it tells you more than just columns (or "factors"). It tells you which
*combinations* of *concrete* values lead to your outcomes of interest most frequently.

For instance, imagine you had to manage a production line. By using traditional approaches, you would learn eg. that
your vendors or the machine models used are a critical factor for defects. In contrast, ambre will tell you that a
defect occurs most likely when the vendor is *"ABC"* and when machine model *"XYZ"* is used. The information we get from
ambre can be more valuable than pure factors and can lead to more precise actions.

Besides, there is a feature to specify common sense knowledge. Let's assume you know already that machine model *XYZ*
produces one defect after another. With the common sense feature, you can tell ambre, and it will not create boring and
confusing rules for things you already know.

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

```python
import pandas as pd
from IPython.display import display

from ambre import Database

# load the famous titanic dataset and add the passengers that survived into our Database
# note: data does not have to be a pandas dataframe. there is also methods to add non-columnar data with varying
#       transaction sizes.
database = Database(["Survived:1"], max_antecedents_length=3)
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
database.insert_common_sense_rule(["parch:0"], ["survived:1"])
derived_rules = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7)
derived_rules = derived_rules.sort_values(by=["confidence", "occurrences"], ascending=[False, False])
display(derived_rules)
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

In some cases you may also be able to group individual items to aggregated items. Aggregated items mean less items, and
the less items you have, the faster is ambre because it needs to deal with less data then.


## Disclaimer
As always - feel free to use but don't blame me if things go wrong.