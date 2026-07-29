"""Integration tests. Slower, and they catch what unit tests structurally cannot.

Run against a disposable environment. If recreating that environment requires a
human, it will drift from production and its results stop meaning anything.
"""

import pytest


@pytest.mark.integration
def test_orphan_run_is_reconciled(workspace, operation_store):
    """A worker that crashes between submitting and recording creates an orphan.

    This sequence produces duplicate execution in production and is invisible to
    every happy-path test.
    """
    op = operation_store.create(payload={"table": "orders"})
    run_id = workspace.submit_run(op.id, idempotency_token=op.id)

    # Simulate the crash: the platform has the run, our store does not.
    operation_store.forget_external_id(op.id)

    reconciled = workspace.reconcile_orphans(operation_store)

    assert run_id in reconciled, "orphan run was never reclaimed"
    assert operation_store.get(op.id).external_id == run_id


@pytest.mark.integration
def test_resubmitting_with_the_same_token_does_not_create_a_second_run(workspace):
    """Databricks guarantees exactly one run per idempotency_token (max 64 chars)."""
    token = "op-0f1e2d3c4b5a6978"
    first = workspace.submit_run("orders", idempotency_token=token)
    second = workspace.submit_run("orders", idempotency_token=token)
    assert first == second
