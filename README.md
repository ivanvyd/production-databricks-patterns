# production-databricks-patterns

Template repository for the *Production Databricks Notes* series. A starting
point, not a framework, and deliberately small enough to read in one sitting.

## What is here

```
databricks.yml          bundle definition, dev / staging / prod targets
src/transforms.py       plain functions, no cluster needed to test
src/pipelines/          thin entry points that call into src/
resources/              job, pipeline and permission definitions
tests/unit/             the failure tests, run per commit
tests/integration/      run against a disposable environment
docs/decisions/         architecture decision records
docs/evidence/          release evidence, one file per release
.github/workflows/      unit tests, bundle validate, scheduled drift check
```

## The point of the structure

Transformation logic lives in `src/` as importable Python. Notebooks and pipeline
files are thin entry points. That single split converts the test suite from
"slow, needs infrastructure" to "runs in CI in seconds", which decides whether
tests run per commit or per quarter.

## The tests worth having

`tests/unit/test_idempotence.py` holds three that the happy path cannot catch:

- reprocessing the same events produces no further change
- shuffling arrival order produces the same final state
- a duplicate carrying the same sequence value is a no-op

`tests/integration/test_reconciliation.py` covers the orphan case: a worker that
crashes between submitting to the platform and recording the run ID. That
sequence produces duplicate execution in production and is invisible to every
happy-path test.

## Commands

```bash
databricks bundle validate -t prod   # parse, resolve, check against the API
databricks bundle plan     -t prod   # what a deploy would change
databricks bundle deploy   -t prod
databricks bundle run      -t prod orders_cdc_job
databricks bundle destroy  -t dev    # dev only, never wire this to prod
```

## Before you deploy this anywhere real

Replace the workspace hosts and service principal names in `databricks.yml`,
and create the groups referenced in `resources/orders_pipeline.yml`. The bundle
grants to groups only; if you need an individual, make a group with one member
so the exception is visible in review.
