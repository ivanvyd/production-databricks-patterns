"""Transformation logic as plain functions.

Nothing here imports a pipeline decorator or touches a cluster. That is the
point: this module is what makes the test suite run in CI in seconds instead of
requiring infrastructure, which decides whether tests run per commit or per
quarter.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def normalise_orders(df: DataFrame) -> DataFrame:
    """Conform a raw order feed to the silver contract."""
    return (
        df.withColumn("order_id", F.col("order_id").cast("string"))
        .withColumn("tenant_id", F.col("tenant_id").cast("string"))
        .withColumn("amount_cents", (F.col("amount") * 100).cast("bigint"))
        .drop("amount")
    )


def sequence_expr() -> F.Column:
    """The ordering claim, in one place.

    A struct so that ties on `updated_at` fall through to `source_lsn` instead of
    resolving arbitrarily. An unresolved tie means the same input can produce
    different output on a replay, which defeats the idempotence the pipeline
    exists for.

    NULL sequencing values are not supported by AUTO CDC, so the pipeline
    asserts non-null on both fields upstream of the flow.
    """
    return F.struct(F.col("updated_at"), F.col("source_lsn"))
