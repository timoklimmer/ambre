"""Initial example snippet. Shows how to use ambre in pyspark."""

# TODO: remove hardcoded values
# TODO: allow all other param values as well

from math import ceil

from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

from ambre import Database


def derive_rules_from_spark_dataframe(spark_dataframe, sort_result=True):
    """Use ambre to derive rules from the given spark dataframe."""
    consequents_of_interest = ["income=>50K"]
    max_antecedents_length = 2
    min_occurrences = 30
    min_confidence = 0.7
    target_batch_size = 100000

    def _derive_rules_by_group(group_df):
        database = Database(consequents_of_interest, max_antecedents_length=max_antecedents_length)
        database.insert_from_pandas_dataframe_rows(group_df, show_progress=False)
        return database.derive_rules_pandas(min_occurrences=min_occurrences, min_confidence=min_confidence)

    # slice the dataframe into groups and derive rules for each group
    number_of_groups = ceil(df.count() / target_batch_size)
    group_by = spark_dataframe.groupBy(
        ((F.rand() * number_of_groups) % number_of_groups).cast("bigint").alias("group_id")
    )
    non_aggregated_rules = group_by.applyInPandas(
        _derive_rules_by_group,
        schema=StructType(
            [
                StructField("antecedents", StringType(), False),
                StructField("consequents", StringType(), False),
                StructField("confidence", DoubleType(), False),
                StructField("lift", DoubleType(), False),
                StructField("occurrences", LongType(), False),
                StructField("support", DoubleType(), False),
                StructField("antecedents_length", LongType(), False),
            ]
        ),
    )

    # aggregate the rules so each rule occurs only once (only if we are partitioning)
    if number_of_groups > 1:
        aggregated_rules = non_aggregated_rules.groupBy("antecedents", "consequents").agg(
            (
                F.sum(non_aggregated_rules.confidence * non_aggregated_rules.occurrences)
                / F.sum(non_aggregated_rules.occurrences)
            ).alias("confidence"),
            (
                F.sum(non_aggregated_rules.lift * non_aggregated_rules.occurrences)
                / F.sum(non_aggregated_rules.occurrences)
            ).alias("lift"),
            F.sum("occurrences").alias("occurrences"),
            (
                F.sum(non_aggregated_rules.support * non_aggregated_rules.occurrences)
                / F.sum(non_aggregated_rules.occurrences)
            ).alias("support"),
            F.first("antecedents_length").alias("antecedents_length"),
        )
    else:
        aggregated_rules = non_aggregated_rules

    # return the result
    if sort_result:
        return aggregated_rules.orderBy(F.col("confidence").desc(), F.col("occurrences").desc())
    else:
        return aggregated_rules
