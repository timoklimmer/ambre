<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/logo_gh_readme_dark_mode.png">
  <img alt="ambre" src="images/logo_gh_readme_light_mode.png" style="display: block; margin-left: auto; margin-right: auto; width: 33%" />
</picture>

---

ambre is a Python package for "association mining-based rules extraction". In a nutshell: **Give it your data, and it
will teach you in which situations certain events are most likely to occur.**

<p align="center">
    <b>Outcome</b> <i>defined by you</i> ← is driven by <b>certain combinations of factors</b> <u><i>identified by ambre</i></u>
</p>

Unlike other approaches, ambre identifies more than just columns and their influence on outcomes. Instead, it finds
concrete value combinations leading to certain outcomes, accompanied by tangible statistics. For instance, ambre is able
to tell you (from unclear data) that a certain to-be-fixed defect occurs with a probability of 92% if the product has
has extra feature *XYZ*, and if it has been produced overnight.

Because ambre analyzes on a very detailed level, while filtering out "the noise", it helps you to derive very precise and targeted business decisions and actions.

**ambre is here to help find the needle in the haystack -- fast and actionable.**


## Example Use Cases
### Reduce Defects in a Production Line
Imagine you had to manage a production line, and your production produces too many defects. Through traditional machine
learning approaches, you may learn for example that your machine vendors as well as the used material are highly correlated with the number of defects encountered.

Contrary, ambre would tell you that a defect occurs at a confidence of 83% when the vendor is *"Litware Inc."* and
material "Nylon 23A-B" is used, having seen 1.234 cases of that in your data.

Because ambre's output is more detailed, the information we get from it is more valuable than pure importances of
factors.

### Increase Customer Satisfaction of a Service Desk
Another example: imagine you were responsible for a service desk. Your CSAT score is terribly low, and you need more
insight into where you can take targeted countermeasures. One option is to sift through numerous reports and try to find
exactly that one bar chart which makes your life good again. The other option is to feed ambre with data about your
tickets and related CSAT scores. Once fed, ambre can show you in a snap where the problematic patterns are.

### Identify Promising Research Directions
Let's imagine you were a researcher, and your goal was to explain why people develop a certain disease. Assuming you did not have an idea of where to go deeper in your research, you could collect some data of what you think might be
relevant.

After being fed with your data, ambre can extract relevant connections, helping you to find the areas where you should focus on. Because ambre automatically eliminates redundant rules, and because you can tell ambre about the rules you already know, it will quickly point you to the connections that matter for your work. Of course, ambre also gives you all the numbers it uses, so you can write comprehensible and reproducable papers.


## Selected Highlights of ambre
### No Tables Required
ambre "databases" are populated with so-called "transactions". A transaction (aka. "itemset") is a set of items that
belong together and form a case/data point. An example transaction for the production line case mentioned above could
be: `{"Litware Inc.", "Nylon 23A-B", "Toronto Plant", "Nightshift", "CW23", "Hole"}`. Unlike with tables, where each row
has a fixed set of items (= the cells in the row), ambre accepts arbitrary-sized transactions. **Simply add what you know
about the respective case, and ambre will find the rules for you.**

> Note: As of now, ambre supports only categorical ("string") data. For numerical data, it is recommended to convert the numbers to categories first. This is by intention to make sure that number ranges meet the domain and hence, the quality of the generated rules is not negatively affected. There might be a more automated support in future.

### Common Sense Filter
To increase usability, ambre has a feature to filter out common sense knowledge. Let's assume you know already that a
certain machine model produces one defect after another. With the common sense feature, you can **tell ambre that you know** that already, and when it generates rules next time, it does not bother you with information you already have.

### Online / Distributed / Federated
When loading data into ambre, you don't have to feed it with batch data. You can add additional individual transactions
whenever desired. Because ambre's databases can be stored to files (and even byte arrays), it can easily be used for
online machine learning solutions. Databases can also be merged, which enables distributed training and federated
learning architectures.

### Frequent Itemsets
ambre's main purpose is to extract rules that lead to certain outcomes of interest. However, the required data structure
underneath is well suited for frequent itemset mining, too. In case you are looking for a frequent itemset mining
solution "only", you can also use ambre for it (see examples below).

### Predictions
Once ambre has been given some data, it can also be used for predictions. One of the big advantages thereby is that it
can predict even if you don't have all necessary data to fill a table row of a fixed schema. By ambre, you can just give
it your factors ("antecedents"), and it will tell you - based on the data collected - at which probabilities the
outcomes ("consequents") will occur.


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

# load an updated version of the well-known German credit dataset into an ambre database
# note: we are using "credit_risk=bad" here because we want to learn when credit risk is bad
print("Loading data...")
database = Database(["credit_risk=bad"], max_antecedents_length=3)
database.insert_from_pandas_dataframe_rows(
    pd.read_csv("packages/ambre/tests/datasets/german-credit-eur.csv")
)

# derive rules
print("Deriving rules...")
derived_rules = database.derive_rules_pandas(min_confidence=0.9, min_occurrences=10)
derived_rules = derived_rules.sort_values(by=["confidence", "occurrences"], ascending=[False, False]).reset_index(
    drop=True
)
display(derived_rules)

