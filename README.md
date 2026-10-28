# Assignment 10: From Vulnerability to Ticket

Code:You Assignment 10. This extends the Ironclad Unified Inventory CLI. It downloads vulnerability findings, matches them to assets, and creates Trello cards for the findings that should be fixed.

**Author:** Jean Irakiza  
**Course:** Code:You  
**Board:** [Trello board](https://trello.com/b/HrXtpD15/s)

## What it does

1. Pulls findings from the Mockaroo API at `https://my.api.mockaroo.com/ironclad/vulns/findings.json`. That endpoint returns 250 findings.
2. Matches each finding to an asset by hostname or IP.
3. Labels severity from the CVSS score, using the CVSS v3.1 ranges.
4. Picks which findings get a ticket from severity, exploit availability, and the asset environment.
5. Creates a Trello card and sets a due date from the score.

The `ticket` command does not call NetBox, Qualys, or CrowdStrike. `main.py` keeps a stub inventory of 9 assets whose hostnames and IPs show up in the Mockaroo data. `--source` is only printed (`Pulling from <source>... (stub)`). The same 9 assets are loaded every time.

## Setup

Python 3.10 or newer. The only extra package is `requests`, used for Mockaroo and Trello. The CLI uses `argparse` and `datetime` from the standard library.

```bash
python -m venv venv
source venv/bin/activate
pip install requests
```

Export credentials in the shell before you run it. Use your own values. They are not stored in the code.

```bash
export IRONCLAD_API_KEY="your_api_key"
export TRELLO_KEY="your_key"
export TRELLO_TOKEN="your_token"
export TRELLO_LIST_ID="your_list_id"
```

`IRONCLAD_API_KEY` is sent as the `X-API-Key` header. The `ticket` command raises an error if it is missing. `TrelloClient` raises an error if `TRELLO_KEY`, `TRELLO_TOKEN`, or `TRELLO_LIST_ID` is missing.

## Usage

```bash
python main.py ticket --limit 5
```

- `--limit` — maximum cards to create. Default is `20`.
- `--source` — `netbox`, `qualys`, `crowdstrike`, or `all`. Default is `all`.

Example:

```text
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

When `--limit` is hit, the command stops and prints that summary for the findings it has processed so far: tickets created, findings skipped, and a count by severity.

## Files

- `main.py` — CLI entry point. Loads the stub inventory, fetches findings, creates cards, skips a hostname and CVE already seen in that run, and prints the summary.
- `vulnerability.py` — turns one API record into a `Vulnerability`. `severity` is a property computed from `cvss_score`. `key()` is `asset_hostname|cve_id`.
- `vulnerability_source.py` — GETs the Mockaroo JSON and builds `Vulnerability` objects. It expects a list.
- `vulnerability_attach.py` — indexes findings by hostname and IP, then attaches them to assets. A finding already attached by hostname is not added again on an IP match.
- `prioritization.py` — `should_ticket(asset, vuln)` decides if a finding gets a card.
- `ticket_builder.py` — card title, markdown description, and ISO 8601 due date.
- `trello_client.py` — reads the Trello env vars and POSTs the card to `https://api.trello.com/1/cards`.

`asset.py`, `inventory_manager.py`, and `inventory_source.py` are the inventory classes for NetBox, Qualys, and CrowdStrike. The `ticket` command does not import them. It uses the stub `Asset` and `InventoryManager` in `main.py`.

## Which findings get a ticket

`should_ticket` in `prioritization.py`:

| Severity | CVSS | Ticket? |
| --- | --- | --- |
| Critical | 9.0 – 10.0 | Yes |
| High | 7.0 – 8.9 | Yes |
| Medium | 4.0 – 6.9 | Only if `exploit_available` is true and the asset `environment` is `prod` |
| Low | 0.0 – 3.9 | No |
| Unknown | score missing or not a number | No |
| `false_positive`, `closed`, or `mitigated` | any | No |

Status and environment are compared in lowercase. A critical finding still gets no ticket if its status is one of those three.

`Vulnerability.severity` uses the same CVSS cutoffs:

```python
if self.cvss_score is None:
    return "unknown"
score = float(self.cvss_score)
if score >= 9.0:
    return "critical"
elif score >= 7.0:
    return "high"
elif score >= 4.0:
    return "medium"
else:
    return "low"
```

A missing CVSS score stays `unknown` and is not ticketed.

## Due dates

`ticket_builder.py` sets Trello's `due` field from the CVSS score:

- Critical (9.0 and up): 7 days from now
- High (7.0 – 8.9): 14 days from now
- Medium (4.0 – 6.9): 30 days from now

The value is `datetime.now()` plus that many days, formatted as ISO 8601. Low findings are not ticketed, so they do not get a due date.

## Duplicates

Each run keeps a `seen_keys` set of `Vulnerability.key()` values (`asset_hostname|cve_id`). If that pair shows up again, the CLI does not create another card.

## Card text

The title looks like `[HIGH] CVE-2021-15740 on npr.org`. The description lists hostname, IP, OS, environment, owner, source, CVE, title, severity, CVSS, whether an exploit is available, status, and the recommended fix.

## Notes

- The Mockaroo key and the Trello key, token, and list id are read from the environment. They are not hardcoded.
- `--limit` caps how many cards one run creates.
- The stub asset list is in `main.py`, so matching works without the Assignment 9 inventory sources.
