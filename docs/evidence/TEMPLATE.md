# Release evidence: <version or date>

Copy this file to `docs/evidence/<YYYY-MM-DD>-<target>.md` and fill it in as the
release happens, not afterwards. Six months later this is how you find which
release introduced the wrong number without reconstructing history from memory.

| Field | Value |
| --- | --- |
| Commit | `<sha>` |
| Target | `staging` / `prod` |
| Bundle CLI version | `<databricks version>` |
| Approved by | `<name>` |
| Deployed at | `<timestamp, timezone>` |
| Deployed by | `<service principal or user>` |

## Tests

```
<paste the output of `pytest tests/unit -m "not integration"`>
```

## Plan

The reviewed artefact is the set of changes about to happen to the environment,
not only the code diff.

```
<paste `databricks bundle plan -t <target>`, or attach plan.json>
```

## Smoke outcome

What was checked after the deploy, by whom, and what the result was. "Looked
fine" is not an outcome; name the table, the row count, or the run ID.

## Anything that went wrong

Including anything that went wrong and was then fixed. A clean record of a messy
release is worth more than a tidy record of a release that was not.
