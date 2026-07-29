# The promotion path, end to end

A written walkthrough of one change moving from a laptop to production, with the commands and what
each one proves. Companion to the *Treating Databricks Projects as Software Products* article.

## 0. The change

Suppose the reliability contract changes: amounts must now be stored in integer cents. The edit
lands in one place, `src/transforms.py`, because that is the point of the structure: the logic is
importable and the pipeline file is a thin entry point.

## 1. Prove it locally, without a cluster

```bash
pytest tests/unit -m "not integration"
```

Seconds, not minutes. The suite includes the three failure tests: reprocessing the same events
changes nothing, shuffled arrival order produces the same final state, and a duplicate carrying the
same sequence value is a no-op. If your change breaks idempotence, it fails here, on your machine,
before any infrastructure is involved.

## 2. Prove the bundle still describes a deployable system

```bash
databricks bundle validate -t dev
```

This catches a misspelled resource type or an unresolved variable. It checks configuration, not
deployed state, and that distinction matters later.

## 3. Deploy to dev, which is deliberately not like prod

```bash
databricks bundle deploy -t dev
databricks bundle run    -t dev orders_cdc_job
```

`mode: development` prefixes every resource with your name and pauses schedules, so your copy exists
alongside everyone else's and never runs on the production cadence. Run it once by hand, look at the
result.

## 4. Open the pull request

CI runs the unit tests and `bundle validate` for staging and prod. A reviewer reads a diff of plain
Python, not a diff of serialised notebook cells.

## 5. See what the deploy would do before it does it

```bash
databricks bundle plan -t staging -o json > plan.json
```

`plan` shows the actions a deploy would perform against what is currently deployed. This is the
reviewed artefact: the reviewer approves not just the code but the set of changes about to happen to
the environment.

## 6. Promote

```bash
databricks bundle deploy -t staging   # then smoke tests
databricks bundle deploy -t prod     # same bundle, different resolved target
```

The same artefact moves through every stage. `mode: production` enforces what dev tolerated: no
user-specific paths, `run_as` a service principal, every pipeline `development: false`. A bundle
that deploys from a laptop but fails here is the check working, not failing.

## 7. Leave evidence

Record in `docs/evidence/` per release: commit, test results, the plan file, who approved, deploy
timestamp and identity, smoke outcome. Six months later this is how you find which release
introduced the wrong number without reconstructing history from memory.

## 8. Watch for drift

The scheduled CI job runs `databricks bundle plan -t prod` daily. A non-empty plan means someone
changed production by hand; the fix is to bring the change back into the repository, not to revert
someone's emergency.
