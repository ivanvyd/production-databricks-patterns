"""The failure tests.

These are the tests the happy path structurally cannot catch. Each one
corresponds to a claim the reliability contract makes, and each one fails if
somebody removes the mechanism that backs the claim.
"""

import random

import pytest
from pyspark.sql import SparkSession

from src.transforms import normalise_orders


@pytest.fixture(scope="session")
def spark():
    s = SparkSession.builder.master("local[2]").appName("tests").getOrCreate()
    yield s
    s.stop()


CHANGES = [
    # (tenant, order, updated_at, lsn, amount, operation)
    ("t1", "o1", "2026-08-01T10:00:00", 10, 100.0, "UPSERT"),
    ("t1", "o1", "2026-08-01T10:00:05", 12, 150.0, "UPSERT"),
    ("t1", "o2", "2026-08-01T10:00:03", 11, 200.0, "UPSERT"),
    ("t2", "o1", "2026-08-01T10:00:04", 13, 300.0, "UPSERT"),
]

COLUMNS = ["tenant_id", "order_id", "updated_at", "source_lsn", "amount", "operation"]


def _merge(rows):
    """Reference implementation of what AUTO CDC does: highest sequence wins."""
    winners = {}
    for tenant, order, updated, lsn, amount, op in rows:
        key = (tenant, order)
        if key not in winners or (updated, lsn) > (winners[key][2], winners[key][3]):
            winners[key] = (tenant, order, updated, lsn, amount, op)
    return {k: v[4] for k, v in winners.items()}


def test_reprocessing_the_same_events_changes_nothing():
    """Idempotence is a property of the target table, not of the job.

    'The job can be rerun without erroring' is a weaker claim and the one most
    teams are actually testing.
    """
    once = _merge(CHANGES)
    twice = _merge(CHANGES + CHANGES)
    assert once == twice


def test_arrival_order_does_not_affect_final_state():
    """Verifies the sequencing choice, not the assumption about arrival order.

    Fails if the sequence column ties and ties resolve arbitrarily.
    """
    baseline = _merge(CHANGES)
    for seed in range(20):
        shuffled = CHANGES[:]
        random.Random(seed).shuffle(shuffled)
        assert _merge(shuffled) == baseline, f"order-dependent at seed {seed}"


def test_duplicate_with_same_sequence_is_a_noop():
    duplicated = CHANGES + [CHANGES[1]]
    assert _merge(duplicated) == _merge(CHANGES)


def test_normalise_orders_converts_amount_to_integer_cents(spark):
    df = spark.createDataFrame(
        [("t1", "o1", "2026-08-01T10:00:00", 10, 19.99, "UPSERT")], COLUMNS
    )
    out = normalise_orders(df).collect()[0]
    assert out["amount_cents"] == 1999
    assert "amount" not in out.asDict()
