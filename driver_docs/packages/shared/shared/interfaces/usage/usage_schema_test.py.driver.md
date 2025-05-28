# Purpose
This Python file is a test suite using the `pytest` framework to validate the functionality of a usage tracking system, specifically focusing on the conversion and computation of usage metrics in different units (SLOC and BYTES). The code defines several `pytest` fixtures to set up initial conditions for `UsageBalance` and `UsageEventSummary` objects, which represent usage data in terms of credits and debits. The tests cover various scenarios, including conversion between units, balance calculations, and validation of date ranges for usage events. The file provides narrow functionality, focusing solely on testing the correctness of usage metric conversions and computations, ensuring that the system behaves as expected under different conditions.
# Imports and Dependencies

---
- `datetime`
- `pytest`
- `dateutil`
- `pydantic`
- `shared.interfaces.usage.usage_schema`
- `shared.usage.utils`


