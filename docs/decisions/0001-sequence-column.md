# ADR 0001: Order CDC events by (updated_at, source_lsn)

Status: accepted
Date: 2026-08-10

## Context

`SEQUENCE BY` decides which version of a record wins. Four candidates were
available, each encoding a different claim about what "later" means.

## Decision

A struct of `updated_at` then `source_lsn`.

`updated_at` is the source system's own statement about when the row changed, so
ordering follows source chronology instead of arrival at our platform.
`source_lsn` breaks ties, which matter because `updated_at` has second resolution
and the source emits several changes per second per key under load.

## Consequences

Both fields carry a non-null expectation upstream of the CDC flow, because AUTO
CDC does not support NULL sequencing values and a nullable sequence column is a
latent failure rather than a configuration nuance.

The `__START_AT` / `__END_AT` columns on the SCD Type 2 target inherit the struct
type. History intervals are therefore readable as timestamps, which was weighted
above the alternative because the history table has business consumers.

Clock skew across source instances remains a known exposure. Accepted: the source
runs a single writer per tenant.
