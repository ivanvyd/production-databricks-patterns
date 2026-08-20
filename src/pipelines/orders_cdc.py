"""Orders CDC pipeline.

Thin entry point. Every decision that could be wrong lives in src/transforms.py
where it can be unit tested without a cluster.
"""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from src.transforms import normalise_orders, sequence_expr

SOURCE = spark.conf.get("source_schema", "raw")


@dp.temporary_view
def orders_raw():
    return spark.readStream.table(f"{SOURCE}.orders_cdf")


@dp.temporary_view
@dp.expect_or_fail("sequence_not_null", "updated_at IS NOT NULL AND source_lsn IS NOT NULL")
@dp.expect_or_drop("tenant_present", "tenant_id IS NOT NULL")
# `amount` is gone by the time this evaluates: normalise_orders derives
# `amount_cents` and drops it.
@dp.expect("amount_non_negative", "amount_cents >= 0")
def orders_clean():
    return normalise_orders(spark.readStream.table("orders_raw"))


dp.create_streaming_table("orders_current")

dp.create_auto_cdc_flow(
    target="orders_current",
    # tenant_id is in the key because a key unique in the source but not in the
    # change feed is a cross-tenant data leak that presents as a quality problem.
    keys=["tenant_id", "order_id"],
    source="orders_clean",
    sequence_by=sequence_expr(),
    apply_as_deletes=F.expr("operation = 'DELETE'"),
    except_column_list=["operation", "source_lsn"],
    stored_as_scd_type="2",
    # Without this, a change to any column opens a new version, including columns
    # nobody analyses.
    track_history_except_column_list=["ingested_at", "etl_batch_id"],
)