# common sense rules
# Let's assume for the sake of the demo here that we know already that duration of 48 months leads to a bad credit risk.
# In that case, we can tell ambre about our common sense knowledge. When ambre knows about it, it will not generate
# rules with knowledge we have already. Btw: we can add as many common sense rules as we like.
print("Consider common sense knowledge...")
database.insert_common_sense_rule(["duration_in_months=48"], ["credit_risk=bad"])
derived_rules = database.derive_rules_pandas(min_confidence=0.9, min_occurrences=10)
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

### Predictions
```python
from IPython.display import display

from ambre import Database

# as always, we need a database first
database = Database(["smoker"])
database.insert_transaction(["smoker", "father smokes", "mother smokes", "poor diet", "adiposity"])
database.insert_transaction(["smoker", "good diet", "father smokes", "vegetarian", "single"])
database.insert_transaction(["non-smoker", "married", "meat lover", "adiposity"])
database.insert_transaction(["smoker", "married", "vegetarian", "father smokes"])
database.insert_transaction(["non-smoker", "good diet", "mother smokes", "likes parties"])
database.insert_transaction(["non-smoker", "vegetarian", "poor diet", "married"])
database.insert_transaction(["smoker", "single", "likes parties"])

# how likely is it that a person is a smoker given that he/she has adipositas and his/her father smokes?
display(database.predict_consequents_pandas(["adiposity", "father smokes"]))

# to skip unknown antecedents, use the skip_unknown_antecedents flag
display(database.predict_consequents_pandas(["adiposity", "hates smoking"], skip_unknown_antecedents=True))
```


## Glossary
|Term|Meaning|
|----|-------|
|Itemset|A set of items or states.|
|Transaction|A set of items that occur together, eg. a basket at a supermarket or all infos around a specific defect instance.|
|Database|Set of all transactions.|
|Frequent Itemset|A set of items that occurs frequently across all transactions.|
|Antecedent|Antecedents are items that lead to/are correlated with one or more consequents ("factors").|
|Consequent|An item which occurs because of/together with one or more antecedents ("outcomes").|
|Rule|Describes how well a certain set of antecedents leads to certain consequents.|
|Support|The proportion of transactions in the dataset which contain the respective itemset.|
|Confidence|Estimates the probability of finding a certain consequence under the condition that certain antecedents have been observed.|
|Lift|The support of the whole rule divided by the support expected under independence. Greater lift values indicate stronger assumptions.|


## Runtime Performance
For ambre to work, it needs a lot of data stored in an internal trie data structure. Setting up and processing that trie
can be time-consuming. The good news however is that ambre's performance is highly dependent on how you configure it.

Here are a few hints:

- To improve ambre's performance, you can set a couple of parameters when creating the database and/or later when using
the database. Whenever possible, you should prefer to set the parameters at the database level because that helps filter out data as early as possible, avoiding unnecessary workload at later steps. Note however that some parameters can only be set after the database has been populated.

- `max_antecedents_length` (integer) controls how many antecedents are returned per rule at maximum when frequent
itemsets or rules are generated. In most of the cases, you are only interested in maybe 3 or 5 antecedents anyway
because results with more antecedents get confusing. It is recommended to set the parameter to a reasonable value when
creating the Database object. Setting max_antecedents_length right can bring dramatic performance improvements (and
memory savings). Note that you can safely use a low parameter value. Results will still be correct, it will just not
generate rules with more than the specified antecedents.

- `min_occurrences` (integer) controls how many occurences are needed at minimum for consideration. In many cases, you
would filter out results with too few occurences anyway. Setting a min_occurences value can speed up things because less
data is generated.

- `min_confidence` (and other min... settings) (number between 0 and 1) are similar to min_occurences. It's just another
way to filter results. You are likely not interested in rules with low confidences anyway. So filtering them out will
reduce data that needs to be processed and hence speed up things.

- `item_alphabet` (string) defines which characters can be used in the item names. ambre has a feature which compresses
item names internally, to save memory. If you already know that your item names contain only alphanumeric characters,
for example, you can set this parameter for example to `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`. The more narrow the item
alphabet, the more memory savings and performance. You can specify any unique sequence of characters here. To completely
disable item compression, set this parameter to None.

- `case_insensitive` (bool) controls whether casing is relevant or not. By default, ambre has this parameter set to
TRUE. If you change it to FALSE - meaning that you differentiate between upper and lower case letters - be sure that you
actually need it. Case insensitivity needs less memory and performs faster.

- Furthermore, it is always a good idea not to pass irrelevant data to ambre. You are probably not interested in data
coming from technical fields such as "created_at", "is_deleted" etc. Removing/not passing such data will improve ambre's
performance. When using the `insert_from_pandas_dataframe_rows` method, you can use the `input_columns` parameter to
load only relevant columns.

- Similarly, the shorter the item names are in your transactions, the better. Also, prefer short column names over
longer ones when memory becomes an issue.

- In some cases you may also be able to group individual items to a group. Grouped items mean less items, and the less
items you have, the faster is ambre because it needs to deal with less data then.

- When the insert performance is a problem, distributing the training, as suggested above, can help.

- Depending on the use case, there may also be a way to work with multiple smaller databases instead of  a single big one.

- The newer your Python version, the better.

...and sometimes, your hardware may just not be fast or large enough. In that case, try to run ambre on a larger VM, ideally in Microsoft Azure ;-)

## Why "ambre"?
ambre stands for ***a***ssociation ***m***ining-***b***ased ***r***ules ***e***xtraction. Just in case you have ever
wondered 😉.

## Disclaimer
As always - feel free to use but don't blame me if things go wrong.

To avoid any misunderstandings: ambre is not an official Microsoft product.