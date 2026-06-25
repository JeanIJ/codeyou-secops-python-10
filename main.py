#!/usr/bin/env python3
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Working stub for this assignment ---
# We use a stub because the real Assignment 9 InventoryManager requires
# complex InventorySource objects that are outside the scope of this assignment.
# The stub uses hostnames that actually appear in the Mockaroo API data.

class Asset:
    def __init__(self, hostname="", ip_address="", os="", environment="", owner_context="", source=""):
        self.hostname = hostname
        self.ip_address = ip_address
        self.os = os
        self.environment = environment
        self.owner_context = owner_context
        self.source = source
        self.vulnerabilities = []

class InventoryManager:
    def __init__(self):
        # These hostnames/IPs come from the actual Mockaroo API output
        self.assets = [
            Asset("exblog.jp", "203.200.174.137", "Ubuntu 22.04", "prod", "IT Team", "netbox"),
            Asset("nymag.com", "16.36.224.168", "RHEL 9", "prod", "DB Team", "qualys"),
            Asset("npr.org", "236.156.35.199", "Windows 11", "office", "HR", "crowdstrike"),
            Asset("paginegialle.it", "254.133.139.35", "Ubuntu 20.04", "prod", "IT Team", "netbox"),
            Asset("miitbeian.gov.cn", "162.105.168.179", "CentOS 7", "prod", "DevOps", "qualys"),
            Asset("buzzfeed.com", "98.151.213.79", "Windows Server 2019", "prod", "Web Team", "crowdstrike"),
            Asset("spiegel.de", "251.4.137.113", "Debian 11", "office", "Content Team", "netbox"),
            Asset("mediafire.com", "3.108.62.242", "Ubuntu 22.04", "prod", "IT Team", "qualys"),
            Asset("g.co", "16.238.0.243", "Windows 10", "office", "Marketing", "crowdstrike"),
        ]
    def pull(self, source):
        print(f"Pulling from {source}... (stub)")

from vulnerability_source import VulnerabilitySource, VULN_API_URL
from vulnerability_attach import attach_vulnerabilities
from prioritization import should_ticket
from trello_client import TrelloClient
from ticket_builder import build_ticket

HEADERS = {"X-API-Key": "cf7bbbd0"}


def build_manager():
    return InventoryManager()


def print_summary(created: int, skipped: int, stats: dict) -> None:
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Tickets created: {created}")
    print(f"Findings skipped: {skipped}")
    print("\nBy Severity:")
    for sev in ["critical", "high", "medium", "low", "unknown"]:
        count = stats.get(sev, 0)
        if count > 0:
            print(f"  {sev.capitalize()}: {count}")


def cmd_ticket(args) -> None:
    print("=" * 50)
    print("IRONCLAD VULNERABILITY TICKETING")
    print("=" * 50)
    
    mgr = build_manager()
    mgr.pull(args.source)
    
    print(f"\nLoaded {len(mgr.assets)} assets.")
    
    vuln_src = VulnerabilitySource(VULN_API_URL, headers=HEADERS)
    vulns = vuln_src.fetch_vulns()
    print(f"Fetched {len(vulns)} vulnerabilities.")
    
    attach_vulnerabilities(mgr.assets, vulns)
    
    matched = sum(1 for a in mgr.assets if getattr(a, 'vulnerabilities', []))
    print(f"Matched to {matched} assets.")
    
    trello = TrelloClient()
    print("Trello client ready.")
    
    created = 0
    skipped = 0
    stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    seen_keys = set()
    
    for asset in mgr.assets:
        for v in getattr(asset, 'vulnerabilities', []):
            stats[v.severity] = stats.get(v.severity, 0) + 1
            
            if v.key() in seen_keys:
                continue
            seen_keys.add(v.key())
            
            if should_ticket(asset, v):
                title, desc, due = build_ticket(asset, v)
                trello.create_card(name=title, desc=desc, due=due)
                created += 1
                print(f"  ✅ {title}")
                
                if args.limit and created >= args.limit:
                    print(f"\nLimit reached: {args.limit}")
                    print_summary(created, skipped, stats)
                    return
            else:
                skipped += 1
    
    print_summary(created, skipped, stats)


def main():
    parser = argparse.ArgumentParser(description="Ironclad Vulnerability Ticket CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    
    p_ticket = sub.add_parser("ticket", help="Create Trello tickets for prioritized vulns")
    p_ticket.add_argument("--source", choices=["netbox", "qualys", "crowdstrike", "all"], default="all")
    p_ticket.add_argument("--limit", type=int, default=20, help="Max cards to create")
    p_ticket.set_defaults(func=cmd_ticket)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()