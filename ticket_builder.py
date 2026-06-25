from datetime import datetime, timedelta
from typing import Tuple, Optional

def build_ticket(asset, vuln) -> Tuple[str, str, Optional[str]]:
    title = f"[{vuln.severity.upper()}] {vuln.cve_id} on {asset.hostname}"

    due = None
    if vuln.cvss_score is not None:
        score = float(vuln.cvss_score)
        if score >= 9.0:
            due = (datetime.now() + timedelta(days=7)).isoformat()
        elif score >= 7.0:
            due = (datetime.now() + timedelta(days=14)).isoformat()
        elif score >= 4.0:
            due = (datetime.now() + timedelta(days=30)).isoformat()

    desc_lines = [
        "## Asset",
        f"- **Hostname:** {asset.hostname}",
        f"- **IP:** {getattr(asset, 'ip_address', 'n/a') or 'n/a'}",
        f"- **OS:** {getattr(asset, 'os', 'n/a') or 'n/a'}",
        f"- **Environment:** {getattr(asset, 'environment', 'n/a') or 'n/a'}",
        f"- **Owner:** {getattr(asset, 'owner_context', 'n/a') or 'n/a'}",
        f"- **Source:** {getattr(asset, 'source', 'n/a') or 'n/a'}",
        "",
        "## Vulnerability",
        f"- **CVE:** {vuln.cve_id}",
        f"- **Title:** {vuln.title}",
        f"- **Severity:** {vuln.severity}",
        f"- **CVSS:** {vuln.cvss_score if vuln.cvss_score is not None else 'n/a'}",
        f"- **Exploit available:** {vuln.exploit_available}",
        f"- **Status:** {vuln.status}",
        "",
        "## Recommended Fix",
        vuln.recommended_fix or "No fix guidance provided.",
        "",
        "## Auto-Generated Note",
        "This ticket was created by the Ironclad Unified Inventory CLI.",
    ]

    return title, "\n".join(desc_lines), due