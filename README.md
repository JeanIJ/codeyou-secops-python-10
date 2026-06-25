


# Assignment 10: From Vulnerability to Ticket

**Jean Irakiza**


**Code:You**


**Board:** [Trello Board](https://trello.com/b/HrXtpD15/s)

---

## Overview

This project extends the Ironclad Unified Inventory CLI to operationalize vulnerability management. It bridges the gap between **visibility** (knowing what is vulnerable) and **action** (creating remediation tickets).

The system:

1. Pulls 250 vulnerability findings from a Mockaroo REST API
2. Correlates findings to known inventory assets by hostname and IP
3. Derives severity from CVSS scores using standard v3.1 ranges
4. Applies risk-based prioritization logic (severity + exploit availability + environment)
5. Automatically creates Trello cards representing remediation tickets with SLA due dates

---

## Architecture

**plain**

```plain
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  Mockaroo API   │────▶│  Python CLI Engine   │────▶│  Trello Board   │
│  (250 vulns)    │     │  - correlate         │     │  (Tickets)      │
└─────────────────┘     │  - prioritize        │     └─────────────────┘
                          │  - ticket            │
                          └─────────────────────┘
```

**Table**

| File                        | Responsibility                                                                   |
| :-------------------------- | :------------------------------------------------------------------------------- |
| `vulnerability.py`        | Data model: parses raw API records into structured`Vulnerability`objects       |
| `vulnerability_source.py` | HTTP client: fetches and validates JSON from the Mockaroo endpoint               |
| `vulnerability_attach.py` | Correlation engine: indexes vulns by hostname/IP and attaches them to assets     |
| `prioritization.py`       | Decision engine: determines which findings deserve tickets based on risk context |
| `trello_client.py`        | Integration layer: authenticates and POSTs cards to Trello REST API              |
| `ticket_builder.py`       | Formatter: generates markdown descriptions and SLA due dates                     |
| `main.py`                 | Orchestrator: CLI entry point, metrics dashboard, duplicate prevention           |

---

## Prioritization Logic

> **Core principle: Severity ≠ Risk**

A vulnerability's CVSS score is only the starting point. Real security teams do not fix everything — they fix what matters in context.

**Table**

| Severity                          | CVSS Range  | Auto-Ticket?     | Exception / Escalation                                                            |
| :-------------------------------- | :---------- | :--------------- | :-------------------------------------------------------------------------------- |
| **Critical**                | 9.0 – 10.0 | ✅ Yes           | Immediate remediation required                                                    |
| **High**                    | 7.0 – 8.9  | ✅ Yes           | Patch within 14 days                                                              |
| **Medium**                  | 4.0 – 6.9  | ⚠️ Conditional | **Only**if`exploit_available=True` **AND**asset`environment=prod` |
| **Low**                     | 0.0 – 3.9  | ❌ No            | Too noisy; tracked but not ticketed                                               |
| **False Positive / Closed** | Any         | ❌ No            | Explicitly excluded to reduce alert fatigue                                       |

**Why this matters:** A Medium vulnerability with public exploit code on a production web server is more dangerous than a High vulnerability on an isolated development laptop. This logic simulates how enterprise vulnerability management programs (VMM) operate.

---

## Severity Derivation

CVSS scores are translated into human-readable severity labels using the industry-standard NIST v3.1 mapping:

**Python**

```python
if score >= 9.0:
    return "critical"
elif score >= 7.0:
    return "high"
elif score >= 4.0:
    return "medium"
else:
    return "low"
```

This is implemented as a `@property` on the `Vulnerability` class so severity is always current and derived dynamically from the raw score.

---

## Challenges Implemented

### 1. Duplicate Prevention

A `seen_keys` set tracks `(hostname|cve_id)` pairs during each run. If the same vulnerability appears on the same host twice, only one ticket is created. This prevents ticket spam and mimics deduplication logic in enterprise SOAR platforms.

### 2. SLA Enforcement

Due dates are automatically assigned based on severity:

* **Critical:** 7 days
* **High:** 14 days
* **Medium:** 30 days

These are passed to Trello's `due` parameter as ISO 8601 timestamps, creating accountability and measurable remediation timelines.

### 3. Metrics Dashboard

After every run, the CLI prints a summary:

**plain**

```plain
Tickets created: 5
Findings skipped: 6
By Severity:
  High: 2
  Medium: 5
  Low: 4
```

This gives leadership a snapshot of risk exposure and team workload without opening the Trello board.

---

## How to Run

**bash**

```bash
# 1. Navigate to project
cd ~/Documents/CodeYou_Projects/soc-assignment-10

# 2. Activate virtual environment
source venv/bin/activate

# 3. Export Trello credentials (never hardcode these)
export TRELLO_KEY="your_key"
export TRELLO_TOKEN="your_token"
export TRELLO_LIST_ID="6a3c5876ec6af73f6e367db0"

# 4. Execute with safety limit
python main.py ticket --limit 5
```

**Output Example:**

**plain**

```plain
==================================================
IRONCLAD VULNERABILITY TICKETING
==================================================
Pulling from all... (stub)

Loaded 9 assets.
Fetched 250 vulnerabilities.
Matched to 9 assets.
Trello client ready.
  ✅ [MEDIUM] CVE-2026-20641 on exblog.jp
  ✅ [HIGH] CVE-2021-15740 on npr.org
  ✅ [MEDIUM] CVE-2022-23371 on paginegialle.it
  ✅ [MEDIUM] CVE-2023-17889 on paginegialle.it
  ✅ [HIGH] CVE-2026-21611 on buzzfeed.com

Limit reached: 5

==================================================
SUMMARY
==================================================
Tickets created: 5
Findings skipped: 6

By Severity:
  High: 2
  Medium: 5
  Low: 4
```

---

## Security Notes

* **No secrets in code.** All Trello credentials are read from environment variables at runtime.
* **Rate limiting.** The `--limit` flag prevents accidental board flooding during testing.
* **Stub inventory.** The `InventoryManager` uses a lightweight stub populated with hostnames that match the Mockaroo dataset, ensuring correlation works without importing complex Assignment 9 dependencies.

---

## Deliverables

**Table**

| Requirement                                 | Status                   |
| :------------------------------------------ | :----------------------- |
| Updated CLI code                            | ✅ 7 Python modules      |
| Trello board screenshot                     | ✅ See board`HrXtpD15` |
| Terminal output (vuln count + ticket count) | ✅ Included above        |
| README explaining prioritization logic      | ✅ This document         |
| README explaining severity derivation       | ✅ This document         |
