<p align="center">
    <img src="logo/logo_small.png"/>
</p>

# ambre

ambre is a package for association mining-based rules extraction. It processes your data and extracts rules of interest
for you, in the form of:

<p align="center">
<i><b>which factors</b> (identified for you by ambre) <b>--lead to--></b> <b>which outcomes of interest</b> (defined by
you)
<br/>
at confidence = x%, with support = n cases
</i>
</p>

**To put in a nutshell: Give it your data, and it tells you under which circumstances your outcomes of interest occur.**

In contrast to other approaches like deriving feature importances, it tells you more than just columns and their
influence on outcomes. Instead, it tells you exactly which *combinations* of *concrete* values lead to your outcomes,
together with tangible statistics that let you easily retrace results.

Extracted rules are minimal. Besides, there are multiple settings to control the rule extraction. In practice, that
means that you can concentrate on the rules that really matter (also read *Common Sense Filter* below).

**ambre is here to help you find the needle in the haystack -- fast and actionable.**

## Example Use Cases
### Reduce Defects in a Production Line
For instance, imagine you had to manage a production line, and your production produces too many defects. Through
traditional machine learning approaches, you would learn for example that (a) your machine vendors as well as (b) the
material used are highly correlated with the number of defects encountered.

Contrary, ambre would tell you that a defect occurs at a confidence of 83% when the vendor is *"Litware Inc."* and
material "Nylon 23A-B" is used, having seen 1.234 cases of that in your data.

Because ambre's output is more detailed, the information we get from it is more valuable than pure importances of
factors.

### Increase Customer Satisfaction of a Service Desk
Another example: imagine you were responsible for a service desk. Your CSAT score is terribly low, and you need more
insight into where you can take targeted countermeasures. One option is to sift through numerous reports and try to find
exactly that one bar chart which makes your life good again. The other option is to feed ambre with your feedback and
ticket data. Once fed, ambre can show you in a snap where to look at and prioritize.

## More Highlights
### Common Sense Filter
To increase usability, ambre has a feature to filter out common sense knowledge. Let's assume you know already that
machine model *XYZ* produces one defect after another. With the common sense feature, you can tell ambre that you know
that already, and when it generates rules next time, it does not bother you with information you already have.

### Online / Distributed / Federated
When loading data into ambre, you don't have to feed it with batch data. You can add additional individual transactions
whenever desired. Because ambre's databases can be stored to files (and even byte arrays), it can easily be used for
online machine learning solutions. Databases can also be merged, which enables distributed training and federated
learning architectures.

### No Tables Required
ambre databases are populated with so-called "transactions". A transaction (aka. "itemset") is a set of items that
belong together and form a case/data point. An example transaction for the production line case mentioned above could be:
`{"Litware Inc.", "Nylon 23A-B", "Toronto Plant", "Nightshift", "CW23", "Hole"}`. Unlike with tables where each row has
a fixed set of items (= the cells in the row), ambre accepts arbitrary-sized transactions. Simply add what you know
about the respective case, and ambre will find the rules for you.

### Frequent Itemsets
ambre's main purpose is to extract rules. The required data structure underneath is however well suited for frequent
itemset mining, too. In case you are looking for a frequent itemset mining solution "only", you can also use ambre for
it.


## Installation

### pip / GitHub

The package is not available on PyPI yet but can be installed from GitHub via *pip* directly.

To install the latest stable release, run

`pip install --upgrade git+https://github.com/timoklimmer/ambre.git@latest#subdirectory=packages/ambre`

Alternatively, if you want to install a specific version, simply specify that specific version instead of "latest".

`pip install --upgrade git+https://github.com/timoklimmer/ambre.git@v1.0.0#subdirectory=packages/ambre`

If you like living on the edge, you can also install the very newest code by running

`pip install --upgrade git+https://github.com/timoklimmer/ambre.git#subdirectory=packages/ambre`

In case you want to install via a `requirements.txt` file, add the respective `git+https://github.com/...` part in
a new line of that file.

### Source Code

To install from source code, clone the repository or download the code and run `pip install -e .` in folder
`packages/ambre`.


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
# notes: - data does not have to be a pandas dataframe. there is also methods to add non-columnar data with varying
#          transaction sizes such as insert_transactions().
#        - we are using "Survived=1" here because we want to know under which conditions people survived best, ie.
#          when column "Survived" has value 1.
print("Loading data...")
database = Database(["Survived=1"], max_antecedents_length=3)
database.insert_from_pandas_dataframe_rows(
    pd.read_csv("packages/ambre/tests/datasets/titanic.csv"),
    input_columns=["Survived", "Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"],
)

