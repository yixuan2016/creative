# Capture Runtime and Connector Tests

Run from the repository root:

```bash
python -m unittest discover -s runtime/tests -v
```

Tests use synthetic data, temporary local stores, and mocked DWS CLI / NDJSON processes only. They do not require a real DWS login and do not verify tenant event delivery.

The 0.5.1 release contains 53 Runtime + DWS Connector tests. The separate repository-wide regression suites are documented in `reports/PDKS_0.5.1_VALIDATION_REPORT.md`.
