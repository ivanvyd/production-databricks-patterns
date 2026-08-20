# production-databricks-patterns

Template repository for the *Production Databricks Notes* series. A starting
point, not a framework, and deliberately small enough to read in one sitting.

The layout here is the one described in [Treating Databricks Projects as Software
Products](https://compiletheory.com/articles/databricks-projects-software-products).

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

`tests/unit/test_idempotence.py` holds four that the happy path cannot catch:

- reprocessing the same events produces no further change
- shuffling arrival order produces the same final state
- a duplicate carrying the same sequence value is a no-op
- 19.99 becomes 1999 cents and not 1998, which is what a double gives you

`tests/integration/test_reconciliation.py` covers the orphan case: a worker that
crashes between submitting to the platform and recording the run ID. That
sequence produces duplicate execution in production and is invisible to every
happy-path test. Its two fixtures are stubs in `tests/integration/conftest.py`;
the tests skip until you point them at a disposable environment.

## Commands

```bash
databricks bundle validate -t prod   # parse, resolve, check against the API
databricks bundle plan     -t prod   # what a deploy would change
databricks bundle deploy   -t prod
databricks bundle run      -t prod orders_cdc_job
databricks bundle destroy  -t dev    # dev only, never wire this to prod
```

## CI

`.github/workflows/ci.yml` runs the unit suite everywhere. `bundle validate` and
the daily drift check need a workspace, so they run only when
`DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` are set as repository
secrets, and skip otherwise. Both commands authenticate before they resolve
anything, there is no offline mode, and a fork never receives secrets at all - so
without the gate this repository would go red every night for a reason nobody
forking it could fix.

Setting the secrets is necessary but not sufficient: the workspace hosts in
`databricks.yml` are placeholders, and the two jobs fail on an unresolvable host
until you replace them.

## Before you deploy this anywhere real

Replace the workspace hosts and the service principal application IDs in
`databricks.yml`, and create the groups referenced in
`resources/orders_pipeline.yml`. `run_as.service_principal_name` wants the
application ID, not the display name - a display name validates and then fails at
deploy. The bundle grants to groups only; if you need an individual, make a group
with one member so the exception is visible in review.