# derive frequent itemsets
print("Deriving frequent itemsets...")
derived_itemsets = (
    database.derive_frequent_itemsets_pandas()
    .sort_values(by=["occurrences", "itemset_length"], ascending=[False, True])
    .reset_index(drop=True)
)
display(derived_itemsets)

# derive rules
print("Deriving rules...")
derived_rules = database.derive_rules_pandas(min_occurrences=30, min_confidence=0.7)
derived_rules = derived_rules.sort_values(by=["confidence", "occurrences"], ascending=[False, False]).reset_index(
    drop=True
)
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

### Distributed / Federated Training
```python
from IPython.display import display

from ambre import Database

# populate first database in a fictive process or location 1
database1 = Database(["bread", "milk"])
database1.insert_transaction(["milk", "bread"])
database1.insert_transaction(["butter"])
# optionally save the database either to a file or byte array as needed
# file       : database1.save_to_file("database1.ambre.db")
# byte array : database1_as_byte_array = database1.as_bytes()

# populate second database in a fictive process or location 2
database2 = Database(["bread", "milk"])
database2.insert_transaction(["bread", "coke"])
database2.insert_transaction(["milk", "honey"])
# optionally save database, similar to above

# populate third database in a fictive process or location 3
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
ambre can bring valuable benefits for business, but under certain circumstances its runtime performance might not meet
your needs. Compared to other machine learning algorithms, it has to create a lot of combinations and store them in an
internal trie data structure. This can take a lot of time, and it seems there is no workaround or smarter method yet.

The good news is that ambre's performance is highly dependent on its configuration. To improve ambre's performance, you
can set a couple of parameters when creating the database and/or later when using the database.

Whenever possible, you should prefer to set the parameters at the database level, because that helps filter data as
early as possible, avoiding unnecessary workload at later steps. Note however that some parameters can only be set at
the respective methods used after the database has been populated.

- `max_antecedents_length` (integer) controls how many antecedents are returned per rule at maximum when frequent
itemsets or rules are generated. In most of the cases, you are only interested in maybe 3 or 5 antecedents anyway
because results with more antecedents get confusing. It is recommended to set the parameter to a reasonable value when creating the Database object. Setting max_antecedents_length right can bring dramatic performance improvements (and
memory savings). Note that you can safely use a low parameter value. Results will still be correct, it will just not generate rules with more than the specified antecedents.

- `min_occurrences` (integer) controls how many occurences are needed at minimum for consideration. In many cases, you
would filter out results with too few occurences anyway. Setting a min_occurences value can speed up things because less
data is generated.

- `min_confidence` (and other min... settings) (number between 0 and 1) are similar to min_occurences. It's just another
way to filter results. You are likely not interested in rules with low confidences anyway. So filtering them out will
reduce data that needs to be processed and hence speed up things.

- `item_alphabet` (string) defines which characters can be used in the item names. ambre has a feature which compresses
item names internally, to save memory. If you already know that your item names contain only alphanumeric characters,
for example, you can set this parameter for example to `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`. The more narrow the item alphabet, the more memory savings and performance. You can specify any unique sequence of characters here. To completely disable item compression, set this parameter to None.

- `case_insensitive` (bool) controls whether casing is relevant or not. By default, ambre has this parameter set to
TRUE. If you change it to FALSE - meaning that you differentiate between upper and lower case letters - be sure that you
actually need it. Case insensitivity needs less memory and performs faster.

Furthermore, it is always a good idea not to pass irrelevant data to ambre. You are probably not interested in data
coming from technical fields such as "created_at", "is_deleted" etc. Removing/not passing such data will improve ambre's
performance.

Similarly, the shorter the item names are in your transactions, the better. Also, prefer short column names over longer ones when memory becomes an issue.

In some cases you may also be able to group individual items to a group. Grouped items mean less items, and the less
items you have, the faster is ambre because it needs to deal with less data then.

If performance is still not sufficient, you can also try distributing the training, as suggested above.


## Disclaimer
As always - feel free to use but don't blame me if things go wrong.