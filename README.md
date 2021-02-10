# ambre

ambre is a package for association mining based rules extraction. Give it your data and tell it what
consequences you are interested in, and it will tell you which factors lead to these consequences.

Find out why things are how they are.

## Installation

The package is not available on PyPI yet. To install, run `pip install -e .` in folder `packages/ambre`.

## Usage Example

```python
import pandas as pd
from IPython.display import display

from ambre import Database

# load the famous titanic dataset and add the passengers that survived into our Database
database = Database(["Survived:0"], max_antecedents_length=3)
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
```

## Disclaimer
As always - feel free to use but don't blame me if things go wrong.