# Contracts

This package contains versioned, implementation-neutral schemas exchanged between the world, agent service, experiment tooling, and stored run records.

Schema validation and compatibility tests belong to this package. Consumers must not create private variants of shared protocol messages.

## Schema, writer, and loader alignment

A schema is the contract for every producer and consumer, including loaders and recorders:

- If a loader indexes a field, the schema must require it or the loader must report its absence as a validation diagnostic. A schema-valid record must not raise `KeyError` or a type error before `validate()` runs.
- A writer must reject schema-invalid records and enforce the same ordering, uniqueness, and identity invariants as the readback validator.
- A reader must independently validate the persisted record; write-time checks alone are not evidence that the stored stream is valid.

Run records in particular must keep `event.id` unique within a run and reject duplicate identifiers before writing.
