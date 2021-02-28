"""Initial example snippet. Shows how to use ambre in pyspark."""

# TODO: remove hardcoded values
# TODO: allow all other param values as well


from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

from ambre import Database


def derive_rules_from_spark_dataframe(spark_dataframe, sort_result=True):
    """Use ambre to derive rules from the given spark dataframe."""
    max_antecedents_length = 2
    min_occurences = 30
    min_confidence = 0.7
    partition_by_column = "native-country"

    def _derive_rules_by_group(group_df):
        database = Database(["income=>50K"], max_antecedents_length=max_antecedents_length)
        database.insert_from_pandas_dataframe_rows(group_df, show_progress=False)
        return database.derive_rules_pandas(min_occurrences=min_occurences, min_confidence=min_confidence)

    # slice the dataframe into groups and derive rules for each group
    # TODO: check if we can use a more generic column for better balance
    group_by = spark_dataframe.groupBy(partition_by_column) if partition_by_column else spark_dataframe.groupBy()
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
    if partition_by_column:
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
