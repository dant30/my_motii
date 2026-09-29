# my_motii_shared

Shared Python contracts used by the Django core and API edge: domain value objects, identifiers,
tenant context, events, schemas, security helpers, storage adapters, caching, logging, permissions,
and throttling.

The package is installed with the backend requirements from the repository root:

```powershell
python -m pip install -r backend\requirements\development.txt
```

Money is represented as integer minor units with explicit currency precision. Quantity arithmetic
uses `Decimal` and requires matching unit codes. Tenant-owned cache/query helpers require an
explicit tenant identity. The Django abstract models live in `my_motii_shared.db_models`; the
`backend/core/apps/common` modules are compatibility re-exports.

Run the shared package tests from the repository root:

```powershell
pytest backend\shared\tests
```
